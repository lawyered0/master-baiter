"""File watcher that bridges OpenClaw workspace JSON files → SQLite.

Watches the master-baiter workspace directory for changes and syncs
session state, evidence chains, and intel data into the dashboard database.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session as DBSession
from watchfiles import awatch, Change

from models import Session, EvidenceEntry, IntelItem, Report
from db import SessionLocal

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"


def sync_session(db: DBSession, session_id: str):
    """Sync a session's state.json into the database."""
    state_file = BASE_DIR / "sessions" / session_id / "state.json"
    if not state_file.exists():
        return

    state = json.loads(state_file.read_text())

    existing = db.query(Session).filter(Session.id == session_id).first()
    if existing:
        existing.channel = state.get("channel", existing.channel)
        existing.sender_id = state.get("sender_id", existing.sender_id)
        existing.scam_type = state.get("scam_type", existing.scam_type)
        existing.severity = state.get("severity", existing.severity)
        existing.persona = state.get("persona", existing.persona)
        existing.status = state.get("status", existing.status)
        existing.mode = state.get("mode", existing.mode)
        existing.message_count = state.get("message_count", existing.message_count)
        if state.get("updated_at"):
            existing.updated_at = datetime.fromisoformat(state["updated_at"])
        # Calculate time wasted
        if state.get("created_at") and state.get("updated_at"):
            created = datetime.fromisoformat(state["created_at"])
            updated = datetime.fromisoformat(state["updated_at"])
            existing.time_wasted_seconds = int((updated - created).total_seconds())
    else:
        created_at = datetime.fromisoformat(state["created_at"]) if state.get("created_at") else datetime.now(timezone.utc)
        updated_at = datetime.fromisoformat(state["updated_at"]) if state.get("updated_at") else created_at
        time_wasted = int((updated_at - created_at).total_seconds())

        db.add(Session(
            id=session_id,
            channel=state.get("channel", ""),
            sender_id=state.get("sender_id", ""),
            scam_type=state.get("scam_type", ""),
            severity=state.get("severity", 0),
            persona=state.get("persona", ""),
            status=state.get("status", "active"),
            mode=state.get("mode", "bait"),
            message_count=state.get("message_count", 0),
            time_wasted_seconds=time_wasted,
            created_at=created_at,
            updated_at=updated_at,
        ))

    db.commit()


def sync_evidence(db: DBSession, session_id: str):
    """Sync a session's evidence chain into the database."""
    chain_file = BASE_DIR / "evidence" / session_id / "chain.jsonl"
    if not chain_file.exists():
        return

    # Get the highest seq already in DB for this session
    last_seq = db.query(EvidenceEntry.seq).filter(
        EvidenceEntry.session_id == session_id
    ).order_by(EvidenceEntry.seq.desc()).first()
    last_seq = last_seq[0] if last_seq else 0

    with open(chain_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry["seq"] <= last_seq:
                continue

            db.add(EvidenceEntry(
                session_id=session_id,
                seq=entry["seq"],
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                direction=entry.get("direction", "inbound"),
                content=entry["content"],
                content_hash=entry["content_hash"],
                chain_hash=entry["chain_hash"],
                previous_hash=entry["previous_hash"],
                sender_id=entry.get("sender_id", ""),
                channel=entry.get("channel", ""),
                metadata_json=json.dumps(entry.get("metadata", {})),
            ))

    db.commit()


def sync_intel(db: DBSession):
    """Sync the global intel database into SQLite."""
    intel_file = BASE_DIR / "analytics" / "intel-db.json"
    if not intel_file.exists():
        return

    intel_data = json.loads(intel_file.read_text())

    for item in intel_data.get("items", []):
        for sid in item.get("linked_sessions", []):
            existing = db.query(IntelItem).filter(
                IntelItem.session_id == sid,
                IntelItem.type == item["type"],
                IntelItem.value == item["value"],
            ).first()

            if existing:
                existing.last_seen = datetime.fromisoformat(item["last_seen"])
            else:
                db.add(IntelItem(
                    session_id=sid,
                    type=item["type"],
                    value=item["value"],
                    platform=item.get("platform", ""),
                    first_seen=datetime.fromisoformat(item["first_seen"]),
                    last_seen=datetime.fromisoformat(item["last_seen"]),
                ))

    db.commit()


def sync_reports(db: DBSession, session_id: str):
    """Sync report markdown files for a session into the database."""
    reports_dir = BASE_DIR / "reports" / session_id
    if not reports_dir.exists():
        return

    type_mapping = {
        "ic3-complaint.md": "ic3",
        "ftc-report.md": "ftc",
        "ncmec-report.md": "ncmec",
        "local-pd-tip.md": "local_pd",
    }

    for report_file in reports_dir.iterdir():
        if not report_file.is_file() or not report_file.name.endswith(".md"):
            continue

        report_type = type_mapping.get(report_file.name)
        if not report_type and report_file.name.startswith("platform-abuse-"):
            report_type = "platform_abuse"

        if not report_type:
            continue

        existing = db.query(Report).filter(
            Report.session_id == session_id,
            Report.report_type == report_type,
        ).first()

        if not existing:
            mtime = datetime.fromtimestamp(report_file.stat().st_mtime, tz=timezone.utc)
            db.add(Report(
                session_id=session_id,
                report_type=report_type,
                status="draft",
                generated_at=mtime,
                file_path=str(report_file),
            ))

    db.commit()


def full_sync():
    """Run a full sync of all workspace data into the database."""
    db = SessionLocal()
    try:
        sessions_dir = BASE_DIR / "sessions"
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    sync_session(db, session_dir.name)

        evidence_dir = BASE_DIR / "evidence"
        if evidence_dir.exists():
            for ev_dir in evidence_dir.iterdir():
                if ev_dir.is_dir():
                    sync_evidence(db, ev_dir.name)

        sync_intel(db)

        # Sync reports
        reports_dir = BASE_DIR / "reports"
        if reports_dir.exists():
            for rpt_dir in reports_dir.iterdir():
                if rpt_dir.is_dir():
                    sync_reports(db, rpt_dir.name)
    finally:
        db.close()


async def watch_workspace(broadcast_fn=None):
    """Watch workspace directory for changes and sync to database."""
    watch_dirs = []
    for subdir in ["sessions", "evidence", "analytics", "reports"]:
        d = BASE_DIR / subdir
        d.mkdir(parents=True, exist_ok=True)
        watch_dirs.append(d)

    async for changes in awatch(*watch_dirs):
        db = SessionLocal()
        try:
            for change_type, path_str in changes:
                path = Path(path_str)

                # Session state changed
                if "sessions" in path.parts and path.name == "state.json":
                    session_id = path.parent.name
                    sync_session(db, session_id)
                    if broadcast_fn:
                        await broadcast_fn("session_update", {"session_id": session_id})

                # Evidence chain updated
                elif "evidence" in path.parts and path.name == "chain.jsonl":
                    session_id = path.parent.name
                    sync_evidence(db, session_id)
                    if broadcast_fn:
                        await broadcast_fn("evidence_update", {"session_id": session_id})

                # Intel database updated
                elif path.name == "intel-db.json":
                    sync_intel(db)
                    if broadcast_fn:
                        await broadcast_fn("intel_update", {})

                # Report file created/updated
                elif "reports" in path.parts and path.name.endswith(".md"):
                    session_id = path.parent.name
                    sync_reports(db, session_id)
                    if broadcast_fn:
                        await broadcast_fn("session_update", {"session_id": session_id})
        finally:
            db.close()
