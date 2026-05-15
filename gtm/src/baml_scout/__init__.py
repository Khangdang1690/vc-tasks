"""BAML Migration Scout — point it at a repo, get a BAML migration plus a report.

This module exposes the high-level library surface. CLI use stays the same:
either `baml-scout <repo>` (after `pip install baml-scout`) or
`python -m baml_scout <repo>`. For programmatic use:

    >>> from baml_scout import scan_repo, LLMClient, get_provider, translate_site
    >>> from baml_scout import seed_baml_examples, validate_baml_file
    >>> sites = scan_repo(Path("./my-project"))
    >>> client = LLMClient(keys=["..."], provider=get_provider("gemini"))
    >>> baml, fn_name = translate_site(client, sites[0], seed_baml_examples(cache))
    >>> v = validate_baml_file(baml)

Re-exports below are the *stable* surface; module-level names (e.g.
`baml_scout.scanner._LLMCallVisitor`) are still importable but treated as
internals — name and behavior may change.
"""

from __future__ import annotations

__version__ = "0.2.0"

# Scanner — find LLM call sites in source.
from .scanner import (
    CallSite,
    PATTERN_TYPES,
    iter_python_files,
    scan_file,
    scan_repo,
)

# Provider abstraction — Gemini default, OpenAI / Anthropic opt-in.
from .providers import (
    DEFAULT_PROVIDER,
    PROVIDER_NAMES,
    GenerationResult,
    Provider,
    ProviderError,
    get_provider,
)

# Translator — convert a CallSite to BAML using any Provider.
from .translator import (
    FreeQuotaExhausted,
    LLMClient,
    GeminiClient,  # backwards-compat alias
    Translation,
    declared_names,
    load_keys_from_env,
    python_usage_snippet,
    seed_baml_examples,
    translate_site,
)

# Validator — run baml-cli check / generate.
from .validator import (
    ValidationResult,
    run_generate,
    validate_baml_file,
    write_baml_project,
)

# Benchmark — head-to-head trials on a translated site.
from .benchmark import (
    BenchmarkResult,
    FormatResult,
    TrialResult,
    benchmark_translation,
)

# Reporter — render the markdown migration report.
from .reporter import (
    DeltaEstimate,
    ReportContext,
    build_context,
    compute_delta,
    render_report,
    write_patch_diff,
)


__all__ = [
    "__version__",
    # scanner
    "CallSite", "PATTERN_TYPES", "iter_python_files", "scan_file", "scan_repo",
    # providers
    "DEFAULT_PROVIDER", "PROVIDER_NAMES", "GenerationResult", "Provider",
    "ProviderError", "get_provider",
    # translator
    "FreeQuotaExhausted", "LLMClient", "GeminiClient", "Translation",
    "declared_names", "load_keys_from_env", "python_usage_snippet",
    "seed_baml_examples", "translate_site",
    # validator
    "ValidationResult", "run_generate", "validate_baml_file", "write_baml_project",
    # benchmark
    "BenchmarkResult", "FormatResult", "TrialResult", "benchmark_translation",
    # reporter
    "DeltaEstimate", "ReportContext", "build_context", "compute_delta",
    "render_report", "write_patch_diff",
]
