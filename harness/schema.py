VULN_CLASSES = [
    "reentrancy",
    "access_control",
    "oracle_manipulation",
    "integer_precision",
    "signature_replay",
    "upgradeability",
    "donation_inflation",
    "unchecked_external_call",
    "mev_invariant",
    "business_logic",
    "none",
]

SINGLE_SHOT_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["vuln_class", "reasoning", "foundry_test"],
    "properties": {
        "vuln_class": {"type": "string", "enum": VULN_CLASSES},
        "reasoning": {"type": "string", "minLength": 1},
        "attacker_contract": {"type": ["string", "null"]},
        "foundry_test": {"type": "string", "minLength": 1},
    },
}

OUTCOMES = ["EXPLOIT", "PARTIAL", "MISS", "HALLUCINATION", "REFUSAL"]
