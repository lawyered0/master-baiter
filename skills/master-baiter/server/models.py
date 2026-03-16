"""SQLAlchemy models for master-baiter dashboard."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    channel = Column(String, nullable=False)
    sender_id = Column(String, nullable=False)
    scam_type = Column(String, default="")
    severity = Column(Integer, default=0)
    persona = Column(String, default="")
    status = Column(String, default="active")  # active, paused, closed, escalated
    mode = Column(String, default="bait")  # bait, passive
    message_count = Column(Integer, default=0)
    time_wasted_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evidence = relationship("EvidenceEntry", back_populates="session", cascade="all, delete-orphan")
    intel_items = relationship("IntelItem", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")


class EvidenceEntry(Base):
    __tablename__ = "evidence_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    direction = Column(String, nullable=False)  # inbound, outbound
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    chain_hash = Column(String, nullable=False)
    previous_hash = Column(String, nullable=False)
    sender_id = Column(String, default="")
    channel = Column(String, default="")
    metadata_json = Column(Text, default="{}")

    session = relationship("Session", back_populates="evidence")


class IntelItem(Base):
    __tablename__ = "intel_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    type = Column(String, nullable=False)  # phone, email, wallet, bank_account, username, name
    value = Column(String, nullable=False)
    platform = Column(String, default="")
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="intel_items")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    report_type = Column(String, nullable=False)  # ic3, ftc, ncmec, local_pd, platform_abuse
    status = Column(String, default="draft")  # draft, reviewed, submitted
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime, nullable=True)
    file_path = Column(String, default="")

    session = relationship("Session", back_populates="reports")
