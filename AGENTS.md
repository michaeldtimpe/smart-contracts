# Agents Guide

Guidelines for AI coding agents working on this repository (Claude Code, Cursor, OpenAI Codex, etc.). Optimized for Claude Code; the conventions generalize.

## Project at a glance

Empirical benchmark testing whether LLMs reliably produce **exploit-grade** Foundry PoCs against EVM smart contracts. Solo researcher, whitepaper deliverable. The full plan lives at `~/.claude/plans/serialized-orbiting-mist.md`. Read `STRATEGY.md` for the research design and `ARCHITECTURE.md` for the system layout before making changes.

## Hard rules

These are non-negotiable and apply to every change:

1. **No transactions to mainnet, ever.** All on-chain interaction is fork-mode only. The agent loop's tool surface (`harness/agent_loop.py:TOOL_DEFINITIONS`) must never include a transaction-submitting capability. If you add a tool, audit it against this rule.
2. **No live-target runs without explicit gating.** `make wild` refuses to run unless `WILD_LIAISON_CONFIRMED=1` and `WILD_PREREG_HASH` are set. Don't bypass this.
3. **No hardcoded model pricing.** Use `pricing.json` (regenerated via `tools/fetch_pricing.py`). API rates change; runs that priced themselves wrong are corrupt data.
4. **No regex extraction of model output.** All structured outputs go through native API schema enforcement (Anthropic tool use, OpenAI `response_format`, Gemini `response_schema`, llama.cpp grammar). See `harness/schema.py` for the contract.
5. **Don't break the canary.** Every Solidity/Vyper file in `dataset/` must contain `// CANARY: <uuid>` from `CANARY.txt`. The importer enforces this. If you write a new dataset tool, preserve the stamp.
6. **Don't commit `.env` or `disclosures/sealed/`.** Both are in `.gitignore`. Anything in `disclosures/` that isn't a redacted aggregate stays sealed until embargo lifts.
7. **Plan-mode for non-trivial changes.** Methodological changes (metric definitions, grading rules, dataset bucket changes) require a plan and explicit human approval. The PREREGISTRATION.md gate exists for a reason — modifying it is never "just a tweak."

## Soft rules (idioms)

- **Default to no comments.** Well-named symbols beat docstring walls. Comment only the non-obvious WHY (a workaround, a hidden constraint).
- **Prefer Edit over Write** for existing files. Only Write when creating new files or rewriting fully.
- **One file per provider.** Don't unify runners with a meta-config. Three modules of 60 lines each is clearer than one module of 200.
- **Tests over docstrings.** Reproducibility comes from `make verify` passing, not from prose explanations.
- **Don't invent abstractions.** No agent frameworks, no plugin systems, no DI containers. The harness is ~150 lines because that's all it needs to be.

## Workflow conventions

### Memory & plans

- **Persistent memory** lives in `~/.claude/projects/-Users-michaeltimpe-Downloads-smart-contracts/memory/`. Read `MEMORY.md` first when resuming. Save user / project / feedback / reference memories per the conventions described there.
- **Plans** live in `~/.claude/plans/`. The approved plan for this project: `serialized-orbiting-mist.md`.
- **Pre-registration**: `PREREGISTRATION.md` in the repo root. **DRAFT until frozen.** Once you commit a freeze hash, never amend silently — amendments invalidate the experiment.

### Phases & gating

| Phase | Gating |
|---|---|
| Scaffolding | Free — edit, write tools, refactor anything not in `dataset/`. |
| Pilot run | Requires `ANTHROPIC_API_KEY` + working RPC URL + `make verify` green. |
| Benchmark run | Requires `BENCHMARK_PREREG_HASH` env + frozen PREREGISTRATION.md. |
| Wild phase | Requires `WILD_LIAISON_CONFIRMED=1` + `WILD_PREREG_HASH` + bug-bounty target list with scope quotes. |

If your task touches a higher phase, do not bypass lower-phase gates. Ask the human.

### Subagent delegation

Use subagents for:
- Bulk dataset import / classification (Bucket A is mostly mechanical).
- Searching Code4rena/Sherlock public reports for Bucket C candidates.
- Running mutation generation across many entries.

Do not use subagents for:
- Methodological decisions (metric definitions, grading rule changes).
- Model-output triage on the wild phase — those are sensitive transcripts, manual review only.
- Writing reference exploits for Bucket B — that's the human's judgment work, not delegate-able.

### Cost discipline

- **Frontier API spend** is gated by `BENCHMARK_BUDGET_USD` and `WILD_BUDGET_USD` env vars. The harness should respect these. Researcher's Anthropic Max plan covers expected Claude usage; out-of-pocket spend is expected to be near $0.
- **Self-hosted open weights** are the default for non-Claude experiments. Use `runners/local_mlx.py`, not API-hosted variants of Llama/Qwen/DeepSeek.
- **Tool-call cost explosion** in the agent loop is real. The compile-retry/semantic-retry split + same-error-twice early-stop in `harness/agent_loop.py` exists for this. Don't relax it.

## Adding a new model

1. Confirm the model is published with a dated version ID. No moving targets.
2. Create `runners/<provider>.py` implementing the `Runner` Protocol from `runners/base.py`.
3. Use the provider's native structured-output mechanism. No regex.
4. Add the model to `PREREGISTRATION.md` Section 4 with `<TBD>` filled in.
5. If pricing is API-based, ensure `tools/fetch_pricing.py` covers the provider, or add it.
6. If self-hosted, record the file SHA in `PREREGISTRATION.md`.
7. Run a single-trial smoke test against one Bucket A entry before integrating into the benchmark loop.

## Adding a new dataset entry

1. Pick a bucket. Bucket B (post-cutoff) requires reference PoCs **written from scratch** — do not copy from a public repo.
2. Stamp `// CANARY: <uuid>` (from `CANARY.txt`) in every `.sol`/`.vy` file.
3. Write `metadata.json` matching `dataset/schema/metadata.schema.json`.
4. For A/B/C: ensure `reference_exploit.t.sol` passes `make verify` against the pinned fork block.
5. Generate the mutated variant via `tools/mutate_dataset.py` (TBD as of writing — may need to be built).
6. For Bucket C: include `README.md` with deployment context. "Found a known design tradeoff" findings grade as MISS, not EXPLOIT.

## Memory hygiene

When you finish a session, save anything load-bearing for future sessions:
- **User memory** if you learned something about the user's role/preferences.
- **Project memory** for decisions, contacts, deadlines, model lineup changes.
- **Feedback memory** for corrections or non-obvious validated approaches.
- **Reference memory** for external systems (e.g., the Alchemy app URL, the Immunefi liaison contact).

Don't save what's already derivable from `git log`, the code, or `PREREGISTRATION.md`.

## Tooling expectations

- `make install` — Foundry + Python deps.
- `make verify` — reference exploits against pinned forks. Required gate before any production run.
- `make pilot` — 5-contract pilot run (single-shot, 1 frontier + 1 local model).
- `make benchmark` — gated on `BENCHMARK_PREREG_HASH`.
- `make wild` — gated on `WILD_LIAISON_CONFIRMED` + `WILD_PREREG_HASH`.
- `make grade RUN_DIR=...` — re-grade an existing run.
- `make analyze` — generate whitepaper figures.

If you add a phase or workflow, add a Make target and document the gate.
