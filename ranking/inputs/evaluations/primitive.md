# Scoring Audit — Primitive

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~42.73/100
- **Data completeness:** 70.6% (12/17)
- **Schema status:** ✅ valid (traction pillar all-null → 0.0 contribution at 15% weight; appropriate for a 3-month-old beta YC pre-seed)

## Bear case (one line)
"Email for agents" is a thin wrapper over SMTP + webhooks that Resend, Postmark, SendGrid, or any agent framework can ship as a feature in a sprint — unless Primitive moves up the stack into agent identity / governance / audit, it has no moat against incumbents that already own developer transactional-email mindshare.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | team.technical_depth | 4 | "engineering roles at Microsoft, AWS, Meta, and Google before co-founding Actual AI... no explicit Staff/Principal title or OSS-lead signal pulls it short of 5" | Multi-FAANG resume without level evidence — anchor 3 = "strong engineers"; anchor 5 = "ex-FAANG staff+." Without staff/principal level confirmed, 4 sits at the high end of 3 territory. | Pull explicit LinkedIn level evidence; if levels are below Staff/Principal, drop to 3. |
| 🟡 | team.founder_market_fit | 4 | "previously co-founding Actual AI (AI agents for engineering managers, $3.2M seed from AlleyCorp per GeekWire 2025) and now building agent-communication infra" | "AI agents for eng managers" → "agent comms infra" is an *adjacent* pivot, not lived-the-problem fit. Anchor 5 = lived the problem at scale; anchor 3 = adjacent. 4 leans optimistic. | Defend by articulating the exact overlap (did Actual AI hit messaging/email pain firsthand?), or drop to 3. |
| 🟡 | product.velocity | null | "No public changelog, blog, or GitHub release surface visible on primitive.dev as of 2026-05" | Skill §C flags null on publicly observable signals as lazy. For a 3-month-old YC company, founder X/LinkedIn or YC profile demos can yield cadence. | Spot-check founder social channels + YC profile; if any cadence is observable, replace null with a 2-3. |
| 🟢 | market.tam_size | 3 | "a meaningful but bounded TAM, neither <$1B nor clearly $100B+" | Reasoning honest about boundaries; 3 (~$10B) is reasonable for the agent-comms slice. | Keep. |
| 🟢 | traction (all four null) | null | "Product in beta per primitive.dev landing; no disclosed paying customers..." | Correct null usage — pre_seed beta, no public traction. Skill explicitly endorses null over 1 here. | Keep. |
| 🟢 | meta (stage) | "pre_seed" | (correctly labeled) | Only true `pre_seed` in the batch — stage aligns with the data. | None. |

## Recommended next actions
1. **Spot-check founder social channels** for product cadence so `velocity` can move off null (lazy-null risk per skill §C).
2. **Substantiate `technical_depth`** with FAANG levels — drop to 3 unless Staff/Principal evidence surfaces.
3. **Sharpen `founder_market_fit`** — articulate the exact overlap between Actual AI's agent work and email-comms pain, or downgrade to 3.
