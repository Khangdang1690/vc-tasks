# Scoring Audit — Mem0

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~79.19/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
"Memory" is being absorbed into the base stack of every agent platform (AWS AgentCore native memory, LangMem, Zep, Letta, Cognee) — if AWS upgrades AgentCore's native memory to parity, the Strands SDK exclusivity loses value and Mem0 competes with its own OSS core against in-cloud free alternatives.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | market.growth_rate | 5 | "Mem0's own API-call growth from 35M in Q1 2025 to 186M in Q3 2025 (~5x in two quarters per mem0.ai/series-a) as a market proxy" | Company API growth ≠ market growth. The skill explicitly warns about this conflation. > 40% CAGR may still hold, but the citation is for the wrong thing. | Substitute analyst CAGR (Gartner/IDC/Forrester) for AI agent infra or agent-memory subcategory. |
| 🟡 | market.tam_size | 4 | "AI agent infrastructure being broadly sized in the tens of billions (LangChain/LangSmith, AWS Bedrock AgentCore, etc.)" | Vendor names ≠ analyst-cited TAM; "tens of billions" not anchored to a primary figure. | Cite named analyst TAM (Gartner agent platforms, IDC AI infra) with figure + year. |
| 🟡 | team.prior_founding_experience | 3 | "Taranjeet being the first growth engineer at Khatabook (YC S18 unicorn) and creator of Embedchain (a popular OSS project, not a venture-backed exit)" | Embedchain was OSS, not a venture-backed prior company; Khatabook role was employee. Anchor 3 = "prior startup, no exit" — strict reading neither founder qualifies. | Defend 3 explicitly as "founder-adjacent operator track record" in the reasoning, or drop to 2. |
| 🟡 | traction.engagement_retention | 3 | "API calls compounding 35M → 186M in two quarters as a soft proxy for non-churning sustained usage" | API growth can come from new logos while existing logos churn — the proxy doesn't separate the two. | Find per-cohort or NRR-style signal; otherwise set to null. |
| 🟢 | product.defensibility | 4 | "AWS Strands SDK exclusivity... plus accumulated user/agent memory state being non-trivial to migrate" | Partnership exclusivity is real but reversible; memory state is portable via export. Borderline 4-vs-3 — defensible at 4. | Keep; add partnership-duration risk note. |
| 🟢 | product.velocity | 5 | "319 releases with the most recent (@mem0/cli v0.2.5) dated 2026-05-14 — the day of this scoring" | Same-day citation is recency-boundary; evidence remains independent of audit date. | Keep. |

## Recommended next actions
1. **Decouple company growth from market growth** in `market.growth_rate` — replace internal API-call delta with a real analyst CAGR; this is the loudest LLM-tell on the card.
2. **Substantiate `market.tam_size`** with a named analyst figure rather than vendor lists.
3. **Resolve `prior_founding_experience: 3`** — either defend founder-adjacent framing explicitly, or drop to 2 to match strict rubric.
