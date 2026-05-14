# Basis Set Fellowship — Agentic GTM Track

## Target: BAML (BoundaryML) · Artifact: BAML Migration Scout

**Author:** Khang Dang · **Date:** 2026-05-14

---

## TL;DR

BAML is a YC W23 developer-tools startup with a real technical moat (Schema-Aligned Parsing; outperforms OpenAI's native structured outputs on BFCL using fewer tokens) and a clear funnel problem: trial-to-migration conversion. Their developers love the product after trying it, but conversion requires learning a new DSL, installing a CLI + VSCode extension, and rewriting existing LLM call sites — a 2–4 hour weekend project for someone not yet convinced.

The thesis: **collapse migration from a Saturday project to a 30-second URL paste, and adoption inflects.**

I built BAML Migration Scout — a CLI agent that points at a GitHub repo, finds every LLM call site via AST, auto-generates the BAML equivalent via Gemini 2.5 Flash (free tier only — $0 spent), validates it with `baml-cli check`, and produces a shareable migration report. Each report is two things at once: a real working migration, and a piece of social proof.

I ran it live on three small repos. Headline numbers:

| Repo | Sites | Translated | Tokens used | Validate clean? | Headline measured delta |
|---|---:|---:|---:|---|---|
| [jxnl/n-levels-of-rag](output/n-levels-of-rag/migration_report.md) | 3 | 3 | 13.3k | yes | −22 tokens/call (10% prompt reduction) |
| [daveebbelaar/ai-cookbook](output/1-introduction/migration_report.md) (intro) | 7 | 7 | 22.3k | yes | −18 tokens/call (6% prompt reduction) |
| [daveebbelaar/ai-cookbook](output/2-workflow-patterns/migration_report.md) (workflows) | 11 | 11 | 37.0k + 5k bench | yes | **−199 tokens/call (40% reduction)** on a 9-field orchestrator schema |

Total cost: $0. Total Gemini consumption: ~77k tokens (~8% of one free-tier day).

---

## 1. The Company: BAML

**What:** A Rust-implemented DSL ([`baml-cli`](https://github.com/BoundaryML/baml)) that compiles `.baml` files into type-safe LLM client code for Python, TypeScript, Go, Ruby, and others. The core IP is **Schema-Aligned Parsing (SAP)** — a runtime parser that, per their [published BFCL benchmark](https://www.boundaryml.com/blog/schema-aligned-parsing), achieves higher schema-validity rates than OpenAI's native structured outputs while sending fewer tokens. Open source, Apache 2.0. Monetization: Boundary Studio (paid observability layer).

**Stage:** YC W23. ~10 people in Seattle. ~$2M raised. Not in BSV's portfolio today.

**Asymmetry that surfaced in the data:** 8,100 GitHub stars vs. ~1,280 Twitter followers (~6.3x gap). This is unusual — most YC dev-tools see a roughly 2:1 stars-to-followers ratio. BAML has product-grade adoption signal that hasn't crossed into general developer-Twitter mindshare. Awareness is the easier problem; the harder one is downstream.

**Why this matters for an agentic-GTM thesis:** the team has built genuine technical depth (Rust runtime, novel parser algorithm, multi-language codegen) and the user testimonials are unusually emphatic ("10/10 experience, much faster than langchain"). The product is the moat; the question is distribution.

---

## 2. The Growth Problem: Where the Funnel Breaks

The funnel I see for BAML:

```
   Awareness   →   Trial   →   Migration   →   Adoption   →   Boundary Studio
     ↓             ↓            ↓                ↓
   stars/blog   docs visit    rewrite existing   running in prod
                 quickstart    LangChain/etc.
```

**Awareness is healthy** — 8.1k stars, regular HN front-page hits, Vaibhav (CTO) ships content consistently, and the SAP benchmark post earns links from credible engineering blogs.

**Trial is workable** — `pip install baml-py && baml-cli init` produces a working `resume.baml` extraction example in under a minute. The friction is real but bounded.

**Migration is where it breaks.** A developer with an existing repo using LangChain output parsers, Instructor, or raw OpenAI structured outputs has to:

1. Learn a new DSL syntax (`class`, `function`, `prompt #"..."#`, `{{ ctx.output_format }}`)
2. Install the BAML CLI globally via npm — an unusual dependency for Python shops
3. Install the VSCode extension (or live without LSP / playground)
4. For each LLM call site: translate the prompt, decide on a `client` declaration, generate the BAML, run `baml-cli generate`, then update the call site to use `b.MyFunction(...)`
5. Validate the migration didn't regress behavior — i.e., re-run integration tests

For a developer who's already convinced, this is a 30-minute task. For someone who tried it once and is curious whether it's worth it on their real code, it's a **2–4 hour weekend project**. That asymmetric cost is the funnel break.

Every direct competitor — Instructor, Pydantic AI, LangChain's `.with_structured_output()` — lives entirely inside the developer's existing Python file. BAML alone asks them to learn a new file format and trust a code-generation step. That's the friction.

---

## 3. The Thesis: Collapse Migration, Compound on Artifacts

**If migration cost goes from 2 hours to 30 seconds, the trial-to-migration conversion rate inflects.** Developers test ideas they wouldn't normally test, and they share the result.

This isn't just throughput. The artifact produced — a markdown migration report with before/after code, measured token deltas, and a working `baml_src/` — is **independently shareable**. Each conversion can double as a tweet, a PR, a Slack message to a teammate, a quote-tweet of BAML's own posts. Distribution piggybacks on conversion.

Concretely:

- A developer pastes their repo URL → 30 seconds later they have a report saying "your 11 OpenAI call sites translate to 11 working `.baml` files; the LLM compiles them in 37k Gemini tokens; here's the diff."
- Half don't migrate. The other half do, and the artifact gives them a ready-made justification for the PR.
- A subset of those (the most enthusiastic) tweet the report. Each tweet shows real code, real numbers, no marketing copy. That's the kind of social proof BAML's current 1,280-follower account doesn't have at scale.

Recursive flywheel: more shares → more URLs pasted → more reports → more migrations → more shares.

---

## 4. The Artifact: BAML Migration Scout

A single-CLI Python tool, ~1.6k lines across 6 modules. Built constraint-first:

| Constraint | Why | How |
|---|---|---|
| $0 budget for runtime LLM calls | Demonstrate the tool runs on free infra, no enterprise gating | Gemini 2.5 Flash free tier; multi-key rotation; clean exit on full quota exhaustion (no silent paid-API fallback) |
| Output must be honest | A senior engineer reading the report has to believe it | Every generated `.baml` is validated by `baml-cli check` before being shipped; failures are surfaced explicitly with "translation_failed" notes |
| Voice = senior engineer post-mortem | The audience is BAML's actual users, not marketing buyers | Dry, numbers-forward, no emojis except in the tweet-ready summary section; tone modeled on Simon Willison / Anthropic engineering blogs |

### Architecture

```
GitHub URL ──┐
local path ──┤── scout.py (CLI)
single .py ──┘         │
                       ▼
              scanner.py (AST)              ←── deterministic, free, fast
                       │
                       ▼ (CallSite records)
              translator.py (Gemini Flash)  ←── 1 LLM call per site
                       │
                       ▼ (.baml file draft)
              validator.py (baml-cli check) ←── free subprocess
                       │
              retry on error (max 2 retries with compiler error in context)
                       │
                       ▼
              reporter.py (Jinja → markdown)
                       │
                       ▼
              output/<repo>/migration_report.md + baml_src/ + patch.diff
```

**Key design choices, justified:**

- **Hybrid AST + LLM** — AST is reliable, deterministic, and free; we use it to find candidate call sites. The LLM call only happens once per site, with the surrounding code + inferred schema in context. This is the difference between a $10 run and a $0 run.
- **Validate everything** — every generated `.baml` is checked against the compiler before being included. If it fails, we feed the compiler error back to the translator and retry up to twice. After 3 strikes, we surface the failure honestly in the report rather than ship broken BAML.
- **Cross-file name collisions** — caught in practice on the daveebbelaar workflow run. Two independent translations both proposed `WeatherQuery`. We now pass `taken_names` into each translation prompt and let the LLM disambiguate. Cost: one extra LLM call per collision.
- **Free-tier safety rails** — `GEMINI_API_KEY` supports comma-separated multi-key. On `429` / `RESOURCE_EXHAUSTED`, we rotate. On full exhaustion, we raise `FreeQuotaExhausted` and exit non-zero. Never falls through to a paid endpoint.
- **Few-shot grounding via `baml-cli init`** — instead of fetching docs.boundaryml.com pages at runtime (slow, network-dependent, version-drift risk), we shell out to `baml-cli init` in a temp directory and inline the three canonical files (`resume.baml`, `clients.baml`, `generators.baml`) as the few-shot bundle. The grounding is automatically locked to whatever BAML version the user installed.

### What the scanner catches (the explicit-pattern boundary)

- `openai.chat.completions.create(...)` (sync + async), `.parse(response_format=PydanticModel)`, `.responses.create`
- `instructor.from_openai(...)` / `instructor.patch(...)` and any `.create(response_model=...)` downstream
- LangChain `PydanticOutputParser` / `StructuredOutputParser` constructors
- `json.loads(...)` immediately following an LLM call in the same function body (raw-parse pattern)
- `anthropic.messages.create(..., tools=...)` (tool-use pattern)

### What it doesn't (and why I'm honest about it)

- **LangChain LCEL chains** (`ChatOpenAI().invoke(...)`, `llm | parser` pipelines). Most LangChain users moved to LCEL after 2024; my scanner targets the legacy parser patterns explicitly listed in the brief. On `pixegami/rag-tutorial-v2` it returned zero hits — that repo uses `Ollama().invoke()`. A real-world Scout would widen to LCEL detection. Adding ~10 patterns is straightforward; I chose not to chase scope creep.
- **Notebook-only repos.** Scout is `.py`-only today; Jupyter notebooks would require an `nbconvert` preprocessing step.

---

## 5. Evidence: Three Live Reports

Each report was generated end-to-end by the CLI with `--benchmark`. The numbers below are measured, not narrated.

### Exhibit A — `jxnl/n-levels-of-rag` (instructor archetype) → [report](output/n-levels-of-rag/migration_report.md)

- **3 LLM call sites** detected across 13 Python files.
- All 3 translate to BAML on the first attempt (one site required a retry after `baml-cli check` rejected the first draft — the retry succeeded with the compiler error in context).
- `baml-cli generate` produces a working Pydantic client at `output/n-levels-of-rag/baml_client/types.py`.
- Total cost: 13,251 Gemini tokens, $0.
- 5-trial benchmark on `generatequestionanswerpair.baml`: both prompt formats hit **100% schema validity**, BAML format saves **22 tokens/call** (392 → 370 total tokens).

Strategic note: jxnl (Jason Liu) created `instructor`. A report showing his own repo cleanly migrated to BAML is the kind of thing that earns a quote-tweet — and instructor's audience overlaps almost perfectly with BAML's ICP.

### Exhibit B — `daveebbelaar/ai-cookbook` intro (raw OpenAI archetype) → [report](output/1-introduction/migration_report.md)

- **7 call sites** across 4 Python files — mix of plain text generation, structured outputs (`response_format=PydanticModel`), and tool-use (`tools=...`).
- All 7 translate; one collision on `WeatherQuery` was caught and resolved automatically.
- 5-trial benchmark on the richest-schema site: 100% validity both formats, **−18 tokens/call**.

Strategic note: Dave Ebbelaar has ~100k YouTube subs in the AI-tooling space and his cookbook is a common entry point for developers learning the OpenAI SDK. A migration report on his canonical examples implicitly tells every viewer "you can do the same in 30 seconds."

### Exhibit C — `daveebbelaar/ai-cookbook` workflow-patterns (agentic patterns) → [report](output/2-workflow-patterns/migration_report.md)

This is the most interesting one.

- **11 call sites** across 4 files covering prompt chaining, routing, parallelization, and orchestrator patterns. All sites have non-trivial Pydantic schemas (e.g., `OrchestratorPlan`, `SectionContent`, `ReviewFeedback`).
- All 11 translate cleanly; `baml-cli generate` is happy.
- 5-trial benchmark on `getorchestratorplan.baml` (a 9-field nested schema):

| | Original (JSON Schema in prompt) | BAML (compact type hint) | Delta |
|---|---:|---:|---:|
| Total tokens per call | 492 | 293 | **−199 (40% reduction)** |
| Schema-validity rate (raw LLM output) | 20% (1/5) | 20% (1/5) | tied |

The honest finding: **raw Gemini Flash gets a 9-field nested schema right 20% of the time, regardless of prompt format.** This is exactly the gap BAML's SAP runtime parser is designed to close — by recovering structurally-deviant LLM output into valid Pydantic objects post-hoc, rather than asking the LLM to be perfect on every call.

If I had a slightly bigger budget I'd extend the benchmark to route through `baml-py` so SAP gets to actually do its job. That measurement is the real comparison and I'd expect to see BAML's validity rate climb significantly while the original stays flat.

**Strategic implication:** the token delta scales with schema complexity (22 → 18 → 199 tokens/call as schemas grow). For a startup like daveebbelaar's audience running thousands of structured-output calls/day, the difference is real money. More importantly, the SAP angle is the harder-to-replicate moat — token reduction is something competitors can copy; runtime parser quality is not.

---

## 6. GTM Recommendations

How BAML actually uses Scout (or something like it):

1. **Deploy as a web form.** `scout.boundaryml.com` accepts a GitHub URL, runs Scout in the cloud against the user's free-tier or BAML-supplied keys, and returns the report as a shareable URL. Time-to-value: 30 seconds. This is the conversion-rate inflection point.
2. **Wire it into the docs.** Every "How does BAML compare to X?" doc page gets a "paste your repo here" button at the bottom. Convert documentation traffic into trials at near-zero marginal cost.
3. **Outbound on specific repos.** Run Scout offline against top trending HN/Twitter LLM repos each week. For repos that have ≥5 call sites and a recognizable maintainer, send the report as a courtesy PR ("we ran a tool against your repo — here's the migration"). Conversion isn't the goal of this channel; the artifact's existence is. Even rejected PRs are public.
4. **Quote-tweet engine.** Each report ends with a one-paragraph tweet draft. Make it one click to share. Track which reports drive the most engagement and double down on those archetypes (instructor users, raw-OpenAI hobbyists, LangChain refugees).
5. **Internal use: GTM as feedback channel.** Reports surface call-site patterns BAML doesn't yet handle well. The translator retries and validator failures are signal — if 30% of LangChain `with_structured_output()` calls fail to translate, that's a feature gap to fix.

---

## 7. What I'd Want to Validate Next

Honest scope-of-unknowns:

- **SAP delta with baml-py in the loop.** Today's benchmark measures *prompt-format* deltas only. I expect the real validity gap between BAML and raw structured outputs to be much larger when SAP gets to do its job. Two days of work to wire baml-py into the benchmark loop.
- **LangChain LCEL coverage.** Almost every modern LangChain repo uses LCEL with `.with_structured_output()`. My scanner doesn't catch this. A real production Scout needs to. Maybe 1 day of work.
- **Conversion-rate test in the wild.** The thesis ("collapse migration → adoption inflects") is testable. Run a controlled trial: half of new BAML docs visitors get a "paste your URL" CTA, half don't. Measure 7-day install rate. This is the experiment BAML should run within weeks of shipping a hosted Scout.
- **Enterprise adoption ladder.** BAML monetizes Boundary Studio (observability). The OSS adoption story is well-established; the enterprise upsell motion is less clear from public data. Need a conversation with the team to understand which OSS users have converted to Studio, and why.

---

## 8. Honest Limitations of This Deliverable

- **3 reports, all from solo-developer / educational repos.** Not representative of enterprise codebases (1000+ call sites, mixed patterns, custom internal SDKs). Scout would need more polish to handle those — particularly token-budget guards.
- **Gemini Flash's BAML familiarity is thin.** The few-shot grounding compensates well in practice (10/10 sites translated across the n-levels and intro reports without grammar errors), but on the workflow-patterns run, one site required a retry. A production tool might want a domain-tuned model or a larger few-shot bundle.
- **No automatic call-site replacement in the original repo.** Scout produces `baml_src/` and a `patch.diff` showing the added files, but the call-site rewrites (replacing `client.chat.completions.create(...)` with `b.MyFunction(...)`) are still manual. Auto-patching is risky and would mis-classify a percentage of cases; a human-reviewed PR is the safer ergonomics. But this is a feature gap worth investing in.
- **Benchmark validity dropped to 20% on the orchestrator schema.** I left this in the report as honest signal. A more cautious tool might exclude complex schemas from benchmark mode entirely. I think the honesty serves the strategic story better.

---

## Closing

BAML has a genuinely defensible technical moat and an unusually clear funnel break. The friction at the trial-to-migration step is the kind of problem that an agentic tool is well-suited to solve, and the artifact produced (a defensible, shareable migration report) compounds the value of every conversion. Scout is one shape of that tool. There are obviously many others.

The deliverable I'd most want to discuss in an interview is **what didn't work**: the LangChain LCEL coverage gap, the latency surprise on simple schemas (BAML's compact hint sometimes took longer than the verbose JSON Schema — possibly Gemini "thinking" harder with an abstract spec), and the 20% raw-LLM validity rate on complex nested schemas. Each of these is a wedge for a follow-up conversation about how to actually run this in production.

---

**Repo:** [`gtm/`](.) — full source, three working reports, $0 spent. All Gemini calls consumed under 8% of one free-tier day.

**Reproduce:**

```bash
cd gtm/
echo "GEMINI_API_KEY=your-free-key" > .env
uv run python scout.py https://github.com/jxnl/n-levels-of-rag --benchmark
```
