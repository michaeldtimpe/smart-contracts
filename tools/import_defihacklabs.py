from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path


REPO_URL = "https://github.com/SunWeb3Sec/DeFiHackLabs.git"
README_RAW = "https://raw.githubusercontent.com/SunWeb3Sec/DeFiHackLabs/main/README.md"

VULN_CLASS_KEYWORDS = [
    ("read-only-reentrancy", "reentrancy"),
    ("reentrancy", "reentrancy"),
    ("price-manipulation", "oracle_manipulation"),
    ("price manipulation", "oracle_manipulation"),
    ("oracle-manipulation", "oracle_manipulation"),
    ("flashloan", "oracle_manipulation"),
    ("flash-loan", "oracle_manipulation"),
    ("flash loan", "oracle_manipulation"),
    ("inflation-attack", "donation_inflation"),
    ("inflation", "donation_inflation"),
    ("donation", "donation_inflation"),
    ("first-depositor", "donation_inflation"),
    ("access-control", "access_control"),
    ("access control", "access_control"),
    ("missing-access-control", "access_control"),
    ("unprotected", "access_control"),
    ("ownership", "access_control"),
    ("delegatecall", "unchecked_external_call"),
    ("unchecked", "unchecked_external_call"),
    ("integer-overflow", "integer_precision"),
    ("integer-underflow", "integer_precision"),
    ("precision-loss", "integer_precision"),
    ("precision", "integer_precision"),
    ("rounding", "integer_precision"),
    ("storage-collision", "upgradeability"),
    ("upgradeable", "upgradeability"),
    ("uninitialized", "upgradeability"),
    ("proxy", "upgradeability"),
    ("signature-replay", "signature_replay"),
    ("signature", "signature_replay"),
    ("ecrecover", "signature_replay"),
    ("sandwich", "mev_invariant"),
    ("mev", "mev_invariant"),
    ("business-logic", "business_logic"),
    ("logic-flaw", "business_logic"),
    ("logic-error", "business_logic"),
    ("incorrect", "business_logic"),
    ("lack-of-validation", "business_logic"),
    ("input-validation", "business_logic"),
]


def fetch_readme() -> str:
    req = urllib.request.Request(
        README_RAW,
        headers={"User-Agent": "smart-contract-llm-benchmark/0.1"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_readme_classifications(readme: str) -> list[dict]:
    entries = []
    pattern = re.compile(r"\[(\d{8})\s+([^\]]+)\]\(past/\d+/README\.md#(\d{8})-([^)]+)\)")
    for m in pattern.finditer(readme):
        date = m.group(1)
        title = m.group(2).strip()
        anchor = m.group(4).lower()
        project_slug = anchor.split("---")[0]
        vuln_class = "business_logic"
        for keyword, klass in VULN_CLASS_KEYWORDS:
            if keyword in anchor:
                vuln_class = klass
                break
        entries.append({
            "date": date,
            "title": title,
            "project_slug": project_slug,
            "anchor": anchor,
            "vuln_class": vuln_class,
        })
    return entries


def clone_repo(workdir: Path) -> Path:
    repo_dir = workdir / "DeFiHackLabs"
    if repo_dir.exists():
        return repo_dir
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(repo_dir)],
        check=True,
    )
    return repo_dir


def walk_test_files(repo_dir: Path) -> list[dict]:
    test_root = repo_dir / "src" / "test"
    out = []
    if not test_root.exists():
        return out
    for sol in test_root.rglob("*_exp.sol"):
        rel = sol.relative_to(repo_dir)
        m = re.search(r"src/test/(\d{4})-(\d{2})/", str(rel))
        if not m:
            continue
        year, month = m.group(1), m.group(2)
        if int(year) >= 2024:
            continue
        project = sol.name.replace("_exp.sol", "")
        out.append({
            "year": year,
            "month": month,
            "project": project,
            "rel_path": str(rel),
            "abs_path": sol,
        })
    return out


def match_test_to_classification(test_entry: dict, classifications: list[dict]) -> dict | None:
    yearmonth = test_entry["year"] + test_entry["month"]
    project_lower = test_entry["project"].lower()
    in_month = [c for c in classifications if c["date"][:6] == yearmonth]
    for c in in_month:
        if c["project_slug"] == project_lower:
            return c
    for c in in_month:
        if project_lower in c["project_slug"] or c["project_slug"] in project_lower:
            return c
    for c in in_month:
        title_slug = re.sub(r"[^a-z0-9]+", "", c["title"].lower())
        if re.sub(r"[^a-z0-9]+", "", project_lower) == title_slug:
            return c
    if in_month:
        return in_month[0]
    return None


def stratified_sample(entries: list[dict], target_per_class: dict[str, int]) -> list[dict]:
    by_class: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_class[e["vuln_class"]].append(e)
    selected = []
    for vuln_class, n in target_per_class.items():
        bucket = by_class.get(vuln_class, [])
        bucket.sort(key=lambda x: x.get("date", "0"), reverse=True)
        selected.extend(bucket[:n])
    return selected


