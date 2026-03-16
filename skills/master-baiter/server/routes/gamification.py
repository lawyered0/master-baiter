"""Gamification API routes — XP, levels, achievements, and fun stats."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session as DBSession

from db import get_db
from models import Session, EvidenceEntry, IntelItem, Report, ScoreEvent, Achievement

# Import the engine for achievement defs and scoring logic
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from gamification_engine import (
    ACHIEVEMENTS,
    level_from_xp,
    check_all_achievements,
    format_duration_human,
    scammer_salary_wasted,
    fun_comparison,
    score_event,
    xp_for_level,
    MESSAGE_MILESTONES,
    TIME_MILESTONES,
)

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


def _build_stats(db: DBSession, session_id: str | None = None) -> dict:
    """Build the stats dict used by the achievement checker."""
    # Global stats
    global_time = db.query(func.sum(Session.time_wasted_seconds)).scalar() or 0
    total_intel = db.query(IntelItem.value).distinct().count()
    total_reports = db.query(Report).count()
    reports_submitted = db.query(Report).filter(Report.status == "submitted").count()
    concurrent_active = db.query(Session).filter(Session.status == "active").count()
    unique_scam_types = db.query(Session.scam_type).filter(Session.scam_type != "").distinct().count()

    # Unique personas ever used
    persona_rows = (
        db.query(Session.persona, func.count(Session.id))
        .filter(Session.persona != "")
        .group_by(Session.persona)
        .all()
    )
    persona_sessions = {}
    for persona, count in persona_rows:
        # Normalize persona name to key
        key = persona.lower().strip().replace(" ", "_").replace("-", "_")
        # Map display names to keys
        name_map = {
            "confused_edna": "confused_edna", "edna": "confused_edna",
            "eager_investor": "eager_investor", "brad": "eager_investor",
            "lonely_heart": "lonely_heart", "diane": "lonely_heart",
            "counter_scammer": "counter_scammer", "viktor": "counter_scammer",
            "helpful_clueless": "helpful_clueless", "pat": "helpful_clueless",
            "helpful_but_clueless": "helpful_clueless",
            "wealthy_cautious": "wealthy_cautious", "richard": "wealthy_cautious",
            "wealthy_but_cautious": "wealthy_cautious",
        }
        mapped = name_map.get(key, key)
        persona_sessions[mapped] = persona_sessions.get(mapped, 0) + count

    unique_personas = len(persona_sessions)

    # Intel by type
    intel_by_type_rows = (
        db.query(IntelItem.type, func.count(distinct(IntelItem.value)))
        .group_by(IntelItem.type)
        .all()
    )
    intel_by_type = {row[0]: row[1] for row in intel_by_type_rows}

    # Report type counts
    report_type_rows = (
        db.query(Report.report_type, func.count(Report.id))
        .group_by(Report.report_type)
        .all()
    )
    report_type_count = {row[0]: row[1] for row in report_type_rows}

    # Daily unique personas (today)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_personas = (
        db.query(Session.persona)
        .filter(Session.persona != "", func.date(Session.created_at) == today_str)
        .distinct()
        .count()
    )

    # Intel streak: count consecutive sessions (by created_at desc) that have intel
    all_sessions = (
        db.query(Session.id)
        .order_by(Session.created_at.desc())
        .all()
    )
    intel_streak = 0
    for (sid,) in all_sessions:
        has_intel = db.query(IntelItem).filter(IntelItem.session_id == sid).first()
        if has_intel:
            intel_streak += 1
        else:
            break

    # Repeat scammer detection
    repeat_senders = (
        db.query(Session.sender_id, func.count(Session.id))
        .filter(Session.sender_id != "")
        .group_by(Session.sender_id)
        .having(func.count(Session.id) >= 2)
        .count()
    )

    stats = {
        "global_time": global_time,
        "total_intel": total_intel,
        "total_reports": total_reports,
        "reports_submitted": reports_submitted,
        "concurrent_active": concurrent_active,
        "unique_scam_types": unique_scam_types,
        "unique_personas": unique_personas,
        "daily_unique_personas": daily_personas,
        "intel_by_type": intel_by_type,
        "persona_sessions": persona_sessions,
        "report_type_count": report_type_count,
        "intel_streak": intel_streak,
        "repeat_scammer": repeat_senders,
        # Session-level defaults
        "session_time": 0,
        "session_messages": 0,
        "session_intel_types": 0,
        "session_intel_type_set": [],
        "session_report_types": 0,
        "session_spans_midnight": 0,
        "persona_time": {},
    }

    # If checking for a specific session, add session-level stats
    if session_id:
        sess = db.query(Session).filter(Session.id == session_id).first()
        if sess:
            stats["session_time"] = sess.time_wasted_seconds or 0
            stats["session_messages"] = sess.message_count or 0

            # Session intel types
            session_intel_types = (
                db.query(IntelItem.type)
                .filter(IntelItem.session_id == session_id)
                .distinct()
                .all()
            )
            type_set = [r[0] for r in session_intel_types]
            stats["session_intel_types"] = len(type_set)
            stats["session_intel_type_set"] = type_set

            # Session report types
            session_report_count = (
                db.query(Report.report_type)
                .filter(Report.session_id == session_id)
                .distinct()
                .count()
            )
            stats["session_report_types"] = session_report_count

            # Persona time for this session's persona
            if sess.persona:
                key = sess.persona.lower().strip().replace(" ", "_").replace("-", "_")
                stats["persona_time"] = {key: sess.time_wasted_seconds or 0}

            # Check if session spans midnight
            if sess.created_at and sess.updated_at:
                if sess.created_at.date() != sess.updated_at.date():
                    stats["session_spans_midnight"] = 1

    return stats


def _sync_achievements(db: DBSession, stats: dict, trigger_session_id: str | None = None) -> list[dict]:
    """Check achievements and persist any newly unlocked ones. Returns new unlocks."""
    already = {a.achievement_id for a in db.query(Achievement.achievement_id).filter(Achievement.unlocked_at.isnot(None)).all()}
    newly_unlocked = check_all_achievements(stats, already)

    now = datetime.now(timezone.utc)
    for ach in newly_unlocked:
        existing = db.query(Achievement).filter(Achievement.achievement_id == ach["id"]).first()
        if existing:
            existing.unlocked_at = now
            existing.session_id = trigger_session_id
        else:
            db.add(Achievement(
                achievement_id=ach["id"],
                name=ach["name"],
                description=ach["description"],
                icon=ach["icon"],
                category=ach["category"],
                xp_reward=ach["xp_reward"],
                unlocked_at=now,
                session_id=trigger_session_id,
            ))

        # Award XP for achievement
        db.add(ScoreEvent(
            session_id=trigger_session_id,
            event_type="achievement_unlocked",
            xp_base=ach["xp_reward"],
            xp_multiplier="1.0",
            xp_awarded=ach["xp_reward"],
            metadata_json=json.dumps({"achievement_id": ach["id"]}),
        ))

    if newly_unlocked:
        db.commit()

    return newly_unlocked


def _get_total_xp(db: DBSession) -> int:
    return db.query(func.sum(ScoreEvent.xp_awarded)).scalar() or 0


@router.get("/profile")
def get_profile(db: DBSession = Depends(get_db)):
    """Player profile: level, XP, title, progress."""
    total_xp = _get_total_xp(db)
    info = level_from_xp(total_xp)

    unlocked_count = db.query(Achievement).filter(Achievement.unlocked_at.isnot(None)).count()
    total_achievements = len(ACHIEVEMENTS)

    # Current intel streak
    all_sessions = db.query(Session.id).order_by(Session.created_at.desc()).all()
    streak = 0
    for (sid,) in all_sessions:
        if db.query(IntelItem).filter(IntelItem.session_id == sid).first():
            streak += 1
        else:
            break

    # Best streak (we track current only — best would need historical data)
    # For now, best = current
    return {
        **info,
        "achievements_unlocked": unlocked_count,
        "achievements_total": total_achievements,
        "current_streak": streak,
    }


@router.get("/achievements")
def get_achievements(category: str = "", db: DBSession = Depends(get_db)):
    """All achievements with locked/unlocked status."""
    # Get unlocked achievements from DB
    unlocked_map = {}
    for ach in db.query(Achievement).filter(Achievement.unlocked_at.isnot(None)).all():
        unlocked_map[ach.achievement_id] = {
            "unlocked_at": ach.unlocked_at.isoformat() if ach.unlocked_at else None,
            "session_id": ach.session_id,
        }

    result = []
    for ach in ACHIEVEMENTS:
        if category and ach["category"] != category:
            continue

        is_unlocked = ach["id"] in unlocked_map
        entry = {
            "id": ach["id"],
            "name": ach["name"] if (is_unlocked or ach["category"] != "hidden") else "???",
            "description": ach["description"] if (is_unlocked or ach["category"] != "hidden") else "Keep baiting to discover...",
            "icon": ach["icon"] if (is_unlocked or ach["category"] != "hidden") else "🔒",
            "category": ach["category"],
            "xp_reward": ach["xp_reward"],
            "unlocked": is_unlocked,
        }
        if is_unlocked:
            entry["unlocked_at"] = unlocked_map[ach["id"]]["unlocked_at"]
            entry["session_id"] = unlocked_map[ach["id"]]["session_id"]

        result.append(entry)

    return {"achievements": result}


@router.get("/leaderboard")
def get_leaderboard(db: DBSession = Depends(get_db)):
    """Top sessions ranked by XP earned."""
    rows = (
        db.query(
            ScoreEvent.session_id,
            func.sum(ScoreEvent.xp_awarded).label("xp"),
        )
        .filter(ScoreEvent.session_id.isnot(None))
        .group_by(ScoreEvent.session_id)
        .order_by(func.sum(ScoreEvent.xp_awarded).desc())
        .limit(20)
        .all()
    )

    entries = []
    for row in rows:
        sess = db.query(Session).filter(Session.id == row.session_id).first()
        entries.append({
            "session_id": row.session_id,
            "xp": row.xp,
            "persona": sess.persona if sess else "",
            "scam_type": sess.scam_type if sess else "",
            "channel": sess.channel if sess else "",
            "time_wasted": sess.time_wasted_seconds if sess else 0,
            "messages": sess.message_count if sess else 0,
        })

    return {"leaderboard": entries}


@router.get("/feed")
def get_feed(limit: int = 20, db: DBSession = Depends(get_db)):
    """Recent XP events (activity feed)."""
    events = (
        db.query(ScoreEvent)
        .order_by(ScoreEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "events": [
            {
                "id": e.id,
                "session_id": e.session_id,
                "event_type": e.event_type,
                "xp_awarded": e.xp_awarded,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/stats")
def get_fun_stats(db: DBSession = Depends(get_db)):
    """Fun/cheeky stats for the achievements view."""
    total_time = db.query(func.sum(Session.time_wasted_seconds)).scalar() or 0
    total_messages = db.query(func.sum(Session.message_count)).scalar() or 0
    total_intel = db.query(IntelItem.value).distinct().count()
    total_reports = db.query(Report).count()
    reports_submitted = db.query(Report).filter(Report.status == "submitted").count()

    # Most used persona
    top_persona = (
        db.query(Session.persona, func.count(Session.id))
        .filter(Session.persona != "")
        .group_by(Session.persona)
        .order_by(func.count(Session.id).desc())
        .first()
    )

    # Longest session
    longest = (
        db.query(Session.time_wasted_seconds)
        .order_by(Session.time_wasted_seconds.desc())
        .first()
    )

    # Most common scam type
    top_scam = (
        db.query(Session.scam_type, func.count(Session.id))
        .filter(Session.scam_type != "")
        .group_by(Session.scam_type)
        .order_by(func.count(Session.id).desc())
        .first()
    )

    return {
        "total_time_wasted_seconds": total_time,
        "total_time_wasted_human": format_duration_human(total_time),
        "scammer_salary_wasted": scammer_salary_wasted(total_time),
        "messages_exchanged": total_messages,
        "most_used_persona": top_persona[0] if top_persona else "None yet",
        "longest_session_seconds": longest[0] if longest else 0,
        "longest_session_human": format_duration_human(longest[0]) if longest and longest[0] else "0s",
        "favorite_scam_type": top_scam[0] if top_scam else "None yet",
        "intel_collected": total_intel,
        "reports_filed": total_reports,
        "reports_submitted": reports_submitted,
        "fun_fact": fun_comparison(total_time),
    }


@router.post("/recalculate")
def recalculate(db: DBSession = Depends(get_db)):
    """Full recalculation of all XP and achievements from session data."""
    # Clear existing score events and achievements (no commit yet —
    # deletions and inserts should be in the same transaction so a
    # crash doesn't leave the DB empty)
    db.query(ScoreEvent).delete()
    db.query(Achievement).delete()

    total_xp = 0
    all_sessions = db.query(Session).all()

    for sess in all_sessions:
        severity = sess.severity or 1

        # XP for session start
        ev = score_event("session_started", severity=severity)
        db.add(ScoreEvent(
            session_id=sess.id, event_type="session_started",
            xp_base=ev["xp_base"], xp_multiplier=str(ev["multiplier"]),
            xp_awarded=ev["xp_awarded"],
        ))
        total_xp += ev["xp_awarded"]

        # XP for messages
        if sess.message_count:
            outbound = sess.message_count // 2  # rough estimate
            inbound = sess.message_count - outbound

            ev_out = score_event("message_sent", severity=severity, count=outbound)
            db.add(ScoreEvent(
                session_id=sess.id, event_type="message_sent",
                xp_base=ev_out["xp_base"], xp_multiplier=str(ev_out["multiplier"]),
                xp_awarded=ev_out["xp_awarded"],
            ))
            total_xp += ev_out["xp_awarded"]

            ev_in = score_event("message_received", severity=severity, count=inbound)
            db.add(ScoreEvent(
                session_id=sess.id, event_type="message_received",
                xp_base=ev_in["xp_base"], xp_multiplier=str(ev_in["multiplier"]),
                xp_awarded=ev_in["xp_awarded"],
            ))
            total_xp += ev_in["xp_awarded"]

            # Message milestones
            for threshold, bonus, label in MESSAGE_MILESTONES:
                if sess.message_count >= threshold:
                    db.add(ScoreEvent(
                        session_id=sess.id, event_type="message_milestone",
                        xp_base=bonus, xp_multiplier="1.0", xp_awarded=bonus,
                        metadata_json=json.dumps({"milestone": label}),
                    ))
                    total_xp += bonus

        # XP for time wasted
        if sess.time_wasted_seconds:
            minutes = sess.time_wasted_seconds // 60
            if minutes > 0:
                ev_time = score_event("time_wasted_min", severity=severity, count=minutes)
                db.add(ScoreEvent(
                    session_id=sess.id, event_type="time_wasted_min",
                    xp_base=ev_time["xp_base"], xp_multiplier=str(ev_time["multiplier"]),
                    xp_awarded=ev_time["xp_awarded"],
                ))
                total_xp += ev_time["xp_awarded"]

            # Time milestones
            for threshold, bonus, label in TIME_MILESTONES:
                if sess.time_wasted_seconds >= threshold:
                    db.add(ScoreEvent(
                        session_id=sess.id, event_type="time_milestone",
                        xp_base=bonus, xp_multiplier="1.0", xp_awarded=bonus,
                        metadata_json=json.dumps({"milestone": label}),
                    ))
                    total_xp += bonus

        # XP for intel
        session_intel = db.query(IntelItem).filter(IntelItem.session_id == sess.id).all()
        for intel in session_intel:
            ev_intel = score_event("intel_extracted", severity=severity)
            db.add(ScoreEvent(
                session_id=sess.id, event_type="intel_extracted",
                xp_base=ev_intel["xp_base"], xp_multiplier=str(ev_intel["multiplier"]),
                xp_awarded=ev_intel["xp_awarded"],
                metadata_json=json.dumps({"intel_type": intel.type}),
            ))
            total_xp += ev_intel["xp_awarded"]

        # XP for reports
        session_reports = db.query(Report).filter(Report.session_id == sess.id).all()
        for report in session_reports:
            ev_rpt = score_event("report_generated", severity=severity)
            db.add(ScoreEvent(
                session_id=sess.id, event_type="report_generated",
                xp_base=ev_rpt["xp_base"], xp_multiplier=str(ev_rpt["multiplier"]),
                xp_awarded=ev_rpt["xp_awarded"],
            ))
            total_xp += ev_rpt["xp_awarded"]

            if report.status == "submitted":
                ev_sub = score_event("report_submitted", severity=severity)
                db.add(ScoreEvent(
                    session_id=sess.id, event_type="report_submitted",
                    xp_base=ev_sub["xp_base"], xp_multiplier=str(ev_sub["multiplier"]),
                    xp_awarded=ev_sub["xp_awarded"],
                ))
                total_xp += ev_sub["xp_awarded"]

    db.commit()

    # Now check achievements against all sessions
    all_new_achievements = []
    for sess in all_sessions:
        stats = _build_stats(db, session_id=sess.id)
        new_achs = _sync_achievements(db, stats, trigger_session_id=sess.id)
        all_new_achievements.extend(new_achs)

    # Also check global-only achievements
    global_stats = _build_stats(db)
    global_achs = _sync_achievements(db, global_stats)
    all_new_achievements.extend(global_achs)

    # Re-query total XP to include achievement XP
    total_xp = _get_total_xp(db)
    level_info = level_from_xp(total_xp)

    return {
        "status": "ok",
        "total_xp": total_xp,
        **level_info,
        "achievements_unlocked": len(all_new_achievements),
        "sessions_scored": len(all_sessions),
    }
