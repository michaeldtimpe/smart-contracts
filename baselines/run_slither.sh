#!/usr/bin/env bash
set -euo pipefail
ENTRY_DIR="${1:?usage: run_slither.sh <entry_dir>}"
OUT_DIR="${2:-results/baselines/slither}"
mkdir -p "$OUT_DIR"
ENTRY_ID=$(basename "$ENTRY_DIR")
slither "$ENTRY_DIR/contract.sol" \
    --json "$OUT_DIR/${ENTRY_ID}.json" \
    --solc-remaps @openzeppelin=lib/openzeppelin-contracts \
    || true
