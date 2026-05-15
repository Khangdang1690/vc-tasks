# BAML Migration Scout

Point it at a GitHub repo, get a working BAML migration plus a shareable report. Built as the deliverable for the Basis Set Ventures fellowship Agentic GTM track, targeting [BAML](https://github.com/BoundaryML/baml) (YC W23).

Read the strategic memo first: [STRATEGIC_MEMO.md](STRATEGIC_MEMO.md).

## What it does

1. Clones a GitHub repo (or reads a local path / single `.py` file).
2. AST-scans every Python file for LLM call sites:
   - `openai.chat.completions.create` / `.parse` / `.responses.create`
   - `instructor.from_openai(...)` / `.patch(...)` + any `response_model=`
   - LangChain `PydanticOutputParser` / `StructuredOutputParser`
   - `json.loads(...)` immediately after an LLM call
   - `anthropic.messages.create(..., tools=...)`
3. For each call site, asks the active LLM provider to generate the equivalent `.baml` file. Default is **Gemini 2.5 Flash on the free tier ($0 spent)**; OpenAI and Anthropic are supported via `--provider` for users who knowingly opt in to paid APIs.
4. Validates every generated `.baml` with `baml-cli check`. Retries up to 2 times with the compiler error in context. Drops sites it can't translate cleanly rather than shipping broken BAML.
5. Runs `baml-cli generate` against the final `baml_src/` to produce a working Pydantic client.
6. Optionally (`--benchmark`) runs 5-trial head-to-head trials on the active provider comparing JSON-Schema-in-prompt vs BAML compact-hint formats. Measures tokens, latency, and schema-validity rate.
7. Renders a markdown migration report with before/after diffs, the generated BAML inline, measured deltas, and a tweet-ready summary.

## Setup

```bash
cd gtm/
uv venv
uv sync
npm install -g @boundaryml/baml   # provides baml-cli
echo "GEMINI_API_KEY=your-free-key" > .env     # get one at https://aistudio.google.com/
```

For rate-limit resilience, comma-separate multiple keys: `GEMINI_API_KEY=key1,key2,key3`. The scout rotates on `429`s and exits cleanly when all keys are exhausted — never silently switches to a paid provider.

### Optional: use OpenAI or Anthropic instead

The default ($0) path only needs `google-genai`. To run the translator on a paid provider you must (a) install the matching extra and (b) pass `--provider` explicitly. A first run on a paid provider prompts for `--yes` confirmation so a stray flag can't bill you.

```bash
# OpenAI
uv sync --extra openai
echo "OPENAI_API_KEY=sk-..." >> .env
uv run python scout.py <repo> --provider openai --yes

# Anthropic
uv sync --extra anthropic
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
uv run python scout.py <repo> --provider anthropic --yes

# Override the model for any provider:
uv run python scout.py <repo> --provider openai --model gpt-4o --yes
```

## Usage

```bash
uv run python scout.py <repo-url-or-path> [--scan-only] [--benchmark] [--out ./output]
                                          [--provider {gemini,openai,anthropic}] [--model NAME] [--yes]
                                          [--verbose]
```

Examples:

```bash
# Just detect call sites, no LLM calls
uv run python scout.py https://github.com/jxnl/n-levels-of-rag --scan-only

# Full migration + report (default: Gemini free tier)
uv run python scout.py https://github.com/jxnl/n-levels-of-rag

# Full migration + report + measured benchmark
uv run python scout.py https://github.com/jxnl/n-levels-of-rag --benchmark

# Local file or directory
uv run python scout.py ./path/to/some_file.py

# Switch provider (paid — see "Optional" section above)
uv run python scout.py <repo> --provider anthropic --yes
```

Output lands in `output/<repo-name>/`:

```
output/<repo-name>/
├── migration_report.md      # the artifact — read this
├── baml_src/                # generated .baml files, ready to drop in
│   ├── clients.baml
│   ├── generators.baml
│   └── <function>.baml      # one per migrated call site
├── baml_client/             # output of baml-cli generate
└── patch.diff               # additive diff of the new baml_src/ files
```

## Three live reports

| Repo | Sites | Report |
|---|---:|---|
| jxnl/n-levels-of-rag | 3 | [output/n-levels-of-rag/migration_report.md](output/n-levels-of-rag/migration_report.md) |
| daveebbelaar/ai-cookbook (intro) | 7 | [output/1-introduction/migration_report.md](output/1-introduction/migration_report.md) |
| daveebbelaar/ai-cookbook (workflow patterns) | 11 | [output/2-workflow-patterns/migration_report.md](output/2-workflow-patterns/migration_report.md) |

## Project layout

```
scout.py        CLI entry point + orchestration
scanner.py      AST visitor — detects LLM call sites
translator.py   Provider-agnostic LLMClient (multi-key rotation, token tracking) + prompt template
providers.py    Provider adapters (Gemini default, OpenAI / Anthropic opt-in)
validator.py    baml-cli check + generate subprocess wrappers
benchmark.py    Optional --benchmark mode (head-to-head trials)
reporter.py     Delta estimation + Jinja rendering
config.py       Central config (model, temps, retries, timeouts, skip-dirs)
utils.py        Shared helpers (fence-strip, token estimator, logger setup)
templates/migration_report.md.j2    The report template
baml_examples.md  Few-shot bundle (seeded from baml-cli init on first run)
```

## Constraints honored

- $0 budget by default. Gemini 2.5 Flash free tier is the only required runtime dependency. Multi-key rotation; clean exit on exhaustion. Paid providers (OpenAI, Anthropic) require explicit `--provider` + `--yes`.
- Every generated `.baml` is validated against the compiler before shipping. Honest about translations that fail.
- Voice for the report: senior engineer's post-mortem. No marketing language. No emojis except in the bottom tweet-ready section.
