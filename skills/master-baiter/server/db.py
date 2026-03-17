"""Database setup and session management.

Engine and session factory are created lazily on first use so that
importing this module doesn't immediately hit the filesystem or fail
if OPENCLAW_WORKSPACE is not yet set / writable.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models import Base

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
DB_DIR = WORKSPACE / "master-baiter" / "db"
DB_PATH = DB_DIR / "master-baiter.db"

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine())
    return _SessionLocal


class _SessionLocalProxy:
    """Proxy that defers sessionmaker creation until first call."""
    def __call__(self):
        return _get_session_factory()()


SessionLocal = _SessionLocalProxy()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(_get_engine())


def get_db():
    """FastAPI dependency for database sessions."""
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()
