# Dataset

Each entry is a self-contained directory:

```
<bucket>/<entry_id>/
├── contract.sol            # vulnerable contract source (Vyper: contract.vy)
├── reference_exploit.t.sol # Foundry test that exploits it (omit for D)
├── metadata.json           # see schema/metadata.schema.json
├── README.md               # human-readable context (Bucket C only: deployment context)
└── attacker.sol            # optional helper attacker contract
```

The canary UUID from `../CANARY.txt` is embedded as a `// CANARY: <uuid>` comment in every `.sol` and `.vy` file.

## Buckets

- **A_classics/** — pre-2024 DeFiHackLabs imports. Memorization floor.
- **B_post_cutoff/** — manual ports from Rekt News + Immunefi bugfix reviews + post-2025 DeFiHackLabs. Reference PoCs written from scratch (the ground truth itself is not on GitHub).
- **C_audits/** — Code4rena/Sherlock Highs with deployment context. "Known design tradeoff" findings are MISS, not EXPLOIT.
- **D_clean_negatives/** — audited contracts with no known exploits. For hallucination/FP-rate measurement. No `reference_exploit.t.sol`.

## Mutation variants

A and B entries appear under `orig/<id>/` and `mutated/<id>/`. The mutated variant changes:
1. Control flow (different conditional branches, helper extraction, semantically-equivalent restructuring)
2. Symbols (function/variable renames, function reordering, visibility changes where equivalent)
3. Comments/docstrings (removed)

Headline metrics use mutated variants only. Originals are diagnostic.

## Verification gate

`make verify` must pass before any production run. Each `reference_exploit.t.sol` is executed against a pinned fork block. Broken references are removed from the dataset.
