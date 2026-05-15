"""LLM-driven translation from a Python LLM call site to BAML.

The translator takes a scanner.CallSite and produces a generated .baml file
that captures the same intent in BAML's DSL. The provider call is grounded
with a few-shot bundle (see seed_baml_examples) and the validator loops it
back with the compiler error on failure.

Default provider is Gemini 2.5 Flash on the free tier ($0 budget). Multi-key
rotation handles 429s and exits cleanly when keys are exhausted — never
silently falls through to a different provider. Other providers (OpenAI,
Anthropic) are supported through providers.py for users who explicitly
opt in via `--provider`.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import config
from providers import (
    DEFAULT_PROVIDER,
    GenerationResult,
    Provider,
    ProviderError,
    get_provider,
)
from scanner import CallSite
from utils import get_logger, strip_markdown_fences


log = get_logger(__name__)


# Re-export config constants under their historical names so any external
# importer that read MODEL / WARN_AT / DAILY_TOKEN_SOFT_LIMIT still works.
DAILY_TOKEN_SOFT_LIMIT = config.DAILY_TOKEN_SOFT_LIMIT
WARN_AT = config.QUOTA_WARN_AT
MODEL = config.DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Few-shot example seeding
# ---------------------------------------------------------------------------


def seed_baml_examples(cache_path: Path, force: bool = False) -> str:
    """Return the few-shot example string. Writes the cache file on first run.

    Strategy: shell out to `baml-cli init` in a temp dir and inline the three
    canonical files (resume.baml / clients.baml / generators.baml). This is
    deterministic, version-locked to the installed CLI, and works offline —
    much more reliable than fetching docs.boundaryml.com.
    """
    if cache_path.exists() and not force:
        return cache_path.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="baml_seed_") as tmp:
        try:
            result = subprocess.run(
                [config.BAML_CLI, "init"],
                cwd=tmp,
                capture_output=True,
                text=True,
                shell=True,
                timeout=config.TIMEOUT_BAML_INIT,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"baml-cli init timed out after {config.TIMEOUT_BAML_INIT}s. "
                "Is `baml-cli` installed and on PATH?"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                "baml-cli is not on PATH. Install with `npm install -g @boundaryml/baml`."
            ) from e
        if result.returncode != 0:
            raise RuntimeError(
                f"baml-cli init failed (rc={result.returncode}): {result.stderr.strip()}\n"
                f"Make sure `npm install -g @boundaryml/baml` succeeded."
            )
        seed_dir = Path(tmp) / "baml_src"
        resume_baml = (seed_dir / "resume.baml").read_text(encoding="utf-8")
        clients_baml = (seed_dir / "clients.baml").read_text(encoding="utf-8")
        generators_baml = (seed_dir / "generators.baml").read_text(encoding="utf-8")

    bundle = _build_example_bundle(resume_baml, clients_baml, generators_baml)
    cache_path.write_text(bundle, encoding="utf-8")
    return bundle


def _build_example_bundle(resume_baml: str, clients_baml: str, generators_baml: str) -> str:
    return f"""# BAML Few-Shot Bundle

This file is the grounding context handed to the translator LLM. It is
seeded automatically on first run from `baml-cli init` so the syntax is
locked to the installed CLI version.

## Key syntactic rules

* `class Foo {{ field type }}` — define a data shape. Types are bare names:
  `string`, `int`, `float`, `bool`, `string[]`, `Foo?` (optional), `Foo | Bar`
  (union), enums via `enum Color {{ RED GREEN BLUE }}`.
* `function FuncName(arg: Type) -> ReturnType` — defines a typed LLM call.
* Inside `function`: `client "<provider>/<model>"` or a reference to a
  named client from clients.baml. The `prompt #" ... "#` block contains
  the actual prompt with `{{{{ arg }}}}` jinja-style interpolation and
  `{{{{ ctx.output_format }}}}` which BAML expands to the schema hint.
* `test name {{ functions [F1, F2] args {{ ... }} }}` — inline test blocks.

## Example 1: canonical extraction (resume parsing)

```baml
{resume_baml.strip()}
```

## Example 2: client + retry policy definitions (clients.baml)

```baml
{clients_baml.strip()}
```

## Example 3: codegen target config (generators.baml)

```baml
{generators_baml.strip()}
```

## Additional patterns the translator should know

### Enum classification

