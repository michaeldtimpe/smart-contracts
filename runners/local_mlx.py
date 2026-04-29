from __future__ import annotations

import json
import time

from runners.base import StructuredResult, looks_like_refusal


class LocalMLXRunner:
    def __init__(self, model_version_id: str, weights_path: str, file_hash: str, quant: str):
        self.model_version_id = model_version_id
        self.weights_path = weights_path
        self.file_hash = file_hash
        self.quant = quant
        self._loaded = None

    def _load(self):
        if self._loaded is None:
            from mlx_lm import load
            self._loaded = load(self.weights_path)
        return self._loaded

    def complete_structured(self, system, user, schema, seed, temperature):
        from mlx_lm import generate

        model, tokenizer = self._load()
        prompt = self._format_prompt(tokenizer, system, user, schema)

        start = time.time()
        text = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=4096,
            temp=temperature,
            seed=seed,
        )
        wall = time.time() - start

        refused = looks_like_refusal(text)
        parsed = self._extract_json(text, schema)
        if parsed is None:
            refused = True

        return StructuredResult(
            raw_output=text,
            parsed=parsed,
            refused=refused,
            cost_usd=0.0,
            tokens_in=len(tokenizer.encode(prompt)),
            tokens_out=len(tokenizer.encode(text)),
        )

    def _format_prompt(self, tokenizer, system: str, user: str, schema: dict) -> str:
        schema_hint = (
            "Respond ONLY with a single JSON object matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "No prose, no Markdown fences."
        )
        messages = [
            {"role": "system", "content": f"{system}\n\n{schema_hint}"},
            {"role": "user", "content": user},
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def _extract_json(self, text: str, schema: dict) -> dict | None:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
        return None

    def complete_with_tools(self, system, user, tools, sandbox, max_tool_calls, max_wall_seconds, early_stop_check):
        raise NotImplementedError("local agent loop TBD — use mlx_lm with grammar-constrained tool-call decoding")
