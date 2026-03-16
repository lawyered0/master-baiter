# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate local police department tip email draft.

Produces a professional email-format document with incident summary,
suspect information, digital evidence summary, relevant statutes, and
recommended next steps.
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


def get_relevant_statutes(scam_type: str) -> list[str]:
    """Return potentially relevant federal and state statutes."""
    base_statutes = [
        "18 U.S.C. 1343 — Wire Fraud",
        "18 U.S.C. 1030 — Computer Fraud and Abuse Act (CFAA)",
    ]

    scam_lower = scam_type.lower()

    if "identity" in scam_lower:
        base_statutes.append("18 U.S.C. 1028 — Identity Theft")
        base_statutes.append("18 U.S.C. 1028A — Aggravated Identity Theft")
    if "crypto" in scam_lower or "investment" in scam_lower or "pig_butchering" in scam_lower:
        base_statutes.append("18 U.S.C. 1956 — Money Laundering")
        base_statutes.append("15 U.S.C. 78j(b) — Securities Fraud (if applicable)")
    if "romance" in scam_lower:
        base_statutes.append("18 U.S.C. 1341 — Mail Fraud (if applicable)")
        base_statutes.append("18 U.S.C. 1956 — Money Laundering")
    if "extortion" in scam_lower or "sextortion" in scam_lower:
        base_statutes.append("18 U.S.C. 873 — Extortion by Officers or Employees")
        base_statutes.append("18 U.S.C. 1951 — Hobbs Act (Extortion)")
    if "bec" in scam_lower or "business" in scam_lower:
        base_statutes.append("18 U.S.C. 1341 — Mail Fraud")
        base_statutes.append("18 U.S.C. 1956 — Money Laundering")
    if "phishing" in scam_lower:
        base_statutes.append("18 U.S.C. 1028 — Fraud in Connection with Identification Documents")
    if "predator" in scam_lower or "enticement" in scam_lower or "grooming" in scam_lower:
        base_statutes.append("18 U.S.C. 2422 — Coercion and Enticement of Minor")
        base_statutes.append("18 U.S.C. 2252A — Child Exploitation")

    return base_statutes


def build_evidence_summary(entries: list[dict]) -> str:
    if not entries:
        return "No evidence entries collected."

    inbound = [e for e in entries if e["direction"] == "inbound"]
    outbound = [e for e in entries if e["direction"] == "outbound"]

    first_hash = entries[0]["chain_hash"]
    last_hash = entries[-1]["chain_hash"]

    return (
        f"- **Total messages:** {len(entries)}\n"
        f"- **Scammer messages:** {len(inbound)}\n"
        f"- **Bait responses:** {len(outbound)}\n"
        f"- **First entry hash:** `{first_hash[:32]}...`\n"
        f"- **Last entry hash:** `{last_hash[:32]}...`\n"
        f"- **Chain format:** SHA-256 linked JSONL (tamper-evident)\n"
        f"- **Integrity:** Independently verifiable via hash chain recomputation"
    )


