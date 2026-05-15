"""Shared helpers used across modules.

The previous layout had token estimation, fence-stripping, and ad-hoc logging
duplicated in two or three places. Putting them here keeps the contract in
one file so a fix to (e.g.) fence handling doesn't have to land twice.
"""

from __future__ import annotations

import logging
import shutil
import sys

from config import BAML_CLI, CHARS_PER_TOKEN


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_LOG_NAME = "baml_scout"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a module logger under the `baml_scout` namespace.

    The CLI configures the root `baml_scout` logger once in scout.main(); all
    library code just calls get_logger(__name__) and inherits that config.
    Default level is WARNING so the rich-console UX is unaffected unless the
    user passes --verbose.
    """
    suffix = name.rsplit(".", 1)[-1] if name else None
    full = f"{_LOG_NAME}.{suffix}" if suffix else _LOG_NAME
    return logging.getLogger(full)


def configure_logging(verbose: bool) -> None:
    """Wire the `baml_scout` logger to stderr at the requested level."""
    root = logging.getLogger(_LOG_NAME)
    # Don't double-attach handlers on re-entry (tests, library use).
    if root.handlers:
        root.setLevel(logging.DEBUG if verbose else logging.WARNING)
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s %(name)s] %(message)s"
    ))
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
    root.propagate = False


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def strip_markdown_fences(text: str) -> str:
    """Strip a leading ```lang fence and trailing ``` fence if present.

    Used by translator.py (BAML output from Gemini sometimes wraps in fences
    despite the prompt saying not to) and benchmark.py (trial outputs).
    """
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def estimate_tokens(text: str) -> int:
    """Rough token estimate (chars / CHARS_PER_TOKEN, floor 1).

    Not a substitute for a real tokenizer — used only for delta estimation
    in the report and as a fallback for benchmark trials when the model SDK
    doesn't expose per-call usage cleanly.
    """
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# baml-cli availability
# ---------------------------------------------------------------------------


def baml_cli_available() -> bool:
    """Return True iff `baml-cli` resolves on PATH.

    Used so we can fail loudly with a remediation hint (npm install -g …)
    rather than letting subprocess raise a bare FileNotFoundError deep in
    the validator.
    """
    # On Windows, npm installs `baml-cli.cmd`; shutil.which handles PATHEXT.
    return shutil.which(BAML_CLI) is not None
