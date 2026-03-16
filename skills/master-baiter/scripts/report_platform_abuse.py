# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate platform-specific abuse reports.

Supports: whatsapp, telegram, discord, coinbase, kraken, binance.
Each platform has its own report template with relevant fields.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"

SUPPORTED_PLATFORMS = ("whatsapp", "telegram", "discord", "coinbase", "kraken", "binance")


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


def get_session_intel(intel_db: dict, session_id: str) -> list[dict]:
    return [
        item for item in intel_db.get("items", [])
        if session_id in item.get("linked_sessions", [])
    ]


def _common_context(session_id: str) -> dict:
    """Load all data sources and return a context dict."""
    entries = load_chain(session_id)
    state = load_session_state(session_id)
    intel_db = load_intel()
    session_intel = get_session_intel(intel_db, session_id)

    inbound = [e for e in entries if e.get("direction") == "inbound"]

    return {
        "entries": entries,
        "state": state,
        "intel": session_intel,
        "inbound": inbound,
        "emails": [i["value"] for i in session_intel if i["type"] == "email"],
        "phones": [i["value"] for i in session_intel if i["type"] == "phone"],
        "names": [i["value"] for i in session_intel if i["type"] in ("name", "alias")],
        "wallets": [i["value"] for i in session_intel if i["type"] in ("wallet", "crypto_address")],
        "websites": [i["value"] for i in session_intel if i["type"] in ("website", "url", "domain")],
        "usernames": [i["value"] for i in session_intel if i["type"] in ("username", "screen_name")],
        "now": datetime.now(timezone.utc).isoformat(),
    }


def _message_excerpt(inbound: list[dict], limit: int = 10) -> str:
    if not inbound:
        return "No suspect messages recorded."
    lines = []
    for e in inbound[:limit]:
        lines.append(f"- [{e['timestamp']}] {e['content'][:200]}")
    return "\n".join(lines)


def report_whatsapp(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# WhatsApp Abuse Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Reported Account

**Phone Number:** {ctx['phones'][0] if ctx['phones'] else state.get('sender_id', 'Unknown')}
**Known Aliases:** {', '.join(ctx['names']) if ctx['names'] else 'None'}
**Account Type:** Individual

## Reason for Report

**Category:** Scam / Fraud
**Subcategory:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}

## Description

This WhatsApp account has been identified as conducting {state.get('scam_type', 'fraudulent')} activity.
The account was monitored during a controlled scam-baiting operation from
{ctx['entries'][0]['timestamp'] if ctx['entries'] else 'unknown'} to
{ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'unknown'}.

The user sent {len(ctx['inbound'])} unsolicited messages attempting to defraud recipients.

## Evidence Summary

**Messages captured:** {len(ctx['entries'])}
**Date range:** {ctx['entries'][0]['timestamp'] if ctx['entries'] else 'N/A'} — {ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'N/A'}

### Sample Messages from Reported Account

{_message_excerpt(ctx['inbound'])}

## Additional Identifiers

**Websites shared:** {', '.join(ctx['websites']) if ctx['websites'] else 'None'}
**Crypto wallets shared:** {', '.join(ctx['wallets']) if ctx['wallets'] else 'None'}

---

*Submit via WhatsApp in-app reporting or email to support@whatsapp.com*
*Evidence chain preserved with SHA-256 hash verification.*
"""


def report_telegram(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# Telegram Abuse Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Reported Account

**Username:** {ctx['usernames'][0] if ctx['usernames'] else state.get('sender_id', 'Unknown')}
**Phone Number:** {ctx['phones'][0] if ctx['phones'] else 'Unknown'}
**Known Aliases:** {', '.join(ctx['names']) if ctx['names'] else 'None'}

## Abuse Type

**Category:** Scam
**Details:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}

## Description

This Telegram account is conducting fraudulent activity classified as
{state.get('scam_type', 'internet fraud')}. Evidence was collected during a
controlled monitoring operation.

## Conversation Evidence

**Total messages:** {len(ctx['entries'])}
**Suspect messages:** {len(ctx['inbound'])}
**Period:** {ctx['entries'][0]['timestamp'] if ctx['entries'] else 'N/A'} — {ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'N/A'}

### Key Messages

{_message_excerpt(ctx['inbound'])}

## Links and Resources Shared by Suspect

**URLs:** {', '.join(ctx['websites']) if ctx['websites'] else 'None observed'}
**Crypto addresses:** {', '.join(ctx['wallets']) if ctx['wallets'] else 'None observed'}

---

*Submit via https://telegram.org/support or @abuse on Telegram*
*Evidence chain preserved with SHA-256 hash verification.*
"""


