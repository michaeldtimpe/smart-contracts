from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from harness.schema import SINGLE_SHOT_OUTPUT_SCHEMA


PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class Trial:
    entry_id: str
    bucket: str
    variant: str
    model_version_id: str
    framing: str
    rep: int
    seed: int
    temperature: float
    started_at: float
    ended_at: float | None = None
    raw_output: str | None = None
    parsed: dict | None = None
    refused: bool = False
    error: str | None = None
    cost_usd: float = 0.0
    cost_tokens_in: int = 0
    cost_tokens_out: int = 0
    metadata: dict = field(default_factory=dict)


def load_prompt(framing: str) -> str:
    path = PROMPTS_DIR / f"system_{framing}.md"
    return path.read_text()


def build_user_message(contract_path: Path, deployment_context: str | None) -> str:
    contract_src = contract_path.read_text()
    parts = [f"Contract source:\n\n```solidity\n{contract_src}\n```"]
    if deployment_context:
        parts.append(f"\nDeployment context:\n\n{deployment_context}")
    return "\n".join(parts)


def run_trial(
    runner,
    entry_dir: Path,
    bucket: str,
    variant: str,
    rep: int,
    seed: int,
    temperature: float,
    framing: str = "primary",
) -> Trial:
    contract_path = entry_dir / "contract.sol"
    if not contract_path.exists():
        contract_path = entry_dir / "contract.vy"
    metadata = json.loads((entry_dir / "metadata.json").read_text())
    deployment_context = None
    readme = entry_dir / "README.md"
    if bucket == "C_audits" and readme.exists():
        deployment_context = readme.read_text()

    system_prompt = load_prompt(framing)
    user_message = build_user_message(contract_path, deployment_context)

    trial = Trial(
        entry_id=metadata["entry_id"],
        bucket=bucket,
        variant=variant,
        model_version_id=runner.model_version_id,
        framing=framing,
        rep=rep,
        seed=seed,
        temperature=temperature,
        started_at=time.time(),
    )

    try:
        result = runner.complete_structured(
            system=system_prompt,
            user=user_message,
            schema=SINGLE_SHOT_OUTPUT_SCHEMA,
            seed=seed,
            temperature=temperature,
        )
        trial.raw_output = result.raw_output
        trial.parsed = result.parsed
        trial.refused = result.refused
        trial.cost_usd = result.cost_usd
        trial.cost_tokens_in = result.tokens_in
        trial.cost_tokens_out = result.tokens_out
    except Exception as e:
        trial.error = repr(e)

    trial.ended_at = time.time()
    return trial


def save_trial(trial: Trial, results_root: Path) -> Path:
    trial_dir = (
        results_root
        / trial.model_version_id
        / trial.bucket
        / trial.variant
        / trial.entry_id
        / f"rep{trial.rep}_seed{trial.seed}_t{trial.temperature}_{trial.framing}"
    )
    trial_dir.mkdir(parents=True, exist_ok=True)
    (trial_dir / "trial.json").write_text(json.dumps(asdict(trial), indent=2, default=str))
    if trial.parsed and trial.parsed.get("foundry_test"):
        (trial_dir / "Exploit.t.sol").write_text(trial.parsed["foundry_test"])
    if trial.parsed and trial.parsed.get("attacker_contract"):
        (trial_dir / "Attacker.sol").write_text(trial.parsed["attacker_contract"])
    return trial_dir
