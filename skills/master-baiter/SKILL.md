---
name: master-baiter
description: "Autonomous scam baiting across all messaging channels. Wastes financial scammers' time with adaptive personas and honeypot traps while extracting identifying intel (wallets, bank accounts, phones, emails). Passive predator/grooming detection with auto-reporting. Generates law enforcement reports (FBI IC3, FTC, NCMEC CyberTipline, local PD) and platform abuse reports. Full-stack dashboard for session monitoring and analytics. Use when: scam detected, fraud baiting, predator alert, generate IC3/FTC/NCMEC report, evidence logging, scammer intel, scam dashboard."
user-invocable: true
metadata: { "openclaw": { "emoji": "🎣", "requires": { "bins": ["uv"] }, "install": [{ "id": "uv-brew", "kind": "brew", "formula": "uv", "bins": ["uv"], "label": "Install uv (brew)" }] } }
---

# Master-Baiter

Dual-mode scam fighter: **active baiting** of financial scammers + **passive detection** of predators/groomers.

## Hard Constraints

- NEVER role-play as a minor. NEVER fetch/curl/open scammer URLs. NEVER send real PII.
- All generated reports are DRAFTS requiring human review before submission.
- If a financial scam conversation turns predatory, IMMEDIATELY switch to passive mode.

## Scam Baiting (Active Mode)

1. Classify inbound message: `cat {baseDir}/references/scam-taxonomy.md`
2. Select persona + honeypot strategy: `cat {baseDir}/references/persona-strategies.md`
3. Respond via `message` tool on the same channel. Use delay tactics: store runs, bank loading, computer updating, verification loops.
4. Log every message (inbound + outbound):

```bash
uv run {baseDir}/scripts/evidence_logger.py --session SESSION_ID --channel CHANNEL --sender SENDER_ID --direction inbound --content "MESSAGE"
```

5. Extract and log intel: names, phone numbers, emails, crypto wallets, bank accounts, mule accounts.
6. Objective: maximize time wasted while extracting maximum identifying information.

## Predator Detection (Passive Mode)

1. Check indicators: `cat {baseDir}/references/predator-indicators.md`
2. PASSIVE ONLY — classify, log evidence, generate reports. NEVER engage or respond.
3. Severity 4-5 triggers automatic NCMEC report generation.

## Escalation

Read `{baseDir}/references/escalation-framework.md` for severity thresholds.

- Sev 1-2: Log + bait. Sev 3: Generate report drafts. Sev 4: All reports + alert operator. Sev 5 (CSAM/imminent harm): STOP all engagement, NCMEC report, alert all channels.

## Evidence & Reports

```bash
# Verify evidence chain integrity
uv run {baseDir}/scripts/hash_verify.py --session SESSION_ID

# Generate reports
uv run {baseDir}/scripts/report_ic3.py --session SESSION_ID
uv run {baseDir}/scripts/report_ftc.py --session SESSION_ID
uv run {baseDir}/scripts/report_ncmec.py --session SESSION_ID
uv run {baseDir}/scripts/report_local_pd.py --session SESSION_ID
uv run {baseDir}/scripts/report_platform_abuse.py --session SESSION_ID --platform PLATFORM
```

## Dashboard

Start the monitoring dashboard:

```bash
uv run {baseDir}/server/main.py
```

Opens at `http://localhost:8147` — live session monitoring, intel database, report management, analytics.

## Workspace Layout

```
master-baiter/sessions/<id>/state.json      # Session state + classification
master-baiter/evidence/<id>/chain.jsonl      # SHA-256 hashed evidence chain
master-baiter/reports/<id>/*.md              # Generated report drafts
master-baiter/analytics/intel-db.json        # Cross-session intel database
master-baiter/db/master-baiter.db            # SQLite dashboard database
```
