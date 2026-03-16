# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Forensic evidence logger with SHA-256 hash chain.

Appends each message as a JSONL entry with a running hash chain
for tamper-evident evidence storage.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"


def get_evidence_dir(session_id: str) -> Path:
    d = BASE_DIR / "evidence" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_session_dir(session_id: str) -> Path:
    d = BASE_DIR / "sessions" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def get_last_chain_hash(chain_file: Path) -> tuple[str, int]:
    """Return (last_chain_hash, sequence_number) from the chain file."""
    if not chain_file.exists() or chain_file.stat().st_size == 0:
        return "0" * 64, 0

    last_line = ""
    with open(chain_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                last_line = line

    if not last_line:
        return "0" * 64, 0

    entry = json.loads(last_line)
    return entry["chain_hash"], entry["seq"]


def log_evidence(
    session_id: str,
    channel: str,
    sender_id: str,
    direction: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    evidence_dir = get_evidence_dir(session_id)
    chain_file = evidence_dir / "chain.jsonl"

    previous_hash, last_seq = get_last_chain_hash(chain_file)
    seq = last_seq + 1
    timestamp = datetime.now(timezone.utc).isoformat()

    content_hash = compute_hash(content)
    chain_input = f"{previous_hash}:{timestamp}:{content_hash}"
    chain_hash = compute_hash(chain_input)

    entry = {
        "seq": seq,
        "timestamp": timestamp,
        "session_id": session_id,
        "channel": channel,
        "sender_id": sender_id,
        "direction": direction,
        "content": content,
        "content_hash": content_hash,
        "chain_hash": chain_hash,
        "previous_hash": previous_hash,
        "metadata": metadata or {},
    }

    with open(chain_file, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    return entry


def update_session_state(
    session_id: str,
    channel: str,
    sender_id: str,
    scam_type: str = "",
    severity: int = 0,
    persona: str = "",
    mode: str = "bait",
    delay_seconds: int = 0,
):
    session_dir = get_session_dir(session_id)
    state_file = session_dir / "state.json"

    if state_file.exists():
        state = json.loads(state_file.read_text())
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        state["message_count"] = state.get("message_count", 0) + 1
        if scam_type:
            state["scam_type"] = scam_type
        if severity is not None and severity != state.get("severity"):
            state["severity"] = severity
        if persona:
            state["persona"] = persona
        if delay_seconds is not None and delay_seconds > 0:
            state["total_delay_seconds"] = state.get("total_delay_seconds", 0) + delay_seconds
            state["last_delay_seconds"] = delay_seconds
    else:
        state = {
            "session_id": session_id,
            "channel": channel,
            "sender_id": sender_id,
            "scam_type": scam_type,
            "severity": severity,
            "persona": persona,
            "mode": mode,
            "status": "active",
            "message_count": 1,
            "total_delay_seconds": delay_seconds,
            "last_delay_seconds": delay_seconds,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    state_file.write_text(json.dumps(state, indent=2))
    return state


def extract_intel(session_id: str, intel_type: str, value: str, platform: str = ""):
    """Add an intel item to the session and global intel database."""
    analytics_dir = BASE_DIR / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    intel_file = analytics_dir / "intel-db.json"

    if intel_file.exists():
        db = json.loads(intel_file.read_text())
    else:
        db = {"items": []}

    now = datetime.now(timezone.utc).isoformat()

    # Check if this intel already exists
    existing = None
    for item in db["items"]:
        if item["type"] == intel_type and item["value"] == value:
            existing = item
            break

    if existing:
        existing["last_seen"] = now
        if session_id not in existing["linked_sessions"]:
            existing["linked_sessions"].append(session_id)
    else:
        db["items"].append({
            "type": intel_type,
            "value": value,
            "platform": platform,
            "first_seen": now,
            "last_seen": now,
            "linked_sessions": [session_id],
        })

    intel_file.write_text(json.dumps(db, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Log evidence for master-baiter sessions")
    parser.add_argument("--session", required=True, help="Session ID")
    parser.add_argument("--channel", required=True, help="Message channel (whatsapp, telegram, etc.)")
    parser.add_argument("--sender", required=True, help="Sender ID")
    parser.add_argument("--direction", required=True, choices=["inbound", "outbound"], help="Message direction")
    parser.add_argument("--content", required=True, help="Message content")
    parser.add_argument("--scam-type", default="", help="Scam classification")
    parser.add_argument("--severity", type=int, default=0, help="Severity 1-5")
    parser.add_argument("--persona", default="", help="Active persona name")
    parser.add_argument("--mode", default="bait", choices=["bait", "passive"], help="Operating mode")
    parser.add_argument("--intel-type", default="", help="Intel type to extract (phone, email, wallet, etc.)")
    parser.add_argument("--intel-value", default="", help="Intel value to extract")
    parser.add_argument("--intel-platform", default="", help="Platform for intel item")
    parser.add_argument("--delay-seconds", type=int, default=0, help="Response delay applied before sending (seconds)")
    parser.add_argument("--delay-reason", default="", help="Human-readable reason for the delay")

    args = parser.parse_args()

    # Build metadata for outbound messages with delay info
    metadata = {}
    if args.delay_seconds and args.direction == "outbound":
        metadata["delay_seconds"] = args.delay_seconds
        metadata["delay_reason"] = args.delay_reason

    # Log the evidence entry
    entry = log_evidence(
        session_id=args.session,
        channel=args.channel,
        sender_id=args.sender,
        direction=args.direction,
        content=args.content,
        metadata=metadata if metadata else None,
    )

    # Update session state
    update_session_state(
        session_id=args.session,
        channel=args.channel,
        sender_id=args.sender,
        scam_type=args.scam_type,
        severity=args.severity,
        persona=args.persona,
        mode=args.mode,
        delay_seconds=args.delay_seconds,
    )

    # Extract intel if provided
    if args.intel_type and args.intel_value:
        extract_intel(
            session_id=args.session,
            intel_type=args.intel_type,
            value=args.intel_value,
            platform=args.intel_platform,
        )

    print(json.dumps({"status": "ok", "seq": entry["seq"], "chain_hash": entry["chain_hash"]}))


if __name__ == "__main__":
    main()
