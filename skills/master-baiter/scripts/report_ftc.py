# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate FTC ReportFraud complaint report.

Reads evidence chain, session state, and intel database to produce
a structured FTC fraud report in Markdown format.
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
    grouped: dict[str, list[dict]] = {}
    for item in intel_db.get("items", []):
        if session_id in item.get("linked_sessions", []):
            t = item["type"]
            grouped.setdefault(t, []).append(item)
    return grouped


def determine_contact_method(channel: str) -> str:
    mapping = {
        "whatsapp": "Phone / Messaging App (WhatsApp)",
        "telegram": "Messaging App (Telegram)",
        "discord": "Online / Messaging App (Discord)",
        "email": "Email",
        "sms": "Phone / Text Message",
        "instagram": "Social Media (Instagram)",
        "facebook": "Social Media (Facebook)",
        "twitter": "Social Media (Twitter/X)",
    }
    return mapping.get(channel.lower(), f"Online ({channel})")


def determine_payment_method(intel: dict[str, list[dict]]) -> str:
    methods = []
    if intel.get("wallet"):
        methods.append("Cryptocurrency")
    if intel.get("bank_account"):
        methods.append("Bank Transfer / Wire")
    if intel.get("gift_card"):
        methods.append("Gift Card")
    if intel.get("cash_app") or intel.get("venmo") or intel.get("zelle"):
        methods.append("Payment App")
    return ", ".join(methods) if methods else "Not yet determined from evidence"


def build_narrative(entries: list[dict], state: dict) -> str:
    if not entries:
        return "No evidence entries available."

    scam_type = state.get("scam_type", "fraud")
    channel = state.get("channel", "unknown platform")

    inbound = [e for e in entries if e["direction"] == "inbound"]
    outbound = [e for e in entries if e["direction"] == "outbound"]

    lines = [
        f"A scammer contacted the bait persona via {channel}. "
        f"The interaction has been classified as: **{scam_type}**.",
        "",
        f"Over the course of {len(entries)} messages ({len(inbound)} from the scammer, "
        f"{len(outbound)} bait responses), the scammer engaged in fraudulent behavior.",
        "",
        "### Conversation Summary",
        "",
    ]
    for e in entries:
        direction = "SCAMMER" if e["direction"] == "inbound" else "BAIT PERSONA"
        lines.append(f"- [{e['timestamp']}] **{direction}**: {e['content']}")

    return "\n".join(lines)


def extract_amounts(entries: list[dict]) -> list[str]:
    """Look for dollar/crypto amounts mentioned in scammer messages."""
    import re
    amounts = []
    pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d+)?\s*(?:BTC|ETH|USDT|USD)')
    for e in entries:
        if e["direction"] == "inbound":
            found = pattern.findall(e["content"])
            amounts.extend(found)
    return list(set(amounts))


def generate_ftc_report(session_id: str) -> str:
    entries = load_chain(session_id)
    state = load_session_state(session_id)
    intel_db = load_intel()
    intel = get_intel_for_session(intel_db, session_id)

    channel = state.get("channel", "unknown")
    contact_method = determine_contact_method(channel)
    payment_method = determine_payment_method(intel)
    now = datetime.now(timezone.utc).isoformat()

    narrative = build_narrative(entries, state)
    amounts = extract_amounts(entries)

    emails = [i["value"] for i in intel.get("email", [])]
    phones = [i["value"] for i in intel.get("phone", [])]
    websites = [i["value"] for i in intel.get("website", [])] + [i["value"] for i in intel.get("url", [])]

    report = f"""# FTC ReportFraud Report

**Generated:** {now}
**Session ID:** {session_id}
**Submit at:** https://reportfraud.ftc.gov/

---

## What Happened

{narrative}

## How Were You Contacted?

- **Method:** {contact_method}
- **Platform/Channel:** {channel}
- **Scammer Identifier:** {state.get("sender_id", "unknown")}

## Company or Person Information

> Information collected about the scammer during the engagement:

- **Sender ID:** {state.get("sender_id", "unknown")}
- **Scam Type:** {state.get("scam_type", "unclassified")}

### Email Addresses
{chr(10).join(f"- `{e}`" for e in emails) if emails else "- None collected"}

### Phone Numbers
{chr(10).join(f"- `{p}`" for p in phones) if phones else "- None collected"}

### Websites
{chr(10).join(f"- `{w}`" for w in websites) if websites else "- None collected"}

## Amount Requested

{chr(10).join(f"- {a}" for a in amounts) if amounts else "- No specific amounts identified in evidence"}

## Payment Method Requested

{payment_method}

## Contact Information Provided by Scammer

| Type | Value | First Seen |
|------|-------|------------|
"""

    all_intel = []
    for items in intel.values():
        all_intel.extend(items)

    if all_intel:
        for item in all_intel:
            report += f"| {item['type']} | `{item['value']}` | {item.get('first_seen', 'N/A')} |\n"
    else:
        report += "| — | No contact info collected | — |\n"

    report += f"""
## Evidence Summary

- **Evidence chain:** `evidence/{session_id}/chain.jsonl`
- **Total entries:** {len(entries)}
- **First contact:** {entries[0]['timestamp'] if entries else 'N/A'}
- **Last contact:** {entries[-1]['timestamp'] if entries else 'N/A'}
- **Chain integrity:** Verify with `hash_verify.py --session {session_id}`

---

*This report was auto-generated by OpenClaw master-baiter from forensic
evidence collected during a controlled counter-scam engagement. No actual
financial loss occurred — all interactions were controlled bait operations.
Verify evidence integrity before submission.*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate FTC ReportFraud report")
    parser.add_argument("--session", required=True, help="Session ID")

    args = parser.parse_args()

    report = generate_ftc_report(args.session)

    report_dir = BASE_DIR / "reports" / args.session
    report_dir.mkdir(parents=True, exist_ok=True)
    output_file = report_dir / "ftc-report.md"
    output_file.write_text(report)

    print(json.dumps({
        "status": "ok",
        "report": str(output_file),
        "type": "ftc",
        "session_id": args.session,
    }))


if __name__ == "__main__":
    main()