```baml
enum Sentiment {{
  POSITIVE
  NEGATIVE
  NEUTRAL
}}

function ClassifySentiment(text: string) -> Sentiment {{
  client "openai/gpt-4o-mini"
  prompt #"
    Classify the sentiment of this text as POSITIVE, NEGATIVE, or NEUTRAL.

    Text: {{{{ text }}}}

    {{{{ ctx.output_format }}}}
  "#
}}
```

### Tool / function calling (Anthropic-style)

```baml
class WeatherQuery {{
  location string
  unit "celsius" | "fahrenheit"
}}

function ChooseWeatherTool(user_message: string) -> WeatherQuery {{
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    The user has asked a weather question. Extract the location and the
    requested temperature unit.

    User: {{{{ user_message }}}}

    {{{{ ctx.output_format }}}}
  "#
}}
```

### Optional fields and nested classes

```baml
class Address {{
  street string
  city string
  state string?
  country string
}}

class Person {{
  name string
  email string?
  age int?
  addresses Address[]
}}

function ExtractPerson(text: string) -> Person {{
  client "openai/gpt-4o-mini"
  prompt #"
    Extract the person from the text.
    {{{{ ctx.output_format }}}}

    Text: {{{{ text }}}}
  "#
}}
```
"""


# ---------------------------------------------------------------------------
# Gemini client with multi-key rotation + token tracking
# ---------------------------------------------------------------------------


@dataclass
class TokenUsage:
    """Aggregate token usage across the session."""
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0

    def add(self, prompt: int, output: int) -> None:
        self.prompt_tokens += prompt
        self.output_tokens += output
        self.total_tokens += prompt + output
        self.call_count += 1


class FreeQuotaExhausted(RuntimeError):
    """All configured provider keys have hit rate / quota limits.

    Name kept historical for backwards-compat — applies to any provider that
    exhausts its keys without falling through to another paid API.
    """


class LLMClient:
    """Provider-agnostic client that rotates keys on rate limits and exits
    cleanly on exhaustion.

    Never silently switches providers. If every key for the active provider
    is rate-limited, raises FreeQuotaExhausted which the CLI surfaces as a
    clean error.
    """

    def __init__(
        self,
        keys: Iterable[str],
        provider: Provider | None = None,
        model: str | None = None,
    ):
        cleaned = [k.strip() for k in keys if k and k.strip()]
        if not cleaned:
            raise ValueError("No API keys provided. Set the appropriate API_KEY env var.")
        self.provider: Provider = provider if provider is not None else get_provider(DEFAULT_PROVIDER)
        self.model = model or self.provider.default_model
        self.keys = cleaned
        self._idx = 0
        self._exhausted: set[int] = set()
        self.usage = TokenUsage()
        self._client = self.provider.make_client(self.keys[self._idx])
        log.debug(
            "LLMClient initialized: provider=%s model=%s keys=%d free_tier=%s",
            self.provider.name, self.model, len(self.keys), self.provider.free_tier,
        )

    @property
    def current_key_label(self) -> str:
        # never expose the full key, just an index for debug
        return f"key#{self._idx + 1}/{len(self.keys)}"

    def _rotate(self) -> bool:
        """Move to the next non-exhausted key. Return True if rotation succeeded."""
        self._exhausted.add(self._idx)
        for i in range(len(self.keys)):
            if i not in self._exhausted:
                self._idx = i
                self._client = self.provider.make_client(self.keys[i])
                log.info("rotated %s key: now using %s", self.provider.name, self.current_key_label)
                return True
        return False

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_retries_per_key: int = config.GEMINI_MAX_RETRIES_PER_KEY,
    ) -> str:
        """Run a single generation, rotating keys on rate-limit errors.

        Returns the text response. Tracks usage on self.usage.
        """
        attempts = 0
        while True:
            attempts += 1
            try:
                result: GenerationResult = self.provider.generate(
                    client=self._client,
                    prompt=prompt,
                    system=system,
                    model=self.model,
                    temperature=config.DEFAULT_TEMPERATURE,
                    max_output_tokens=config.DEFAULT_MAX_OUTPUT_TOKENS,
                    timeout_s=config.TIMEOUT_GEMINI_CALL,
                )
            except BaseException as e:
                if self.provider.is_rate_limit_error(e):
                    log.warning("rate-limit on %s (%s); rotating", self.provider.name, self.current_key_label)
                    if not self._rotate():
                        raise FreeQuotaExhausted(
                            f"All {self.provider.name} API keys are rate-limited or exhausted. "
                            + self._exhaustion_hint()
                        ) from e
                    time.sleep(config.GEMINI_BACKOFF_AFTER_ROTATE)
                    continue
                if self.provider.is_server_error(e):
                    log.warning("%s 5xx on %s (attempt %d): %s", self.provider.name, self.current_key_label, attempts, e)
                    if attempts <= max_retries_per_key:
                        time.sleep(config.GEMINI_BACKOFF_AFTER_5XX)
                        continue
                    if not self._rotate():
                        raise FreeQuotaExhausted(
                            f"All {self.provider.name} keys returned server errors; bailing rather than retry-loop."
                        ) from e
                    attempts = 0
                    continue
                raise

            if result.prompt_tokens or result.output_tokens:
                self.usage.add(result.prompt_tokens, result.output_tokens)
            if not result.text:
                raise RuntimeError(
                    f"Empty response from {self.provider.name} ({self.current_key_label})"
                )
            return result.text

    def _exhaustion_hint(self) -> str:
        if self.provider.free_tier:
            return (
                f"Wait for the daily reset or add another key to {self.provider.api_key_env}."
            )
        return f"Rotate to a fresh key or raise your {self.provider.name} rate limits."

    def quota_warning(self) -> str | None:
        # Only meaningful for free-tier providers — for paid, the user manages
        # their own spend, and a "you used a lot of tokens" warning is noise.
        if not self.provider.free_tier:
            return None
        if self.usage.total_tokens >= WARN_AT:
            return (
                f"Session has consumed {self.usage.total_tokens:,} tokens "
                f"({self.usage.total_tokens / DAILY_TOKEN_SOFT_LIMIT:.0%} of the ~1M/day free-tier ceiling). "
                f"Consider stopping or adding another {self.provider.api_key_env}."
            )
        return None


# Backwards-compat alias: existing imports of GeminiClient still work, now
# routed through the provider abstraction with Gemini as default.
class GeminiClient(LLMClient):
    """Backwards-compat wrapper: LLMClient pinned to Gemini.

    New code should construct `LLMClient(keys, provider=get_provider("..."))`
    directly. This subclass exists so older entry points keep working.
    """

    def __init__(self, keys: Iterable[str], model: str = MODEL):
        super().__init__(keys=keys, provider=get_provider("gemini"), model=model)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


# A generated BAML file slug. e.g. "extract_person.baml" or "classify_sentiment.baml".
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Translation:
    """Result of translating one CallSite to BAML."""
    site: CallSite
    baml_filename: str | None = None
    baml_source: str | None = None
    python_usage: str | None = None  # snippet showing how to call the generated client
    function_name: str | None = None
    schema_name: str | None = None
    error: str | None = None  # if translation failed
    attempts: int = 0
    validator_errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.baml_source is not None and self.error is None


SYSTEM_PROMPT = """You are a BAML migration assistant. You convert Python LLM call sites
to BAML (BoundaryML) functions. BAML is a DSL that generates type-safe LLM client
code. Every BAML function declares a typed return shape, so the language runtime
guarantees the output conforms to the schema (via Schema-Aligned Parsing).

