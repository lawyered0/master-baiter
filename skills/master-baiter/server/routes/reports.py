"""Report management API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from db import get_db
from models import Report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports(
    report_type: str | None = Query(None),
    status: str | None = Query(None),
    session_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: DBSession = Depends(get_db),
):
    q = db.query(Report)
    if report_type:
        q = q.filter(Report.report_type == report_type)
    if status:
        q = q.filter(Report.status == status)
    if session_id:
        q = q.filter(Report.session_id == session_id)

    total = q.count()
    reports = q.order_by(desc(Report.generated_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "reports": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "report_type": r.report_type,
                "status": r.status,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "file_path": r.file_path,
            }
            for r in reports
        ],
    }


@router.get("/{report_id}")
def get_report(report_id: int, db: DBSession = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}, 404

    # Read report file content if it exists
    content = ""
    if report.file_path:
        try:
            with open(report.file_path, "r") as f:
                content = f.read()
        except FileNotFoundError:
            content = "(Report file not found)"

    return {
        "id": report.id,
        "session_id": report.session_id,
        "report_type": report.report_type,
        "status": report.status,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
        "file_path": report.file_path,
        "content": content,
    }


@router.post("/{report_id}/mark-reviewed")
def mark_reviewed(report_id: int, db: DBSession = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}, 404

    report.status = "reviewed"
    db.commit()

    return {"status": "ok", "report_id": report_id, "new_status": "reviewed"}


@router.post("/{report_id}/mark-submitted")
def mark_submitted(report_id: int, db: DBSession = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}, 404

    report.status = "submitted"
    report.submitted_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "ok", "report_id": report_id, "new_status": "submitted"}
