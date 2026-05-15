"""Central configuration for BAML Migration Scout.

Single source of truth for tunables that used to be magic numbers scattered
across modules. Anything that a user might reasonably want to override lives
here. Things that are part of the public artifact contract (e.g. file layout
under output/) stay in their owning module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# LLM provider defaults
# ---------------------------------------------------------------------------

# Gemini 2.5 Flash free tier. The published daily cap moves around — we treat
# ~1M tokens/day as the conservative ceiling and warn at 80%.
DAILY_TOKEN_SOFT_LIMIT = int(os.environ.get("BAML_SCOUT_DAILY_LIMIT", "1000000"))
QUOTA_WARN_FRACTION = 0.8
QUOTA_WARN_AT = int(DAILY_TOKEN_SOFT_LIMIT * QUOTA_WARN_FRACTION)

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_OUTPUT_TOKENS = 2048

# Translation retry budget per call site: 1 initial + N retries with the
# compiler error fed back in context.
TRANSLATION_RETRIES = 2  # → 3 attempts total

# Backoff (seconds) between Gemini retries.
GEMINI_BACKOFF_AFTER_ROTATE = 0.5
GEMINI_BACKOFF_AFTER_5XX = 1.0
GEMINI_MAX_RETRIES_PER_KEY = 1


# ---------------------------------------------------------------------------
# Subprocess timeouts (seconds)
# ---------------------------------------------------------------------------

# Every external command gets a hard ceiling so a hung CLI can't deadlock
# the scout. Values are generous — the real bug we're guarding against is a
# wedged process, not a slow one.
TIMEOUT_GIT_CLONE = 120
TIMEOUT_GIT_GENERIC = 10
TIMEOUT_BAML_INIT = 30
TIMEOUT_BAML_CHECK = 30
TIMEOUT_BAML_GENERATE = 60
TIMEOUT_GEMINI_CALL = 90


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

# Lines of source above/below the LLM call to hand the translator as context.
SCAN_CONTEXT_BEFORE = 5
SCAN_CONTEXT_AFTER = 8

# Window for the raw_json_after pattern: a json.loads within N lines of an
# LLM call counts as a raw-parse site worth migrating.
RAW_JSON_AFTER_WINDOW = 6

# Directory names skipped during repo walks. Shared between scanner.py and
# the file-count helper in scout.py so they cannot drift.
SKIP_DIRS = frozenset({
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "site-packages",
    ".tox",
    ".idea",
    ".vscode",
})


# ---------------------------------------------------------------------------
# Reporter / token estimation
# ---------------------------------------------------------------------------

# Standard rough rule for English text. Same constant is used by reporter.py
# (for delta estimation) and benchmark.py (for trial token fallback).
CHARS_PER_TOKEN = 4

# JSON Schema overhead estimates for the schema-size delta. These are
# heuristics, not measurements — flagged as such in the report.
JSON_SCHEMA_BYTES_PER_FIELD = 30
JSON_SCHEMA_BASE_OVERHEAD = 80


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

DEFAULT_BENCHMARK_TRIALS = 5


# ---------------------------------------------------------------------------
# baml-cli invocation
# ---------------------------------------------------------------------------

BAML_CLI = "baml-cli"
BAML_NO_VERSION_CHECK = "--no-version-check"


@dataclass(frozen=True)
class StubClient:
    """Minimal client definition used in validator stub clients.baml."""
    name: str
    provider: str
    model: str
    api_key_env: str


# Stub clients the validator writes alongside generated functions so
# `baml-cli check` resolves provider references. These are validation-only;
# the generated baml files inline their own `client "provider/model"`.
VALIDATOR_STUB_CLIENTS = (
    StubClient("DefaultOpenAI", "openai", "gpt-4o-mini", "OPENAI_API_KEY"),
    StubClient("DefaultAnthropic", "anthropic", "claude-3-5-sonnet-20241022", "ANTHROPIC_API_KEY"),
    StubClient("DefaultGemini", "google-ai", DEFAULT_MODEL, "GEMINI_API_KEY"),
)
