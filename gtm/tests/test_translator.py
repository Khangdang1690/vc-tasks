"""Tests for translator.py — only the pure-function helpers.

GeminiClient / LLMClient need real keys and would burn quota; covered by
the live scout.py smoke run instead. Here we exercise the small helpers
that have outsized leverage on output correctness.
"""

from __future__ import annotations

import pytest

from baml_scout.translator import (
    _detect_function_name,
    declared_names,
    python_usage_snippet,
    seed_baml_examples,
)


class TestDeclaredNames:
    def test_function_name(self):
        baml = 'function ExtractKeywords(q: string) -> string[] { client "x" prompt #"y"# }'
        assert declared_names(baml) == ["ExtractKeywords"]

    def test_class_and_enum(self):
        baml = """
        class Address { street string; city string }
        enum Sentiment { POSITIVE NEGATIVE NEUTRAL }
        function Foo(x: string) -> Address { client "openai/gpt-4o-mini" prompt #"y"# }
        """
        names = declared_names(baml)
        assert set(names) == {"Address", "Sentiment", "Foo"}

    def test_empty_baml_returns_empty(self):
        assert declared_names("") == []

    def test_lowercase_names_ignored(self):
        # The regex requires a leading uppercase letter — bare-lowercase class
        # names aren't valid BAML and shouldn't show up here.
        baml = "class lowercase { name string }"
        assert declared_names(baml) == []


class TestDetectFunctionName:
    def test_picks_first_function(self):
        baml = 'function MyFunction(x: string) -> string { client "y" prompt #"z"# }'
        assert _detect_function_name(baml) == "MyFunction"

    def test_no_function_returns_none(self):
        assert _detect_function_name("class Foo { name string }") is None


class TestPythonUsageSnippet:
    def test_includes_function_call(self):
        snippet = python_usage_snippet("ExtractKeywords")
        assert "from baml_client import b" in snippet
        assert "b.ExtractKeywords(...)" in snippet


class TestSeedBamlExamples:
    def test_bundled_resource_is_usable(self):
        """Verify the package-data wiring: a fresh seed_baml_examples() call
        without any cache must return the wheel-bundled BAML examples.

        This is the regression test that catches a broken pyproject.toml
        force-include block — the most fragile part of the packaging story.
        """
        text = seed_baml_examples()
        assert isinstance(text, str)
        assert len(text) > 1000  # Bundle is ~7-8KB; if it's empty something's wrong.
        assert "function " in text  # Has BAML function examples.
        assert "class " in text     # Has BAML class examples.
