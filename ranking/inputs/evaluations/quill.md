# Scoring Audit — Quill

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~62.19/100
- **Data completeness:** 88.2% (15/17)
- **Schema status:** ✅ valid

## Bear case (one line)
"Local-first sovereign AI" is a thesis, not a moat — Apple Intelligence is shipping on-device assistants natively in macOS/iOS, and the AI-meeting-notes category has 10+ well-funded competitors (Otter, Granola, Fathom, Fireflies, Zoom AI Companion); Quill's privacy story has to convert into enterprise contracts faster than Microsoft Copilot/Zoom roll out compliant equivalents.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | market.growth_rate | 5 | "...AI personal/work assistants being among the fastest-growing AI software subsegments in 2025–2026 (siliconangle.com 2026-03-03 coverage)..." | Tech-press "framing" is not a CAGR figure; >40% claim uncited | Substitute named analyst CAGR for AI personal assistants / productivity AI |
| 🟡 | market.tam_size | 4 | "...broadly sized in the multi-tens-of-billions (referenced in siliconangle.com 2026-03-03 'chief of AI staff' framing)..." | "Multi-tens-of-billions" not anchored to a primary figure | Cite Gartner / IDC TAM for productivity AI / AI assistants segment |
| 🟡 | team.team_completeness | 4 | "...already having hired Founding COO/Growth Yacob Berhane and Head of Enterprise Clayton Bryan alongside the two founders..." | Anchor 5 = tech + commercial + design; design lead not named. 4 is right if tech + commercial only. | Keep 4 (rubric-correct); only revisit if a design lead becomes public |
| 🟡 | traction.users_customers | 2 | "...free local + paid subscription tiers ($6.99/$16.99 per month) and Microsoft Store + App Store listings... accumulating G2 reviews within 3 months of launch..." | Anchor 1 = none, 3 = early adopters, 5 = 1k+ active. G2 reviews + App Store presence = early adopters → arguably 3 not 2. | Find a public user/download count; otherwise reconsider 2 vs 3 |
| 🟡 | traction.revenue_signal | 2 | "...launching publicly in Feb 2026 alongside the seed announcement... G2 reviews existing but no named enterprise customers or ARR disclosed..." | Anchor 3 = paid pilots. Public paid tiers exist ($6.99/$16.99); if any subscribers, this is on the 2/3 boundary. | Confirm whether paid subscribers exist (yes → 3; no → keep 2) |
| 🟢 | traction.growth_rate / engagement_retention | null | "Company launched 2026-02-25..." | Correct null usage — 3 months of public existence; honest. | Keep |
| 🟢 | team.network_credibility | 5 | "...Basis Set Ventures with 500 Global, Morado Ventures, AME Cloud, and Naval Ravikant participating..." | Tier-1 VC + named angel (Naval) = clean 5. | Keep |

## Recommended next actions
1. **Resolve `users_customers` / `revenue_signal` boundary** — pull App Store / Microsoft Store install counts; if any are public, both scores likely lift by one.
2. **Cite analyst TAM/CAGR** for the market pillar — current cites lean on tech-press framing.
3. **Bear-case the local-first thesis** in `notes` — Apple Intelligence and Microsoft Copilot are the silent competitive risk, not Otter.
