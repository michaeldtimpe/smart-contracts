from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path


MODELS_DEV_URL = "https://models.dev/api.json"

PROVIDER_KEYS = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": "google",
}


def fetch() -> dict:
    req = urllib.request.Request(
        MODELS_DEV_URL,
        headers={"User-Agent": "smart-contract-llm-benchmark/0.1 (research)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def extract_pricing(data: dict) -> dict:
    out: dict = {"fetched_at": dt.datetime.now(dt.UTC).isoformat(), "source": MODELS_DEV_URL, "providers": {}}
    for provider_name, provider_key in PROVIDER_KEYS.items():
        provider = data.get(provider_key)
        if not provider:
            continue
        models_block = provider.get("models", {})
        provider_out: dict = {}
        for model_id, model in models_block.items():
            cost = model.get("cost") or {}
            if not cost:
                continue
            provider_out[model_id] = {
                "input_per_mtok": cost.get("input"),
                "output_per_mtok": cost.get("output"),
                "cache_write_per_mtok": cost.get("cache_write"),
                "cache_read_per_mtok": cost.get("cache_read"),
                "context": (model.get("limit") or {}).get("context"),
                "max_output": (model.get("limit") or {}).get("output"),
            }
        if provider_out:
            out["providers"][provider_name] = provider_out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("pricing.json"))
    ap.add_argument("--print-claude", action="store_true")
    args = ap.parse_args()

    data = fetch()
    pricing = extract_pricing(data)
    args.out.write_text(json.dumps(pricing, indent=2))
    print(f"Wrote {args.out} ({sum(len(v) for v in pricing['providers'].values())} models across {len(pricing['providers'])} providers)")

    if args.print_claude:
        for model_id, info in pricing["providers"].get("anthropic", {}).items():
            if "claude" in model_id.lower():
                print(f"  {model_id}: ${info['input_per_mtok']}/Mtok in, ${info['output_per_mtok']}/Mtok out")


if __name__ == "__main__":
    sys.exit(main())