You output BAML source code only. No commentary, no markdown fences, no explanation.
If the input is ambiguous, make a defensible choice and proceed — do not refuse.

The generated BAML file must:
  1. Be syntactically valid (`baml-cli check` will verify).
  2. Define one `function` and any `class` / `enum` types it references.
  3. Use a `client` reference appropriate for the model name from the source.
     Inline form is fine: `client "openai/gpt-4o-mini"` or `client "anthropic/claude-3-5-sonnet-20241022"`.
     For unknown models, use `client "openai/gpt-4o-mini"`.
  4. Use `{{ ctx.output_format }}` inside the prompt so the schema hint is
     auto-injected by the BAML runtime.
  5. Include a `test` block ONLY if a clear input example is obvious. Skip it otherwise.
"""


PROMPT_TEMPLATE = """## BAML reference

{examples}

## Migration task

The user has a Python codebase using LLM patterns. We've detected a call site
of type **{pattern_type}** and want to migrate it to a single .baml file.

### Source file: `{file}:{line}`

### Pattern notes
{notes}

### Inferred schema (Pydantic class, if any)

{schema_block}

### Source snippet (the call itself)

```python
{snippet}
```

### Surrounding context (a few lines before/after for intent)

```python
{context}
```

## Output requirements

Produce a single BAML file. Use one function. Pick a clear function name in
PascalCase (e.g. ExtractResume, ClassifySentiment, ChooseTool). Include any
class/enum definitions the function refers to. Do not include `clients.baml`
or `generators.baml` content — only the function-level file.

