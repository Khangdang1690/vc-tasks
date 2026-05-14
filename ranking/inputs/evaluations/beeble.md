# Scoring Audit — Beeble

- **File audited:** `ranking/inputs/startups.json`
- **Current total:** ~61.69/100
- **Data completeness:** 100% (17/17)
- **Schema status:** ✅ valid

## Bear case (one line)
"PBR-aware relighting" is a hard-tech wedge today, but Runway, Luma, Wonder Dynamics, and Adobe Firefly Video are all racing to ship relighting features inside generalist video tools — a five-AI-researcher team with a $4.75M seed has 12–18 months before the wedge erodes against incumbents with 100× the capital.

## Flagged scores

| Severity | Field | Value | Reasoning excerpt | Issue | Suggested action |
|:---|:---|:---:|:---|:---|:---|
| 🔴 | traction.users_customers | 5 | "...ProductionHUB reporting ~3 million downloads of the SwitchLight mobile app (productionhub.com/press/86314) plus pro-studio cloud/desktop users..." | Anchor 5 = "strong design partners or 1k+ active users". 3M *downloads* ≠ active users; reasoning admits "much of that volume is free mobile". The professional users (the actual customers) are small in number per the bear-case logic. | Separate free-mobile downloads from pro-tier active users; if pro count is <1k, drop to 3 or 4 (named-design-partners) |
| 🟡 | team.technical_depth | 4 | "...five AI researchers shipping a 4K video-to-PBR relighting model used in professional Nuke pipelines and on TV productions (Superman & Lois S4, per beeble.ai)..." | Defensible 4. To get to 5 the rubric wants "PhD in the field" or "OSS lead" — none of the five researchers' specific credentials (PhD, FAANG-staff) are cited. | Pull researcher LinkedIn / publication records; if PhD-led ML team is confirmed, defend 5 |
| 🟡 | market.tam_size | 3 | "...VFX software / virtual-production tools market being broadly sized in the high single-digit-to-low-tens-of-billions (per CineD coverage and industry reporting on virtual production growth)..." | "Per CineD coverage" without a specific analyst figure | Cite Grand View Research / virtual-production TAM analyst |
| 🟡 | product.velocity | 4 | "...three major version releases (SwitchLight 1.0 → 2.0 → 3.0) between 2023 and 2025 plus Beeble Studio desktop and cloud launches..." | Three major releases across ~3 years is the 2-anchor (stagnant-to-monthly territory) for the *velocity* sub-score. Anchor 5 = weekly shipping. The 4 overstates without monthly-changelog evidence. | Drop to 3 (monthly-shipping evidence missing) or find a public changelog with monthly cadence |
| 🟡 | traction.engagement_retention | 3 | "...SwitchLight being deployed on TV production (Superman & Lois S4 per beeble.ai) and 'Oscar-winning facilities' as named recurring users plus a paid Studio tier ($500–$3000/yr per cined.com) as a qualitative-retention proxy..." | Proxy-based; "Oscar-winning facilities" is vague — name them. | Specify which named studios are recurring; otherwise keep 3 |
| 🟢 | team.prior_founding_experience | 1 | "...all five Beeble co-founders were prior research scientists at Krafton/Lunit (employee roles, not founder roles)..." | Honest 1, well-cited via founder personal site. | Keep |

## Recommended next actions
1. **Separate free-mobile downloads from professional users** in `users_customers` — the bear-case professional cohort is the value carrier; 3M downloads alone doesn't earn the 5.
2. **Re-audit `product.velocity`** — three major releases across three years is monthly-shipping territory at best, not weekly. Drop to 3 unless a monthly changelog is found.
3. **Specify named recurring studio customers** in `engagement_retention` ("Oscar-winning facilities" is too vague to back a 3).
