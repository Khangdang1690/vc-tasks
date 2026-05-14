# Data Contract — Claude Code → Ranking Pipeline

This is the contract Claude Code must satisfy when filling in `inputs/startups.json`.
The pipeline validates against [ranking/contract.py](ranking/contract.py) (Pydantic v2).

## Shape

Every sub-score is an object: `{"value": <int 1..5> | null, "reasoning": "..."}`.

```jsonc
{
  "schema_version": "1.0",
  "startups": [
    {
      "name": "Tigris Data",
      "website": "https://www.tigrisdata.com",
      "one_liner": "Globally-distributed S3-compatible object storage.",
      "stage": "series_a",  // "pre_seed" | "seed" | "series_a" | "series_b" | "series_c"

      "team": {
        "founder_market_fit": {
          "value": 4,
          "reasoning": "From founder LinkedIns showing 6+ years on Uber's storage team, we can infer strong founder-market fit."
        },
        "technical_depth": {
          "value": 5,
          "reasoning": "From the founder's GitHub showing OSS leadership on FoundationDB, we can infer world-class technical depth."
        },
        "prior_founding_experience": {"value": null, "reasoning": ""},
        "team_completeness": {
          "value": 3,
          "reasoning": "From the team page listing two technical co-founders and no commercial hire, we can infer a coverage gap."
        },
        "network_credibility": {
          "value": 4,
          "reasoning": "From a $25M Series A led by Spark (TechCrunch, 2024-09), we can infer strong network credibility."
        }
      },
      "market":   { /* same shape, 4 sub-scores */ },
      "product":  { /* same shape, 4 sub-scores */ },
      "traction": { /* same shape, 4 sub-scores */ },

      "notes": "Strong infra play, riding S3-egress backlash tailwind."
    }
  ]
}
```

## Rules

- **Every sub-score is `{"value": ..., "reasoning": "..."}`.** No bare integers.
- **`value`** is an integer in `[1, 5]` **or** `null` when unknown.
- **`reasoning`** is **required** whenever `value` is non-null. Whitespace-only is rejected.
- **Reasoning format:** `"From <specific evidence>, we can infer that <conclusion>."`
  - Cite the source inline (URL, publication + date, or named source). Primary sources preferred.
  - Brief is good — one sentence. Be specific, not vague.
- When `value` is `null`, `reasoning` may be empty (or used to record "no public info").
- `null` ≠ `0` ≠ `1`. `null` means "I couldn't find evidence." `1` means "I found evidence it's poor."
- **All 17 sub-score keys must be present** in every startup (set `value: null` if unknown).
- **No extra fields.** Pydantic is set to `extra="forbid"`; the pipeline rejects unknown keys.
- `competitive_intensity_inv` is **inverted**: a 5 means *low* competition (greenfield).

## Stage

The pipeline supports five stages: `pre_seed`, `seed`, `series_a`, `series_b`, `series_c`.

> **1→5 is always *relative to peers at the same stage.*** Cross-stage totals are
> not directly comparable — a Series C scoring 5 on `revenue_signal` is not the
> same bar as a seed scoring 5. The report stratifies leaderboards by stage so
> rankings stay apples-to-apples. The Traction anchors below are explicitly
> per-stage; Team / Market / Product anchors are stage-invariant.

### Pillar Weights by Stage

Earlier stages weight founder/team signal heavier; later stages weight execution/traction heavier.

| Stage | Team | Market | Product | Traction |
|---|---:|---:|---:|---:|
| pre_seed | 45% | 25% | 20% | 10% |
| seed     | 40% | 25% | 20% | 15% |
| series_a | 30% | 25% | 20% | 25% |
| series_b | 20% | 25% | 25% | 30% |
| series_c | 15% | 20% | 25% | 40% |

Edit [ranking/weights.py](ranking/weights.py) to change the thesis.

## Scoring Anchors (1 → 5)

### Team (stage-invariant)

| Field | 1 | 5 |
|---|---|---|
| founder_market_fit | No domain background | Lived the problem / built it at scale before |
| technical_depth | Generalist team | World-class (ex-FAANG staff, PhD, OSS lead) |
| prior_founding_experience | First-timers | Prior exit ≥ $100M |
| team_completeness | Solo / one-dimensional | Tech + commercial + design covered |
| network_credibility | No notable backers | Top-tier accelerator + tier-1 VC + named advisors |

### Market (stage-invariant)

| Field | 1 | 5 |
|---|---|---|
| tam_size | < $1B | > $100B |
| growth_rate | Flat / shrinking | > 40% CAGR |
| timing | Too early / too late | Clear inflection now |
| competitive_intensity_inv | Crowded, commoditized | Greenfield / structural advantage |

### Product (stage-invariant)

| Field | 1 | 5 |
|---|---|---|
| differentiation | Me-too | Category-defining angle |
| technical_moat | None | Hard tech / data network effects / IP |
| velocity | Stagnant | Weekly shipping cadence visible |
| defensibility | Easy to switch | High switching costs / lock-in |

### Traction (stage-dependent)

The Traction pillar is the one whose anchors shift most by stage — a Series C
with $5M ARR is struggling, while a seed with $5M ARR is exceptional.

#### `revenue_signal`

| Stage | 1 | 5 |
|---|---|---|
| pre_seed | No revenue concept | First LOIs / paid pilots |
| seed     | $0, no pilots | Growing ARR with named logos |
| series_a | < $100k ARR | $1–5M ARR with >100% NRR |
| series_b | < $2M ARR | $10M+ ARR, multi-product, >110% NRR |
| series_c | < $10M ARR | $50M+ ARR, international / multi-product |

#### `users_customers`

| Stage | 1 | 5 |
|---|---|---|
| pre_seed | None | A handful of design-partner conversations |
| seed     | None | 1k+ active users or named design partners |
| series_a | < 100 active accounts | 10k+ active users or 25+ paying customers |
| series_b | < 1k active accounts | 100k+ users or 100+ paying customers (incl. enterprise logos) |
| series_c | < 10k active accounts | 1M+ users or 500+ enterprise logos |

#### `growth_rate`

| Stage | 1 | 5 |
|---|---|---|
| pre_seed | No usage signal | Pre-launch waitlist growing weekly |
| seed     | Flat | > 20% MoM |
| series_a | Flat or < 10% MoM | > 15% MoM sustained |
| series_b | Flat | 2-3x YoY |
| series_c | Flat or contracting | > 60% YoY at scale |

#### `engagement_retention`

| Stage | 1 | 5 |
|---|---|---|
| pre_seed | No retention data | Strong qualitative pull from design partners |
| seed     | Poor / churny | Strong qualitative retention / early NRR > 100% |
| series_a | < 90% logo retention | NRR > 110% |
| series_b | < 100% NRR | NRR > 120% |
| series_c | < 105% NRR | NRR > 125%, low logo churn |

## Math (so you know how your scores will be aggregated)

```
pillar_raw    = mean(non-null sub-score VALUES)     # [1.0, 5.0]
pillar_norm   = (raw - 1) / 4 * 100                 # [0, 100]
pillar_norm   = 0.0 if pillar has zero filled sub-scores (warning emitted)
total         = Σ pillar_norm_i * weight_i(stage)   # [0, 100]
completeness  = filled_sub_scores / 17
```

## Tie-breaking (deterministic, within each stage cohort)

1. Total desc
2. Team normalized desc
3. Market normalized desc
4. Data completeness desc
5. Name asc (case-insensitive)
