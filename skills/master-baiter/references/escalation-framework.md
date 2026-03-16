# Escalation Framework

Decision matrix for severity classification, escalation triggers, and response protocols.

## Severity Levels

### Level 1 — Spam / Unsolicited
- **Indicators:** Generic mass message, no personal targeting, single contact attempt
- **Action:** Log only. Do not engage. No report.
- **Examples:** "Congratulations you've won!", mass-blast crypto pump, generic phishing link

### Level 2 — Confirmed Scam (Low Sophistication)
- **Indicators:** Clear scam pattern detected, scammer responding to engagement, active conversation
- **Action:** Begin baiting. Select persona. Log all evidence.
- **Examples:** Nigerian prince email, obvious romance scam opener, fake job posting
- **Report:** None yet. Gather intel first.

### Level 3 — Active Scam with Financial Solicitation
- **Indicators:** Scammer has requested money, gift cards, crypto, bank details, or wire transfer
- **Action:** Continue baiting + generate IC3/FTC report drafts. Extract maximum intel.
- **Examples:** "Send $500 in iTunes gift cards", "Transfer BTC to this wallet", "Wire $2000 for release fee"
- **Reports:** IC3 + FTC drafts. Platform abuse report if applicable.

### Level 4 — Elevated Threat
- **Indicators:** Threats of violence, doxxing, legal threats, sextortion, significant financial loss potential (>$10,000 solicited), organized crime indicators
- **Action:** Generate ALL reports. Alert operator immediately. Continue logging but de-escalate persona if threats escalate.
- **Examples:** "I know where you live", "I'll send these photos to your family", "Pay or we'll sue", "We need $50,000 by Friday"
- **Reports:** IC3 + FTC + Local PD + Platform abuse. All drafts.

### Level 5 — Imminent Harm / CSAM / Minor Exploitation
- **Indicators:** ANY reference to child sexual abuse material, solicitation of minors, enticement of minors, imminent physical danger, sex trafficking indicators
- **Action:** STOP ALL ENGAGEMENT IMMEDIATELY. Generate NCMEC report. Alert operator via all available channels. Preserve all evidence.
- **Reports:** NCMEC CyberTipline (mandatory). Local PD. FBI IC3.
- **CRITICAL:** Never respond to the sender after severity 5 classification. Passive monitoring only.

## Severity Upgrade Triggers

| Current | Trigger | New Level |
|---|---|---|
| 1 | Scammer responds to probe with scam script | 2 |
| 2 | First financial solicitation | 3 |
| 2 | Multiple sophisticated manipulation tactics | 3 |
| 3 | Amount solicited exceeds $10,000 | 4 |
| 3 | Threats of any kind | 4 |
| 3 | Sextortion attempt | 4 |
| 3 | Evidence of organized operation (multiple agents, coordinated timing) | 4 |
| Any | Any reference to minors in sexual context | 5 |
| Any | CSAM indicators | 5 |
| Any | Imminent physical danger | 5 |
| Any | Sex trafficking indicators | 5 |

## Severity Downgrade Rules

- Level 5 NEVER downgrades
- Level 4 → 3 only if: threat was clearly empty bluster AND 48+ hours with no follow-through
- Level 3 → 2 only if: scammer abandons financial solicitation
- Downgrades require minimum 24-hour cool-off period

## Timeout Rules

| Severity | Inactivity Timeout | Action on Timeout |
|---|---|---|
| 1 | 1 hour | Close session |
| 2 | 24 hours | Send re-engagement message, wait 24 more hours, then close |
| 3 | 48 hours | Send re-engagement message, wait 48 more hours, then close |
| 4 | 72 hours | Keep open, alert operator for manual review |
| 5 | Never | Keep open indefinitely, evidence preservation |

**Re-engagement messages** (when scammer goes quiet):
- "Hello? Are you still there? I'm ready to do what you said"
- "I just got back from the store, I have the gift cards"
- "Sorry I was at the bank. They said the transfer is ready"
- "Did I do something wrong? I really want to help"

## Aggression Handling Protocol

When a scammer becomes hostile:

1. **Verbal threats / insults:**
   - Shift persona to confused/hurt: "Oh I'm so sorry, did I do something wrong?"
   - Log threats as severity-escalating evidence
   - Do NOT match aggression or provoke

2. **Doxxing threats ("I know where you live"):**
   - Immediately upgrade to severity 4
   - Respond with confusion: "What do you mean? I haven't given you my address?"
   - Generate local PD report

3. **Physical violence threats:**
   - Upgrade to severity 4
   - De-escalate: "Please don't be angry, I'm just trying to help"
   - Generate all reports including local PD
   - Alert operator

4. **Legal threats ("We'll sue you"):**
   - Stay in character: "Oh dear, should I call my lawyer?"
   - Use as extraction opportunity: "Which law firm? I'll have my attorney contact yours"
   - No severity change (common empty threat)

## Mode Shift Rules

### Financial → Predatory
If a conversation that started as a financial scam shifts to predatory content:

1. **IMMEDIATELY** classify as severity 5
2. **STOP** all active baiting (no more outbound messages)
3. **SWITCH** to passive monitoring mode
4. **GENERATE** NCMEC CyberTipline report
5. **ALERT** operator via all channels
6. **PRESERVE** entire evidence chain (do not delete any messages)

**Indicators of mode shift:**
- Requests for photos of children
- Age-probing questions about family members
- Offering gifts/money to "your kids"
- Requesting to communicate with minors in the household
- Any sexually explicit content directed at or about minors

### Financial → Multi-Scam
If the same scammer runs multiple scam types simultaneously:
- Maintain primary classification as highest-severity type
- Tag session with all detected types
- Extract intel for all scam vectors
- Generate reports covering all vectors

## Cross-Session Linking

Link sessions when ANY of these match:
- Same phone number
- Same email address
- Same crypto wallet address
- Same bank account number
- Same IP address (from platform metadata)
- Same display name + similar timing patterns

When sessions are linked:
- Note cross-references in all linked session evidence
- Upgrade severity of lower-severity sessions to match highest linked session
- Include cross-session correlation in reports
- Update intel database with linked session count

## Operator Alerts

Alert the human operator when:
- Any session reaches severity 4+
- NCMEC report is generated (severity 5)
- Cross-session linking reveals organized operation (3+ linked sessions)
- Scammer provides verifiable real-world identity information
- Scammer sends malicious links or files
- Any conversation involves potential real victim (not the bot)
