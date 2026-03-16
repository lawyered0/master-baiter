# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate FBI IC3 (Internet Crime Complaint Center) complaint report.

Reads evidence chain, session state, and intel database to produce
a structured IC3 complaint form in Markdown format.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"


def load_chain(session_id: str) -> list[dict]:
    chain_file = BASE_DIR / "evidence" / session_id / "chain.jsonl"
    if not chain_file.exists():
        return []
    entries = []
    with open(chain_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_session_state(session_id: str) -> dict:
    state_file = BASE_DIR / "sessions" / session_id / "state.json"
    if not state_file.exists():
        return {}
    return json.loads(state_file.read_text())


def load_intel() -> dict:
    intel_file = BASE_DIR / "analytics" / "intel-db.json"
    if not intel_file.exists():
        return {"items": []}
    return json.loads(intel_file.read_text())


def get_intel_for_session(intel_db: dict, session_id: str) -> dict[str, list[dict]]:
    """Group intel items linked to this session by type."""
    grouped: dict[str, list[dict]] = {}
    for item in intel_db.get("items", []):
        if session_id in item.get("linked_sessions", []):
            t = item["type"]
            grouped.setdefault(t, []).append(item)
    return grouped


def classify_complaint(state: dict) -> str:
    scam_type = state.get("scam_type", "").lower()
    mapping = {
        "romance": "Romance Scam",
        "investment": "Investment / Cryptocurrency Fraud",
        "crypto": "Investment / Cryptocurrency Fraud",
        "pig_butchering": "Investment / Cryptocurrency Fraud",
        "tech_support": "Tech Support Fraud",
        "phishing": "Phishing / Spoofing",
        "bec": "Business Email Compromise",
        "extortion": "Extortion",
        "advance_fee": "Advance Fee Fraud",
        "lottery": "Lottery / Sweepstakes Fraud",
        "employment": "Employment Fraud",
        "identity_theft": "Identity Theft",
    }
    for key, label in mapping.items():
        if key in scam_type:
            return label
    return "Internet Fraud"


def build_incident_narrative(entries: list[dict]) -> str:
    if not entries:
        return "No evidence entries available."
    lines = []
    for e in entries:
        direction = "SCAMMER" if e["direction"] == "inbound" else "BAIT PERSONA"
        lines.append(f"[{e['timestamp']}] {direction}: {e['content']}")
    return "\n".join(lines)


def generate_ic3_report(session_id: str) -> str:
    entries = load_chain(session_id)
    state = load_session_state(session_id)
    intel_db = load_intel()
    intel = get_intel_for_session(intel_db, session_id)

    complaint_type = classify_complaint(state)
    channel = state.get("channel", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    first_ts = entries[0]["timestamp"] if entries else "N/A"
    last_ts = entries[-1]["timestamp"] if entries else "N/A"

    # Extract intel fields
    emails = [i["value"] for i in intel.get("email", [])]
    phones = [i["value"] for i in intel.get("phone", [])]
    wallets = [i["value"] for i in intel.get("wallet", [])]
    websites = [i["value"] for i in intel.get("website", [])] + [i["value"] for i in intel.get("url", [])]

    narrative = build_incident_narrative(entries)

    report = f"""# IC3 Internet Crime Complaint Report

**Generated:** {now}
**Session ID:** {session_id}
**Evidence entries:** {len(entries)}
**Hash chain verified:** Verify with `hash_verify.py --session {session_id}`

---

## Complaint Type

{complaint_type}

## Victim Information

> Victim details are redacted in this automated report. The complainant
> (or authorized representative) should fill in victim particulars when
> submitting to ic3.gov.

- **Redacted for privacy** — complete before submission.

## Subject (Scammer) Information

- **Contact channel:** {channel}
- **Sender ID:** {state.get("sender_id", "unknown")}
- **Scam classification:** {state.get("scam_type", "unclassified")}
- **Severity rating:** {state.get("severity", "N/A")}/5

### Email Addresses
{chr(10).join(f"- `{e}`" for e in emails) if emails else "- None collected"}

### Phone Numbers
{chr(10).join(f"- `{p}`" for p in phones) if phones else "- None collected"}

### Websites / URLs
{chr(10).join(f"- `{w}`" for w in websites) if websites else "- None collected"}

### Digital Currency Addresses
{chr(10).join(f"- `{w}`" for w in wallets) if wallets else "- None collected"}

## Incident Description

**Date of first contact:** {first_ts}
**Date of last contact:** {last_ts}
**Method of contact:** {channel}

### Narrative

{narrative}

## Financial Transactions

> Review evidence chain for any financial transaction details.
> No payments were made by the bait persona (all interactions are
> controlled counter-scam engagements).

## Digital Evidence

- Evidence chain file: `evidence/{session_id}/chain.jsonl`
- Total entries: {len(entries)}
- Chain integrity can be independently verified via SHA-256 hash chain.

---

*This report was auto-generated by OpenClaw master-baiter from forensic
evidence collected during a controlled counter-scam engagement. All
interactions were initiated by the scammer. Verify evidence integrity
before submission.*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate FBI IC3 complaint report")
    parser.add_argument("--session", required=True, help="Session ID")

    args = parser.parse_args()

    report = generate_ic3_report(args.session)

    report_dir = BASE_DIR / "reports" / args.session
    report_dir.mkdir(parents=True, exist_ok=True)
    output_file = report_dir / "ic3-complaint.md"
    output_file.write_text(report)

    print(json.dumps({
        "status": "ok",
        "report": str(output_file),
        "type": "ic3",
        "session_id": args.session,
    }))


if __name__ == "__main__":
    main()
