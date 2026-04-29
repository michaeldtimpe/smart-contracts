# Lessons

A running log of mistakes made and what we learned. Append-only — old entries stay even after the issue is fixed, because the next person hitting the same wall benefits from seeing how we got out.

Format: `## YYYY-MM-DD — short title` then a paragraph or two on what happened, what we did, and the takeaway.

---

## 2026-04-29 — `forge install --no-commit` flag was removed

Tried to install Foundry libs with `forge install foundry-rs/forge-std --no-commit`. Modern Foundry doesn't have this flag — the install behavior changed and the equivalent is now `--commit` (default off). Wasted a step.

**Takeaway**: don't reach for flags from memory; check `forge install --help` when on a new toolchain version. Documented commands age fast in this ecosystem.

---

## 2026-04-29 — Homebrew Python is PEP 668 externally-managed

`pip install -e .` against the system Python failed with PEP 668 errors (Homebrew marks its Python as externally managed). Standard problem on macOS in 2024+. Solution was a local `.venv/`.

**Takeaway**: always venv. The `Makefile`'s `install` target should create the venv automatically — currently it doesn't, which is a footgun for anyone running `make install` on a fresh checkout. Fix when convenient.

---

## 2026-04-29 — `urllib.request` 403'd against models.dev

`tools/fetch_pricing.py` failed with 403 Forbidden on the first attempt. Cause: `urllib`'s default `User-Agent: Python-urllib/3.x` is blocked by some CDNs. Fixed by setting `User-Agent: smart-contract-llm-benchmark/0.1 (research)`.

**Takeaway**: when scraping or fetching from any third-party service, set a real UA from the start. Saves a debug round-trip.

---

## 2026-04-29 — DeFiHackLabs README index doesn't link directly to test files

Initial importer assumed README anchors pointed to `src/test/...sol` paths. They actually point to `past/YYYY/README.md#anchor` summaries. Test paths have to be derived from a filesystem walk of `src/test/YYYY-MM/<Project>_exp.sol` and matched back to README entries.

**Takeaway**: when integrating with an external corpus, walk the filesystem first and use the index to *enrich*, not as the source of truth. Filesystem state is canonical.

---

## 2026-04-29 — Stratified sample collapsed when many bugs share a month

First pass at the test-to-classification join used `max(date_in_month)` as the matcher, which meant every PoC in the same month inherited the same vuln class. Stratified sample over-counted some classes and under-counted others.

**Takeaway**: when matching from a many-to-many index, match on multiple keys (date AND project slug). Single-key matches are guaranteed to collapse on common collisions.

---

## 2026-04-29 — Imported tests broke on `import "../interface.sol"`

DeFiHackLabs tests import a shared `interface.sol` from one directory up. After moving each test into its own entry directory, the relative import path no longer resolved. First run produced 20 unrunnable tests.

**Takeaway**: when importing from another repo's structure into ours, audit ALL relative imports, not just the obvious ones. Fixed by copying `interface.sol` next to each entry and rewriting the import path. Trade-off: ~200KB duplicated 20×, but each entry is now self-contained which is the right property for a benchmark.

---

## 2026-04-29 — Fork-block extractor only matches one Foundry pattern

Initial regex matched `vm.createSelectFork("eth", BLOCK_NUMBER)` and got 12/20 entries. The other 8 use `vm.rollFork(BLOCK)` or split-arg patterns or compute the block from a constant. Result: 8 entries with `fork_block: null` in metadata, which would fail `make verify` until backfilled.

**Takeaway**: Foundry has at least four ways to pin a fork block. A robust extractor needs all of them OR a fallback that prompts for manual entry. For now, the 8 missing blocks are flagged for backfill; the extractor is documented as best-effort, not exhaustive.

---

## 2026-04-29 — Plan rounds compounded, but were necessary

The research plan went through four explicit feedback rounds before approval (initial → mutation/canary additions → pass@1 + clean negatives + Apple Silicon → wild phase). Each round added real rigor (mutation deep-refactor, Q8/Q16 quantization, refusal-as-outcome, continuous-halt rule, pre-signaled disclosure). Tempting to view this as "slow" but it would have been worse to ship a flawed design and re-run 2,160 trials.

**Takeaway**: for whitepaper-grade work, plan iteration cost is paid once; benchmark re-run cost is paid every time the design has a hole. Default to planning depth proportional to the cost of redoing the experiment.

---

## 2026-04-29 — "Use Claude as our test model" simplified the lineup

User has Anthropic Max with sufficient API allowance. Switching from a 6-model OpenAI/Gemini/Claude/open-weights lineup to a 3-Claude-versions + 3-open-weights lineup eliminates ~$3k of expected API spend, removes the silent-API-update risk for two providers (OpenAI, Gemini), and gives a within-vendor capability gradient (Opus → Sonnet → Haiku) that's analytically interesting in its own right.

**Takeaway**: when budget or availability changes the lineup, look for whether the change *also* improves methodological cleanliness. Often you can turn a constraint into a feature. Within-vendor gradients are worth comparing alongside cross-vendor.
