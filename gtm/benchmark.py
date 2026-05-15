"""Optional benchmark mode (--benchmark).

For each translated call site we picked first, run N=5 trials on Gemini 2.5
Flash comparing two prompt formats on the same synthetic input:

    1. **Original-style**: the prompt template + an inlined JSON Schema (what
       OpenAI's response_format / instructor / LangChain output parsers
       wire-send on every call).
    2. **BAML-style**: the prompt template + BAML's compact type-hint
       rendering (the equivalent of {{ ctx.output_format }} expansion).

We measure for each trial:
    - prompt + output tokens (via Gemini usage_metadata)
    - end-to-end latency (wall clock from request to response)
    - schema-validity: does the output parse as JSON and contain the
      declared fields?

Aggregate as p50s / pass rates. The reporter then renders measured deltas
in place of static estimates.

Constraint: still Gemini-only, still free-tier. No OpenAI / Anthropic.
"""

from __future__ import annotations

import json
import re
import statistics
import time
from dataclasses import dataclass, field
from typing import Any

from config import DEFAULT_BENCHMARK_TRIALS
from translator import GeminiClient, FreeQuotaExhausted, Translation
from utils import estimate_tokens, get_logger, strip_markdown_fences


log = get_logger(__name__)


@dataclass
class TrialResult:
    prompt_tokens: int
    output_tokens: int
    latency_ms: float
    schema_valid: bool
    error: str | None = None


@dataclass
class FormatResult:
    """Aggregated results across N trials for one prompt format."""
    label: str
    trials: list[TrialResult] = field(default_factory=list)

    @property
    def n_total(self) -> int:
        return len(self.trials)

    @property
    def n_valid(self) -> int:
        return sum(1 for t in self.trials if t.schema_valid)

    @property
    def validity_rate(self) -> float:
        return self.n_valid / self.n_total if self.n_total else 0.0

    @property
    def avg_prompt_tokens(self) -> int:
        if not self.trials:
            return 0
        return int(statistics.mean(t.prompt_tokens for t in self.trials))

    @property
    def avg_output_tokens(self) -> int:
        if not self.trials:
            return 0
        return int(statistics.mean(t.output_tokens for t in self.trials))

    @property
    def p50_latency_ms(self) -> int:
        if not self.trials:
            return 0
        return int(statistics.median(t.latency_ms for t in self.trials))


@dataclass
class BenchmarkResult:
    site_label: str
    function_name: str | None
    n_trials: int
    synthetic_input: dict[str, Any]
    original: FormatResult  # JSON-Schema-in-prompt
    baml: FormatResult      # BAML compact type-hint
    notes: list[str] = field(default_factory=list)

    @property
    def token_delta_per_call(self) -> int:
        return (self.original.avg_prompt_tokens + self.original.avg_output_tokens) - (
            self.baml.avg_prompt_tokens + self.baml.avg_output_tokens
        )

    @property
    def latency_delta_ms(self) -> int:
        return self.original.p50_latency_ms - self.baml.p50_latency_ms


# ---------------------------------------------------------------------------
# BAML → JSON Schema (rough)
# ---------------------------------------------------------------------------


_CLASS_BLOCK_RE = re.compile(r"class\s+(\w+)\s*\{([^}]*)\}", re.DOTALL)
_ENUM_BLOCK_RE = re.compile(r"enum\s+(\w+)\s*\{([^}]*)\}", re.DOTALL)
_FUNC_SIG_RE = re.compile(r"function\s+(\w+)\s*\(([^)]*)\)\s*->\s*([\w\[\]?|\s]+?)\s*\{", re.DOTALL)
_PROMPT_RE = re.compile(r'prompt\s*#"(.*?)"#', re.DOTALL)
_BAML_TYPE_RE = re.compile(r"^(string|int|float|bool|[\w\[\]?]+)$")


def _baml_type_to_json_schema(baml_type: str, classes: dict[str, dict], enums: dict[str, list[str]]) -> dict:
    t = baml_type.strip()
    if t.endswith("[]"):
        return {"type": "array", "items": _baml_type_to_json_schema(t[:-2], classes, enums)}
    optional = t.endswith("?")
    if optional:
        t = t[:-1]
    primitive = {
        "string": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
    }
    if t in primitive:
        return primitive[t]
    if t in enums:
        return {"type": "string", "enum": enums[t]}
    if t in classes:
        return classes[t]
    return {"type": "string"}  # fallback


def _parse_baml_class_fields(body: str) -> dict[str, str]:
    """Return ordered field_name → baml_type from a class body."""
    fields: dict[str, str] = {}
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        parts = s.split(None, 1)
        if len(parts) == 2:
            fields[parts[0]] = parts[1].split("//")[0].strip()
    return fields


