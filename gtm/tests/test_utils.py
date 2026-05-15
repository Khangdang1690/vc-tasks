"""Unit tests for utils.py — pure-function helpers, no network or subprocess."""

from __future__ import annotations

import pytest

from baml_scout.utils import (
    baml_cli_available,
    estimate_tokens,
    strip_markdown_fences,
)


class TestStripMarkdownFences:
    def test_strips_full_fenced_block(self):
        inp = "```baml\nfunction Foo() -> string {}\n```"
        assert strip_markdown_fences(inp) == "function Foo() -> string {}"

    def test_strips_unlabeled_fences(self):
        assert strip_markdown_fences("```\nhi\n```") == "hi"

    def test_strips_opening_fence_without_closing(self):
        # Sometimes models hallucinate an opening but no close.
        assert strip_markdown_fences("```py\nx = 1") == "x = 1"

    def test_passthrough_when_no_fence(self):
        assert strip_markdown_fences("function Bar() {}") == "function Bar() {}"

    def test_preserves_surrounding_whitespace_via_strip(self):
        assert strip_markdown_fences("\n\n```py\nx\n```\n\n") == "x"

    def test_empty_input(self):
        assert strip_markdown_fences("") == ""

    def test_only_fence(self):
        assert strip_markdown_fences("```") == ""


class TestEstimateTokens:
    def test_short_text(self):
        # 11 chars / 4 = 2 (floor)
        assert estimate_tokens("hello world") == 2

    def test_empty_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_minimum_is_one_for_non_empty(self):
        # Single char would give 0 from int division, but the floor is 1.
        assert estimate_tokens("a") == 1

    def test_scales_linearly(self):
        # 40 chars / 4 = 10
        assert estimate_tokens("x" * 40) == 10


class TestBamlCliAvailable:
    def test_returns_bool(self):
        # Either installed or not — both are valid, just check the contract.
        assert isinstance(baml_cli_available(), bool)
