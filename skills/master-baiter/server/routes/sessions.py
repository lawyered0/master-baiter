"""Session management API routes."""

import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from db import get_db
from models import Session, EvidenceEntry, IntelItem, Report

_SAFE_ID = re.compile(r'^[a-zA-Z0-9_-]+$')

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
def list_sessions(
    status: str | None = Query(None),
    scam_type: str | None = Query(None),
    severity_min: int | None = Query(None),
    severity_max: int | None = Query(None),
    channel: str | None = Query(None),
    mode: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: DBSession = Depends(get_db),
):
    q = db.query(Session)
    if status:
        q = q.filter(Session.status == status)
    if scam_type:
        q = q.filter(Session.scam_type == scam_type)
    if severity_min is not None:
        q = q.filter(Session.severity >= severity_min)
    if severity_max is not None:
        q = q.filter(Session.severity <= severity_max)
    if channel:
        q = q.filter(Session.channel == channel)
    if mode:
        q = q.filter(Session.mode == mode)

    total = q.count()
    sessions = q.order_by(desc(Session.updated_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "sessions": [
            {
                "id": s.id,
                "channel": s.channel,
                "sender_id": s.sender_id,
                "scam_type": s.scam_type,
                "severity": s.severity,
                "persona": s.persona,
                "status": s.status,
                "mode": s.mode,
                "message_count": s.message_count,
                "time_wasted_seconds": s.time_wasted_seconds,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ],
    }


@router.get("/{session_id}")
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    if not _SAFE_ID.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    intel = db.query(IntelItem).filter(IntelItem.session_id == session_id).all()
    reports = db.query(Report).filter(Report.session_id == session_id).all()

    return {
        "id": session.id,
        "channel": session.channel,
        "sender_id": session.sender_id,
        "scam_type": session.scam_type,
        "severity": session.severity,
        "persona": session.persona,
        "status": session.status,
        "mode": session.mode,
        "message_count": session.message_count,
        "time_wasted_seconds": session.time_wasted_seconds,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "intel": [
            {"type": i.type, "value": i.value, "platform": i.platform}
            for i in intel
        ],
        "reports": [
            {
                "id": r.id,
                "report_type": r.report_type,
                "status": r.status,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in reports
        ],
    }


@router.get("/{session_id}/transcript")
def get_transcript(
    session_id: str,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: DBSession = Depends(get_db),
):
    if not _SAFE_ID.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    entries = (
        db.query(EvidenceEntry)
        .filter(EvidenceEntry.session_id == session_id)
        .order_by(EvidenceEntry.seq)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "session_id": session_id,
        "entries": [
            {
                "seq": e.seq,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "direction": e.direction,
                "content": e.content,
                "sender_id": e.sender_id,
                "channel": e.channel,
            }
            for e in entries
        ],
    }


@router.post("/{session_id}/escalate")
def escalate_session(session_id: str, severity: int = Query(..., ge=1, le=5), db: DBSession = Depends(get_db)):
    if not _SAFE_ID.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.severity = severity
    session.status = "escalated" if severity >= 4 else session.status
    session.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "ok", "session_id": session_id, "severity": severity}


@router.post("/{session_id}/close")
def close_session(session_id: str, db: DBSession = Depends(get_db)):
    if not _SAFE_ID.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "closed"
    session.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "ok", "session_id": session_id}
