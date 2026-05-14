# evaluations/

Per-startup audit reports written by the `startup-scoring-critic` skill.

One file per startup, named `<slug>.md` where `<slug>` is the lowercased,
hyphenated `name` field from `inputs/startups.json` (e.g. `tigris-data.md`,
`mem0.md`, `baml.md`).

These files are **outputs of the critic step**, not inputs to the ranking pipeline.
They live under `inputs/` because they are research artifacts that inform revisions
to `inputs/startups.json` before the final rank step.

Re-running the critic overwrites existing files for the same startup. If you
remove a startup from `inputs/startups.json`, its evaluation file becomes stale;
the critic will flag this but will not auto-delete it.
