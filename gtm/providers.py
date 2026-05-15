"""LLM provider adapters.

Default and recommended provider is Gemini 2.5 Flash on the free tier — it's
the only provider that costs $0 per call. OpenAI and Anthropic are supported
for users who knowingly opt in to paid APIs via `--provider`. The orchestrator
emits an explicit warning when a non-free provider is selected so a stray
flag can't silently bill someone.

Design notes:
  * Each provider is a small class that knows how to (a) construct its SDK
    client from an API key, (b) issue a single generate call returning a
    uniform GenerationResult, and (c) classify exceptions into our two
    internal categories (rate-limit / server-error).
  * SDK modules are imported lazily inside each provider's `__init__` so
    that `pip install baml-migration-scout` alone doesn't drag in `openai`
    or `anthropic` — they're optional extras.
  * Rate-limit semantics differ: Gemini's free tier has a daily reset and
    string-matches `resource_exhausted`; OpenAI/Anthropic both raise typed
    `RateLimitError` exceptions. The classifiers normalize this for the
    multi-key rotation loop in translator.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class GenerationResult:
    """Uniform return shape from any provider's generate() call."""
    text: str
    prompt_tokens: int
    output_tokens: int


class ProviderError(RuntimeError):
    """Raised when a provider name is unknown or its SDK isn't installed."""


class Provider(Protocol):
    """Adapter interface for an LLM provider."""

    name: str
    default_model: str
    api_key_env: str
    # True iff the provider has a sustained $0 tier we shouldn't bill past.
    # Drives the quota warning + the paid-provider confirmation in scout.py.
    free_tier: bool

    def make_client(self, api_key: str) -> Any: ...

    def generate(
        self,
        client: Any,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float,
        max_output_tokens: int,
        timeout_s: int,
    ) -> GenerationResult: ...

    def is_rate_limit_error(self, exc: BaseException) -> bool: ...

    def is_server_error(self, exc: BaseException) -> bool: ...


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Gemini 2.5 Flash via google-genai. Free-tier daily reset; the project
    default. Multi-key rotation on 429s lives in translator.py — this
    adapter only handles error classification."""

    name = "gemini"
    default_model = "gemini-2.5-flash"
    api_key_env = "GEMINI_API_KEY"
    free_tier = True

    def __init__(self) -> None:
        from google import genai
        from google.genai import errors as genai_errors
        from google.genai import types as genai_types
        self._genai = genai
        self._errors = genai_errors
        self._types = genai_types

    def make_client(self, api_key: str) -> Any:
        return self._genai.Client(api_key=api_key)

    def generate(
        self,
        client: Any,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float,
        max_output_tokens: int,
        timeout_s: int,
    ) -> GenerationResult:
        cfg = self._types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            http_options=self._types.HttpOptions(timeout=timeout_s * 1000),
        )
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        prompt_tokens = output_tokens = 0
        if resp.usage_metadata:
            prompt_tokens = resp.usage_metadata.prompt_token_count or 0
            output_tokens = resp.usage_metadata.candidates_token_count or 0
        text = (resp.text or "").strip()
        return GenerationResult(text=text, prompt_tokens=prompt_tokens, output_tokens=output_tokens)

    def is_rate_limit_error(self, exc: BaseException) -> bool:
        if not isinstance(exc, self._errors.ClientError):
            return False
        code = getattr(exc, "code", None)
        msg = str(exc).lower()
        return code == 429 or "resource_exhausted" in msg or "rate" in msg or "quota" in msg

    def is_server_error(self, exc: BaseException) -> bool:
        return isinstance(exc, self._errors.ServerError)


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------


class OpenAIProvider:
    """OpenAI via the v1+ Python SDK. Paid — opt-in only."""

    name = "openai"
    default_model = "gpt-4o-mini"
    api_key_env = "OPENAI_API_KEY"
    free_tier = False

    def __init__(self) -> None:
        try:
            import openai
        except ImportError as e:
            raise ProviderError(
                "openai SDK not installed. Install with `uv pip install openai` "
                "or `pip install 'baml-migration-scout[openai]'`."
            ) from e
        self._openai = openai

    def make_client(self, api_key: str) -> Any:
        return self._openai.OpenAI(api_key=api_key)

    def generate(
        self,
        client: Any,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float,
        max_output_tokens: int,
        timeout_s: int,
    ) -> GenerationResult:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
            timeout=timeout_s,
        )
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        return GenerationResult(text=text, prompt_tokens=prompt_tokens, output_tokens=output_tokens)

    def is_rate_limit_error(self, exc: BaseException) -> bool:
        return isinstance(exc, self._openai.RateLimitError)

    def is_server_error(self, exc: BaseException) -> bool:
        # APIError covers 5xx; APITimeoutError covers timeouts.
        return isinstance(exc, (self._openai.APIError, self._openai.APITimeoutError)) and not isinstance(
            exc, self._openai.RateLimitError
        )


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


class AnthropicProvider:
    """Anthropic via the official Python SDK. Paid — opt-in only."""

    name = "anthropic"
    default_model = "claude-3-5-sonnet-20241022"
    api_key_env = "ANTHROPIC_API_KEY"
    free_tier = False

    def __init__(self) -> None:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError(
                "anthropic SDK not installed. Install with `uv pip install anthropic` "
                "or `pip install 'baml-migration-scout[anthropic]'`."
            ) from e
        self._anthropic = anthropic

    def make_client(self, api_key: str) -> Any:
        return self._anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        client: Any,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float,
        max_output_tokens: int,
        timeout_s: int,
    ) -> GenerationResult:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "timeout": timeout_s,
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        # Anthropic returns a list of content blocks; the first text block is
        # the text we want. Tool/extended blocks would need richer handling,
        # but the translator prompt explicitly asks for plain text output.
        text_parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        text = "".join(text_parts).strip()
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        return GenerationResult(text=text, prompt_tokens=prompt_tokens, output_tokens=output_tokens)

    def is_rate_limit_error(self, exc: BaseException) -> bool:
        return isinstance(exc, self._anthropic.RateLimitError)

    def is_server_error(self, exc: BaseException) -> bool:
        return isinstance(exc, (self._anthropic.APIError, self._anthropic.APITimeoutError)) and not isinstance(
            exc, self._anthropic.RateLimitError
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


_REGISTRY: dict[str, type] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

# Names exposed to CLI --provider. Order matters: first entry is the default.
PROVIDER_NAMES = tuple(_REGISTRY.keys())
DEFAULT_PROVIDER = "gemini"


def get_provider(name: str) -> Provider:
    """Instantiate a provider by name. Raises ProviderError if unknown or
    the underlying SDK isn't installed.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ProviderError(
            f"Unknown provider {name!r}. Available: {', '.join(PROVIDER_NAMES)}."
        )
    return cls()
