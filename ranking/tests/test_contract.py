"""Schema validation tests for the data contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ranking.contract import Score, StartupBatch

FIXTURE = Path(__file__).parent / "fixtures" / "sample.json"


def _load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates():
    StartupBatch.model_validate(_load())


def test_score_value_below_one_rejected():
    raw = _load()
    raw["startups"][0]["team"]["founder_market_fit"] = {
        "value": 0,
        "reasoning": "From X, we can infer Y.",
    }
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_score_value_above_five_rejected():
    raw = _load()
    raw["startups"][0]["team"]["founder_market_fit"] = {
        "value": 6,
        "reasoning": "From X, we can infer Y.",
    }
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_null_value_with_empty_reasoning_accepted():
    raw = _load()
    raw["startups"][0]["team"]["founder_market_fit"] = {
        "value": None,
        "reasoning": "",
    }
    StartupBatch.model_validate(raw)


def test_scored_without_reasoning_rejected():
    raw = _load()
    raw["startups"][0]["team"]["founder_market_fit"] = {
        "value": 4,
        "reasoning": "",
    }
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_scored_with_whitespace_only_reasoning_rejected():
    with pytest.raises(ValidationError):
        Score.model_validate({"value": 3, "reasoning": "   "})


def test_score_extra_field_rejected():
    raw = _load()
    raw["startups"][0]["team"]["founder_market_fit"] = {
        "value": 4,
        "reasoning": "From X, we can infer Y.",
        "mystery": "x",
    }
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_pillar_extra_field_rejected():
    raw = _load()
    raw["startups"][0]["team"]["mystery_field"] = {
        "value": 3,
        "reasoning": "x",
    }
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_missing_pillar_field_rejected():
    raw = _load()
    del raw["startups"][0]["team"]["founder_market_fit"]
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_unknown_stage_rejected():
    raw = _load()
    raw["startups"][0]["stage"] = "series_a"
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_bad_schema_version_rejected():
    raw = _load()
    raw["schema_version"] = "2.0"
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)


def test_no_evidence_field_anywhere():
    """The new contract removes the separate evidence array entirely."""
    raw = _load()
    raw["startups"][0]["evidence"] = [{"claim": "x", "source": "https://x.com"}]
    with pytest.raises(ValidationError):
        StartupBatch.model_validate(raw)
