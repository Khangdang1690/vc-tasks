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
      "stage": "seed",                                   // "pre_seed" | "seed"

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

## Scoring Anchors (1 → 5)

### Team (40%)

| Field | 1 | 5 |
|---|---|---|
| founder_market_fit | No domain background | Lived the problem / built it at scale before |
| technical_depth | Generalist team | World-class (ex-FAANG staff, PhD, OSS lead) |
| prior_founding_experience | First-timers | Prior exit ≥ $100M |
| team_completeness | Solo / one-dimensional | Tech + commercial + design covered |
| network_credibility | No notable backers | Top-tier accelerator + tier-1 VC + named advisors |

### Market (25%)

| Field | 1 | 5 |
|---|---|---|
| tam_size | < $1B | > $100B |
| growth_rate | Flat / shrinking | > 40% CAGR |
| timing | Too early / too late | Clear inflection now |
| competitive_intensity_inv | Crowded, commoditized | Greenfield / structural advantage |

### Product (20%)

| Field | 1 | 5 |
|---|---|---|
| differentiation | Me-too | Category-defining angle |
| technical_moat | None | Hard tech / data network effects / IP |
| velocity | Stagnant | Weekly shipping cadence visible |
| defensibility | Easy to switch | High switching costs / lock-in |

### Traction (15%)

| Field | 1 | 5 |
|---|---|---|
| revenue_signal | $0, no pilots | Growing ARR with named logos |
| users_customers | None | Strong design partners or 1k+ active users |
| growth_rate | Flat | > 20% MoM |
| engagement_retention | Poor / churny | NRR > 110% or strong qualitative retention |

## Math (so you know how your scores will be aggregated)

```
pillar_raw    = mean(non-null sub-score VALUES)     # [1.0, 5.0]
pillar_norm   = (raw - 1) / 4 * 100                 # [0, 100]
pillar_norm   = 0.0 if pillar has zero filled sub-scores (warning emitted)
total         = Σ pillar_norm_i * weight_i          # [0, 100]
completeness  = filled_sub_scores / 17
```

## Tie-breaking (deterministic)

1. Total desc
2. Team normalized desc
3. Market normalized desc
4. Data completeness desc
5. Name asc (case-insensitive)
