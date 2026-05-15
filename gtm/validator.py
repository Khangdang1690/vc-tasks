"""Validate generated .baml files by running baml-cli check in a subprocess.

We use `baml-cli check --from <dir>` rather than `generate` because:
  * check is fast (no codegen step)
  * check returns parser/typechecker errors which are exactly what we want
    to feed back to the translator
  * we run `generate` once at the end on the final, validated baml_src/
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from config import (
    BAML_CLI,
    BAML_NO_VERSION_CHECK,
    DEFAULT_MODEL,
    TIMEOUT_BAML_CHECK,
    TIMEOUT_BAML_GENERATE,
    VALIDATOR_STUB_CLIENTS,
)
from utils import baml_cli_available, get_logger


log = get_logger(__name__)


def _stub_clients_baml() -> str:
    """Build the validator clients.baml from the configured stub list.

    Centralizing this means a future provider addition (or model bump) only
    needs a config edit, not a string-template edit.
    """
    blocks = []
    for c in VALIDATOR_STUB_CLIENTS:
        blocks.append(
            f"client<llm> {c.name} {{\n"
            f"  provider {c.provider}\n"
            f"  options {{\n"
            f"    model \"{c.model}\"\n"
            f"    api_key env.{c.api_key_env}\n"
            f"  }}\n"
            f"}}"
        )
    return "\n\n".join(blocks)


_DEFAULT_GENERATORS_BAML = """
generator target {
    output_type "python/pydantic"
    output_dir "../"
    version "0.222.0"
    default_client_mode sync
}
"""

# Materialized once on import. The model list is small and static.
_DEFAULT_CLIENTS_BAML = _stub_clients_baml()


@dataclass
class ValidationResult:
    """Outcome of a baml-cli check or generate invocation.

    `ok` is True iff the subprocess returned 0 within its timeout. `stderr`
    and `stdout` are the captured streams (whitespace preserved) so the
    translator can feed compiler errors back into the next attempt.
    """
    ok: bool
    stderr: str
    stdout: str


def _ensure_cli_present() -> None:
    """Raise a clear error if baml-cli isn't on PATH.

    Previously this surfaced as a generic FileNotFoundError from subprocess
    or a misleading "Gemini call failed" error in the orchestrator. Failing
    eagerly here points the user at the actual remediation.
    """
    if not baml_cli_available():
        raise FileNotFoundError(
            f"`{BAML_CLI}` is not on PATH. Install it with "
            "`npm install -g @boundaryml/baml`."
        )


def _run_baml(cmd: list[str], *, timeout: int) -> ValidationResult:
    """Run a baml-cli subprocess with a hard timeout and structured result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=sys.platform == "win32",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        log.warning("%s timed out after %ds", " ".join(cmd), timeout)
        return ValidationResult(ok=False, stderr=f"timed out after {timeout}s", stdout=e.stdout or "")
    return ValidationResult(
        ok=result.returncode == 0,
        stderr=result.stderr,
        stdout=result.stdout,
    )


def validate_baml_file(baml_source: str, filename: str = "migration.baml") -> ValidationResult:
    """Write the single .baml file (plus stub clients+generators) into a temp
    baml_src/ dir and run baml-cli check against it.
    """
    _ensure_cli_present()
    with tempfile.TemporaryDirectory(prefix="baml_validate_") as tmp:
        baml_src = Path(tmp) / "baml_src"
        baml_src.mkdir(parents=True, exist_ok=True)

        (baml_src / filename).write_text(baml_source, encoding="utf-8")
        (baml_src / "clients.baml").write_text(_DEFAULT_CLIENTS_BAML.strip() + "\n", encoding="utf-8")
        (baml_src / "generators.baml").write_text(_DEFAULT_GENERATORS_BAML.strip() + "\n", encoding="utf-8")

        cmd = [BAML_CLI, "check", BAML_NO_VERSION_CHECK, "--from", str(baml_src)]
        return _run_baml(cmd, timeout=TIMEOUT_BAML_CHECK)


def write_baml_project(baml_dir: Path, files: dict[str, str]) -> None:
    """Materialize a complete baml_src/ project: stub clients + generators +
    every generated function file. Used for the final output.
    """
    baml_dir.mkdir(parents=True, exist_ok=True)
    (baml_dir / "clients.baml").write_text(_DEFAULT_CLIENTS_BAML.strip() + "\n", encoding="utf-8")
    (baml_dir / "generators.baml").write_text(_DEFAULT_GENERATORS_BAML.strip() + "\n", encoding="utf-8")
    for name, body in files.items():
        (baml_dir / name).write_text(body, encoding="utf-8")


def run_generate(baml_dir: Path) -> ValidationResult:
    """Run `baml-cli generate` over a complete baml_src/ project."""
    _ensure_cli_present()
    cmd = [BAML_CLI, "generate", BAML_NO_VERSION_CHECK, "--from", str(baml_dir)]
    return _run_baml(cmd, timeout=TIMEOUT_BAML_GENERATE)


# Default model is re-exported so callers (or tests) can sanity-check that
# the stub clients agree with the translator default.
__all__ = [
    "ValidationResult",
    "validate_baml_file",
    "write_baml_project",
    "run_generate",
    "DEFAULT_MODEL",
]
