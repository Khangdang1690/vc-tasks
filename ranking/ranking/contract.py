"""Data contract between Claude Code (the research step) and the ranking pipeline.

Single source of truth for the input JSON shape. Each sub-score is an object:

    {"value": <int 1..5> | null, "reasoning": "From <evidence>, we can infer that <something>."}

`value` is null when the metric is genuinely unknown. `reasoning` is required whenever
`value` is non-null — it should cite the specific evidence used (URL or named source
inline) and state the inference drawn. This replaces a separate evidence array: every
score is self-justifying.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Score(_Strict):
    value: Optional[int] = Field(default=None, ge=1, le=5)
    reasoning: str = ""

    @model_validator(mode="after")
    def _require_reasoning_when_scored(self) -> "Score":
        if self.value is not None and not self.reasoning.strip():
            raise ValueError(
                "reasoning is required when value is set "
                "(format: 'From <evidence>, we can infer that <something>.')"
            )
        return self


class Team(_Strict):
    founder_market_fit: Score
    technical_depth: Score
    prior_founding_experience: Score
    team_completeness: Score
    network_credibility: Score


class Market(_Strict):
    tam_size: Score
    growth_rate: Score
    timing: Score
    competitive_intensity_inv: Score


class Product(_Strict):
    differentiation: Score
    technical_moat: Score
    velocity: Score
    defensibility: Score


class Traction(_Strict):
    revenue_signal: Score
    users_customers: Score
    growth_rate: Score
    engagement_retention: Score


class Startup(_Strict):
    name: str = Field(min_length=1)
    website: HttpUrl
    one_liner: str = ""
    stage: Literal["pre_seed", "seed"]
    team: Team
    market: Market
    product: Product
    traction: Traction
    notes: str = ""


class StartupBatch(_Strict):
    schema_version: Literal["1.0"]
    startups: list[Startup]


PILLAR_MODELS: dict[str, type[_Strict]] = {
    "team": Team,
    "market": Market,
    "product": Product,
    "traction": Traction,
}
