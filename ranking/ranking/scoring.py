"""Deterministic scoring + ranking. No I/O, no randomness, no datetime.

Math:
  pillar_raw       = mean(non-null sub-scores)            in [1.0, 5.0]
  pillar_norm      = (raw - 1) / 4 * 100                  in [0, 100]
  pillar_norm      = 0.0  if the pillar has 0 sub-scores filled (warning recorded)
  total            = sum(pillar_norm_i * weight_i)        in [0, 100]
  data_completeness = non_null_sub_scores / total_sub_scores

Tie-break ladder:
  1. total desc
  2. team_norm desc
  3. market_norm desc
  4. data_completeness desc
  5. name asc (case-insensitive, then case-sensitive for full stability)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ranking.contract import Startup, StartupBatch
from ranking.weights import PILLARS, WEIGHTS


@dataclass(frozen=True)
class PillarResult:
    name: str
    normalized: float
    raw_mean: Optional[float]
    filled: int
    total: int
    missing: bool

    @property
    def completeness(self) -> float:
        return self.filled / self.total if self.total else 0.0


@dataclass(frozen=True)
class ScoredStartup:
    startup: Startup
    pillars: dict[str, PillarResult]
    total: float
    data_completeness: float
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _pillar_sub_scores(startup: Startup, pillar: str) -> list[Optional[int]]:
    model = getattr(startup, pillar)
    return [getattr(model, f).value for f in type(model).model_fields]


def score_pillar(startup: Startup, pillar: str) -> PillarResult:
    sub = _pillar_sub_scores(startup, pillar)
    total = len(sub)
    filled_vals = [v for v in sub if v is not None]
    filled = len(filled_vals)
    if filled == 0:
        return PillarResult(
            name=pillar,
            normalized=0.0,
            raw_mean=None,
            filled=0,
            total=total,
            missing=True,
        )
    raw_mean = sum(filled_vals) / filled
    normalized = (raw_mean - 1.0) / 4.0 * 100.0
    return PillarResult(
        name=pillar,
        normalized=normalized,
        raw_mean=raw_mean,
        filled=filled,
        total=total,
        missing=False,
    )


def score_startup(startup: Startup) -> ScoredStartup:
    pillars = {p: score_pillar(startup, p) for p in PILLARS}
    total = sum(pillars[p].normalized * WEIGHTS[p] for p in PILLARS)
    filled = sum(p.filled for p in pillars.values())
    total_subs = sum(p.total for p in pillars.values())
    completeness = filled / total_subs if total_subs else 0.0
    warnings = tuple(
        f"pillar '{p.name}' has no filled sub-scores; counted as 0"
        for p in pillars.values()
        if p.missing
    )
    return ScoredStartup(
        startup=startup,
        pillars=pillars,
        total=round(total, 2),
        data_completeness=round(completeness, 4),
        warnings=warnings,
    )


def _tiebreak_key(s: ScoredStartup) -> tuple:
    return (
        -s.total,
        -s.pillars["team"].normalized,
        -s.pillars["market"].normalized,
        -s.data_completeness,
        s.startup.name.lower(),
        s.startup.name,
    )


def rank(batch: StartupBatch) -> list[ScoredStartup]:
    scored = [score_startup(s) for s in batch.startups]
    scored.sort(key=_tiebreak_key)
    return scored
