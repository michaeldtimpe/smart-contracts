from __future__ import annotations

import json
import os

from google import genai
from google.genai import types

from runners.base import StructuredResult, looks_like_refusal


PRICING_PER_MTOK = {}


class GeminiRunner:
    def __init__(self, model_version_id: str, api_key: str | None = None):
        self.model_version_id = model_version_id
        self.client = genai.Client(api_key=api_key or os.environ["GOOGLE_API_KEY"])

    def _price(self, tokens_in: int, tokens_out: int) -> float:
        p = PRICING_PER_MTOK.get(self.model_version_id, {"in": 0.0, "out": 0.0})
        return (tokens_in * p.get("in", 0.0) + tokens_out * p.get("out", 0.0)) / 1_000_000

    def complete_structured(self, system, user, schema, seed, temperature):
        response = self.client.models.generate_content(
            model=self.model_version_id,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                seed=seed,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        raw = response.text or ""
        refused = looks_like_refusal(raw)
        parsed = None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            refused = True

        usage = response.usage_metadata
        return StructuredResult(
            raw_output=raw,
            parsed=parsed,
            refused=refused,
            cost_usd=self._price(usage.prompt_token_count, usage.candidates_token_count),
            tokens_in=usage.prompt_token_count,
            tokens_out=usage.candidates_token_count,
        )

    def complete_with_tools(self, system, user, tools, sandbox, max_tool_calls, max_wall_seconds, early_stop_check):
        raise NotImplementedError("agent_loop integration TBD — wire Gemini function calls to sandbox here")
