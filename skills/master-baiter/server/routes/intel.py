"""Intel database API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session as DBSession

from db import get_db
from models import IntelItem

router = APIRouter(prefix="/api/intel", tags=["intel"])


@router.get("")
def list_intel(
    type: str | None = Query(None),
    platform: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: DBSession = Depends(get_db),
):
    q = db.query(
        IntelItem.type,
        IntelItem.value,
        func.min(IntelItem.platform).label("platform"),
        func.min(IntelItem.first_seen).label("first_seen"),
        func.max(IntelItem.last_seen).label("last_seen"),
        func.count(distinct(IntelItem.session_id)).label("session_count"),
    ).group_by(IntelItem.type, IntelItem.value)

    if type:
        q = q.filter(IntelItem.type == type)
    if platform:
        q = q.filter(IntelItem.platform == platform)

    total = q.count()
    items = q.order_by(func.max(IntelItem.last_seen).desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "type": row.type,
                "value": row.value,
                "platform": row.platform,
                "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "session_count": row.session_count,
            }
            for row in items
        ],
    }


@router.get("/search")
def search_intel(q: str = Query(..., min_length=1), db: DBSession = Depends(get_db)):
    items = (
        db.query(IntelItem)
        .filter(IntelItem.value.contains(q))
        .order_by(IntelItem.last_seen.desc())
        .limit(50)
        .all()
    )

    return {
        "query": q,
        "results": [
            {
                "type": i.type,
                "value": i.value,
                "platform": i.platform,
                "session_id": i.session_id,
                "first_seen": i.first_seen.isoformat() if i.first_seen else None,
                "last_seen": i.last_seen.isoformat() if i.last_seen else None,
            }
            for i in items
        ],
    }


@router.get("/network/{intel_value}")
def get_intel_network(intel_value: str, db: DBSession = Depends(get_db)):
    """Get all sessions linked to a specific intel value (cross-session correlation)."""
    items = (
        db.query(IntelItem)
        .filter(IntelItem.value == intel_value)
        .all()
    )

    session_ids = list(set(i.session_id for i in items))
    # Get all intel for those sessions to build the network
    all_intel = (
        db.query(IntelItem)
        .filter(IntelItem.session_id.in_(session_ids))
        .all()
    )

    nodes = {}
    edges = []

    for item in all_intel:
        node_key = f"{item.type}:{item.value}"
        if node_key not in nodes:
            nodes[node_key] = {
                "id": node_key,
                "type": item.type,
                "value": item.value,
                "platform": item.platform,
            }
        edges.append({
            "source": node_key,
            "target": f"session:{item.session_id}",
        })

    for sid in session_ids:
        nodes[f"session:{sid}"] = {"id": f"session:{sid}", "type": "session", "value": sid}

    return {
        "query_value": intel_value,
        "nodes": list(nodes.values()),
        "edges": edges,
        "session_count": len(session_ids),
    }
