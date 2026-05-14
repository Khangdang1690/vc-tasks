# Scoring Audit — Flint

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~63.19/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
K-12 AI tutoring is becoming a feature inside LMS incumbents (PowerSchool, Canvas, Google Classroom Gemini) and ChatGPT EDU — once districts standardize on a bundled solution, switching out of an existing LMS contract is institutionally harder than swapping in Flint, regardless of product quality.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | meta (stage) | "seed" | notes: "Stage='seed' per schema constraint; actual stage is Series A." | $15M Series A is materially past seed; comparison with true seeds inflates `users_customers` (5) and `revenue_signal` (4) relative to peers. | Add stage-weight or filter in the ranker; acknowledged in notes |
| 🟡 | team.founder_market_fit | 3 | "...prior company being Gatherly (virtual events, not K-12)... focused founder energy but no prior K-12 operating background." | Honest 3 — virtual events to K-12 is genuinely adjacent at best. Anchor 3 = "adjacent experience". OK. | Keep |
| 🟡 | team.prior_founding_experience | 4 | "...Gatherly (~250k users, $2M revenue, $3M+ raised, customers including Google/MIT, ultimately acquired per AlleyWatch 2025-11)... acquisition price was undisclosed and not confirmed at $100M+." | Honest 4 — acquisition occurred but price unconfirmed. Strict reading of anchor 5 = "$100M+ exit" → 4 is correct. | Keep; if Gatherly acquisition price ever surfaces and exceeds $100M, revise |
| 🟡 | market.tam_size | 4 | "...K-12 EdTech software market being sized broadly in the tens of billions globally (referenced in EdTech Digest 2025-11-19 and AlleyWatch 2025-11 coverage)..." | "Referenced in coverage" — no analyst figure. K-12 EdTech is typically cited around $80–120B globally (HolonIQ), so a 4 may even be conservative. | Cite HolonIQ / Grand View / Brighteye analyst TAM with figure + year |
| 🟡 | traction.growth_rate | 3 | "...user base growing from '400,000+ daily users' (flintk12.com, 2025-11) to '500,000+ educators and students' (flintk12.com homepage as of 2026-05) over ~6 months as a soft proxy implying ~3–4% MoM..." | Two different metrics being compared: "daily users" → "educators and students" (combined headcount). Apples-to-oranges. Arithmetic: 400k → 500k over 6 months = ~3.8% MoM if equivalent — but the metrics aren't equivalent. | Find apples-to-apples MoM (DAU or paid-seat count); the 3 is plausible but the math doesn't hold as cited |
| 🟡 | traction.engagement_retention | 4 | "...Cognita district-level contract... plus institutional LMS-integration and staff-training costs... creating annual-contract stickiness..." | "Annual-contract stickiness" is procurement inertia, not retention. Anchor 5 = "NRR > 110% or strong qualitative retention". Without NRR/renewal data, 4 may overstate. | Find renewal-rate or NRR signal; otherwise drop to 3 |
| 🟢 | product.technical_moat | 2 | "...teacher-and-student-facing wrapper over state-of-the-art LLMs... without proprietary models or unique data network effects disclosed..." | Honest 2 — appropriately modest. | Keep |

## Recommended next actions
1. **Tighten `traction.growth_rate`** with consistent metrics (DAU→DAU or paid-seat→paid-seat); current cite mixes incompatible counts.
2. **Substantiate `tam_size`** with HolonIQ K-12 EdTech analyst figure — likely defends 4 or upgrades to 5.
3. **Source NRR/renewal data** for `engagement_retention`; "procurement stickiness" isn't the anchor.
