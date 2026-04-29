# EVM Smart Contract LLM Exploit Benchmark

Empirical study testing whether frontier and open-source LLMs reliably produce exploit-grade PoCs for known EVM vulnerabilities. Solo research effort. Whitepaper deliverable.

## Documentation

- [STRATEGY.md](STRATEGY.md) — research design, hypothesis, phases, threats to validity.
- [ARCHITECTURE.md](ARCHITECTURE.md) — system layout, data flow, reproducibility guarantees.
- [AGENTS.md](AGENTS.md) — guidelines for AI coding agents working on the repo.
- [LESSONS.md](LESSONS.md) — running log of mistakes and what we learned.
- [PREREGISTRATION.md](PREREGISTRATION.md) — pre-registration document. **DRAFT until frozen.**

The full approved plan (history of decisions and trade-offs) is at `~/.claude/plans/serialized-orbiting-mist.md`.

## Phases

1. **Pilot** — 5 contracts × 1 frontier + 1 local model, single-shot harness. Pipeline validation. M1 Max 64GB, Q4_K_M open weights.
2. **Benchmark** — 60 contracts (Buckets A/B/C/D) × 6 models × 2 harnesses × 3 reps = 2,160 trials. Models: 3 Claude versions (Opus 4.7, Sonnet 4.6, Haiku 4.5) + 3 self-hosted open-weights (DeepSeek-V3, Qwen 3 32B, Llama 3.3 70B). M5 Max 128GB, Q8_0 / Q16 open weights. Frontier API ceiling **$5k**, expected $0–500 (Anthropic Max covers Claude).
3. **Wild** — ~30 live audited contracts with active bug bounties, agentic loop only, top 3 models from benchmark. Frontier API hard cap **$2k**. Continuous-halt on EXPLOIT, encrypted transcripts, audit-firm liaison on standby.

## Layout

```
dataset/        Test contracts + reference Foundry PoCs + metadata
harness/        single_shot.py, agent_loop.py, prompts (primary + shadow framing)
runners/        Per-model API/local runners (Claude, GPT, Gemini, mlx)
baselines/      Slither, Mythril, Semgrep (detection-only baseline)
grading/        Foundry pass/fail → outcome classification
results/        Per-run transcripts, costs, outcomes
disclosures/    Sealed reports for live findings (opened post-embargo)
analysis/       Notebooks for the whitepaper figures
```

## Canary

Every dataset file carries the canary UUID from `CANARY.txt`. Future researchers can grep model outputs for it to detect post-hoc training-data leakage of this benchmark.

## Disclosure

Live-target findings (any phase) follow a 90-day embargo via Immunefi or audit-firm liaison. Sealed reports go in `disclosures/` and are opened only after fix confirmation. The repo never publishes working exploits against live contracts.
