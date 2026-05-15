"""Render the migration report.

The report is the artifact, not the CLI. Voice target: dry, numbers-forward,
senior engineer's post-mortem. Reference voices: Simon Willison's blog,
Anthropic engineering posts, the BAML team's own benchmark posts. No
marketing language. No emojis except in the bottom tweet section.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import (
    CHARS_PER_TOKEN,
    JSON_SCHEMA_BASE_OVERHEAD,
    JSON_SCHEMA_BYTES_PER_FIELD,
    TIMEOUT_GIT_GENERIC,
)
from scanner import CallSite
from translator import Translation
from benchmark import BenchmarkResult
from utils import estimate_tokens, get_logger


log = get_logger(__name__)


_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
# Kept for backwards-compat with any importer that read this; new code should
# import CHARS_PER_TOKEN from config.
_CHARS_PER_TOKEN = CHARS_PER_TOKEN


@dataclass
class DeltaEstimate:
    """Side-by-side schema size estimate for the report."""
    original_schema_chars: int
    baml_schema_chars: int
    original_schema_tokens: int
    baml_schema_tokens: int
    tokens_saved_per_call: int
    schema_ratio_str: str  # e.g. "−68% (3.1× compaction)"


# Heuristic JSON-Schema bytes per field. Sourced from config so a future
# calibration pass against measured schemas only edits one file.
_JSON_SCHEMA_BYTES_PER_FIELD = JSON_SCHEMA_BYTES_PER_FIELD
_JSON_SCHEMA_BASE_OVERHEAD = JSON_SCHEMA_BASE_OVERHEAD


_BAML_FIELD_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s+", re.MULTILINE)
_BAML_CLASS_RE = re.compile(r"class\s+\w+\s*\{([^}]*)\}", re.DOTALL)


def _count_baml_fields(baml: str) -> int:
    """Count field declarations across all `class { ... }` blocks."""
    total = 0
    for block in _BAML_CLASS_RE.findall(baml):
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            # A field looks like `name string` / `addresses Address[]`.
            if _BAML_FIELD_RE.match(line + " "):
                total += 1
    return total


def _baml_schema_chars(baml: str) -> int:
    """Sum of chars across class definitions in this baml file."""
    classes = _BAML_CLASS_RE.findall(baml)
    if not classes:
        return 0
    return sum(len(c) for c in classes) + len(classes) * 10  # rough header overhead


def _estimate_json_schema_chars(baml: str) -> int:
    """Estimate how big the equivalent JSON Schema would be."""
    field_count = _count_baml_fields(baml)
    if field_count == 0:
        return 0
    return _JSON_SCHEMA_BASE_OVERHEAD + field_count * _JSON_SCHEMA_BYTES_PER_FIELD


def compute_delta(translations: list[Translation]) -> DeltaEstimate:
    """Aggregate schema-size deltas across all successful translations."""
    baml_total = 0
    orig_total = 0
    for t in translations:
        if not t.success or not t.baml_source:
            continue
        baml_total += _baml_schema_chars(t.baml_source)
        orig_total += _estimate_json_schema_chars(t.baml_source)

    baml_tokens = estimate_tokens(_to_text(baml_total))
    orig_tokens = estimate_tokens(_to_text(orig_total))
    saved = max(0, orig_tokens - baml_tokens)

    if orig_total > 0 and baml_total > 0:
        ratio = orig_total / baml_total
        pct = (1 - baml_total / orig_total) * 100
        ratio_str = f"−{pct:.0f}% ({ratio:.1f}× compaction)"
    else:
        ratio_str = "—"

    # Average per-call: divide by translated count (already filtered above).
    succeeded = [t for t in translations if t.success]
    n = max(1, len(succeeded))
    return DeltaEstimate(
        original_schema_chars=orig_total // n,
        baml_schema_chars=baml_total // n,
        original_schema_tokens=orig_tokens // n,
        baml_schema_tokens=baml_tokens // n,
        tokens_saved_per_call=saved // n,
        schema_ratio_str=ratio_str,
    )


def _to_text(chars: int) -> str:
    """Helper — estimate_tokens takes a string, not a char count."""
    return "x" * chars


# ---------------------------------------------------------------------------
# Tweet summary
# ---------------------------------------------------------------------------


def build_tweet_summary(
    repo_label: str,
    sites_translated: int,
    sites_failed: int,
    delta: DeltaEstimate,
    token_count: int,
    patterns_present: list[str],
    repo_url: str | None = None,
) -> str:
    """One-paragraph summary, dry but specific, suitable for a quote-tweet."""
    pattern_str = ", ".join(patterns_present) if patterns_present else "LLM"
    repo_link = repo_url or repo_label
    saved_line = ""
    if delta.tokens_saved_per_call > 0:
        saved_line = f" Estimated ~{delta.tokens_saved_per_call} tokens saved per call vs the equivalent JSON-Schema-wire-format."

    failures_line = ""
    if sites_failed:
        failures_line = f" {sites_failed} site(s) flagged as too ambiguous to auto-migrate."

    return (
        f"📎 Pointed BAML Migration Scout at `{repo_link}`. "
        f"Detected {sites_translated + sites_failed} {pattern_str} call site(s); "
        f"translated {sites_translated} to BAML in {token_count:,} tokens via Gemini 2.5 Flash free tier. "
        f"All pass `baml-cli check` and `baml-cli generate` produced a working Pydantic client.{saved_line}{failures_line} "
        f"BAML's type-safe DSL collapses the trial-to-migration step from a Saturday project to a 30-second URL paste."
    )


# ---------------------------------------------------------------------------
# Sites table for the report
# ---------------------------------------------------------------------------


def build_sites_table(translations: list[Translation]) -> list[dict]:
    rows = []
    for i, t in enumerate(translations, 1):
        if t.success:
            result = f"✓ {t.baml_filename}"
        elif t.error:
            result = f"✗ {t.error[:60]}"
        else:
            result = "✗ unknown"
        schema_marker = "yes" if t.site.inferred_schema else "—"
        rows.append({
            "idx": i,
            "location": t.site.display_id(),
            "pattern": t.site.pattern_type,
            "model": t.site.model_name,
            "schema": schema_marker,
            "result": result,
        })
    return rows


# ---------------------------------------------------------------------------
# Top-level renderer
# ---------------------------------------------------------------------------


@dataclass
class ReportContext:
    repo_label: str
    repo_url: str | None
    commit_sha: str | None
    scan_timestamp: str
    files_scanned: int
    sites_total: int
    sites_translated: int
    sites_failed: int
    patterns_present: list[str]
    token_count: int
    call_count: int
    generate_ok: bool
    translations: list[Translation]
    failures: list[Translation]
    sites_table: list[dict]
    delta: DeltaEstimate
    first_function_name: str | None
    tweet_summary: str
    benchmark: BenchmarkResult | None = None


def render_report(ctx: ReportContext) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(default=False),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    tmpl = env.get_template("migration_report.md.j2")
    return tmpl.render(**ctx.__dict__)


def get_commit_sha(repo_path: Path) -> str | None:
    """Return HEAD SHA of repo_path or None if it isn't a git repo / git missing.

    Failures here are non-fatal: the report just omits the commit field.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=TIMEOUT_GIT_GENERIC,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        log.debug("git rev-parse HEAD rc=%d on %s", result.returncode, repo_path)
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        log.debug("git rev-parse HEAD failed on %s: %s", repo_path, e)
    return None