def import_entry(entry: dict, dataset_root: Path, canary: str, repo_dir: Path) -> dict:
    entry_id = f"{entry.get('date', entry['year']+entry['month']+'00')}_{re.sub(r'[^a-zA-Z0-9]+', '_', entry['project']).strip('_').lower()}"[:64]
    entry_dir = dataset_root / "A_classics" / "orig" / entry_id
    entry_dir.mkdir(parents=True, exist_ok=True)

    test_src_text = entry["abs_path"].read_text()
    canary_comment = f"// CANARY: {canary}\n"
    if canary_comment.strip() not in test_src_text:
        test_src_text = canary_comment + test_src_text
    test_src_text = test_src_text.replace('"../interface.sol"', '"./interface.sol"')
    test_src_text = test_src_text.replace("'../interface.sol'", "'./interface.sol'")
    (entry_dir / "reference_exploit.t.sol").write_text(test_src_text)

    fork_block, fork_chain_alias = _extract_fork(test_src_text)

    shared_interface = repo_dir / "src" / "test" / "interface.sol"
    if shared_interface.exists():
        (entry_dir / "interface.sol").write_text(shared_interface.read_text())

    placeholder = (
        canary_comment
        + f"// SOURCE: https://github.com/SunWeb3Sec/DeFiHackLabs/blob/main/{entry['rel_path']}\n"
        + "// NOTE: The on-chain target contract is referenced by deployed address inside the test.\n"
        + "// For mutation variants, the model receives this contract.sol stub plus the addresses;\n"
        + "// the contract bytecode is fetched from a forked archive node at the pinned block.\n"
    )
    (entry_dir / "contract.sol").write_text(placeholder)

    chain_alias_map = {
        "mainnet": "ethereum", "eth": "ethereum",
        "polygon": "polygon", "matic": "polygon",
        "arbitrum": "arbitrum", "optimism": "optimism",
        "bsc": "bsc", "bnb": "bsc", "binance": "bsc",
        "base": "base",
    }
    chain = chain_alias_map.get((fork_chain_alias or "").lower(), "ethereum")

    metadata = {
        "entry_id": entry_id,
        "bucket": "A_classics",
        "variant": "orig",
        "vuln_class": entry["vuln_class"],
        "severity": "high",
        "chain": chain,
        "language": "solidity",
        "fork_block": fork_block,
        "source_url": f"https://github.com/SunWeb3Sec/DeFiHackLabs/blob/main/{entry['rel_path']}",
        "incident_date": (
            f"{entry['date'][:4]}-{entry['date'][4:6]}-{entry['date'][6:8]}"
            if entry.get("date") else f"{entry['year']}-{entry['month']}-01"
        ),
        "training_cutoff_label": {},
        "patch_status": "pre_patch",
        "design_tradeoff_notes": "",
        "mutation_seed": None,
        "mutation_methods": [],
        "canary": canary,
        "_import": {
            "project": entry["project"],
            "defihacklabs_test_path": entry["rel_path"],
        },
    }
    (entry_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata


def _extract_fork(test_src: str) -> tuple[int | None, str | None]:
    m = re.search(r'createSelectFork\(\s*"([^"]+)"\s*,\s*([0-9_]+)\s*\)', test_src)
    if m:
        return int(m.group(2).replace("_", "")), m.group(1)
    m = re.search(r'createFork\(\s*"([^"]+)"\s*,\s*([0-9_]+)\s*\)', test_src)
    if m:
        return int(m.group(2).replace("_", "")), m.group(1)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, default=Path("dataset"))
    ap.add_argument("--canary", type=Path, default=Path("CANARY.txt"))
    ap.add_argument("--workdir", type=Path, default=Path(".cache/import"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    canary = args.canary.read_text().strip()

    print("[1/5] Fetching DeFiHackLabs README index...", flush=True)
    readme = fetch_readme()
    classifications = parse_readme_classifications(readme)
    print(f"  {len(classifications)} dated entries classified from README anchors.")

    print(f"[2/5] Cloning DeFiHackLabs to {args.workdir}...", flush=True)
    repo_dir = clone_repo(args.workdir)

    print("[3/5] Walking src/test/ for *_exp.sol files (pre-2024 only)...", flush=True)
    test_files = walk_test_files(repo_dir)
    print(f"  {len(test_files)} pre-2024 test files found.")

    print("[4/5] Joining test files with vuln-class classifications...", flush=True)
    enriched = []
    for tf in test_files:
        match = match_test_to_classification(tf, classifications)
        if match:
            tf["date"] = match["date"]
            tf["vuln_class"] = match["vuln_class"]
            tf["title"] = match["title"]
        else:
            tf["date"] = tf["year"] + tf["month"] + "01"
            tf["vuln_class"] = "business_logic"
            tf["title"] = tf["project"]
        enriched.append(tf)

    target_per_class = {
        "reentrancy": 3,
        "access_control": 3,
        "oracle_manipulation": 4,
        "integer_precision": 2,
        "signature_replay": 1,
        "upgradeability": 2,
        "donation_inflation": 1,
        "unchecked_external_call": 1,
        "business_logic": 3,
    }
    selected = stratified_sample(enriched, target_per_class)
    counts = defaultdict(int)
    for e in selected:
        counts[e["vuln_class"]] += 1
    print(f"  Stratified sample: {len(selected)} entries:")
    for k in sorted(counts):
        print(f"    {k}: {counts[k]}")

    if args.dry_run:
        print("\nDry run — sample selections:")
        for e in selected[:10]:
            print(f"  {e['date']} {e['project']:30} [{e['vuln_class']}]  -> {e['rel_path']}")
        return 0

    print(f"[5/5] Importing entries to {args.dataset}/A_classics/orig/...", flush=True)
    imported = []
    for e in selected:
        result = import_entry(e, args.dataset, canary, repo_dir)
        imported.append(result)
        print(f"  [OK] {result['entry_id']}")
    print(f"\nImported {len(imported)} entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
