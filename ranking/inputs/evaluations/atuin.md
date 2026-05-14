# Scoring Audit — Atuin

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~55.75/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
Solo-founder devtool with a bounded TAM and free-OSS-led monetization — if the paid Desktop/Hub tier doesn't convert the 200k+ free CLI base into paid seats before Warp, Ghostty, or a modern shell ships native encrypted history sync, Atuin's wedge becomes a feature inside someone else's terminal product.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🟡 | team.technical_depth | 5 | "29.7k stars... OSS-lead-level depth that clears the '10k+ stars' 5-anchor" | The "10k+ stars" threshold is fabricated — the rubric describes "OSS project lead" qualitatively, not by star count. Score is defensible (primary author of 29.7k-star Rust project since 2021) but the cite invents a number. | Keep 5; rewrite reasoning to cite the qualitative "OSS project lead" anchor language, drop the invented threshold. |
| 🟡 | team.team_completeness | 2 | "sole named founder with no commercial or design co-founder visible... we can infer a one-dimensional team" | "One-dimensional" is literally the anchor-1 phrase. 2 sits between anchor 1 (solo) and anchor 3 (decent split, gap); reasoning supports 1. | Drop to 1, or surface a non-founder commercial/design lead from LinkedIn to defend the 2. |
| 🟡 | market.tam_size | 2 | "closer to the low end (<$1B) than mainstream devtools categories" | Reasoning bounds TAM at "<$1B," which is anchor 1, not 2. | Drop to 1, or cite a dev-experience/shell-tools analyst TAM that defends 2. |
| 🟡 | traction.users_customers | 5 | "atuin.sh citing '200,000+ developers' using the CLI and 29.7k GitHub stars" | Primary source is the company's own marketing site; "developers" ≠ "active users" the 5-anchor requires. Stars are cumulative, not active-user signal. | Source third-party install counts (Homebrew analytics, crates.io downloads); drop to 4 if no active-user evidence surfaces. |
| 🟡 | traction.growth_rate | 2 | "29.7k stars over ~5 years... implying single-digit-percent MoM steady growth... soft proxy" | Cumulative stars-over-years is a stock metric, not a rate — the inference is structurally wrong. | Set to null (no MoM data exists) or substitute a trailing-30-day star/download rate. |
| 🟢 | traction.engagement_retention | 3 | "220M+ synced records... and 200,000+ developers persisting across multiple years... soft proxy" | Proxy is honest at the 3 anchor — no NRR is realistic for free-OSS. | Keep; trim to one sentence and label "proxy, no NRR." |

## Recommended next actions
1. **Resolve `team_completeness` to 1** unless a non-founder leader can be cited — team pillar is 40% weight, biggest swing on the card (~ -3 points if dropped).
2. **Replace `traction.growth_rate` cite** — cumulative stars ≠ growth; set null or find real MoM.
3. **Re-source `users_customers`** with a third-party install signal; drop to 4 if active-user evidence missing.
