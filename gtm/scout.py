"""BAML Migration Scout — CLI entry point.

Point it at a GitHub repo (or local path) and it'll:
  1. clone the repo (or read the local path),
  2. find every LLM call site via AST scanning,
  3. translate each to BAML and validate with baml-cli,
  4. emit a migration report.

Usage:
    uv run python scout.py https://github.com/owner/repo
    uv run python scout.py ./path/to/local/file_or_dir
    uv run python scout.py <target> --out ./output/custom_dir --benchmark
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import config
from providers import DEFAULT_PROVIDER, PROVIDER_NAMES, Provider, ProviderError, get_provider
from scanner import CallSite, iter_python_files, scan_file, scan_repo
from translator import (
    FreeQuotaExhausted,
    LLMClient,
    Translation,
    declared_names,
    load_keys_from_env,
    python_usage_snippet,
    seed_baml_examples,
    translate_site,
)
from validator import validate_baml_file, write_baml_project, run_generate
from reporter import build_context, render_report, write_patch_diff
from benchmark import benchmark_translation
from utils import configure_logging, get_logger


log = get_logger(__name__)


# Force UTF-8 stdout on Windows so rich can render box-drawing chars cleanly.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, io.UnsupportedOperation):
        pass

# Default to 140 cols when running in a pipe or narrow terminal — keeps the
# table readable in CI logs and shared screenshots without forcing the user's
# terminal width.
console = Console(width=max(shutil.get_terminal_size((140, 24)).columns, 140))


# -- target resolution -----------------------------------------------------


def _is_github_url(target: str) -> bool:
    if not target.startswith(("http://", "https://", "git@")):
        return False
    parsed = urlparse(target)
    return "github.com" in (parsed.netloc or target)


def _repo_name_from_url(url: str) -> str:
    tail = url.rstrip("/").split("/")[-1]
    if tail.endswith(".git"):
        tail = tail[:-4]
    return tail or "repo"


def _clone_repo(url: str, dest: Path) -> Path:
    """Shallow-clone a GitHub repo into dest. Uses git CLI for portability."""
    console.print(f"[dim]Cloning [bold]{url}[/bold] → {dest}[/dim]")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=config.TIMEOUT_GIT_CLONE,
        )
    except subprocess.TimeoutExpired:
        console.print(
            f"[red]git clone timed out after {config.TIMEOUT_GIT_CLONE}s.[/red] "
            "Network slow, or the repo is huge."
        )
        sys.exit(2)
    except FileNotFoundError:
        console.print("[red]git is not on PATH.[/red] Install Git and try again.")
        sys.exit(2)
    if result.returncode != 0:
        console.print(f"[red]git clone failed:[/red] {result.stderr.strip()}")
        sys.exit(2)
    return dest


def _resolve_target(target: str, workspace: Path) -> tuple[Path, str, bool]:
    """Return (repo_root, display_name, is_single_file)."""
    if _is_github_url(target):
        name = _repo_name_from_url(target)
        dest = workspace / name
        _clone_repo(target, dest)
        return dest, name, False

    p = Path(target).resolve()
    if not p.exists():
        console.print(f"[red]Path not found:[/red] {target}")
        sys.exit(2)

    if p.is_file():
        # Wrap the single file in a synthetic repo root so scanner.scan_repo
        # paths remain repo-relative and clean.
        return p.parent, p.name, True

    return p, p.name, False


# -- scan summary ----------------------------------------------------------


def _print_summary(sites: list[CallSite], target_label: str) -> None:
    if not sites:
        console.print(Panel.fit(
            f"No LLM call sites found in [bold]{target_label}[/bold].\n"
            "If this is unexpected, the AST scanner may not cover the framework in use yet.",
            border_style="yellow",
        ))
        return

    table = Table(
        title=f"Detected {len(sites)} LLM call site(s) in {target_label}",
        header_style="bold cyan",
        show_lines=False,
        expand=False,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Location", style="bold", no_wrap=True, overflow="fold")
    table.add_column("Pattern", no_wrap=True)
    table.add_column("Model", no_wrap=True)
    table.add_column("Schema", style="green", no_wrap=True)
    table.add_column("Retry", justify="center", no_wrap=True)
    table.add_column("Notes", style="dim", overflow="fold")

    for i, s in enumerate(sites, 1):
        schema_marker = "yes" if s.inferred_schema else ("-" if s.pattern_type != "instructor" else "?")
        retry = "yes" if s.retry_logic_present else ""
        notes = ", ".join(s.notes) if s.notes else ""
        table.add_row(
            str(i),
            s.display_id(),
            s.pattern_type,
            s.model_name or "—",
            schema_marker,
            retry,
            notes,
        )

    console.print(table)

    by_pattern: dict[str, int] = {}
    for s in sites:
        by_pattern[s.pattern_type] = by_pattern.get(s.pattern_type, 0) + 1
    summary = " · ".join(f"{k}: {v}" for k, v in sorted(by_pattern.items()))
    console.print(f"[dim]By pattern → {summary}[/dim]")


# -- translation orchestration ---------------------------------------------


_BAML_EXAMPLES_CACHE = Path(__file__).resolve().parent / "baml_examples.md"
_TRANSLATION_ATTEMPTS = config.TRANSLATION_RETRIES + 1  # initial + retries


def _translate_all(sites: list[CallSite], args, provider: Provider) -> tuple[list[Translation], dict]:
    """Translate every CallSite. Validates each output with baml-cli check
    and retries up to TRANSLATION_RETRIES times with the compiler error in context.
    """
    load_dotenv()
    keys = load_keys_from_env(provider)
    if not keys:
        signup_hint = (
            "Get a free key at https://aistudio.google.com/."
            if provider.name == "gemini"
            else f"Set the {provider.api_key_env} env var with your {provider.name} key."
        )
        console.print(Panel.fit(
            f"[red]{provider.api_key_env} is not set.[/red]\n\n"
            f"Create a .env file in the project root with:\n"
            f"  {provider.api_key_env}=your-key-here\n\n"
            f"{signup_hint}",
            border_style="red",
        ))
        sys.exit(2)

    console.print(f"[dim]Loaded {len(keys)} {provider.name} key(s) from .env[/dim]")
    examples = seed_baml_examples(_BAML_EXAMPLES_CACHE)
    console.print(f"[dim]Few-shot bundle: {len(examples):,} chars ({_BAML_EXAMPLES_CACHE.name})[/dim]")

    model = getattr(args, "model", None) or provider.default_model
    client = LLMClient(keys, provider=provider, model=model)
    results: list[Translation] = []
    used_names: dict[str, int] = {}
    taken_names: list[str] = []  # cross-translation: class/enum/fn names already taken

    for i, site in enumerate(sites, 1):
        console.print(
            f"[dim]({i}/{len(sites)})[/dim] translating "
            f"[bold]{site.display_id()}[/bold] [{site.pattern_type}]"
        )
        t = Translation(site=site)
        previous_error: str | None = None
        previous_attempt: str | None = None

        for attempt in range(1, _TRANSLATION_ATTEMPTS + 1):
            t.attempts = attempt
            try:
                baml, fn_name = translate_site(
                    client,
                    site,
                    examples,
                    previous_error=previous_error,
                    previous_attempt=previous_attempt,
                    taken_names=taken_names,
                )
            except FreeQuotaExhausted as e:
                console.print(f"[red]{e}[/red]")
                t.error = str(e)
                results.append(t)
                return results, _usage_dict(client)
            except Exception as e:
                t.error = f"Gemini call failed: {e}"
                break

            v = validate_baml_file(baml, filename="migration.baml")
            if v.ok:
                # Cross-file collision check: if this file declares any class/
                # function/enum names that were already taken by an earlier
                # translation, retry with the constraint visible to the LLM.
                new_names = declared_names(baml)
                collisions = [n for n in new_names if n in taken_names]
                if collisions and attempt < _TRANSLATION_ATTEMPTS:
                    console.print(f"[yellow]  attempt {attempt} produced name collision(s): {collisions}; retrying[/yellow]")
                    previous_error = (
                        f"The names {collisions} are already used by other migrated files "
                        f"in this project. Pick different names."
                    )
                    previous_attempt = baml
                    continue
                t.baml_source = baml
                t.function_name = fn_name
                t.baml_filename = _unique_filename(fn_name, used_names)
                t.python_usage = python_usage_snippet(fn_name) if fn_name else None
                taken_names.extend(new_names)
                break
            else:
                err = (v.stderr or v.stdout or "").strip()
                t.validator_errors.append(err)
                console.print(f"[yellow]  attempt {attempt} failed baml-cli check[/yellow]")
                previous_error = err
                previous_attempt = baml

        if not t.success and not t.error:
            t.error = f"baml-cli check rejected all {_TRANSLATION_ATTEMPTS} attempts"

        console.print(
            f"  [green]ok[/green] {t.baml_filename}" if t.success
            else f"  [red]failed[/red]: {t.error[:120] if t.error else 'unknown'}"
        )
        results.append(t)

        if (warn := client.quota_warning()):
            console.print(f"[yellow]{warn}[/yellow]")

    console.print(
        f"[dim]Session usage: {client.usage.call_count} calls, "
        f"{client.usage.total_tokens:,} tokens "
        f"({client.usage.prompt_tokens:,} prompt + {client.usage.output_tokens:,} output)[/dim]"
    )
    return results, _usage_dict(client)


def _usage_dict(client: LLMClient) -> dict:
    return {
        "call_count": client.usage.call_count,
        "total_tokens": client.usage.total_tokens,
        "prompt_tokens": client.usage.prompt_tokens,
        "output_tokens": client.usage.output_tokens,
        "quota_warning": client.quota_warning(),
    }


def _unique_filename(fn_name: str | None, used: dict[str, int]) -> str:
    base = (fn_name or "migration").lower()
    # baml file convention: lower_snake_case.baml
    import re as _re
    base = _re.sub(r"[^a-z0-9_]+", "_", base).strip("_") or "migration"
    used[base] = used.get(base, 0) + 1
    suffix = "" if used[base] == 1 else f"_{used[base]}"
    return f"{base}{suffix}.baml"


# -- main ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scout",
        description="BAML Migration Scout — scan a repo for LLM call sites and generate a BAML migration report.",
    )
    parser.add_argument(
        "target",
        help="GitHub repo URL, local directory, or single .py file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output/<repo-name>/).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run head-to-head trials on the active provider for measured deltas (extra LLM cost).",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Detect call sites and exit without translating (no LLM calls).",
    )
    parser.add_argument(
        "--keep-clone",
        action="store_true",
        help="Don't delete the cloned repo after scanning.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging to stderr (key rotation, dropped files, retries).",
    )
    parser.add_argument(
        "--provider",
        choices=PROVIDER_NAMES,
        default=DEFAULT_PROVIDER,
        help=(
            f"LLM provider for translation (default: {DEFAULT_PROVIDER}, free tier). "
            f"openai and anthropic require their own paid keys and the matching SDK extra."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the provider's default model (e.g. gpt-4o-mini, claude-3-5-sonnet-20241022).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the paid-provider confirmation prompt.",
    )
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    # Resolve provider early so we can fail fast on missing SDK / bad name,
    # and gate paid providers behind an explicit confirmation. --scan-only
    # skips this entirely since no LLM calls happen.
    provider: Provider | None = None
    if not args.scan_only:
        try:
            provider = get_provider(args.provider)
        except ProviderError as e:
            console.print(Panel.fit(f"[red]{e}[/red]", border_style="red"))
            return 2
        if not provider.free_tier and not args.yes:
            console.print(Panel.fit(
                f"[yellow]Provider {provider.name!r} is a PAID API.[/yellow]\n\n"
                f"This run will bill calls against the API key in {provider.api_key_env}. "
                f"Rough cost depends on repo size — see --scan-only to estimate sites first.\n\n"
                f"Re-run with [bold]--yes[/bold] to confirm, or omit [bold]--provider[/bold] "
                f"to fall back to the free-tier default ({DEFAULT_PROVIDER}).",
                border_style="yellow",
            ))
            return 2

    workspace = Path(tempfile.mkdtemp(prefix="baml_scout_"))
    try:
        repo_root, name, is_single_file = _resolve_target(args.target, workspace)
        provider_line = (
            "—" if provider is None
            else f"{provider.name} ({args.model or provider.default_model})"
            + ("" if provider.free_tier else "  [yellow]PAID[/yellow]")
        )
        console.print(Panel.fit(
            f"[bold]Target:[/bold] {args.target}\n"
            f"[bold]Resolved:[/bold] {repo_root}\n"
            f"[bold]Mode:[/bold] {'single file' if is_single_file else 'repo walk'}\n"
            f"[bold]Provider:[/bold] {provider_line}",
            title="BAML Migration Scout",
            border_style="cyan",
        ))

        if is_single_file:
            sites = scan_file(repo_root / name, repo_root)
        else:
            sites = scan_repo(repo_root)

        _print_summary(sites, name)

        if args.scan_only or not sites:
            return 0

        # ---- Translate every site -------------------------------------
        assert provider is not None  # we returned early above if scan-only
        translations, usage_summary = _translate_all(sites, args, provider)
        successes = [t for t in translations if t.success]
        failures = [t for t in translations if not t.success]
        if failures:
            console.print(
                f"[bold]Translated[/bold] {len(successes)}/{len(translations)} sites; "
                f"[red]{len(failures)} failed[/red]"
            )
        else:
            console.print(f"[bold green]Translated all {len(translations)} sites[/bold green]")

        # ---- Write baml_src/, run generate, render report --------------
        out_dir = args.out / name
        baml_src = out_dir / "baml_src"
        files = {
            t.baml_filename: t.baml_source for t in successes if t.baml_filename and t.baml_source
        }
        generate_ok = False
        if files:
            write_baml_project(baml_src, files)
            gen = run_generate(baml_src)
            generate_ok = gen.ok
            if gen.ok:
                console.print(f"[green]baml-cli generate succeeded[/green] → {baml_src}")
            else:
                console.print(f"[yellow]baml-cli generate had issues:[/yellow]\n{gen.stderr.strip()[:500]}")
            write_patch_diff(baml_src, out_dir / "patch.diff")

        files_scanned = sum(1 for _ in iter_python_files(repo_root))

        bench_result = None
        if args.benchmark and successes:
            # Pick the translation with the richest schema (most class chars).
            # Benchmarking on a site that returns plain `string` is uninteresting
            # because the JSON-Schema delta is trivial.
            target = max(
                successes,
                key=lambda t: len(t.baml_source or "") if "class " in (t.baml_source or "") else 0,
            )
            console.print(
                f"[bold]--benchmark[/bold] running head-to-head trials on "
                f"[dim]{target.baml_filename}[/dim] (richest schema among translated sites)"
            )
            try:
                bench_client = LLMClient(
                    load_keys_from_env(provider),
                    provider=provider,
                    model=args.model or provider.default_model,
                )
                bench_result = benchmark_translation(bench_client, target, n_trials=config.DEFAULT_BENCHMARK_TRIALS)
                if bench_result:
                    usage_summary["total_tokens"] += bench_client.usage.total_tokens
                    usage_summary["call_count"] += bench_client.usage.call_count
                    console.print(
                        f"  trials: {bench_result.n_trials} · "
                        f"original validity: {bench_result.original.validity_rate:.0%} · "
                        f"baml validity: {bench_result.baml.validity_rate:.0%} · "
                        f"token Δ: {bench_result.token_delta_per_call}/call"
                    )
            except FreeQuotaExhausted as e:
                console.print(f"[red]benchmark aborted (quota): {e}[/red]")

        ctx = build_context(
            repo_label=name,
            repo_url=args.target if _is_github_url(args.target) else None,
            repo_path=repo_root,
            files_scanned=files_scanned,
            translations=translations,
            token_count=usage_summary["total_tokens"],
            call_count=usage_summary["call_count"],
            generate_ok=generate_ok,
            benchmark=bench_result,
        )
        report_md = render_report(ctx)
        (out_dir / "migration_report.md").write_text(report_md, encoding="utf-8")
        console.print(f"[green]Report written:[/green] {out_dir / 'migration_report.md'}")

        if usage_summary.get("quota_warning"):
            console.print(f"[yellow]{usage_summary['quota_warning']}[/yellow]")

        return 0 if not failures else 1

    finally:
        if args.keep_clone:
            console.print(f"[dim]Kept clone at {workspace}[/dim]")
        else:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
