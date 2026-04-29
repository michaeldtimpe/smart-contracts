#!/usr/bin/env bash
set -euo pipefail
ENTRY_DIR="${1:?usage: run_semgrep.sh <entry_dir>}"
OUT_DIR="${2:-results/baselines/semgrep}"
mkdir -p "$OUT_DIR"
ENTRY_ID=$(basename "$ENTRY_DIR")
semgrep \
    --config "p/smart-contracts" \
    --json \
    --output "$OUT_DIR/${ENTRY_ID}.json" \
    "$ENTRY_DIR/contract.sol" \
    || true
