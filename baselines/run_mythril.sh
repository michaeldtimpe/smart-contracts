#!/usr/bin/env bash
set -euo pipefail
ENTRY_DIR="${1:?usage: run_mythril.sh <entry_dir>}"
OUT_DIR="${2:-results/baselines/mythril}"
mkdir -p "$OUT_DIR"
ENTRY_ID=$(basename "$ENTRY_DIR")
myth analyze "$ENTRY_DIR/contract.sol" \
    -o jsonv2 \
    --execution-timeout 300 \
    > "$OUT_DIR/${ENTRY_ID}.json" \
    || true