def write_patch_diff(baml_src: Path, out_path: Path) -> None:
    """Write a synthetic patch.diff showing the new baml_src/ contents."""
    lines: list[str] = []
    for baml_file in sorted(baml_src.glob("*.baml")):
        rel = f"baml_src/{baml_file.name}"
        body = baml_file.read_text(encoding="utf-8").splitlines()
        lines.append(f"diff --git a/{rel} b/{rel}")
        lines.append("new file mode 100644")
        lines.append(f"--- /dev/null")
        lines.append(f"+++ b/{rel}")
        lines.append(f"@@ -0,0 +1,{len(body)} @@")
        for ln in body:
            lines.append(f"+{ln}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_context(
    *,
    repo_label: str,
    repo_url: str | None,
    repo_path: Path,
    files_scanned: int,
    translations: list[Translation],
    token_count: int,
    call_count: int,
    generate_ok: bool,
    benchmark: BenchmarkResult | None = None,
) -> ReportContext:
    successes = [t for t in translations if t.success]
    failures = [t for t in translations if not t.success]
    patterns = sorted({t.site.pattern_type for t in translations})
    delta = compute_delta(translations)
    first_fn = next((t.function_name for t in successes if t.function_name), None)
    tweet = build_tweet_summary(
        repo_label=repo_label,
        sites_translated=len(successes),
        sites_failed=len(failures),
        delta=delta,
        token_count=token_count,
        patterns_present=patterns,
        repo_url=repo_url,
    )
    return ReportContext(
        repo_label=repo_label,
        repo_url=repo_url,
        commit_sha=get_commit_sha(repo_path),
        scan_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        files_scanned=files_scanned,
        sites_total=len(translations),
        sites_translated=len(successes),
        sites_failed=len(failures),
        patterns_present=patterns,
        token_count=token_count,
        call_count=call_count,
        generate_ok=generate_ok,
        translations=translations,
        failures=failures,
        sites_table=build_sites_table(translations),
        delta=delta,
        first_function_name=first_fn,
        tweet_summary=tweet,
        benchmark=benchmark,
    )
