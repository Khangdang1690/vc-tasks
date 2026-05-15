"""Tests for reporter.py — delta math and tweet summary on real-shaped inputs."""

from __future__ import annotations

from textwrap import dedent
from unittest.mock import MagicMock

import pytest

from baml_scout.reporter import (
    DeltaEstimate,
    _baml_schema_chars,
    _count_baml_fields,
    _estimate_json_schema_chars,
    build_tweet_summary,
    compute_delta,
)


def _make_translation(baml_source: str, success: bool = True):
    """Build a minimal Translation-shape mock just for compute_delta."""
    t = MagicMock()
    t.success = success
    t.baml_source = baml_source if success else None
    return t


class TestBamlFieldCount:
    def test_counts_flat_fields(self):
        baml = dedent("""
            class Foo {
              name string
              age int
              email string?
            }
        """)
        assert _count_baml_fields(baml) == 3

    def test_skips_comments_and_blank_lines(self):
        baml = dedent("""
            class Foo {
              // this is a comment, shouldn't count
              name string

              age int
            }
        """)
        assert _count_baml_fields(baml) == 2

    def test_no_class_blocks(self):
        assert _count_baml_fields("function Foo() -> string {}") == 0


class TestSchemaSizing:
    def test_baml_chars_zero_when_no_classes(self):
        assert _baml_schema_chars("function Foo() {}") == 0

    def test_json_schema_chars_zero_when_no_fields(self):
        assert _estimate_json_schema_chars("function Foo() {}") == 0

    def test_json_schema_chars_scales_with_fields(self):
        baml = dedent("""
            class Foo {
              a string
              b string
              c string
            }
        """)
        # base_overhead (80) + 3 fields × 30 = 170
        assert _estimate_json_schema_chars(baml) == 170


class TestComputeDelta:
    def test_empty_translations(self):
        d = compute_delta([])
        assert d.tokens_saved_per_call == 0
        assert d.schema_ratio_str == "—"

    def test_with_real_class(self):
        baml = dedent("""
            class Person {
              name string
              age int
              email string
            }
            function ExtractPerson(text: string) -> Person {
              client "openai/gpt-4o-mini"
              prompt #"{{ text }} {{ ctx.output_format }}"#
            }
        """)
        d = compute_delta([_make_translation(baml)])
        # JSON Schema overhead should exceed BAML class definition.
        assert d.original_schema_chars > d.baml_schema_chars
        assert "compaction" in d.schema_ratio_str
        assert d.tokens_saved_per_call >= 0


class TestTweetSummary:
    def test_includes_translated_count(self):
        delta = DeltaEstimate(0, 0, 0, 0, 0, "—")
        summary = build_tweet_summary(
            repo_label="acme/repo",
            sites_translated=5,
            sites_failed=0,
            delta=delta,
            token_count=10_000,
            patterns_present=["instructor"],
        )
        assert "translated 5" in summary
        assert "instructor" in summary
        assert "10,000 tokens" in summary

    def test_mentions_failures_when_present(self):
        delta = DeltaEstimate(0, 0, 0, 0, 0, "—")
        summary = build_tweet_summary(
            repo_label="acme/repo",
            sites_translated=3,
            sites_failed=2,
            delta=delta,
            token_count=1000,
            patterns_present=["instructor"],
        )
        assert "2 site(s) flagged" in summary

    def test_uses_repo_url_when_given(self):
        delta = DeltaEstimate(0, 0, 0, 0, 0, "—")
        summary = build_tweet_summary(
            repo_label="acme/repo",
            sites_translated=1,
            sites_failed=0,
            delta=delta,
            token_count=1,
            patterns_present=["openai"],
            repo_url="https://github.com/acme/repo",
        )
        assert "https://github.com/acme/repo" in summary
