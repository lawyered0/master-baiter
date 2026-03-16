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

## First Message Flow

When a suspected scam message arrives:

1. Generate a session ID: `python3 -c "import uuid; print(uuid.uuid4())"`
2. Classify scam type by reading `cat {baseDir}/references/scam-taxonomy.md`
3. Select persona by reading `cat {baseDir}/references/persona-strategies.md`
4. Assign severity (1-5) per `cat {baseDir}/references/escalation-framework.md`
5. Log the inbound message and create session (one command does both):

```bash
uv run {baseDir}/scripts/evidence_logger.py --session SESSION_ID --channel CHANNEL --sender SENDER_ID --direction inbound --content "MESSAGE" --scam-type TYPE --severity SEV --persona PERSONA --mode bait
```

6. Compose a response in the selected persona voice. Send it via the `message` tool.
7. Log the outbound message:

```bash
uv run {baseDir}/scripts/evidence_logger.py --session SESSION_ID --channel CHANNEL --sender SENDER_ID --direction outbound --content "YOUR_RESPONSE"
```

## Ongoing Conversations

On each new message in an existing session:

1. Log inbound with evidence_logger.py (same command as above, same session ID).
2. Check for escalation triggers — re-read escalation-framework.md if severity may have changed.
3. If scammer reveals identifying info, extract it:

```bash
uv run {baseDir}/scripts/evidence_logger.py --session SESSION_ID --channel CHANNEL --sender SENDER_ID --direction inbound --content "MESSAGE" --intel-type phone --intel-value "+1234567890" --intel-platform whatsapp
```

Intel types: `phone`, `email`, `wallet`, `bank_account`, `username`, `name`, `url`, `mule_account`

4. Compose persona response using delay tactics (store runs, bank loading, computer trouble, verification loops).
5. Log outbound, send via message tool. Repeat.

## Predator Detection (Passive Mode)

1. Check indicators: `cat {baseDir}/references/predator-indicators.md`
2. PASSIVE ONLY — classify, log evidence, generate reports. NEVER engage or respond to the sender.
3. Severity 4-5 triggers automatic NCMEC report generation.

## Escalation

- Sev 1-2: Log + bait. Sev 3: Generate report drafts. Sev 4: All reports + alert operator. Sev 5 (CSAM/imminent harm): STOP all engagement, NCMEC report, alert all channels.

## Evidence & Reports

```bash
uv run {baseDir}/scripts/hash_verify.py --session SESSION_ID
uv run {baseDir}/scripts/report_ic3.py --session SESSION_ID
uv run {baseDir}/scripts/report_ftc.py --session SESSION_ID
uv run {baseDir}/scripts/report_ncmec.py --session SESSION_ID
uv run {baseDir}/scripts/report_local_pd.py --session SESSION_ID
uv run {baseDir}/scripts/report_platform_abuse.py --session SESSION_ID --platform PLATFORM
```

## Dashboard

```bash
uv run {baseDir}/server/main.py
```

Opens at `http://localhost:8147` — live session monitoring, intel database, report management, analytics.
