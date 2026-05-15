"""Tests for the Provider abstraction — registry shape + lazy SDK loading."""

from __future__ import annotations

import pytest

from baml_scout.providers import (
    DEFAULT_PROVIDER,
    PROVIDER_NAMES,
    GeminiProvider,
    Provider,
    ProviderError,
    get_provider,
)


class TestRegistry:
    def test_default_is_gemini(self):
        assert DEFAULT_PROVIDER == "gemini"

    def test_provider_names_include_three(self):
        # Order matters for the CLI choices listing; lock it.
        assert PROVIDER_NAMES == ("gemini", "openai", "anthropic")

    def test_unknown_provider_raises(self):
        with pytest.raises(ProviderError, match="Unknown provider"):
            get_provider("not-a-real-provider")


class TestGeminiProvider:
    """google-genai is a required dep so Gemini must always load."""

    def test_loads(self):
        p = get_provider("gemini")
        assert isinstance(p, GeminiProvider)
        assert p.name == "gemini"
        assert p.default_model == "gemini-2.5-flash"
        assert p.api_key_env == "GEMINI_API_KEY"
        assert p.free_tier is True


class TestOpenAIProvider:
    """openai is an optional extra — it may or may not be installed."""

    def test_loads_or_raises_provider_error(self):
        try:
            p = get_provider("openai")
        except ProviderError as e:
            # When the extra isn't installed, we get a clear ProviderError
            # pointing the user at `pip install 'baml-scout[openai]'`.
            assert "openai" in str(e).lower()
            return
        assert p.name == "openai"
        assert p.api_key_env == "OPENAI_API_KEY"
        assert p.free_tier is False


class TestAnthropicProvider:
    """anthropic is an optional extra — same shape as OpenAI test above."""

    def test_loads_or_raises_provider_error(self):
        try:
            p = get_provider("anthropic")
        except ProviderError as e:
            assert "anthropic" in str(e).lower()
            return
        assert p.name == "anthropic"
        assert p.api_key_env == "ANTHROPIC_API_KEY"
        assert p.free_tier is False
