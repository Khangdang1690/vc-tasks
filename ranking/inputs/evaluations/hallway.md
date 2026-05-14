# Scoring Audit — Hallway

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~37.35/100
- **Data completeness:** 76.5% (13/17)
- **Schema status:** ✅ valid

## Bear case (one line)
A two-founder Missouri team competing in a category (in-product help / mascot AI) where Intercom Fin, HubSpot Breeze, Drift, Character.ai, and Inworld already own the shelf — with a script-tag integration and third-party LLMs, there is no proprietary IP and no structural reason a customer chooses Hallway over a built-in feature of the SaaS they already use.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | traction.users_customers | 2 | "...listing customers including Neopets, PointHound, CHKK, TerraZero, and Basis Set without disclosed ARR or distinguishing paid-vs-pilot status..." | "Basis Set" is Basis Set Ventures — a VC firm, not a customer. Listing investors as customers is a factual confusion. The reasoning needs cleanup. Even with that fix, "a handful of named logos" supports the 2 anchor cleanly. | Remove Basis Set from the customer list; verify the remaining four are customers (not investors/portfolio peers). Keep 2 if confirmed |
| 🔴 | traction.revenue_signal | 2 | "...customers including Neopets, PointHound, CHKK, TerraZero, and Basis Set..." | Same Basis Set issue as above (investor mislabeled as customer). | Same fix — remove Basis Set, keep 2 if remaining four are confirmed paid |
| 🟡 | market.competitive_intensity_inv | 3 | "...Character.ai, Inworld AI, and embedded chatbot products (Intercom Fin, HubSpot Breeze, Drift) being adjacent but not direct competitors in the specific 'mascot for your product' niche..." | Niche-narrowing argument — once the category is narrowed to "mascot for your product" any newcomer looks greenfield. But the broader category (in-product help + AI character) is saturated; bear case is that the niche framing isn't durable. | Either accept narrow framing (keep 3) or broaden to "in-product help/character AI" and drop to 2 |
| 🟡 | product.velocity | null | "No public changelog, blog, or GitHub release surface visible on hallway.ai..." | Skill flags null on observable signals as lazy. For a script-tag SaaS, even a marketing-site "what's new" tab or founder X/LinkedIn posts can indicate cadence. | Spot-check founder Twitter/X and LinkedIn for shipping updates; if any cadence is observable, replace null with 2–3 |
| 🟡 | team.team_completeness | 2 | "...only two co-founders being publicly named (Crunchbase organization/hallway-dea3) with no commercial/design lead disclosed..." | Honest 2. Anchor 1 = solo, 3 = decent split with a gap. Two technical co-founders with no commercial lead is on the 2/1 boundary. | Keep 2 (correct anchor); only revise if a third hire is found |
| 🟡 | team.network_credibility | 2 | "...Redbud VC leading the seed via Cohort III... only named institutional investor and the company being based in Columbia, Missouri rather than a tier-1 hub..." | Anchor 1 = no notable backers, 3 = one tier-1 angel/accelerator. Redbud is a credible micro-VC but not tier-1. 2 is the correct floor between the two anchors. | Keep |
| 🟢 | (traction nulls on growth/retention) | null | "No public MoM growth figure..." | Honest null usage. | Keep |

## Recommended next actions
1. **Fix the Basis Set confusion** in both `users_customers` and `revenue_signal` — investor ≠ customer. Verify the remaining logos are paid customers, not pilots or portfolio peers.
2. **Spot-check founder social channels** to take `velocity` off null (the only observable surface for a thin-press-profile company).
3. **Sharpen `competitive_intensity_inv`** — if you broaden to in-product help/character AI, this drops to 2; the 3 only holds inside a narrowly-defined "mascot for your product" niche.
