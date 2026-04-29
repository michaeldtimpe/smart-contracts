from __future__ import annotations

import json
import os

from openai import OpenAI

from runners.base import StructuredResult, looks_like_refusal


PRICING_PER_MTOK = {}


class OpenAIRunner:
    def __init__(self, model_version_id: str, api_key: str | None = None):
        self.model_version_id = model_version_id
        self.client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    def _price(self, tokens_in: int, tokens_out: int) -> float:
        p = PRICING_PER_MTOK.get(self.model_version_id, {"in": 0.0, "out": 0.0})
        return (tokens_in * p.get("in", 0.0) + tokens_out * p.get("out", 0.0)) / 1_000_000

    def complete_structured(self, system, user, schema, seed, temperature):
        response = self.client.chat.completions.create(
            model=self.model_version_id,
            temperature=temperature,
            seed=seed,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "finding", "strict": True, "schema": schema},
            },
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = response.choices[0].message.content or ""
        parsed = None
        refused = looks_like_refusal(raw)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            refused = True

        usage = response.usage
        return StructuredResult(
            raw_output=raw,
            parsed=parsed,
            refused=refused,
            cost_usd=self._price(usage.prompt_tokens, usage.completion_tokens),
            tokens_in=usage.prompt_tokens,
            tokens_out=usage.completion_tokens,
        )

    def complete_with_tools(self, system, user, tools, sandbox, max_tool_calls, max_wall_seconds, early_stop_check):
        raise NotImplementedError("agent_loop integration TBD — wire OpenAI tool calls to sandbox here")
