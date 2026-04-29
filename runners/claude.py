from __future__ import annotations

import json
import os
from pathlib import Path

from anthropic import Anthropic

from runners.base import StructuredResult, looks_like_refusal


PRICING_FILE = Path(__file__).parent.parent / "pricing.json"


def _load_pricing(model_id: str) -> dict:
    if not PRICING_FILE.exists():
        return {"input_per_mtok": 0.0, "output_per_mtok": 0.0}
    data = json.loads(PRICING_FILE.read_text())
    anthropic_models = data.get("providers", {}).get("anthropic", {})
    entry = anthropic_models.get(model_id)
    if not entry:
        for k, v in anthropic_models.items():
            if k.startswith(model_id):
                entry = v
                break
    return entry or {"input_per_mtok": 0.0, "output_per_mtok": 0.0}


class ClaudeRunner:
    def __init__(self, model_version_id: str, api_key: str | None = None):
        self.model_version_id = model_version_id
        self.client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self._pricing = _load_pricing(model_version_id)

    def _price(self, tokens_in: int, tokens_out: int) -> float:
        in_rate = self._pricing.get("input_per_mtok") or 0.0
        out_rate = self._pricing.get("output_per_mtok") or 0.0
        return (tokens_in * in_rate + tokens_out * out_rate) / 1_000_000

    def complete_structured(self, system, user, schema, seed, temperature):
        tool = {
            "name": "submit_finding",
            "description": "Submit your structured analysis.",
            "input_schema": schema,
        }
        response = self.client.messages.create(
            model=self.model_version_id,
            max_tokens=8192,
            temperature=temperature,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": "submit_finding"},
            messages=[{"role": "user", "content": user}],
        )

        raw = json.dumps([b.model_dump() for b in response.content])
        parsed = None
        refused = False

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_finding":
                parsed = block.input
                break
            if block.type == "text" and looks_like_refusal(block.text):
                refused = True

        cost = self._price(response.usage.input_tokens, response.usage.output_tokens)
        return StructuredResult(
            raw_output=raw,
            parsed=parsed,
            refused=refused or parsed is None,
            cost_usd=cost,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )

    def complete_with_tools(self, system, user, tools, sandbox, max_tool_calls, max_wall_seconds, early_stop_check):
        raise NotImplementedError("agent_loop integration TBD — wire Anthropic tool-use turns to sandbox here")
