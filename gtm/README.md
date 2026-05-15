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

## Install

```bash
pip install baml-scout                       # core, Gemini-only ($0 path)
pip install 'baml-scout[openai]'             # add OpenAI adapter
pip install 'baml-scout[anthropic]'          # add Anthropic adapter
pip install 'baml-scout[all]'                # all providers
npm install -g @boundaryml/baml              # provides baml-cli (required for validation)
echo "GEMINI_API_KEY=your-free-key" > .env   # get one at https://aistudio.google.com/
```

For rate-limit resilience, comma-separate multiple keys: `GEMINI_API_KEY=key1,key2,key3`. The scout rotates on `429`s and exits cleanly when all keys are exhausted — never silently switches to a paid provider.

### From source (development)

```bash
git clone https://github.com/Khangdang1690/vc-tasks.git
cd vc-tasks/gtm
uv sync --dev
uv run pytest          # 63 tests, no network
uv run baml-scout --help
```

### Switching to a paid provider

A first run on a paid provider hits an explicit "this is a PAID API" confirmation; pass `--yes` to acknowledge.

```bash
echo "OPENAI_API_KEY=sk-..." >> .env
baml-scout <repo> --provider openai --yes

echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
baml-scout <repo> --provider anthropic --yes

baml-scout <repo> --provider openai --model gpt-4o --yes
```

## Usage

```bash
baml-scout <repo-url-or-path> [--scan-only] [--benchmark] [--out ./output]
                              [--provider {gemini,openai,anthropic}] [--model NAME] [--yes]
                              [--verbose]
```

Also available: `python -m baml_scout <args>` if you didn't install the entry point.

Examples:

```bash
# Just detect call sites, no LLM calls
baml-scout https://github.com/jxnl/n-levels-of-rag --scan-only

# Full migration + report (default: Gemini free tier)
baml-scout https://github.com/jxnl/n-levels-of-rag

# Full migration + report + measured benchmark
baml-scout https://github.com/jxnl/n-levels-of-rag --benchmark

# Local file or directory
baml-scout ./path/to/some_file.py

# Switch provider (paid — see above)
baml-scout <repo> --provider anthropic --yes
```

## Library use

The CLI is a thin wrapper around an importable Python API. Useful if you want to build the scout into a CI step, a Slack bot, or a hosted demo.

```python
from pathlib import Path
from baml_scout import (
    scan_repo,                       # AST detection
    get_provider, LLMClient,         # provider abstraction
    seed_baml_examples, translate_site,  # translation
    validate_baml_file,              # baml-cli check
    build_context, render_report,    # markdown report
)

sites = scan_repo(Path("./my-project"))

provider = get_provider("gemini")           # or "openai", "anthropic"
client = LLMClient(["YOUR-KEY"], provider=provider)
examples = seed_baml_examples()             # wheel-bundled, no first-run shell-out

for site in sites:
    baml, fn_name = translate_site(client, site, examples)
    result = validate_baml_file(baml)
    if result.ok:
        print(fn_name, "→ valid BAML")
```

Every public name in [src/baml_scout/__init__.py](src/baml_scout/__init__.py) is part of the stable surface; module-private names (`_…`) may change without notice.

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
src/baml_scout/
├── __init__.py        Public library API (re-exports the stable surface)
├── __main__.py        Lets `python -m baml_scout` work without an install
├── cli.py             CLI entry point + orchestration (was scout.py)
├── scanner.py         AST visitor — detects LLM call sites
├── translator.py      Provider-agnostic LLMClient + prompt template
├── providers.py       Provider adapters (Gemini default, OpenAI / Anthropic opt-in)
├── validator.py       baml-cli check + generate subprocess wrappers
├── benchmark.py       Optional --benchmark mode (head-to-head trials)
├── reporter.py        Delta estimation + Jinja rendering
├── config.py          Central config (model, temps, retries, timeouts, skip-dirs)
├── utils.py           Shared helpers (fence-strip, token estimator, logger setup)
├── baml_examples.md   Wheel-bundled few-shot seed
└── templates/
    └── migration_report.md.j2

tests/                 pytest suite (63 tests, no network)
pyproject.toml         Hatchling build; src layout; scripts entry → baml-scout
```

## Constraints honored

- $0 budget by default. Gemini 2.5 Flash free tier is the only required runtime dependency. Multi-key rotation; clean exit on exhaustion. Paid providers (OpenAI, Anthropic) require explicit `--provider` + `--yes`.
- Every generated `.baml` is validated against the compiler before shipping. Honest about translations that fail.
- Voice for the report: senior engineer's post-mortem. No marketing language. No emojis except in the bottom tweet-ready section.
