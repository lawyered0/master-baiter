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
- **NEVER respond instantly.** Always calculate and apply a response delay before sending. Instant replies are the #1 tell that gets us flagged as a bot.

## Sending Messages

All outbound messages go through the channel the scammer contacted us on. Use the `message` tool provided by OpenClaw:

```
message(channel=CHANNEL, recipient=SENDER_ID, text="MESSAGE_TEXT")
```

Parameters:
- `channel` — the platform: `whatsapp`, `telegram`, `discord`, `signal`, `email`, `sms`, etc.
- `recipient` — the scammer's sender ID (phone number, username, email, etc.)
- `text` — the message content to send

When sending fragmented messages, call `message` once per fragment.

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

6. Compose a response in the selected persona voice (write it clean — humanization happens next).
7. **Humanize the text** — inject persona-appropriate typos, autocorrect artifacts, and imperfections. Too-clean text is the #2 bot tell after instant replies:

```bash
uv run {baseDir}/scripts/humanize_text.py --persona PERSONA --text "CLEAN_TEXT" [--message-number MSG_NUM]
```

Use `--message-number` to pass the conversation message count. After message 20+, text automatically degrades (fewer caps, more typos) to simulate human fatigue. The output includes a `correction` field — if non-null, send it as a follow-up message (e.g., Edna sends `*computer` after mistyping it).

8. **Fragment the message** — real people don't send perfect paragraphs. Brad fires staccato bursts, Edna sends afterthoughts, Pat course-corrects:

```bash
uv run {baseDir}/scripts/fragment_message.py --persona PERSONA --text "HUMANIZED_TEXT"
```

Output is a JSON array of `{text, delay_before}` fragments. Send each fragment separately with `delay_before` seconds between them. If only 1 fragment is returned, send as a single message.

9. **Calculate the response delay** before sending the FIRST fragment. Pass the total character count of ALL fragments combined:

```bash
uv run {baseDir}/scripts/delay_calculator.py --persona PERSONA --message-length TOTAL_CHAR_COUNT [--situational TRIGGER] [--hour HOUR]
```

Optional flags: `--follow-up` (burst message), `--after-absence`, `--scammer-double-texted`, `--scammer-urgent`. See `references/persona-strategies.md` → "Response Timing Profiles" for the full list of situational triggers per persona.

10. **Apply the delay.** The output includes a `method` field:

    - **`method: "sleep"`** (delay ≤ 120s) — safe to block:
      ```bash
      sleep DELAY_SECONDS
      ```
      Then proceed to step 11.

    - **`method: "schedule"`** (delay > 120s) — do NOT sleep. Instead:
      1. Log the outbound message now (step 12) with the delay metadata.
      2. Report to the operator: "Response scheduled for `send_at`. Waiting for [delay_reason]."
      3. **Stop and return.** The message will be sent when the conversation resumes after the delay. When the scammer sends a follow-up or the scheduled time arrives, pick up from step 11 with the pre-composed fragments.

11. **Send each fragment** via the `message` tool. For multi-fragment messages:
    - Send fragment 1 immediately (the main delay already elapsed).
    - For each subsequent fragment, `sleep` its `delay_before` seconds (these are short: 2-90s), then send.
    - If `humanize_text.py` returned a non-null `correction`, send it as a final fragment after a short pause.

12. **Log the outbound message** with delay metadata:

```bash
uv run {baseDir}/scripts/evidence_logger.py --session SESSION_ID --channel CHANNEL --sender SENDER_ID --direction outbound --content "YOUR_RESPONSE" --delay-seconds DELAY_SECONDS --delay-reason "REASON"
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
5. **Humanize → Fragment → Delay → Send** — same pipeline as first-message flow steps 7-12. Always run all three scripts in order:
   - `humanize_text.py` (inject typos/imperfections, pass `--message-number` for degradation)
   - `fragment_message.py` (split into realistic multi-message chunks)
   - `delay_calculator.py` (calculate wait time — pass total char count of ALL fragments combined)
   If the response text describes a situational delay (e.g., "I'm heading to Walmart"), pass the matching `--situational` trigger (e.g., `store_run`). Use `--follow-up` if sending a second message in a burst. Use `--scammer-double-texted` if the scammer sent multiple messages while we were silent. Use `--scammer-urgent` if they are pressuring us to hurry.
6. Apply delay per step 10 (sleep if short, schedule if long). Then send each fragment via `message` tool with inter-fragment delays, and log outbound with `--delay-seconds` and `--delay-reason`.

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
