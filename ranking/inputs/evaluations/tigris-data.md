# Scoring Audit — Tigris Data

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~72.38/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
Cloudflare R2's zero-egress S3-compat already embedded in millions of Workers projects, plus AWS quietly trimming egress fees, collapses Tigris's primary wedge before the multi-region/AI-locality story compounds into pricing power.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | traction.growth_rate | 5 | "'has grown 8x every year since its founding' (≈19% MoM compounded)" | Reasoning's own arithmetic (≈19% MoM) sits *below* the >20% MoM 5-anchor — internal contradiction with the score. | Either find an explicit MoM/QoQ ≥ 20% figure in press, or drop value to 4 to match the arithmetic. |
| 🟡 | market.tam_size | 4 | "AWS S3 alone generates multi-billion-dollar annual revenue and global cloud storage is widely sized in the tens of billions" | Hand-wavy "widely sized"; AWS S3 revenue is incumbent slice, not TAM. The 4 may still hold but the citation quality is weak. | Cite Gartner/IDC/451 cloud object-storage TAM figure; defend 4 or upgrade to 5 if > $100B substantiated. |
| 🟡 | market.growth_rate | 4 | "Tigris's own '8x every year' usage growth as a market proxy" | Conflates company growth with market growth — same number used twice across pillars. | Replace with a named analyst CAGR (Gartner/IDC) for object storage or AI-inference data layer. |
| 🟡 | traction.engagement_retention | 3 | "8x year-over-year usage growth being mathematically incompatible with heavy churn as a soft proxy" | Reverse-engineering retention from top-line growth is unsafe — new logos can mask churn. Reasoning admits proxy. | Source a direct NRR/cohort/DAU signal, or set to null. |
| 🟢 | team.technical_depth | 4 | "without an explicit FAANG staff/principal title or OSS-lead signal it falls short of a 5" | Honest under-the-bar acknowledgement — Uber storage team at hyperscale earns the 4 cleanly. | Keep. |
| 🟢 | meta (stage mismatch) | "seed" | notes: "Despite a Series A, stage='seed' is used because the schema only allows pre_seed\|seed" | Known schema constraint; absolute scores will over-credit a Series A vs. true pre/seed peers. | None — flag for downstream; consider a stage-weight in the ranker if cross-stage comparability matters. |

## Recommended next actions
1. **Recompute `traction.growth_rate`** — reasoning's own ≈19% MoM is under the 20% MoM 5-anchor; either drop to 4 or substantiate explicit > 20% MoM in press. Highest-impact change (traction pillar, 15% weight, swings total by ~0.94).
2. **Anchor the market pillar to analyst figures** — replace company-as-market-proxy in both `market.growth_rate` and `market.tam_size` with named Gartner/IDC numbers; market pillar carries 25%.
3. **Resolve `engagement_retention`** — either source a direct retention signal (NRR, cohort retention) or set to null; proxy-from-growth is the weakest reasoning on the card.
