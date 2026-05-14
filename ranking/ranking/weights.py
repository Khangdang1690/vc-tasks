"""Pillar weights. Single source of truth.

Weights are per-stage: earlier stages weight founder/team signal heavier,
later stages weight execution/traction heavier. Editing these numbers re-runs
the pipeline with a new thesis. Keep each row summed to 1.0.
"""

from __future__ import annotations

from ranking.contract import STAGES

PILLARS: tuple[str, ...] = ("team", "market", "product", "traction")

WEIGHTS_BY_STAGE: dict[str, dict[str, float]] = {
    "pre_seed": {"team": 0.45, "market": 0.25, "product": 0.20, "traction": 0.10},
    "seed":     {"team": 0.40, "market": 0.25, "product": 0.20, "traction": 0.15},
    "series_a": {"team": 0.30, "market": 0.25, "product": 0.20, "traction": 0.25},
    "series_b": {"team": 0.20, "market": 0.25, "product": 0.25, "traction": 0.30},
    "series_c": {"team": 0.15, "market": 0.20, "product": 0.25, "traction": 0.40},
}


def weights_for(stage: str) -> dict[str, float]:
    return WEIGHTS_BY_STAGE[stage]


# Backward-compat alias: legacy callers that imported `WEIGHTS` get seed weights.
WEIGHTS: dict[str, float] = WEIGHTS_BY_STAGE["seed"]


assert set(WEIGHTS_BY_STAGE.keys()) == set(STAGES), (
    f"WEIGHTS_BY_STAGE keys {set(WEIGHTS_BY_STAGE.keys())} must match STAGES {set(STAGES)}"
)
for _stage, _row in WEIGHTS_BY_STAGE.items():
    assert set(_row.keys()) == set(PILLARS), (
        f"WEIGHTS_BY_STAGE[{_stage!r}] keys must match PILLARS"
    )
    _total = sum(_row.values())
    assert abs(_total - 1.0) < 1e-9, (
        f"WEIGHTS_BY_STAGE[{_stage!r}] must sum to 1.0, got {_total}"
    )