def generate_local_pd_report(session_id: str) -> str:
    entries = load_chain(session_id)
    state = load_session_state(session_id)
    intel_db = load_intel()
    intel = get_intel_for_session(intel_db, session_id)

    channel = state.get("channel", "unknown")
    scam_type = state.get("scam_type", "internet fraud")
    severity = state.get("severity", 0)
    now = datetime.now(timezone.utc).isoformat()

    first_ts = entries[0]["timestamp"] if entries else "N/A"
    last_ts = entries[-1]["timestamp"] if entries else "N/A"

    emails = [i["value"] for i in intel.get("email", [])]
    phones = [i["value"] for i in intel.get("phone", [])]
    wallets = [i["value"] for i in intel.get("wallet", [])]
    websites = [i["value"] for i in intel.get("website", [])] + [i["value"] for i in intel.get("url", [])]
    usernames = [i["value"] for i in intel.get("username", [])]

    statutes = get_relevant_statutes(scam_type)
    evidence_summary = build_evidence_summary(entries)

    # Build identifier list
    identifiers = []
    if emails:
        for e in emails:
            identifiers.append(f"- Email: `{e}`")
    if phones:
        for p in phones:
            identifiers.append(f"- Phone: `{p}`")
    if wallets:
        for w in wallets:
            identifiers.append(f"- Crypto wallet: `{w}`")
    if websites:
        for w in websites:
            identifiers.append(f"- Website/URL: `{w}`")
    if usernames:
        for u in usernames:
            identifiers.append(f"- Username: `{u}`")
    identifiers.append(f"- Platform ID: `{state.get('sender_id', 'unknown')}`")

    identifier_text = "\n".join(identifiers) if identifiers else "- Platform ID only (see above)"

    report = f"""# Law Enforcement Tip — Internet Fraud Report

**Generated:** {now}
**Session ID:** {session_id}

---

**TO:** [Local Police Department — Cybercrime Unit / Detective Bureau]
**FROM:** [Reporting Party — Complete Before Sending]
**DATE:** {now[:10]}
**RE:** Internet Fraud Tip — {scam_type.replace("_", " ").title()} via {channel.title()}

---

Dear Detective / Cybercrime Unit,

I am writing to report suspected internet fraud that was detected and
documented through a controlled counter-scam monitoring operation. The
evidence described below has been collected with forensic integrity
(SHA-256 hash chain) and is available for review.

## Incident Summary

An individual operating on **{channel}** engaged in what has been
classified as **{scam_type.replace("_", " ")}** (severity: {severity}/5).
The activity was first detected on **{first_ts}** and the most recent
interaction occurred on **{last_ts}**. A total of **{len(entries)}**
messages were captured and preserved in a tamper-evident evidence chain.

## Suspect Identifying Information

{identifier_text}

## Digital Evidence Summary

{evidence_summary}

> The complete evidence chain is stored in a SHA-256 hash-linked JSONL
> file. Each entry contains the message content, timestamp, sender ID,
> and a cryptographic hash linking it to the previous entry. This chain
> can be independently verified to confirm no tampering has occurred.
> Hash verification reference: run `hash_verify.py --session {session_id}`

## Potentially Relevant Statutes

{chr(10).join(f"- {s}" for s in statutes)}

> Note: Statute applicability depends on jurisdiction and specific facts.
> This list is provided for reference only.

## Recommended Next Steps

1. **Preserve evidence** — Request the full evidence chain file for
   independent verification and case file inclusion.
2. **Platform subpoena** — Consider issuing a preservation request and/or
   subpoena to {channel.title()} for account records associated with
   the suspect identifier(s) listed above.
3. **Financial tracing** — If cryptocurrency wallet addresses are
   identified, consider blockchain analysis to trace fund flows.
4. **Cross-reference** — Check suspect identifiers against existing
   cases and FBI IC3 complaints.
5. **Coordinate** — For cases involving interstate or international
   elements, consider coordination with FBI or Secret Service.

## Attachments Available Upon Request

- Full evidence chain (`chain.jsonl`) with hash verification
- Session state and metadata
- Intel database entries for linked identifiers

Please do not hesitate to reach out for additional information or to
obtain the full evidence package.

Respectfully,

[Reporting Party Name]
[Contact Information]

---

*This report was auto-generated by OpenClaw master-baiter from forensic
evidence collected during a controlled counter-scam engagement. Evidence
integrity is maintained via SHA-256 hash chain and should be independently
verified.*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate local PD tip email draft")
    parser.add_argument("--session", required=True, help="Session ID")

    args = parser.parse_args()

    report = generate_local_pd_report(args.session)

    report_dir = BASE_DIR / "reports" / args.session
    report_dir.mkdir(parents=True, exist_ok=True)
    output_file = report_dir / "local-pd-tip.md"
    output_file.write_text(report)

    print(json.dumps({
        "status": "ok",
        "report": str(output_file),
        "type": "local_pd",
        "session_id": args.session,
    }))


if __name__ == "__main__":
    main()
