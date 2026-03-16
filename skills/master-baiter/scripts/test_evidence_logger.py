# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Tests for evidence_logger.py and hash_verify.py."""

import json
import os
import sys
from pathlib import Path

import pytest

# Ensure scripts directory is importable
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import evidence_logger
import hash_verify


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Create a temporary workspace and point modules at it."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    monkeypatch.setenv("OPENCLAW_WORKSPACE", str(ws))
    # Patch module-level constants
    monkeypatch.setattr(evidence_logger, "WORKSPACE", ws)
    monkeypatch.setattr(evidence_logger, "BASE_DIR", ws / "master-baiter")
    monkeypatch.setattr(hash_verify, "WORKSPACE", ws)
    monkeypatch.setattr(hash_verify, "BASE_DIR", ws / "master-baiter")
    return ws


SESSION_ID = "test-session-001"


class TestLogEvidence:
    def test_first_entry_has_zero_previous_hash(self, workspace):
        entry = evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="whatsapp",
            sender_id="+1234567890",
            direction="inbound",
            content="Hello, I have an investment opportunity for you!",
        )
        assert entry["seq"] == 1
        assert entry["previous_hash"] == "0" * 64
        assert entry["content_hash"]
        assert entry["chain_hash"]

    def test_sequential_entries_chain(self, workspace):
        e1 = evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="telegram",
            sender_id="scammer42",
            direction="inbound",
            content="Hey are you interested in crypto?",
        )
        e2 = evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="telegram",
            sender_id="bait-persona",
            direction="outbound",
            content="Sure tell me more!",
        )
        assert e2["seq"] == 2
        assert e2["previous_hash"] == e1["chain_hash"]

    def test_content_hash_is_deterministic(self, workspace):
        content = "Test message content"
        expected = evidence_logger.compute_hash(content)
        entry = evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="sms",
            sender_id="x",
            direction="inbound",
            content=content,
        )
        assert entry["content_hash"] == expected


class TestGetLastChainHash:
    def test_empty_file(self, workspace):
        chain_file = workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        chain_file.parent.mkdir(parents=True, exist_ok=True)
        chain_file.write_text("")
        h, seq = evidence_logger.get_last_chain_hash(chain_file)
        assert h == "0" * 64
        assert seq == 0

    def test_nonexistent_file(self, workspace):
        chain_file = workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        h, seq = evidence_logger.get_last_chain_hash(chain_file)
        assert h == "0" * 64
        assert seq == 0

    def test_returns_last_entry(self, workspace):
        evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="email",
            sender_id="x",
            direction="inbound",
            content="msg1",
        )
        e2 = evidence_logger.log_evidence(
            session_id=SESSION_ID,
            channel="email",
            sender_id="x",
            direction="inbound",
            content="msg2",
        )
        chain_file = (
            workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        )
        h, seq = evidence_logger.get_last_chain_hash(chain_file)
        assert h == e2["chain_hash"]
        assert seq == 2


class TestExtractIntel:
    def test_creates_intel_entry(self, workspace):
        evidence_logger.extract_intel(
            session_id=SESSION_ID,
            intel_type="phone",
            value="+15551234567",
            platform="whatsapp",
        )
        intel_file = workspace / "master-baiter" / "analytics" / "intel-db.json"
        assert intel_file.exists()
        db = json.loads(intel_file.read_text())
        assert len(db["items"]) == 1
        assert db["items"][0]["type"] == "phone"
        assert db["items"][0]["value"] == "+15551234567"
        assert SESSION_ID in db["items"][0]["linked_sessions"]

    def test_deduplicates_intel(self, workspace):
        evidence_logger.extract_intel(SESSION_ID, "email", "scam@evil.com")
        evidence_logger.extract_intel(SESSION_ID, "email", "scam@evil.com")
        intel_file = workspace / "master-baiter" / "analytics" / "intel-db.json"
        db = json.loads(intel_file.read_text())
        assert len(db["items"]) == 1

    def test_links_multiple_sessions(self, workspace):
        evidence_logger.extract_intel("sess-a", "wallet", "0xABC123")
        evidence_logger.extract_intel("sess-b", "wallet", "0xABC123")
        intel_file = workspace / "master-baiter" / "analytics" / "intel-db.json"
        db = json.loads(intel_file.read_text())
        assert len(db["items"]) == 1
        assert set(db["items"][0]["linked_sessions"]) == {"sess-a", "sess-b"}


class TestUpdateSessionState:
    def test_creates_state_file(self, workspace):
        state = evidence_logger.update_session_state(
            session_id=SESSION_ID,
            channel="whatsapp",
            sender_id="+1234",
            scam_type="romance",
            severity=3,
            persona="grandma",
            mode="bait",
        )
        assert state["session_id"] == SESSION_ID
        assert state["scam_type"] == "romance"
        state_file = (
            workspace / "master-baiter" / "sessions" / SESSION_ID / "state.json"
        )
        assert state_file.exists()

    def test_increments_message_count(self, workspace):
        evidence_logger.update_session_state(SESSION_ID, "tg", "x")
        state = evidence_logger.update_session_state(SESSION_ID, "tg", "x")
        assert state["message_count"] == 2


class TestVerifyChain:
    def test_valid_chain(self, workspace):
        for i in range(5):
            evidence_logger.log_evidence(
                session_id=SESSION_ID,
                channel="whatsapp",
                sender_id="scammer",
                direction="inbound",
                content=f"Scam message {i}",
            )
        result = hash_verify.verify_chain(SESSION_ID)
        assert result["valid"] is True
        assert result["chain_length"] == 5

    def test_detects_tampered_content(self, workspace):
        for i in range(3):
            evidence_logger.log_evidence(
                session_id=SESSION_ID,
                channel="whatsapp",
                sender_id="scammer",
                direction="inbound",
                content=f"Message {i}",
            )
        # Tamper with the chain file
        chain_file = (
            workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        )
        lines = chain_file.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["content"] = "TAMPERED CONTENT"
        lines[1] = json.dumps(entry, separators=(",", ":"))
        chain_file.write_text("\n".join(lines) + "\n")

        result = hash_verify.verify_chain(SESSION_ID)
        assert result["valid"] is False
        assert "content hash mismatch" in result["error"].lower()

    def test_detects_missing_chain_file(self, workspace):
        result = hash_verify.verify_chain("nonexistent-session")
        assert result["valid"] is False
        assert "not found" in result["error"].lower()

    def test_empty_chain(self, workspace):
        chain_file = (
            workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        )
        chain_file.parent.mkdir(parents=True, exist_ok=True)
        chain_file.write_text("")
        result = hash_verify.verify_chain(SESSION_ID)
        assert result["valid"] is True
        assert result["chain_length"] == 0

    def test_detects_broken_previous_hash(self, workspace):
        for i in range(3):
            evidence_logger.log_evidence(
                session_id=SESSION_ID,
                channel="sms",
                sender_id="x",
                direction="inbound",
                content=f"Msg {i}",
            )
        chain_file = (
            workspace / "master-baiter" / "evidence" / SESSION_ID / "chain.jsonl"
        )
        lines = chain_file.read_text().strip().split("\n")
        entry = json.loads(lines[2])
        entry["previous_hash"] = "a" * 64
        lines[2] = json.dumps(entry, separators=(",", ":"))
        chain_file.write_text("\n".join(lines) + "\n")

        result = hash_verify.verify_chain(SESSION_ID)
        assert result["valid"] is False
