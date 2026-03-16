# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate NCMEC CyberTipline report.

ONLY generates reports for predator detection cases. Refuses to produce
output if the session mode is not 'passive' or the scam_type does not
indicate predatory behavior.

All content descriptions are text-only — no actual harmful content is
included in the report.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"

PREDATORY_KEYWORDS = [
    "predator",
    "enticement",
    "csam",
    "sextortion",
    "minor",
    "child",
    "grooming",
    "exploitation",
    "predatory",
    "underage",
]


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


def is_predator_case(state: dict) -> bool:
    """Determine if this session qualifies for NCMEC reporting."""
    mode = state.get("mode", "")
    scam_type = state.get("scam_type", "").lower()

    if mode != "passive":
        return False

    for keyword in PREDATORY_KEYWORDS:
        if keyword in scam_type:
            return True

    return False


def classify_incident_type(state: dict) -> str:
    scam_type = state.get("scam_type", "").lower()
    if "enticement" in scam_type:
        return "Online Enticement of Children for Sexual Acts"
    if "sextortion" in scam_type:
        return "Child Sexual Molestation / Sextortion"
    if "grooming" in scam_type:
        return "Online Enticement — Grooming"
    if "misleading" in scam_type or "domain" in scam_type:
        return "Misleading Domain Name"
    if "exploitation" in scam_type:
        return "Child Sexual Exploitation"
    return "Online Enticement of Children for Sexual Acts"


def build_incident_timeline(entries: list[dict]) -> str:
    """Build a timeline of events with content descriptions only."""
    if not entries:
        return "No evidence entries available."

    lines = []
    for e in entries:
        direction = "REPORTED PERSON" if e["direction"] == "inbound" else "DECOY"
        # Provide a description rather than raw content for safety
        content_len = len(e["content"])
        lines.append(
            f"| {e['seq']} | {e['timestamp']} | {direction} | "
            f"Text message ({content_len} chars) | `{e['content_hash'][:16]}...` |"
        )
    return "\n".join(lines)


def generate_ncmec_report(session_id: str) -> tuple[str | None, str | None]:
    """Returns (report_text, error_message). One will be None."""
    state = load_session_state(session_id)

    if not state:
        return None, "Session state not found"

    if not is_predator_case(state):
        mode = state.get("mode", "unknown")
        scam_type = state.get("scam_type", "unknown")
        return None, (
            f"NCMEC report refused: session mode is '{mode}' and scam_type is '{scam_type}'. "
            f"NCMEC CyberTipline reports are ONLY generated for predator detection cases "
            f"(mode must be 'passive' and scam_type must indicate predatory behavior)."
        )

    entries = load_chain(session_id)
    intel_db = load_intel()
    intel = get_intel_for_session(intel_db, session_id)

    incident_type = classify_incident_type(state)
    channel = state.get("channel", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    first_ts = entries[0]["timestamp"] if entries else "N/A"
    last_ts = entries[-1]["timestamp"] if entries else "N/A"

    emails = [i["value"] for i in intel.get("email", [])]
    phones = [i["value"] for i in intel.get("phone", [])]
    usernames = [i["value"] for i in intel.get("username", [])]
    ips = [i["value"] for i in intel.get("ip", [])]

    timeline = build_incident_timeline(entries)

    report = f"""# NCMEC CyberTipline Report

**Generated:** {now}
**Session ID:** {session_id}
**Submit at:** https://report.cybertipline.org/

> **IMPORTANT:** This report contains descriptions of potentially illegal
> predatory behavior. NO actual harmful content (images, video, or explicit
> text) is included — only text descriptions and metadata. Review carefully
> before submission.

---

## Incident Type

**{incident_type}**

## Electronic Service Provider (ESP) / Platform Information

- **Platform/Channel:** {channel}
- **Reporting entity:** OpenClaw counter-predator detection system
- **Detection method:** Passive monitoring with decoy engagement

## Reported Person Information

- **Platform identifier:** {state.get("sender_id", "unknown")}
- **Channel:** {channel}

### Known Email Addresses
{chr(10).join(f"- `{e}`" for e in emails) if emails else "- None collected"}

### Known Phone Numbers
{chr(10).join(f"- `{p}`" for p in phones) if phones else "- None collected"}

### Known Usernames / Screen Names
{chr(10).join(f"- `{u}`" for u in usernames) if usernames else "- None collected"}

### Known IP Addresses
{chr(10).join(f"- `{ip}`" for ip in ips) if ips else "- None collected"}

## Incident Details

- **First contact:** {first_ts}
- **Last contact:** {last_ts}
- **Total interactions:** {len(entries)}
- **Session mode:** {state.get("mode", "unknown")}
- **Severity rating:** {state.get("severity", "N/A")}/5

### Incident Timeline

> Content below is described by type and metadata only. Actual message
> content is stored in the verified evidence chain and can be provided
> to law enforcement upon request.

| Seq | Timestamp | Source | Content Description | Content Hash |
|-----|-----------|--------|---------------------|--------------|
{timeline}

## Content Descriptions

> **No actual harmful content is included in this report.**
>
> The evidence chain contains {len(entries)} text-based messages exchanged
> on {channel}. Messages from the reported person were captured during
> passive monitoring. Each message is individually hashed (SHA-256) and
> linked in a tamper-evident chain for forensic integrity.
>
> Full message content is available in the verified evidence chain file
> and should be provided to law enforcement or NCMEC directly upon request.

## Evidence Integrity

- **Evidence chain:** `evidence/{session_id}/chain.jsonl`
- **Verification:** Run `hash_verify.py --session {session_id}`
- **Chain type:** SHA-256 hash chain with sequential integrity checks

---

*This report was auto-generated by OpenClaw master-baiter operating in
passive detection mode. The system detected potential predatory behavior
and collected evidence using a tamper-evident hash chain. All evidence
should be verified for integrity before submission to NCMEC or law
enforcement.*
"""
    return report, None


def main():
    parser = argparse.ArgumentParser(description="Generate NCMEC CyberTipline report")
    parser.add_argument("--session", required=True, help="Session ID")

    args = parser.parse_args()

    report, error = generate_ncmec_report(args.session)

    if error:
        print(json.dumps({
            "status": "refused",
            "error": error,
            "type": "ncmec",
            "session_id": args.session,
        }))
        sys.exit(1)

    report_dir = BASE_DIR / "reports" / args.session
    report_dir.mkdir(parents=True, exist_ok=True)
    output_file = report_dir / "ncmec-report.md"
    output_file.write_text(report)

    print(json.dumps({
        "status": "ok",
        "report": str(output_file),
        "type": "ncmec",
        "session_id": args.session,
    }))


if __name__ == "__main__":
    main()
