# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Verify the integrity of an evidence hash chain.

Walks the chain.jsonl file and re-computes each hash to detect tampering.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def verify_chain(session_id: str) -> dict:
    chain_file = BASE_DIR / "evidence" / session_id / "chain.jsonl"

    if not chain_file.exists():
        return {"valid": False, "error": "Chain file not found", "chain_length": 0}

    entries = []
    with open(chain_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                return {
                    "valid": False,
                    "error": f"Invalid JSON at line {line_num}",
                    "chain_length": len(entries),
                    "first_break": line_num,
                }

    if not entries:
        return {"valid": True, "chain_length": 0, "first_break": None}

    expected_prev = "0" * 64

    for i, entry in enumerate(entries):
        # Verify sequence number
        if entry["seq"] != i + 1:
            return {
                "valid": False,
                "error": f"Sequence gap at entry {i + 1}: expected seq {i + 1}, got {entry['seq']}",
                "chain_length": len(entries),
                "first_break": i + 1,
            }

        # Verify previous hash linkage
        if entry["previous_hash"] != expected_prev:
            return {
                "valid": False,
                "error": f"Previous hash mismatch at seq {entry['seq']}",
                "chain_length": len(entries),
                "first_break": entry["seq"],
            }

        # Verify content hash
        expected_content_hash = compute_hash(entry["content"])
        if entry["content_hash"] != expected_content_hash:
            return {
                "valid": False,
                "error": f"Content hash mismatch at seq {entry['seq']}",
                "chain_length": len(entries),
                "first_break": entry["seq"],
            }

        # Verify chain hash
        chain_input = f"{entry['previous_hash']}:{entry['timestamp']}:{entry['content_hash']}"
        expected_chain_hash = compute_hash(chain_input)
        if entry["chain_hash"] != expected_chain_hash:
            return {
                "valid": False,
                "error": f"Chain hash mismatch at seq {entry['seq']}",
                "chain_length": len(entries),
                "first_break": entry["seq"],
            }

        expected_prev = entry["chain_hash"]

    return {
        "valid": True,
        "chain_length": len(entries),
        "first_break": None,
        "first_entry": entries[0]["timestamp"] if entries else None,
        "last_entry": entries[-1]["timestamp"] if entries else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify evidence chain integrity")
    parser.add_argument("--session", required=True, help="Session ID to verify")

    args = parser.parse_args()
    result = verify_chain(args.session)

    print(json.dumps(result, indent=2))
    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
