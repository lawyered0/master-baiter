"""Evidence chain API routes."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from db import get_db
from models import EvidenceEntry

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"


@router.get("/{session_id}")
def get_evidence(
    session_id: str,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: DBSession = Depends(get_db),
):
    entries = (
        db.query(EvidenceEntry)
        .filter(EvidenceEntry.session_id == session_id)
        .order_by(EvidenceEntry.seq)
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = db.query(EvidenceEntry).filter(EvidenceEntry.session_id == session_id).count()

    return {
        "session_id": session_id,
        "total": total,
        "entries": [
            {
                "seq": e.seq,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "direction": e.direction,
                "content": e.content,
                "content_hash": e.content_hash,
                "chain_hash": e.chain_hash,
                "previous_hash": e.previous_hash,
                "sender_id": e.sender_id,
                "channel": e.channel,
            }
            for e in entries
        ],
    }


@router.get("/{session_id}/verify")
def verify_evidence(session_id: str):
    """Run hash chain verification on a session's evidence."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    script = SCRIPTS_DIR / "hash_verify.py"
    result = subprocess.run(
        [sys.executable, str(script), "--session", session_id],
        capture_output=True,
        text=True,
        env={**os.environ, "OPENCLAW_WORKSPACE": str(WORKSPACE)},
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "valid": False,
            "error": result.stderr or "Verification failed",
        }
