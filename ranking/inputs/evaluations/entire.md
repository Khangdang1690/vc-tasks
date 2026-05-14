# Scoring Audit — Entire

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~68.50/100
- **Data completeness:** 76.5% (13/17)
- **Schema status:** ✅ valid (traction pillar empty → 0.0 contribution at 15% weight; appropriate for 3-month-old launch)

## Bear case (one line)
A $60M seed at $300M for a former-GitHub-CEO ships massive expectations on day one; the launch product (an MIT-licensed CLI git hook) has no proprietary infrastructure and is trivially replicable — if Cursor/Copilot/Claude Code ship native session-context-to-git in 2026, Entire is competing with platforms that already own the developer.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | market.tam_size | 5 | "...developer-platform market — encompassing GitHub, GitLab, JetBrains, and the emerging AI-coding tier — being broadly sized in the hundreds of billions (referenced in TechCrunch 2026-02-10 'largest in dev tools history' framing)..." | "Largest seed in dev tools history" is about the deal size, not the TAM. "Hundreds of billions" is asserted without an analyst figure. Dev-tools TAM is typically cited at $20–50B. | Cite a named Gartner/IDC dev-tools-software TAM; if <$100B, drop to 4 |
| 🟡 | market.growth_rate | 5 | "...AI dev-tools being the fastest-growing software category in 2025–2026 (referenced in TechCrunch 2026-02-10 and Felicis's own rationale)..." | Investor narrative is not an analyst growth rate. The >40% CAGR claim should be sourced from an independent analyst. | Substitute named analyst CAGR for AI dev tools / AI coding assistants |
| 🟡 | team.technical_depth | 5 | "...Thomas Dohmke leading GitHub through the Copilot era as CEO and shipping AI dev tooling at hundreds-of-millions-of-developers scale..." | CEO/leadership ≠ "world-class engineer (ex-FAANG staff+, PhD, OSS lead)" per anchor. The 5 stretches the anchor toward leadership track. Defensible-but-stretched. | Either rewrite anchoring on leadership-as-depth justification, or drop to 4 with the same evidence |
| 🟡 | team.prior_founding_experience | 4 | "...Dohmke having founded HockeyApp (mobile-app distribution, acquired by Microsoft in 2014) prior to running GitHub... not publicly disclosed at the $100M+ level..." | Honest treatment of the gap to 5. HockeyApp acquisition is widely reported in the low-tens-of-millions; anchor 3 = "prior startup, no exit" and 5 = "exit ≥ $100M". A confirmed-but-small exit puts this at 4-on-stretch or 3-on-strict. | Acceptable at 4 if "running GitHub as CEO" is treated as scaled-past-meaningful-revenue; otherwise drop to 3 |
| 🟡 | team.team_completeness | 4 | "...entire.io news disclosing 15 employees with plans to scale past 30 engineers and $60M in capital to hire across functions..." | "Plans to hire" is forward-looking, not current state. Anchor 5 = tech + commercial + design currently covered. 4 requires evidence of current coverage, not hiring intent. | Confirm named commercial + design leads exist today; otherwise drop to 3 |
| 🟢 | traction (all four nulls) | null | "Just launched 2026-02-10; no disclosed customers or revenue." | Correct null usage — 3-month-old launch. Skill endorses null over 1. | Keep |
| 🟢 | meta (stage) | "seed" | (seed labeled, $60M seed at $300M is genuinely a seed round) | Stage label matches the round naming, though deal size is post-seed-scale. | None |

## Recommended next actions
1. **Defend the market pillar 5s** with named analyst figures (TAM + CAGR) — the dev-tools-TAM and AI-CAGR claims need analyst citation, not investor-narrative or deal-size citation.
2. **Re-anchor `technical_depth`** — either justify leadership-as-depth explicitly or drop to 4. CEO ≠ engineer-IC by the rubric.
3. **Confirm current `team_completeness`** — pull named commercial/design hires that exist today vs. hiring plans.