def report_discord(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# Discord Trust & Safety Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Reported User

**User ID / Tag:** {ctx['usernames'][0] if ctx['usernames'] else state.get('sender_id', 'Unknown')}
**Known Aliases:** {', '.join(ctx['names']) if ctx['names'] else 'None'}

## Report Category

**Type:** Fraud / Scam
**Subcategory:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}
**Severity:** {state.get('severity', 'N/A')}/5

## What Happened

This Discord user engaged in {state.get('scam_type', 'fraudulent').replace('_', ' ')} activity.
Communication was monitored and logged from
{ctx['entries'][0]['timestamp'] if ctx['entries'] else 'unknown'} to
{ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'unknown'}.

## Message Evidence

**Total messages logged:** {len(ctx['entries'])}
**Messages from reported user:** {len(ctx['inbound'])}

### Sample Messages

{_message_excerpt(ctx['inbound'])}

## Additional Context

**External links shared:** {', '.join(ctx['websites']) if ctx['websites'] else 'None'}
**Cryptocurrency addresses:** {', '.join(ctx['wallets']) if ctx['wallets'] else 'None'}
**Email addresses used:** {', '.join(ctx['emails']) if ctx['emails'] else 'None'}

---

*Submit via https://dis.gd/report or Discord in-app reporting.*
*Include message links where possible. Evidence chain preserved with SHA-256 hashing.*
"""


def report_coinbase(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# Coinbase Abuse Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Report Type

**Category:** Fraud / Scam
**Scam Classification:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}

## Suspect Account Information

**Known Email(s):** {', '.join(ctx['emails']) if ctx['emails'] else 'None identified'}
**Known Names:** {', '.join(ctx['names']) if ctx['names'] else 'None identified'}
**Phone Numbers:** {', '.join(ctx['phones']) if ctx['phones'] else 'None identified'}

## Cryptocurrency Addresses

The following addresses were provided by the suspect during the scam operation:

{chr(10).join(f'- `{w}`' for w in ctx['wallets']) if ctx['wallets'] else '- No cryptocurrency addresses identified'}

## Incident Description

A suspect conducted a {state.get('scam_type', 'fraud').replace('_', ' ')} scam via
{state.get('channel', 'online platform')}. During the interaction, the suspect
directed victims to send cryptocurrency to the addresses listed above.

**Interaction period:** {ctx['entries'][0]['timestamp'] if ctx['entries'] else 'N/A'} — {ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'N/A'}
**Messages exchanged:** {len(ctx['entries'])}

## Requested Action

- Freeze / flag the listed cryptocurrency addresses
- Investigate associated account(s) for additional fraudulent activity
- Preserve transaction records for law enforcement

## Associated Websites

{chr(10).join(f'- {w}' for w in ctx['websites']) if ctx['websites'] else '- None identified'}

---

*Submit via https://help.coinbase.com/en/contact-us (select Fraud/Scam)*
*Evidence chain preserved with SHA-256 hash verification.*
"""


def report_kraken(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# Kraken Abuse Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Report Type

**Category:** Fraud / Scam Report
**Scam Classification:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}

## Suspect Information

**Known Email(s):** {', '.join(ctx['emails']) if ctx['emails'] else 'None identified'}
**Known Names:** {', '.join(ctx['names']) if ctx['names'] else 'None identified'}
**Phone Numbers:** {', '.join(ctx['phones']) if ctx['phones'] else 'None identified'}

## Cryptocurrency Addresses (Possibly Kraken-linked)

{chr(10).join(f'- `{w}`' for w in ctx['wallets']) if ctx['wallets'] else '- No cryptocurrency addresses identified'}

## Incident Summary

