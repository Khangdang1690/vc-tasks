# Scoring Audit — Parasail

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~78.38/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
Inference is a commoditizing API — Together, Fireworks, Replicate, Modal, Groq, and the hyperscalers' own gateways are racing the price floor; "no owned silicon" cuts both ways (capital-light, but zero structural cost advantage vs. competitors that own GPUs), and a single rate-card war collapses margins below 0% within a year.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | team.technical_depth | 5 | "Mike Henry's track record building Mythic's analog AI chip and Tim Harris's deep-tech GNSS work at Swift Navigation... 500B+ tokens/day across a global GPU mesh" | Anchor 5 specifies "world-class (ex-FAANG staff+, PhD in the field, OSS project lead)". Founders are accomplished *founders*, not the IC archetype the anchor describes. Mythic filed for bankruptcy in 2022 — fact omitted from reasoning. | Re-research the IC engineering bench (CTO/principal-eng titles, FAANG levels, papers); drop to 4 unless top-IC signal surfaces. Add Mythic bankruptcy to `notes`. |
| 🟡 | team.prior_founding_experience | 4 | "Mike Henry having raised $165M at Mythic and Tim Harris having raised $250M at Swift Navigation" | "Raised $X" ≠ "exited at $X"; Mythic's bankruptcy isn't acknowledged. Anchor 5 = exit ≥ $100M. | Confirm Swift Navigation outcome (still independent? Trimble acquisition figure?); document Mythic bankruptcy; possibly drop to 3. |
| 🟡 | traction.revenue_signal | 5 | "named paying customers (Elicit, Rasa, Oumi, Weights & Biases) and processing 500B+ tokens/day on a pay-per-token model" | Anchor 5 = "growing ARR with named logos." Token throughput is volume, not ARR. The 30% MoM revenue cite (TechCrunch) is parked under `growth_rate` — moving it here makes the 5 clean. | Merge the TechCrunch 30% MoM revenue line into this reasoning; otherwise the current cite supports 4. |
| 🟡 | market.tam_size | 5 | "AI inference compute being projected at >$100B annual spend by 2030 across multiple analyst frameworks (referenced in SiliconAngle 2026-04-15 and DCD coverage)" | "Multiple analyst frameworks" not named — at this score level (>$100B) name at least one analyst directly. | Cite Gartner/IDC/McKinsey inference compute TAM with figure + year. |
| 🟢 | product.defensibility | 3 | "inference being commoditized via OpenAI-compatible APIs" | Consistent with bear case; 3 is justified given `competitive_intensity_inv: 1`. | Keep. |
| 🟢 | market.competitive_intensity_inv | 1 | "the inference-cloud space being extremely crowded with Together AI, Fireworks AI, Replicate, Modal, RunPod, Lambda Labs, Anyscale, Groq, Cerebras, plus AWS Bedrock and Vertex AI" | Inversion applied correctly: crowded → low score. Strong citation. | Keep. |

## Recommended next actions
1. **Re-research `technical_depth`** — pull CTO/principal-eng evidence; the current founder-track rationale doesn't clear the 5-anchor. Acknowledge Mythic's bankruptcy in notes regardless.
2. **Move the TechCrunch 30% MoM line** into `revenue_signal` to defend the 5 (ARR growth + named logos together); else drop to 4.
3. **Name the inference-TAM analyst** in `market.tam_size` rather than "multiple analyst frameworks."
