# Scoring Audit — BAML

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~62.50/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
DSL+compiler distribution is uphill — LangChain/LangGraph/Pydantic AI all ship as plain Python libraries and capture the same workflows without asking developers to learn a new language; if Apache-2.0 BAML is "borrowed" into a competitor or AI-coding assistants emit Pydantic/Instructor by default, the language wedge erodes.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | market.tam_size | 4 | "LangChain alone raised at $1.1B in 2024 per public reporting" | LangChain valuation ≠ TAM — conflates company valuation with category size. | Substitute named analyst TAM (Gartner LLMOps / AI dev tools / AI infra) with figure + year. |
| 🟡 | market.growth_rate | 5 | "the AI-agent dev-tools category being the fastest-growing software segment in 2024–2026 (referenced throughout TechCrunch/SuperDataScience coverage)" | Asserts > 40% CAGR without naming a specific analyst — "referenced throughout coverage" is vague. | Cite a Gartner/IDC/Forrester CAGR for AI dev tools or LLMOps with figure + year. |
| 🟡 | traction.users_customers | 4 | "8.2k GitHub stars... plus named-logo testimonials including SAP, Amazon engineers, and YC-batch peers" | "Amazon engineers" are individuals, not "Amazon" as customer; SAP/Aer/PMMI/Vetrec are testimonials, paid-status unconfirmed; stars ≠ active users. | Confirm institutional paid adoption, or downgrade to 3. |
| 🟡 | traction.growth_rate | 3 | "333 releases... 6 alpha builds dated 2026-05-07 to 2026-05-08 alone as a soft proxy for accelerating contributor + user activity" | Release-count is a product-velocity proxy, not a user/revenue growth proxy — two separate metrics. | Find a real growth signal (download MoM, paid-seat trajectory); else set to null. |
| 🟡 | team.prior_founding_experience | 1 | "the YC company pivoted 13 times within itself (Gloo → Boundary/BAML is the same legal entity, not a prior founding)" | Strict-reading correct, but 3 years of in-entity pivoting gives more product-iteration scar tissue than true first-timers. The 1 understates reality. | Keep 1 (rubric-correct); add pivot-history context in `notes` for downstream readers. |
| 🟢 | team.technical_depth | 4 | "8.2k stars and the founder's decade of AI perf work at FAANG-tier shops" | "Sub-10k-stars" framing is invented; rubric is qualitative. The 4 is right (BAML is the lead's project) but the cite invents a threshold. | Keep 4; rewrite without the fabricated star threshold. |

## Recommended next actions
1. **Anchor the market pillar to real analyst figures** — replace LangChain-valuation-as-TAM and "fastest-growing... referenced throughout" with named CAGRs.
2. **Separate product-velocity from user-growth** in `traction.growth_rate` — release cadence ≠ user growth; set to null if MoM unavailable.
3. **Tighten `users_customers`** — distinguish "Amazon engineers writing testimonials" from "Amazon as paying customer"; downgrade unless paid-seat evidence is found.
