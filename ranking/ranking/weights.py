"""Pillar weights. Single source of truth.

Editing these numbers re-runs the pipeline with a new thesis. Keep them summed to 1.0.
"""

from __future__ import annotations

WEIGHTS: dict[str, float] = {
    "team": 0.40,
    "market": 0.25,
    "product": 0.20,
    "traction": 0.15,
}

PILLARS: tuple[str, ...] = ("team", "market", "product", "traction")

_total = sum(WEIGHTS.values())
assert abs(_total - 1.0) < 1e-9, f"WEIGHTS must sum to 1.0, got {_total}"
assert set(WEIGHTS.keys()) == set(PILLARS), "WEIGHTS keys must match PILLARS"
