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


# Minimal stub clients.baml that the project needs to typecheck against.
# We use a single openai client + a single anthropic client + a Gemini client.
# This is the *minimum* surface; if a function references something else, the
# translator was instructed to inline `client "provider/model"` instead.
_DEFAULT_CLIENTS_BAML = """
client<llm> DefaultOpenAI {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> DefaultAnthropic {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> DefaultGemini {
  provider google-ai
  options {
    model "gemini-2.5-flash"
    api_key env.GEMINI_API_KEY
  }
}
"""

_DEFAULT_GENERATORS_BAML = """
generator target {
    output_type "python/pydantic"
    output_dir "../"
    version "0.222.0"
    default_client_mode sync
}
"""


@dataclass
class ValidationResult:
    ok: bool
    stderr: str
    stdout: str


def _baml_cli_invocation() -> list[str]:
    # On Windows the npm-installed binary is `baml-cli.cmd`; subprocess needs
    # the explicit extension OR shell=True. We use shell=True to keep this
    # portable across PowerShell / cmd / bash.
    return ["baml-cli", "check", "--no-version-check"]


def validate_baml_file(baml_source: str, filename: str = "migration.baml") -> ValidationResult:
    """Write the single .baml file (plus stub clients+generators) into a temp
    baml_src/ dir and run baml-cli check against it.
    """
    with tempfile.TemporaryDirectory(prefix="baml_validate_") as tmp:
        baml_src = Path(tmp) / "baml_src"
        baml_src.mkdir(parents=True, exist_ok=True)

        (baml_src / filename).write_text(baml_source, encoding="utf-8")
        (baml_src / "clients.baml").write_text(_DEFAULT_CLIENTS_BAML.strip() + "\n", encoding="utf-8")
        (baml_src / "generators.baml").write_text(_DEFAULT_GENERATORS_BAML.strip() + "\n", encoding="utf-8")

        cmd = _baml_cli_invocation() + ["--from", str(baml_src)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=sys.platform == "win32",
        )
        return ValidationResult(
            ok=result.returncode == 0,
            stderr=result.stderr,
            stdout=result.stdout,
        )


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
    cmd = ["baml-cli", "generate", "--no-version-check", "--from", str(baml_dir)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=sys.platform == "win32",
    )
    return ValidationResult(
        ok=result.returncode == 0,
        stderr=result.stderr,
        stdout=result.stdout,
    )
