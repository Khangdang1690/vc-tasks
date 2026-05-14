"""Scoring math, tie-breaking, and determinism tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranking.cli import run as cli_run
from ranking.contract import STAGES, StartupBatch
from ranking.scoring import rank, score_pillar, score_startup
from ranking.weights import WEIGHTS, WEIGHTS_BY_STAGE, weights_for

FIXTURE = Path(__file__).parent / "fixtures" / "sample.json"


def _load_batch() -> StartupBatch:
    return StartupBatch.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _score(value: int | None, reasoning: str = "") -> dict:
    if value is None:
        return {"value": None, "reasoning": ""}
    return {"value": value, "reasoning": reasoning or f"From test fixture (value={value}), we can infer this anchor."}


def _uniform_pillar(value: int | None, fields: list[str]) -> dict:
    return {f: _score(value) for f in fields}


def _uniform_startup(name: str, website: str, value: int) -> dict:
    return {
        "name": name,
        "website": website,
        "one_liner": "uniform-score test",
        "stage": "seed",
        "team": _uniform_pillar(value, [
            "founder_market_fit", "technical_depth", "prior_founding_experience",
            "team_completeness", "network_credibility",
        ]),
        "market": _uniform_pillar(value, [
            "tam_size", "growth_rate", "timing", "competitive_intensity_inv",
        ]),
        "product": _uniform_pillar(value, [
            "differentiation", "technical_moat", "velocity", "defensibility",
        ]),
        "traction": _uniform_pillar(value, [
            "revenue_signal", "users_customers", "growth_rate", "engagement_retention",
        ]),
        "notes": "",
    }


# ---------- pillar math ----------

def test_pillar_normalization_all_threes():
    batch = _load_batch()
    charlie = next(s for s in batch.startups if s.name == "Charlie Co")
    result = score_pillar(charlie, "market")
    assert result.raw_mean == pytest.approx(3.0)
    assert result.normalized == pytest.approx(50.0)
    assert result.filled == 4
    assert not result.missing


def test_pillar_null_is_excluded_from_mean():
    batch = _load_batch()
    bravo = next(s for s in batch.startups if s.name == "Bravo Inc")
    # team has 4 filled: 3, 4, null, 3, 3 → mean of [3, 4, 3, 3] = 3.25
    result = score_pillar(bravo, "team")
    assert result.filled == 4
    assert result.raw_mean == pytest.approx(3.25)
    assert result.normalized == pytest.approx((3.25 - 1) / 4 * 100)


def test_missing_pillar_records_warning_and_zero():
    batch = _load_batch()
    charlie = next(s for s in batch.startups if s.name == "Charlie Co")
    scored = score_startup(charlie)
    team = scored.pillars["team"]
    assert team.missing
    assert team.normalized == 0.0
    assert team.raw_mean is None
    assert any("team" in w for w in scored.warnings)


def test_total_uses_weights():
    batch = _load_batch()
    charlie = next(s for s in batch.startups if s.name == "Charlie Co")
    scored = score_startup(charlie)
    # team=0, market=50, product=50, traction=50; use stage-specific weights.
    w = weights_for(charlie.stage)
    expected = 0 * w["team"] + 50 * (w["market"] + w["product"] + w["traction"])
    assert scored.total == pytest.approx(round(expected, 2))


# ---------- ranking ----------

def test_ranking_is_total_desc():
    batch = _load_batch()
    ranked = rank(batch)
    totals = [s.total for s in ranked]
    assert totals == sorted(totals, reverse=True)


def test_alpha_beats_bravo():
    # Alpha has stronger team (heaviest pillar) and full data
    batch = _load_batch()
    ranked = rank(batch)
    names = [s.startup.name for s in ranked]
    assert names.index("Alpha Labs") < names.index("Bravo Inc")


# ---------- tie-breaking ----------

def test_tiebreak_by_name_alphabetical():
    raw = {
        "schema_version": "1.0",
        "startups": [
            _uniform_startup("Zebra Co", "https://zebra.example.com", 3),
            _uniform_startup("Apex Co", "https://apex.example.com", 3),
        ],
    }
    batch = StartupBatch.model_validate(raw)
    ranked = rank(batch)
    assert [s.startup.name for s in ranked] == ["Apex Co", "Zebra Co"]


def test_higher_team_wins_when_other_pillars_equal():
    raw = {
        "schema_version": "1.0",
        "startups": [
            _uniform_startup("Low Team", "https://low.example.com", 5),
            _uniform_startup("High Team", "https://high.example.com", 5),
        ],
    }
    # mutate Low Team's team pillar to 2s
    for f in raw["startups"][0]["team"]:
        raw["startups"][0]["team"][f] = _score(2)
    batch = StartupBatch.model_validate(raw)
    ranked = rank(batch)
    assert ranked[0].startup.name == "High Team"
    assert ranked[0].total > ranked[1].total


# ---------- weights ----------

def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("stage", STAGES)
def test_per_stage_weights_sum_to_one(stage: str):
    assert sum(WEIGHTS_BY_STAGE[stage].values()) == pytest.approx(1.0)


def test_pillar_weights_exposed_on_result():
    batch = _load_batch()
    alpha = next(s for s in batch.startups if s.name == "Alpha Labs")
    scored = score_startup(alpha)
    assert scored.pillar_weights == weights_for(alpha.stage)


def test_weights_vary_by_stage():
    # Same sub-scores, but team-heavy: 5s on team, 1s elsewhere.
    # pre_seed weights team at 0.45; series_c weights team at 0.15.
    # So pre_seed total should be strictly higher than series_c.
    raw_pre = _uniform_startup("Team Heavy PS", "https://ps.example.com", 1)
    raw_pre["stage"] = "pre_seed"
    for f in raw_pre["team"]:
        raw_pre["team"][f] = _score(5)

    raw_c = json.loads(json.dumps(raw_pre))
    raw_c["name"] = "Team Heavy SC"
    raw_c["website"] = "https://sc.example.com"
    raw_c["stage"] = "series_c"

    batch = StartupBatch.model_validate(
        {"schema_version": "1.0", "startups": [raw_pre, raw_c]}
    )
    pre, sc = batch.startups
    assert score_startup(pre).total > score_startup(sc).total


# ---------- end-to-end determinism ----------

def test_cli_output_is_byte_deterministic(tmp_path):
    out1 = tmp_path / "run1.md"
    out2 = tmp_path / "run2.md"
    assert cli_run(FIXTURE, str(out1)) == 0
    assert cli_run(FIXTURE, str(out2)) == 0
    assert out1.read_bytes() == out2.read_bytes()


def test_cli_rejects_invalid_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "1.0", "startups": []}', encoding="utf-8")
    assert cli_run(bad, str(tmp_path / "out.md")) == 0
    bad.write_text('{"schema_version": "1.0"}', encoding="utf-8")
    assert cli_run(bad, str(tmp_path / "out.md")) == 2
