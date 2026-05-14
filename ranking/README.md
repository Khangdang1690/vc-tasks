# ranking

Deterministic ranking pipeline for tech startups across pre-seed → Series C.

Claude Code (separately) researches each startup and fills in a structured JSON file
against the data contract in [ranking/contract.py](ranking/contract.py). The pipeline
validates the JSON, scores each startup on **Team / Market / Product / Traction**, ranks
them within stage cohorts, and writes a Markdown report. Given the same input it always
produces a byte-identical output — no randomness, no clocks, no network.

## Weights (per stage)

Earlier stages weight founder/team signal heavier; later stages weight execution/traction heavier.

| Stage | Team | Market | Product | Traction |
|---|---:|---:|---:|---:|
| pre_seed | 45% | 25% | 20% | 10% |
| seed     | 40% | 25% | 20% | 15% |
| series_a | 30% | 25% | 20% | 25% |
| series_b | 20% | 25% | 25% | 30% |
| series_c | 15% | 20% | 25% | 40% |

Cross-stage totals are not directly comparable — the report stratifies leaderboards by
stage. Traction anchors are also stage-specific (see [CONTRACT.md](CONTRACT.md)). Edit
[ranking/weights.py](ranking/weights.py) to change the thesis.

## Setup

```pwsh
cd ranking
uv sync
```

This creates `.venv/` and installs `pydantic` (runtime) and `pytest` (dev).

## Run

```pwsh
uv run python -m ranking inputs/startups.json out/report.md
# or write to stdout
uv run python -m ranking inputs/startups.json -
```

## Test

```pwsh
uv run pytest -q
```

## Workflow

1. **Research** — In a fresh Claude Code session, fill in `inputs/startups.json` from web research.
2. **Critique** — In another fresh session, invoke the `startup-scoring-critic` skill (defined at `.claude/skills/startup-scoring-critic/SKILL.md`). It writes one Markdown audit file per startup to `inputs/evaluations/<slug>.md` and replies with a session summary.
3. **Revise** — Address the critic's must-fix items; re-research where flagged.
4. **Rank** — `uv run python -m ranking inputs/startups.json out/report.md`.

See [CONTRACT.md](CONTRACT.md) for the input format and scoring anchors.
