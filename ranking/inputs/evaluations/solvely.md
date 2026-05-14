# Scoring Audit — Solvely

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~73.25/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
Consumer EdTech with 10M users but no proprietary base model is a thin layer over commodity LLMs at the mercy of OpenAI/Anthropic pricing — Photomath (Google), Chegg, and ChatGPT EDU can replicate every feature, and student attention is famously cheap to lose once a free, better incumbent appears.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | team.prior_founding_experience | 5 | "...Du Zhang... having previously sold an online tutoring marketplace for over $100M (per asugsvsummit.com/speakers/du-zhang speaker bio)..." | Single source = conference speaker bio, which is self-reported. A claim of $100M+ exit at the 5-anchor demands corroboration via Crunchbase / press release / acquirer announcement / SEC filing. Speaker bios routinely inflate. | Find a second source (Crunchbase exit record, acquirer's press release, or contemporaneous news). If none surfaces, drop to 4 |
| 🟡 | team.founder_market_fit | 5 | "...having previously sold an online tutoring marketplace for over $100M..." | Same single-source problem — `founder_market_fit: 5` rests on the same uncorroborated bio claim. If the prior exit can't be verified, this drops to 4 (adjacent strong) or 3 (adjacent). | Corroborate; if exit unverifiable, drop to 3–4 |
| 🟡 | traction.users_customers | 5 | "...solvely.ai citing 10M+ learners across 150+ countries and 200M+ learning sessions completed..." | Single source = company's own marketing site. The App Store/Play ratings (cited separately in `engagement_retention`) corroborate scale via review counts (31k+ iOS + 80k+ Android), but the "10M+ learners" specific number is uncorroborated. | Cross-check with Sensor Tower / Data.ai / app-store download estimates; if app-store data supports millions of MAU, defend 5 |
| 🟡 | traction.growth_rate | 5 | "...company going from 2023 launch to 10M+ users by 2025–2026 (solvely.ai) — implying average compounded MoM growth comfortably above 20% to reach that scale..." | "Comfortably above 20%" isn't computed. Reaching 10M from a launch base over 24 months requires roughly 60–80% MoM if starting at zero — defensible but should be shown, not asserted. The base-rate also relies on the uncorroborated 10M figure. | Compute the implied MoM explicitly; verify with app-store download-trend data |
| 🟡 | market.tam_size | 4 | "...consumer EdTech / homework-help / tutoring market being broadly sized in the multi-tens-of-billions globally (Photomath sold to Google for ~$700M, Chegg historic peak revenue $700M+ — public references)..." | Acquisition prices and peak revenue ≠ TAM. K-12 consumer EdTech TAM analyst figures typically run $5–15B globally; 4 may overstate. | Cite HolonIQ / Grand View consumer EdTech TAM |
| 🟢 | product.velocity | 5 | "...seven point releases in October 2025 alone (4.6.9 → 4.7.6 between Oct 4 and Oct 27)..." | Strong, specific evidence. | Keep |

## Recommended next actions
1. **Corroborate the $100M+ exit claim** (currently the entire team pillar hinges on one speaker-bio source). If unverified, two scores drop one anchor each → meaningful total impact via team 40% weight.
2. **Verify `users_customers: 5`** with third-party app-analytics data (Sensor Tower / Data.ai).
3. **Compute the MoM growth math** for `traction.growth_rate` — don't assert "comfortably above 20%" without showing the arithmetic.
