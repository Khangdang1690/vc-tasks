# Scoring Audit — Reve

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~74.75/100
- **Data completeness:** 88.2% (15/17)
- **Schema status:** ✅ valid

## Bear case (one line)
A #1 benchmark ranking in March 2025 doesn't survive twelve months in image-gen — Midjourney V7, GPT-image-1, Imagen 3, Recraft, and Flux all leapfrog quarterly; one major model + a UI refresh in 14 months (velocity:2) suggests Reve cannot match the frontier release cadence its competitors set, regardless of how much money is in the bank.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | meta (stage) | "seed" | notes: "PitchBook lists $390M total raised — large for a 2023-founded company, treat as PitchBook-reported. ... Stage='seed' per schema; actual stage almost certainly post-seed given reported funding scale." | $390M reported total ≈ Series B/C scale. Scoring against pre_seed/seed peers is fundamentally apples-to-oranges; team scores especially are stage-inflated. Author flagged. | Either filter Reve from the seed cohort or add stage normalization to the ranker |
| 🟡 | team.network_credibility | 5 | "...PitchBook (profiles/company/769520-71) listing $390M raised with Basis Set Ventures and Top Harvest Capital as investors... treated as PitchBook-reported and not independently confirmed in press coverage." | $390M is unprecedented for a 2023-founded image-gen company without major press coverage — extraordinary claim, single source (PitchBook), no press release or filing cited. Either PitchBook is wrong, or this is one of the biggest stealth raises of the decade. | Find a press release, SEC filing, or TC/PR story confirming any portion of the $390M; if unverifiable, drop to 4 (Basis Set is real tier-1; the figure is the suspect part) |
| 🟡 | market.tam_size | 5 | "...generative-AI image/visual content being a foundational layer of the multi-hundreds-of-billions global creative software + media production economy..." | Stacked-market TAM — creative software + media production are two different markets glued together. Skill specifically warns against this. Image-AI TAM alone is multi-billions, not hundreds-of-billions. | Cite a single named analyst TAM for generative-AI image/visual content; if <$100B, drop to 4 |
| 🟡 | market.growth_rate | 5 | "...image-generation AI being the fastest-growing creative-AI subsegment (per VentureBeat 2024 and eweek.com coverage)..." | Tech-press framing, not analyst CAGR | Substitute named analyst CAGR for generative-AI image/visual segment |
| 🟡 | product.differentiation | 4 | "...Reve Image 1.0 leading Artificial Analysis's image-quality ranking and uniquely handling readable text/typography that incumbents like Midjourney struggle with (eweek.com 2024 coverage)..." | Benchmark leadership in March 2025 is 14 months stale at this audit; competitors have shipped major versions since. Defensible-but-time-bound. | Verify Reve's current Artificial Analysis rank; if no longer #1, drop to 3 |
| 🟡 | team.prior_founding_experience | 4 | "...Mike Speiser's long Sutter Hill Ventures incubation track record (multiple infra unicorns) and Jon Watte's prior VP Technology role at IMVU (acquired)... specific personal exit dollar amounts at $100M+ are not confirmed..." | Sutter Hill incubator role ≠ "founder with prior exit ≥ $100M" strictly. Speiser is famously the SHV incubator behind Snowflake/Pure/etc. but as investor/incubator, not founder-CEO with personal exit. | Either justify the SHV-incubator role explicitly as founder-track or drop to 3 |
| 🟢 | team.technical_depth | 5 | "...PhD-level generative-imaging researchers (Taesung Park, Michael Gharbi), an ex-Adobe Senior Director of Product (Christian Cantrell as CPO), and Reve Image 1.0 ranking #1 on Artificial Analysis ahead of Midjourney v6.1 / Imagen 3 / Recraft V3..." | Pix2pix/CycleGAN authorship is genuine top-of-field research credential. Clean 5 for once. | Keep |
| 🟢 | product.velocity | 2 | "...Reve having shipped only one major model (Reve Image 1.0 / Halfmoon, March 2025 per VentureBeat) plus a 2026 single-panel UI update..." | Honest 2 — internally consistent with the bear case. | Keep |
| 🟢 | traction (growth_rate, engagement_retention) | null | "No public MoM growth figure..." | Correct null usage. | Keep |

## Recommended next actions
1. **Verify the $390M figure** — without a press release, filing, or TC story, the `network_credibility: 5` rationale rests on a single PitchBook entry. Highest research priority.
2. **Replace stacked-market TAM** in `market.tam_size` with a single named analyst figure for generative-AI image/visual content.
3. **Re-check Reve's current Artificial Analysis rank** — if no longer #1, the `differentiation: 4` cite is stale and should drop.