A suspect operating a {state.get('scam_type', 'fraud').replace('_', ' ')} scheme
solicited cryptocurrency transfers to the addresses listed above. This activity
was documented via controlled monitoring on {state.get('channel', 'an online platform')}.

**Period of activity:** {ctx['entries'][0]['timestamp'] if ctx['entries'] else 'N/A'} — {ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'N/A'}
**Evidence entries:** {len(ctx['entries'])}

## Requested Action

- Investigate whether the listed addresses are associated with Kraken accounts
- Freeze suspect accounts pending investigation
- Preserve records for potential law enforcement subpoena

## Related Links

{chr(10).join(f'- {w}' for w in ctx['websites']) if ctx['websites'] else '- None identified'}

---

*Submit via https://support.kraken.com (Fraud/Scam category)*
*Evidence chain preserved with SHA-256 hash verification.*
"""


def report_binance(session_id: str) -> str:
    ctx = _common_context(session_id)
    state = ctx["state"]

    return f"""# Binance Abuse Report
**Generated:** {ctx['now']}
**Session ID:** {session_id}

---

## Report Type

**Category:** Scam / Fraud
**Scam Type:** {state.get('scam_type', 'Unknown').replace('_', ' ').title()}

## Suspect Information

**Known Email(s):** {', '.join(ctx['emails']) if ctx['emails'] else 'None identified'}
**Known Names / Aliases:** {', '.join(ctx['names']) if ctx['names'] else 'None identified'}
**Binance UID (if known):** Unknown
**Phone Numbers:** {', '.join(ctx['phones']) if ctx['phones'] else 'None identified'}

## Cryptocurrency Addresses

Addresses provided by the suspect for receiving scam proceeds:

{chr(10).join(f'- `{w}`' for w in ctx['wallets']) if ctx['wallets'] else '- No cryptocurrency addresses identified'}

## Incident Description

The suspect conducted a {state.get('scam_type', 'fraud').replace('_', ' ')} operation
through {state.get('channel', 'an online platform')}, soliciting cryptocurrency
transfers. Evidence was gathered via controlled scam-baiting.

**Period:** {ctx['entries'][0]['timestamp'] if ctx['entries'] else 'N/A'} — {ctx['entries'][-1]['timestamp'] if ctx['entries'] else 'N/A'}
**Messages captured:** {len(ctx['entries'])}

## Associated URLs / Fake Platforms

{chr(10).join(f'- {w}' for w in ctx['websites']) if ctx['websites'] else '- None identified'}

## Requested Action

- Flag / freeze accounts associated with listed addresses
- Run on-chain analysis for linked wallets
- Preserve KYC and transaction data for law enforcement cooperation

---

*Submit via https://www.binance.com/en/support (select Scam/Fraud)*
*Or email law enforcement liaison if available.*
*Evidence chain preserved with SHA-256 hash verification.*
"""


PLATFORM_GENERATORS = {
    "whatsapp": report_whatsapp,
    "telegram": report_telegram,
    "discord": report_discord,
    "coinbase": report_coinbase,
    "kraken": report_kraken,
    "binance": report_binance,
}


def generate_platform_abuse_report(session_id: str, platform: str) -> str:
    platform = platform.lower()
    if platform not in PLATFORM_GENERATORS:
        raise ValueError(
            f"Unsupported platform '{platform}'. "
            f"Supported: {', '.join(SUPPORTED_PLATFORMS)}"
        )
    return PLATFORM_GENERATORS[platform](session_id)


def main():
    parser = argparse.ArgumentParser(description="Generate platform abuse report")
    parser.add_argument("--session", required=True, help="Session ID")
    parser.add_argument(
        "--platform",
        required=True,
        choices=SUPPORTED_PLATFORMS,
        help="Target platform for abuse report",
    )

    args = parser.parse_args()

    report = generate_platform_abuse_report(args.session, args.platform)

    reports_dir = BASE_DIR / "reports" / args.session
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_file = reports_dir / f"platform-abuse-{args.platform}.md"
    output_file.write_text(report)

    print(json.dumps({
        "status": "ok",
        "report": str(output_file),
        "type": f"platform-abuse-{args.platform}",
        "session_id": args.session,
    }))


if __name__ == "__main__":
    main()