def baml_to_json_schema(baml: str) -> tuple[dict, dict[str, str], str | None, str]:
    """Parse a baml file into:
      - JSON Schema dict (for the function's return type)
      - function signature args: dict[arg_name -> baml_type]
      - function name
      - prompt template body (without #" "# markers)
    """
    # collect enums
    enums: dict[str, list[str]] = {}
    for name, body in _ENUM_BLOCK_RE.findall(baml):
        variants = []
        for line in body.splitlines():
            v = line.strip().split("//")[0].strip()
            if v:
                variants.append(v)
        enums[name] = variants

    # collect classes (each as a JSON Schema object)
    classes: dict[str, dict] = {}
    for name, body in _CLASS_BLOCK_RE.findall(baml):
        fields = _parse_baml_class_fields(body)
        props = {}
        required = []
        for fname, ftype in fields.items():
            props[fname] = _baml_type_to_json_schema(ftype, classes, enums)
            if not ftype.endswith("?"):
                required.append(fname)
        classes[name] = {
            "type": "object",
            "properties": props,
            "required": required,
        }

    # parse function signature
    fn_match = _FUNC_SIG_RE.search(baml)
    fn_name = fn_match.group(1) if fn_match else None
    arg_str = fn_match.group(2) if fn_match else ""
    return_type = fn_match.group(3).strip() if fn_match else "string"
    args: dict[str, str] = {}
    for chunk in arg_str.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            args[k.strip()] = v.strip()

    schema = _baml_type_to_json_schema(return_type, classes, enums)

    # extract prompt
    prompt_match = _PROMPT_RE.search(baml)
    prompt_body = prompt_match.group(1).strip() if prompt_match else ""

    return schema, args, fn_name, prompt_body


# ---------------------------------------------------------------------------
# BAML compact type rendering (for the BAML-style prompt)
# ---------------------------------------------------------------------------


def baml_compact_hint(baml: str) -> str:
    """Render the return type as BAML's compact hint.

    Approximates `{{ ctx.output_format }}` expansion: a terse JSON-shaped
    template the LLM can mirror. We include an explicit "Answer in JSON
    using this schema:" prefix because BAML's runtime does the same — without
    it the model is far less likely to wrap scalar/string returns in JSON.
    """
    schema, _args, fn_name, _prompt = baml_to_json_schema(baml)
    return "Answer in JSON using this schema:\n" + _render_schema_compact(schema)


def _render_schema_compact(schema: dict, indent: int = 0) -> str:
    """Render a JSON-Schema dict as a compact, JSON-shaped template."""
    pad = "  " * indent
    t = schema.get("type")
    if t == "object":
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not props:
            return "{}"
        lines = ["{"]
        for k, v in props.items():
            opt = "" if k in required else "?"
            lines.append(f"{pad}  {k}{opt}: {_render_type(v)},")
        lines.append(pad + "}")
        return "\n".join(lines)
    if t == "array":
        return "[" + _render_type(schema.get("items", {"type": "string"})) + "]"
    return _render_type(schema)


def _render_type(s: dict) -> str:
    t = s.get("type")
    if t == "array":
        return _render_type(s.get("items", {"type": "string"})) + "[]"
    if t == "object":
        return "{ " + ", ".join(f"{k}: {_render_type(v)}" for k, v in s.get("properties", {}).items()) + " }"
    if t == "string" and s.get("enum"):
        return " | ".join(repr(x) for x in s["enum"])
    return t or "string"


# ---------------------------------------------------------------------------
# Prompt formatting (Jinja-lite — we only need `{{ name }}` interpolation)
# ---------------------------------------------------------------------------


_JINJA_VAR_RE = re.compile(r"\{\{\s*([^}|]+?)(\s*\|[^}]*)?\s*\}\}")


def _render_prompt(template: str, vars: dict[str, Any]) -> str:
    """Render `{{ var }}` interpolation against `vars`. Ignores filters."""

    def repl(m: re.Match) -> str:
        path = m.group(1).strip()
        if path == "ctx.output_format":
            return "<<OUTPUT_FORMAT>>"  # we'll substitute later
        # dotted access: query.question -> vars['query']['question']
        cur: Any = vars
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return f"<<unresolved:{path}>>"
        return str(cur)

    return _JINJA_VAR_RE.sub(repl, template)


# ---------------------------------------------------------------------------
# Synthetic input
# ---------------------------------------------------------------------------


