"""Render ranked startups as a Markdown report.

Pure: same input → byte-identical Markdown. No timestamps, no env reads.
"""

from __future__ import annotations

from ranking.contract import STAGE_LABEL, STAGES, Startup
from ranking.scoring import PillarResult, ScoredStartup
from ranking.weights import PILLARS, WEIGHTS_BY_STAGE

_BAR_WIDTH = 20


def _bar(pct: float) -> str:
    filled = round(pct / 100.0 * _BAR_WIDTH)
    filled = max(0, min(_BAR_WIDTH, filled))
    return "█" * filled + "░" * (_BAR_WIDTH - filled)


def _fmt(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}"


def _weights_line(stage: str) -> str:
    row = WEIGHTS_BY_STAGE[stage]
    return " / ".join(f"{p.title()} {row[p] * 100:.0f}%" for p in PILLARS)


def _leaderboard(scored: list[ScoredStartup]) -> str:
    lines = [
        "| Rank | Startup | Total | Team | Market | Product | Traction | Data |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for i, s in enumerate(scored, start=1):
        lines.append(
            "| {rank} | {name} | {total:.2f} | {team:.1f} | {market:.1f} | {product:.1f} | {traction:.1f} | {comp:.0%} |".format(
                rank=i,
                name=s.startup.name,
                total=s.total,
                team=s.pillars["team"].normalized,
                market=s.pillars["market"].normalized,
                product=s.pillars["product"].normalized,
                traction=s.pillars["traction"].normalized,
                comp=s.data_completeness,
            )
        )
    return "\n".join(lines)


def _pillar_header(p: PillarResult, weights: dict[str, float]) -> str:
    weight_pct = weights[p.name] * 100
    if p.missing:
        return (
            f"**{p.name.title()} ({weight_pct:.0f}%)** — _no data_ — "
            f"normalized 0.00, filled {p.filled}/{p.total}"
        )
    return (
        f"**{p.name.title()} ({weight_pct:.0f}%)** — raw {_fmt(p.raw_mean)} / 5, "
        f"normalized {p.normalized:.2f}, filled {p.filled}/{p.total} "
        f"`{_bar(p.normalized)}`"
    )


def _sub_score_table(startup: Startup, pillar_name: str) -> str:
    model = getattr(startup, pillar_name)
    fields = list(type(model).model_fields)
    lines = [
        "| Sub-score | Value | Reasoning |",
        "|:---|:---:|:---|",
    ]
    for f in fields:
        sc = getattr(model, f)
        value_cell = "—" if sc.value is None else str(sc.value)
        reasoning_cell = sc.reasoning.strip() if sc.reasoning else "_unknown — no public evidence found_"
        # Escape pipes in reasoning so they don't break the table.
        reasoning_cell = reasoning_cell.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {f} | {value_cell} | {reasoning_cell} |")
    return "\n".join(lines)


def _startup_section(rank_pos: int, s: ScoredStartup) -> str:
    st = s.startup
    parts: list[str] = []
    parts.append(f"### {rank_pos}. {st.name} — {s.total:.2f}/100")
    parts.append("")
    parts.append(f"- **Website:** <{st.website}>")
    parts.append(f"- **Stage:** {STAGE_LABEL[st.stage]}")
    parts.append(f"- **One-liner:** {st.one_liner}")
    parts.append(f"- **Data completeness:** {s.data_completeness:.0%}")
    parts.append("")
    for name in PILLARS:
        parts.append(_pillar_header(s.pillars[name], s.pillar_weights))
        parts.append("")
        parts.append(_sub_score_table(st, name))
        parts.append("")
    if st.notes:
        parts.append(f"**Notes:** {st.notes}")
        parts.append("")
    if s.warnings:
        parts.append("**Warnings**")
        parts.append("")
        for w in s.warnings:
            parts.append(f"- ⚠️ {w}")
        parts.append("")
    return "\n".join(parts)


def render(scored: list[ScoredStartup]) -> str:
    sections: list[str] = []
    sections.append("# Startup Ranking Report")
    sections.append("")
    sections.append(
        "_Scores in [0, 100]. Pillar weights vary by stage; see CONTRACT.md. "
        "Leaderboards are stratified by stage — cross-stage totals are not directly comparable. "
        "Deterministic output._"
    )
    sections.append("")
    sections.append("## Leaderboards")
    sections.append("")

    by_stage: dict[str, list[ScoredStartup]] = {stage: [] for stage in STAGES}
    for s in scored:
        by_stage[s.startup.stage].append(s)

    for stage in STAGES:
        cohort = by_stage[stage]
        if not cohort:
            continue
        sections.append(f"### {STAGE_LABEL[stage]} ({len(cohort)})")
        sections.append("")
        sections.append(f"_Weights: {_weights_line(stage)}._")
        sections.append("")
        sections.append(_leaderboard(cohort))
        sections.append("")

    sections.append("## Per-Startup Breakdown")
    sections.append("")
    for stage in STAGES:
        cohort = by_stage[stage]
        if not cohort:
            continue
        for i, s in enumerate(cohort, start=1):
            sections.append(_startup_section(i, s))
    return "\n".join(sections).rstrip() + "\n"
