# Scoring Audit — Vizcom

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~68.94/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
Adobe Firefly, Autodesk's generative-design moves, and frontier image models (Imagen, Midjourney V7, GPT-image-1) are closing on industrial-design quality monthly — Vizcom's vertical specialization gives a head start but no structural moat against incumbents that own the surrounding CAD/PLM software customers already pay for.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | meta (stage) | "seed" | notes: "Stage='seed' per schema constraint; actual stage is Series B." | $52M total raised across seed + Series A + Series B (Index, Radical). Comparison with true seeds inflates `revenue_signal` (5) and team scores relative to peers. | Add stage-weight or filter; acknowledged in notes |
| 🟡 | traction.revenue_signal | 5 | "...Ford, Honda, Nissan, Polaris, Gulfstream, Dell, Sonos, Stanley Black & Decker, Brooks, Skechers, and Columbia as customers — a Fortune-500-heavy roster..." | Anchor 5 = "growing ARR with named logos". Logos are confirmed; "growing ARR" is inferred from logo expansion, not directly cited. Still, the logo density is unusual for the cohort, so 5 is defensible. | Add an ARR or revenue-trajectory citation (any analyst, press, or investor-quote that mentions growth) to lock the 5 |
| 🟡 | market.tam_size | 4 | "...industrial-design / 3D-rendering / CAD software market being broadly sized in the multi-tens-of-billions (Autodesk, Adobe, Dassault all multi-billion revenue businesses..." | Incumbent revenue ≠ TAM. The 4 is plausible — CAD software TAM is typically ~$10–15B; combining with media/3D could stretch to multi-tens-of-billions, but it isn't cited. | Cite a specific CAD-software / 3D-content-creation analyst TAM with figure + year |
| 🟡 | market.growth_rate | 4 | "...generative-AI design tooling being one of the fastest-growing creative-software subsegments in 2024–2026 (per Maginative 2024 and Radical Ventures 2025 announcements)..." | Investor announcement + tech-press framing — neither is an analyst CAGR. The 4 is plausible but uncited. | Substitute analyst CAGR for generative-AI / creative-software segment |
| 🟡 | traction.growth_rate | 3 | "...trajectory of three funding rounds in three years ($5M seed 2023 → $20M Series A 2024 → $27M Series B 2025... continually expanding the named-logo enterprise list..." | Funding rounds and logo additions are not a growth-rate metric. Anchor 3 = ~5% MoM. The 3 is asserted without an MoM signal. | Set to null until an MoM/QoQ revenue or paid-seat figure is sourced |
| 🟢 | team.prior_founding_experience | 1 | "...Honda → NVIDIA industrial-design path with no prior founded company..." | Honest 1 — first-time founders, well-cited via LinkedIn. | Keep |
| 🟢 | product.differentiation | 4 | "...industrial-design-specific with 3D-model integration, sketch-to-render, and material/scene editing tailored to designers..." | Sharp vertical-specialization angle is real and well-described. | Keep |

## Recommended next actions
1. **Source `traction.growth_rate` properly** — funding-round cadence isn't growth; set to null or find paid-seat MoM.
2. **Lock `revenue_signal: 5`** by adding a growth/ARR citation alongside the logo list (any analyst, press, or investor quote with a $ or % figure).
3. **Cite analyst TAM** for `market.tam_size` and a real CAGR for `market.growth_rate` (CAD + 3D content-creation analyst sources).
