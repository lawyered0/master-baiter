"""Analytics API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from db import get_db
from models import Session, EvidenceEntry, IntelItem, Report

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(db: DBSession = Depends(get_db)):
    total_sessions = db.query(Session).count()
    active_sessions = db.query(Session).filter(Session.status == "active").count()
    total_time_wasted = db.query(func.sum(Session.time_wasted_seconds)).scalar() or 0
    total_messages = db.query(func.sum(Session.message_count)).scalar() or 0
    total_intel = db.query(IntelItem.value).distinct().count()
    total_reports = db.query(Report).count()
    reports_submitted = db.query(Report).filter(Report.status == "submitted").count()

    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "total_time_wasted_seconds": total_time_wasted,
        "total_time_wasted_hours": round(total_time_wasted / 3600, 1),
        "total_messages": total_messages,
        "total_intel_items": total_intel,
        "total_reports": total_reports,
        "reports_submitted": reports_submitted,
    }


@router.get("/scam-types")
def get_scam_types(db: DBSession = Depends(get_db)):
    results = (
        db.query(
            Session.scam_type,
            func.count(Session.id).label("count"),
            func.sum(Session.time_wasted_seconds).label("total_time"),
            func.avg(Session.severity).label("avg_severity"),
        )
        .filter(Session.scam_type != "")
        .group_by(Session.scam_type)
        .order_by(func.count(Session.id).desc())
        .all()
    )

    return {
        "types": [
            {
                "scam_type": r.scam_type,
                "count": r.count,
                "total_time_seconds": r.total_time or 0,
                "avg_severity": round(r.avg_severity, 1) if r.avg_severity else 0,
            }
            for r in results
        ],
    }


@router.get("/trends")
def get_trends(db: DBSession = Depends(get_db)):
    """Daily session counts and time wasted for the last 30 days."""
    results = (
        db.query(
            func.date(Session.created_at).label("date"),
            func.count(Session.id).label("sessions"),
            func.sum(Session.time_wasted_seconds).label("time_wasted"),
            func.sum(Session.message_count).label("messages"),
        )
        .group_by(func.date(Session.created_at))
        .order_by(func.date(Session.created_at).desc())
        .limit(30)
        .all()
    )

    return {
        "daily": [
            {
                "date": str(r.date),
                "sessions": r.sessions,
                "time_wasted_seconds": r.time_wasted or 0,
                "messages": r.messages or 0,
            }
            for r in reversed(results)
        ],
    }


@router.get("/effectiveness")
def get_effectiveness(db: DBSession = Depends(get_db)):
    total = db.query(Session).count() or 1

    avg_duration = db.query(func.avg(Session.time_wasted_seconds)).scalar() or 0
    avg_messages = db.query(func.avg(Session.message_count)).scalar() or 0

    sessions_with_intel = (
        db.query(IntelItem.session_id)
        .distinct()
        .count()
    )

    sessions_with_reports = (
        db.query(Report.session_id)
        .distinct()
        .count()
    )

    # Top scammer identifiers (most linked sessions)
    top_intel = (
        db.query(
            IntelItem.type,
            IntelItem.value,
            func.count(IntelItem.session_id.distinct()).label("session_count"),
        )
        .group_by(IntelItem.type, IntelItem.value)
        .order_by(func.count(IntelItem.session_id.distinct()).desc())
        .limit(10)
        .all()
    )

    return {
        "avg_session_duration_seconds": round(avg_duration),
        "avg_session_duration_minutes": round(avg_duration / 60, 1),
        "avg_messages_per_session": round(avg_messages, 1),
        "intel_extraction_rate": round(sessions_with_intel / total * 100, 1),
        "report_generation_rate": round(sessions_with_reports / total * 100, 1),
        "top_scammer_identifiers": [
            {"type": r.type, "value": r.value, "session_count": r.session_count}
            for r in top_intel
        ],
    }


@router.get("/channels")
def get_channel_breakdown(db: DBSession = Depends(get_db)):
    results = (
        db.query(
            Session.channel,
            func.count(Session.id).label("count"),
            func.sum(Session.time_wasted_seconds).label("total_time"),
        )
        .filter(Session.channel != "")
        .group_by(Session.channel)
        .order_by(func.count(Session.id).desc())
        .all()
    )

    return {
        "channels": [
            {
                "channel": r.channel,
                "count": r.count,
                "total_time_seconds": r.total_time or 0,
            }
            for r in results
        ],
    }