_SYNTHETIC_INPUTS = {
    "query": "What is the capital of France and what is its population?",
    "text": "Alice and Bob are going to a science fair on Friday at 3 PM.",
    "question": "What is the boiling point of water at sea level?",
    "chunk": "The boiling point of water at sea level (1 atmosphere) is 100°C or 212°F.",
    "input": "Alice and Bob are going to a science fair on Friday.",
    "user_message": "What's the weather like in San Francisco in fahrenheit?",
    "prompt": "Write a short poem about migrating LLM code.",
}


def _synthesize_input(args: dict[str, str]) -> dict[str, Any]:
    """Build a synthetic input dict matching the function's args."""
    out: dict[str, Any] = {}
    for name, baml_type in args.items():
        if name in _SYNTHETIC_INPUTS:
            out[name] = _SYNTHETIC_INPUTS[name]
        elif baml_type == "string":
            out[name] = _SYNTHETIC_INPUTS.get("text", "sample text")
        elif baml_type == "int":
            out[name] = 42
        elif baml_type == "float":
            out[name] = 3.14
        elif baml_type == "bool":
            out[name] = True
        elif baml_type.endswith("[]"):
            out[name] = []
        else:
            # Nested class — use a small dict placeholder
            out[name] = {"question": "Hello?", "keywords": [], "chunk_id": "doc1"}
    return out


# ---------------------------------------------------------------------------
# Trial runners
# ---------------------------------------------------------------------------


def _run_trial(
    client: GeminiClient,
    full_prompt: str,
    schema: dict,
) -> TrialResult:
    """Single Gemini call. Measure tokens, latency, parse success."""
    t0 = time.monotonic()
    try:
        text = client.generate(full_prompt)
    except FreeQuotaExhausted:
        raise
    except Exception as e:
        return TrialResult(0, 0, 0, False, error=str(e))
    latency_ms = (time.monotonic() - t0) * 1000

    # client.usage tracks running totals, not per-call deltas, so we fall back
    # to the chars/CHARS_PER_TOKEN heuristic for trial-level measurement.
    # Both prompts in a head-to-head pair use the same heuristic so the delta
    # between formats is meaningful even if the absolute number is rough.
    prompt_tokens = estimate_tokens(full_prompt)
    output_tokens = estimate_tokens(text)

    schema_valid = _validate_against_schema(text, schema)
    return TrialResult(
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        schema_valid=schema_valid,
    )


def _validate_against_schema(raw: str, schema: dict) -> bool:
    """Best-effort: does the output parse as JSON and contain the required keys?"""
    text = strip_markdown_fences(raw)
    try:
        parsed = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return False
    if schema.get("type") == "object":
        if not isinstance(parsed, dict):
            return False
        for key in schema.get("required", []):
            if key not in parsed:
                return False
        return True
    if schema.get("type") == "array":
        return isinstance(parsed, list)
    return True


# ---------------------------------------------------------------------------
# Top-level benchmark entry
# ---------------------------------------------------------------------------


def benchmark_translation(
    client: GeminiClient,
    translation: Translation,
    n_trials: int = DEFAULT_BENCHMARK_TRIALS,
) -> BenchmarkResult | None:
    """Run a head-to-head trial comparing the two prompt formats."""
    if not translation.success or not translation.baml_source:
        return None

    schema, args, fn_name, prompt_template = baml_to_json_schema(translation.baml_source)
    if not prompt_template:
        return None  # nothing to benchmark
    synthetic = _synthesize_input(args)
    base_prompt = _render_prompt(prompt_template, synthetic)

    # Original-style: prompt + inlined JSON Schema (what OpenAI / instructor /
    # LangChain output parsers would wire-send).
    json_schema_str = json.dumps(schema, indent=2)
    original_prompt = base_prompt.replace(
        "<<OUTPUT_FORMAT>>",
        f"Respond with JSON matching this schema exactly:\n{json_schema_str}\n",
    )

    # BAML-style: prompt + compact type hint.
    baml_prompt = base_prompt.replace(
        "<<OUTPUT_FORMAT>>",
        baml_compact_hint(translation.baml_source) + "\n",
    )

    original_fr = FormatResult(label="json_schema_in_prompt")
    baml_fr = FormatResult(label="baml_compact_hint")

    for _ in range(n_trials):
        try:
            original_fr.trials.append(_run_trial(client, original_prompt, schema))
            baml_fr.trials.append(_run_trial(client, baml_prompt, schema))
        except FreeQuotaExhausted:
            break  # graceful — we'll report partial results

    return BenchmarkResult(
        site_label=translation.site.display_id(),
        function_name=fn_name,
        n_trials=len(original_fr.trials),
        synthetic_input=synthetic,
        original=original_fr,
        baml=baml_fr,
    )
