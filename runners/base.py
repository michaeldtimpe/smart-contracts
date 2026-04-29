from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class StructuredResult:
    raw_output: str
    parsed: dict | None
    refused: bool
    cost_usd: float
    tokens_in: int
    tokens_out: int


class Runner(Protocol):
    model_version_id: str

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: dict,
        seed: int,
        temperature: float,
    ) -> StructuredResult: ...

    def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict],
        sandbox,
        max_tool_calls: int,
        max_wall_seconds: int,
        early_stop_check,
    ): ...


REFUSAL_PHRASES = [
    "i cannot help with that",
    "i can't help with that",
    "i'm not able to assist",
    "i won't generate",
    "i must decline",
    "as an ai",
    "i'm sorry, but i can't",
    "i'm sorry, but i cannot",
]


def looks_like_refusal(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(phrase in lower for phrase in REFUSAL_PHRASES)
