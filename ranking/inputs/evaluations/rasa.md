# Scoring Audit — Rasa

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~65.75/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
9-year-old OSS conversational-AI shop competing against the post-ChatGPT wave on legacy NLU primitives — 180 employees with one OSS release in 16 months suggests the company has shifted to enterprise services mode while OpenAI's Assistants API, Voiceflow, and native cloud agent platforms eat the developer mindshare Rasa once owned.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | meta (stage) | "seed" | notes: "NOTE: schema constrains stage to pre_seed\|seed but this is a Series C company — using 'seed' for schema compliance; critic should flag the stage mismatch." | $83.8M raised across 9 rounds, latest a $30M Series C 2024-02-14. The anchors implicitly compare seed/pre-seed companies — Rasa being scored alongside them inflates `team_completeness`, `network_credibility`, and `users_customers` artificially. | Add a stage-weight or filter in the ranker, or exclude Series-C-and-later from the file. Acknowledged by author, but ranker can't see it. |
| 🟡 | market.tam_size | 4 | "...conversational-AI and contact-center-automation market being broadly sized in the multi-tens-of-billions across enterprise CX, voice agents, and chatbots (referenced in TechCrunch 2024-02-14 coverage)..." | "Referenced in coverage" — no analyst figure named | Cite Gartner CCaaS / conversational AI TAM with figure + year |
| 🟡 | market.growth_rate | 4 | "...2025–2026 voice-AI/agent renaissance reviving the conversational-AI category (per rasa.com/events and TechCrunch 2024-02-14 framing of multimodal voice AI)..." | Company-event page is not a market growth signal; "framing" ≠ CAGR | Substitute named analyst CAGR for conversational AI / contact center automation |
| 🟡 | team.prior_founding_experience | 1 | "...Rasa is the first venture for both co-founders with no prior exit, we can infer the strict 'first-timers' anchor applies — though both are deeply seasoned within Rasa itself." | Strictly correct, but the rubric's intent is to assess founder pattern-matching for seed-stage decisions — for a 9-year-old Series C, the score is meaningless. | Keep 1 (rubric-correct) but reinforces the stage-mismatch problem |
| 🟡 | traction.users_customers | 4 | "...50M+ downloads and 15,000+ forum members, plus historical enterprise customers including Adobe and T-Mobile..." | 50M downloads accumulated over 9 years is largely historical; "historical" customer mentions (Adobe/T-Mobile from old TC coverage) may no longer be current. Anchor specifies active users. | Confirm Adobe/T-Mobile are still customers; downgrade if many are churned-legacy |
| 🟡 | traction.growth_rate | 2 | "...the OSS repo shipping only one release in the prior 16 months (github.com/RasaHQ/rasa) as a soft proxy for slowing product momentum..." | OSS release cadence is a product-velocity proxy, not a user/revenue growth proxy. The 2 may be directionally right but the cited evidence doesn't measure growth. | Find a revenue/headcount trajectory; the proxy is the wrong measurement |
| 🟢 | team.team_completeness | 5 | "...180 employees as of 2026-02-28 with separate CEO and CTO roles plus an executive team across the 9-year company..." | True at 5, but trivially so for a Series C — see stage mismatch | None — symptom of the stage issue |
| 🟢 | team.network_credibility | 5 | "...$83.8M across 9 rounds including a Series B led by Andreessen Horowitz..." | a16z lead = tier-1, easy 5. | Keep |

## Recommended next actions
1. **Resolve the stage problem** — Rasa shouldn't be ranked against pre_seed/seed peers without a stage-weight. Either filter out or add explicit stage normalization in the pipeline.
2. **Re-source `market` pillar** — both `tam_size` and `growth_rate` rest on vague "referenced in coverage" cites; need named analyst figures.
3. **Drop OSS-release-cadence as a growth proxy** in `traction.growth_rate` — substitute revenue or headcount trajectory, or set to null.