If the source uses a known model, route the BAML `client` to the equivalent
provider/model. Defaults: openai/gpt-4o-mini for unknown OpenAI; anthropic/claude-3-5-sonnet-20241022 for anthropic.

Output only the .baml source. No markdown fences.
{retry_block}"""


_FUNC_RE = re.compile(r"function\s+([A-Z][A-Za-z0-9_]+)\s*\(", re.MULTILINE)
_CLASS_RE = re.compile(r"^\s*class\s+([A-Z][A-Za-z0-9_]+)\s*\{", re.MULTILINE)
_ENUM_RE = re.compile(r"^\s*enum\s+([A-Z][A-Za-z0-9_]+)\s*\{", re.MULTILINE)


def declared_names(baml: str) -> list[str]:
    """Return all class / enum / function names declared in a baml file."""
    names: list[str] = []
    names.extend(_FUNC_RE.findall(baml))
    names.extend(_CLASS_RE.findall(baml))
    names.extend(_ENUM_RE.findall(baml))
    return names


def _slugify(name: str) -> str:
    s = _SLUG_RE.sub("_", name.lower()).strip("_")
    return s or "migrated"


def _detect_function_name(baml: str) -> str | None:
    m = _FUNC_RE.search(baml)
    return m.group(1) if m else None


def translate_site(
    client: GeminiClient,
    site: CallSite,
    examples: str,
    previous_error: str | None = None,
    previous_attempt: str | None = None,
    taken_names: list[str] | None = None,
) -> tuple[str, str | None]:
    """Run one Gemini call to generate a BAML file for this site.

    Returns (baml_source, detected_function_name). Caller is responsible for
    validating with baml-cli and looping on errors.
    """
    schema_block = site.inferred_schema or "(no nearby Pydantic class found — infer the shape from the prompt)"
    notes = "\n".join(f"- {n}" for n in site.notes) or "- (none)"

    name_block = ""
    if taken_names:
        joined = ", ".join(sorted(set(taken_names)))
        name_block = (
            "\n## Naming constraint\n\n"
            f"The following class and function names are already used by other migrated files in this project "
            f"and must NOT be re-used: {joined}. Pick distinct names (e.g. add a context-specific suffix or prefix)."
        )

    retry_block = ""
    if previous_error and previous_attempt:
        retry_block = (
            "\n## Previous attempt failed validation\n\n"
            "Your last output was rejected by `baml-cli check` with this error:\n\n"
            f"```\n{previous_error.strip()}\n```\n\n"
            "Here is what you generated last time:\n\n"
            f"```baml\n{previous_attempt.strip()}\n```\n\n"
            "Fix the error and regenerate the complete file."
        )

    prompt = PROMPT_TEMPLATE.format(
        examples=examples,
        pattern_type=site.pattern_type,
        file=site.file,
        line=site.line,
        notes=notes,
        schema_block=schema_block,
        snippet=site.raw_snippet,
        context=site.surrounding_context,
        retry_block=retry_block + name_block,
    )

    raw = client.generate(prompt, system=SYSTEM_PROMPT)
    baml = strip_markdown_fences(raw)
    fn_name = _detect_function_name(baml)
    log.debug("translated %s → fn=%s (%d chars)", site.display_id(), fn_name, len(baml))
    return baml, fn_name


def python_usage_snippet(function_name: str, return_type: str | None = None, arg_hint: str = "...") -> str:
    """Generate a tiny Python usage example showing how to invoke the BAML client."""
    return (
        "from baml_client import b\n\n"
        f"result = b.{function_name}({arg_hint})\n"
        "print(result)"
    )


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------


def load_keys_from_env(provider: Provider | None = None) -> list[str]:
    """Read the provider's API key env var (comma-separated for multi-key).

    Defaults to Gemini (GEMINI_API_KEY) when no provider is given, preserving
    the original signature. Multi-key splitting makes sense for free-tier
    rotation; for paid providers it usually resolves to a single key.
    """
    env_var = provider.api_key_env if provider is not None else "GEMINI_API_KEY"
    raw = os.environ.get(env_var, "")
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]
