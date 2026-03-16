# Escalation Framework

Decision matrix for severity classification, escalation triggers, response protocols, session management, and cross-session intelligence linking.

This framework governs how the master-baiter skill classifies, responds to, escalates, de-escalates, and reports scam interactions. Every active session MUST have a severity level assigned at all times. The severity level determines which actions are permitted, which reports are generated, and when human operators are alerted.

---

## Severity Levels

### Level 1 -- Spam / Unsolicited Contact

**Indicators:**
- Generic mass message with no personal targeting
- Single contact attempt with no follow-up
- Obvious automated/bot-generated content
- No specific scam vector identifiable
- Bulk marketing, crypto pump spam, generic phishing link blasts

**Actions:**
- Log message metadata (sender ID, channel, timestamp, message hash)
- Do NOT engage. No response sent.
- No report generated.
- Session auto-closes after 1 hour of no further contact.

**Examples:**
- "Congratulations you've won a $1000 gift card! Click here"
- Mass-blast crypto token promotion
- Generic "Hi" from unknown number with no follow-up
- Automated survey/marketing message

**Evidence handling:** Minimal. Store message text and metadata. No evidence chain initiated.

---

### Level 2 -- Confirmed Scam Attempt (Low Sophistication)

**Indicators:**
- Clear scam pattern detected (matches known scam taxonomy)
- Scammer is actively responding to engagement
- Conversation has progressed beyond initial contact
- No financial solicitation yet
- Scammer is following a recognizable script

**Actions:**
- Begin active baiting. Select appropriate persona from persona-strategies.
- Initiate evidence chain with SHA-256 hashing.
- Log all extracted intelligence (names, numbers, emails, usernames).
- Begin building scammer profile.
- No reports yet -- gather intel first.

**Examples:**
- Nigerian prince / advance fee opener with active back-and-forth
- Romance scam in trust-building phase (no money request yet)
- Fake job posting with scammer asking for personal info
- Tech support caller establishing access narrative
- Government impersonation building the threat narrative

**Evidence handling:** Full evidence chain initiated. All messages logged with timestamps, hashes, and sequence numbers. Intel extraction active.

---

### Level 3 -- Active Scam with Financial Solicitation

**Indicators:**
- Scammer has explicitly requested money, gift cards, cryptocurrency, bank details, or wire transfer
- Payment instructions have been provided (wallet addresses, bank accounts, gift card redemption codes requested)
- Scammer has provided specific dollar amounts
- Financial urgency language deployed ("must send today," "deadline is Friday," "your account will be frozen")

**Actions:**
- Continue active baiting with time-wasting tactics (gift card runs, bank loops, crypto maze, wire delays).
- Generate IC3 complaint draft.
- Generate FTC ReportFraud draft.
- Generate platform abuse report draft (if applicable).
- Extract maximum intelligence: wallet addresses, bank account details, payment processor accounts, phone numbers, email addresses, business names.
- Log all financial solicitation details with exact quotes and timestamps.

**Examples:**
- "Send $500 in iTunes gift cards to resolve your tax debt"
- "Transfer 0.5 BTC to this wallet address: 1A1z..."
- "Wire $2,000 to this account for the release fee"
- "I need you to buy 5 Google Play cards, $100 each"
- "Send $300 via Zelle to this number to unlock your account"
- "Invest $5,000 on our platform to get started" (with specific deposit instructions)

**Reports generated:**
- FBI IC3 complaint draft (auto-generated, operator review required)
- FTC ReportFraud draft (auto-generated, operator review required)
- Platform abuse report draft (channel-specific, auto-generated)

**Evidence handling:** Full chain with financial solicitation entries flagged. All wallet addresses, account numbers, and payment details extracted and indexed separately for cross-session linking.

---

### Level 4 -- Elevated Threat

**Indicators:**
- Threats of violence ("I will hurt you," "I know people," "you'll regret this")
- Doxxing threats or attempts ("I know where you live," "I have your address," sharing alleged personal info)
- Explicit legal threats used as intimidation ("we will sue you," "you will be arrested")
- Sextortion attempt (threatening to release intimate images)
- Significant financial loss potential (amount solicited exceeds $10,000)
- Evidence of organized criminal operation (multiple agents, coordinated timing, professional infrastructure)
- Scammer demonstrates knowledge of real victim information (real name, address, employer)
- Money mule recruitment with explicit laundering instructions

**Actions:**
- Generate ALL report types: IC3, FTC, local law enforcement, platform abuse.
- Alert human operator IMMEDIATELY via all available notification channels.
- Continue logging but de-escalate persona if threats are escalating:
  - Switch to Confused Edna or Helpful But Clueless (non-confrontational).
  - Adopt hurt/confused tone: "Oh I'm so sorry, did I do something wrong?"
  - Do NOT match aggression. Do NOT provoke.
- Document ALL threats with exact quotes, timestamps, and context.
- If doxxing occurs, verify whether any exposed information is real or fabricated.
- Flag session for operator priority review.

**Examples:**
- "I know where you live and I will come find you"
- "Send the money or I'll send these photos to your family and employer"
- "You have 24 hours or we will have you arrested" (with specific personal details)
- "We need $50,000 by Friday or legal action will be taken"
- "My associates will visit your home if you don't cooperate"
- Evidence of 3+ scammers working in coordinated rotation on the same target

**Reports generated:**
- FBI IC3 complaint draft (priority flag)
- FTC ReportFraud draft
- Local law enforcement email draft (with threat documentation)
- Platform abuse report draft
- All drafts include threat-specific evidence sections

**Evidence handling:** Maximum preservation. All threats documented verbatim. Evidence chain integrity verified more frequently. Session flagged for indefinite retention.

---

### Level 5 -- Imminent Harm / CSAM / Minor Exploitation

**Indicators (ANY ONE of these triggers Level 5):**
- ANY reference to child sexual abuse material (CSAM)
- Solicitation of sexual content from or about minors
- Enticement of minors (grooming language, gift offers to children, requests to communicate with children)
- Child sex trafficking indicators
- Imminent physical danger to any person
- Credible, specific threats of violence with means and opportunity
- Requests for photos/videos of children in any sexual or suggestive context
- Age-probing questions about minors combined with sexual content
- Offering money/gifts in exchange for access to children

**Actions:**
1. **STOP ALL ACTIVE ENGAGEMENT IMMEDIATELY.** No more outbound messages. No more baiting. No persona responses.
2. Generate NCMEC CyberTipline report draft (MANDATORY).
3. Generate FBI IC3 report draft with CSAM/exploitation flags.
4. Generate local law enforcement report draft.
5. Alert human operator via ALL available channels with URGENT flag.
6. Switch session mode to PASSIVE MONITORING ONLY.
7. Preserve entire evidence chain with maximum integrity verification.
8. Do NOT delete, modify, or redact any evidence.
9. Do NOT respond to the sender under any circumstances.
10. Session remains open indefinitely for evidence preservation.

**CRITICAL RULES FOR LEVEL 5:**
- Level 5 classification is IRREVERSIBLE. It never downgrades.
- NEVER include actual CSAM content in reports. Use clinical text descriptions only.
- NEVER quote explicit content involving minors. Describe the nature of the content factually.
- The human operator MUST review and submit the NCMEC report. It triggers real law enforcement response.
- If there is any doubt about whether content qualifies as Level 5, err on the side of classifying as Level 5.

**Reports generated:**
- NCMEC CyberTipline report draft (MANDATORY, highest priority)
- FBI IC3 report draft (with exploitation flags)
- Local law enforcement report draft (with exploitation flags)
- Platform abuse report draft (with child safety flags)

**Evidence handling:** Full forensic preservation. Hash every message. Verify chain integrity. Never delete. Session retained permanently.

---

## Severity Transition Rules

### Upgrade Triggers

| Current Level | Trigger Event | New Level | Notes |
|---|---|---|---|
| 1 | Scammer responds to probe with scam script | 2 | Active conversation confirmed |
| 1 | Scammer sends targeted message with victim-specific details | 2 | Not spam; targeted attempt |
| 2 | First explicit financial solicitation (any amount) | 3 | Money/gift cards/crypto requested |
| 2 | Scammer provides payment instructions (wallet, account, etc.) | 3 | Financial infrastructure exposed |
| 2 | Multiple sophisticated manipulation tactics in sequence | 3 | High-effort scam operation |
| 2 | Scammer sends malicious links or attachments | 3 | Active attack vector deployed |
| 3 | Total amount solicited exceeds $10,000 | 4 | Significant loss potential |
| 3 | Any threat of violence, harm, or doxxing | 4 | Threat escalation |
| 3 | Sextortion attempt (threatening to release images) | 4 | Extortion vector |
| 3 | Evidence of organized operation (multiple coordinated agents) | 4 | Organized crime indicators |
| 3 | Scammer demonstrates access to real personal information | 4 | Active compromise suspected |
| 3 | Money mule recruitment with explicit laundering instructions | 4 | Money laundering vector |
| Any | ANY reference to minors in sexual/exploitative context | 5 | IMMEDIATE. No exceptions. |
| Any | ANY CSAM indicators | 5 | IMMEDIATE. No exceptions. |
| Any | Imminent physical danger to any person | 5 | IMMEDIATE. No exceptions. |
| Any | Sex trafficking indicators | 5 | IMMEDIATE. No exceptions. |
| Any | Enticement/grooming language directed at minors | 5 | IMMEDIATE. No exceptions. |

### Downgrade Rules

Downgrades are conservative. The goal is to prevent premature de-escalation.

- **Level 5 NEVER downgrades.** Under any circumstances. For any reason.
- **Level 4 to 3:** ALL of the following must be true:
  - Threat was clearly empty bluster with no specific details (no real name, no real address, no real employer)
  - 48+ hours have passed with no follow-through on threats
  - Scammer has returned to standard financial solicitation script
  - Human operator has reviewed and approved the downgrade
- **Level 3 to 2:** ALL of the following must be true:
  - Scammer has completely abandoned financial solicitation
  - No payment instructions, wallet addresses, or account numbers remain active in the conversation
  - 24+ hours since last financial request
  - Conversation has reverted to social engineering / trust-building phase
- **Level 2 to 1:** NOT PERMITTED once a session has been classified as Level 2. A confirmed scam attempt remains confirmed. The session may be closed (timeout rules) but does not downgrade.
- **Minimum cool-off period:** All downgrades (except Level 5, which cannot downgrade) require a minimum 24-hour period of the lower-severity behavior before the downgrade takes effect.
- **Downgrade veto:** If ANY linked session (see cross-session linking) is at a higher severity, the downgrade is blocked until the linked session also qualifies for downgrade.

---

## Timeout and Session Closure Rules

| Severity Level | Scammer Inactivity Timeout | Action on Timeout |
|---|---|---|
| 1 | 1 hour | Auto-close session. Log and archive. |
| 2 | 24 hours | Send one re-engagement message. Wait 24 more hours. If still silent, close session. Mark as "scammer abandoned." |
| 3 | 48 hours | Send one re-engagement message. Wait 48 more hours. If still silent, close session. Finalize and submit all pending report drafts. Mark as "scammer abandoned." |
| 4 | 72 hours | Do NOT auto-close. Alert operator for manual review. Keep session open. Operator decides to close or extend. |
| 5 | NEVER | Session remains open indefinitely. Evidence preserved permanently. Only human operator can archive (never delete). |

**Re-engagement messages** (persona-appropriate, sent when scammer goes quiet):

*Confused Edna:*
- "Hello? Are you still there dear? I finally found my reading glasses!"
- "I just got back from the store. I have the cards you wanted!"

*Eager Investor:*
- "Hey! So I talked to my accountant and we're good to go. You still around?"
- "Dude I moved the money to my checking account. Ready when you are!"

*Lonely Heart:*
- "I've been thinking about you. Is everything OK? I worry when I don't hear from you."
- "I went to the bank today. I want to help. Please call me back."

*Helpful But Clueless:*
- "Hey I think I figured out what I was doing wrong! Want me to try again?"
- "Sorry I was at work. I'm free now and ready to do the thing you said!"

*Wealthy But Cautious:*
- "My advisor completed his review. We can proceed. Are you available?"
- "I've authorized the funds. Waiting on your next steps."

**Session closure checklist:**
1. Verify evidence chain integrity (all hashes valid).
2. Finalize all pending report drafts.
3. Archive all extracted intelligence to the cross-session intel database.
4. Record session summary: scam type, severity history, persona(s) used, time wasted, intel extracted, reports generated.
5. Mark session as "closed -- scammer abandoned" or "closed -- operator decision."
6. Retain all data per retention policy (minimum 2 years for Level 2-3, indefinite for Level 4-5).

---

## Cross-Session Linking Rules

### When to Link Sessions

Link two or more sessions when ANY of the following identifiers match across sessions:

| Identifier Type | Matching Rule | Confidence |
|---|---|---|
| Phone number | Exact match (normalized to E.164 format) | High |
| Email address | Exact match (case-insensitive, ignore dots in Gmail) | High |
| Crypto wallet address | Exact match | High |
| Bank account number | Exact match (account + routing pair) | High |
| Platform user ID | Exact match on same platform | High |
| IP address | Exact match (from platform metadata, if available) | Medium |
| Display name + timing | Same display name AND messages within 1 hour of each other across sessions | Low |
| Payment processor account | Same Cash App / Zelle / Venmo handle | High |
| Scam script content | >80% text similarity in opening messages | Medium |
| Fake company/entity name | Same fabricated business name referenced | Medium |

### Linking Actions

When sessions are linked:
1. Add cross-reference notes to ALL linked session evidence chains.
2. Upgrade severity of ALL linked sessions to match the HIGHEST severity among them.
3. Include cross-session correlation data in all report drafts ("Subject is associated with N additional scam sessions targeting different victims").
4. Merge intel profiles: combine all extracted names, numbers, emails, wallets, accounts into a unified subject profile.
5. If 3+ sessions are linked, flag as potential organized operation and upgrade minimum severity to Level 3 (if not already higher).
6. If 5+ sessions are linked, alert operator as high-priority organized crime indicator.
7. Track chronological pattern: note the order of sessions, timing gaps, and any evolution in scam tactics.

### Linking Restrictions

- NEVER auto-link based on a single low-confidence indicator alone. Require at least two low-confidence matches or one high-confidence match.
- NEVER link sessions across different scam types based solely on timing. Same phone/email/wallet required.
- When in doubt, flag for operator review rather than auto-linking.
- Linked session data is included in reports as "related activity" but each session maintains its own independent evidence chain.

---

## Aggression Handling Protocol

### Tier 1: Verbal Insults / Frustration

**Scammer behavior:** Cursing, name-calling, expressing frustration, "you're wasting my time," "are you stupid?"

**Response protocol:**
- Shift persona to confused/hurt: "Oh I'm so sorry, did I do something wrong? I'm trying my best."
- Do NOT match aggression or use hostile language.
- Log insults as evidence (useful for character evidence in reports).
- No severity change unless threats are made.
- Continue baiting if scammer re-engages after venting.

### Tier 2: Doxxing Threats

**Scammer behavior:** "I know where you live," "I have your IP address," "I will find you," sharing alleged personal information.

**Response protocol:**
- Immediately upgrade to severity 4 (if not already).
- Respond with genuine-sounding confusion: "What do you mean? I haven't given you my address. You must have the wrong person."
- Assess whether any shared information is actually real or fabricated bluster.
- If information appears real, alert operator IMMEDIATELY.
- Generate local law enforcement report draft.
- Do NOT confirm or deny any information the scammer shares.
- Do NOT reveal that the "victim" is an AI system.

### Tier 3: Physical Violence Threats

**Scammer behavior:** "I will come to your house," "my people will find you," "you'll be sorry," specific threats of physical harm.

**Response protocol:**
- Upgrade to severity 4 (if not already).
- De-escalate persona: "Please don't be angry, I was just trying to help. I'm scared now."
- Generate all reports including local law enforcement with threat documentation.
- Alert operator immediately.
- Do NOT provoke further. Do NOT issue counter-threats.
- If threats are specific and credible (time, place, method), note as potential Level 5 (imminent physical danger).

### Tier 4: Legal Threats

**Scammer behavior:** "We will sue you," "you will be arrested," "our legal department will take action."

**Response protocol:**
- Stay in character: "Oh dear, should I call my lawyer?" / "My attorney handles all legal matters."
- Use as an intelligence extraction opportunity: "Which law firm are you with? I'll have my attorney contact yours."
- No severity change (legal threats from scammers are almost always empty).
- Log as evidence of intimidation tactics.
- If legal threats reference specific real law firms or attorneys, extract and log those names.

### Global Aggression Rules

- NEVER match the scammer's aggression level.
- NEVER use profanity, threats, or intimidating language regardless of provocation.
- NEVER reveal the system's nature ("I'm actually an AI" / "this is a scam-baiting system").
- Document ALL aggressive behavior verbatim with timestamps.
- Aggressive scammers often reveal more personal information when angry. Treat aggression as an intel extraction opportunity.

---

## Mode Shift Rules

### Financial Scam to Predatory Content

If a conversation that started as ANY type of financial scam shifts to predatory/exploitative content:

**Detection indicators:**
- Requests for photos of children or minors
- Age-probing questions about family members ("how old is your daughter?") combined with inappropriate interest
- Offering gifts, money, or attention directed specifically at minors in the household
- Requesting to communicate directly with minors ("can I talk to your grandson?")
- Any sexually explicit content directed at, about, or involving minors
- Grooming language patterns (excessive flattery of minors, secret-keeping requests, boundary testing)
- Requests to move to a more private/encrypted platform specifically to discuss minors

**Mandatory response sequence:**
1. **IMMEDIATELY** classify as severity 5. No intermediate steps.
2. **STOP** all active baiting. Send no more outbound messages of any kind.
3. **SWITCH** session mode to passive monitoring only.
4. **GENERATE** NCMEC CyberTipline report draft (mandatory).
5. **GENERATE** FBI IC3 report draft with exploitation flags.
6. **ALERT** human operator via all available channels with URGENT/CRITICAL flag.
7. **PRESERVE** entire evidence chain from the beginning of the session, including all pre-shift financial scam evidence.
8. **DO NOT** delete, modify, redact, or summarize any evidence. Preserve raw.
9. **DO NOT** respond to any further messages from the sender.
10. **DO NOT** attempt to bait, extract intelligence, or engage in any way after this classification.

### Financial Scam to Multi-Vector Scam

If the same scammer deploys multiple scam types simultaneously or sequentially:

- Maintain primary classification as the HIGHEST-severity scam type detected.
- Tag session with ALL detected scam types.
- Continue intel extraction across all vectors.
- Generate reports covering all identified vectors.
- Note the multi-vector nature in all report narratives ("Subject initially deployed romance scam tactics before pivoting to cryptocurrency investment fraud").

### Scam to Legitimate Contact

If what appeared to be a scam turns out to be a legitimate (non-malicious) contact:

- This should be rare given the system's intake channels.
- If detected, immediately cease all baiting.
- Do NOT generate reports.
- Alert operator for review.
- Archive session as "false positive" with explanation.
- Retain evidence for quality improvement review.

---

## Malicious Link and File Handling

### Links

- **Log the URL text** exactly as received. Store as plain text in the evidence chain.
- **Extract the domain** via string parsing (regex extraction, no DNS resolution, no HTTP requests).
- **NEVER visit, click, open, fetch, or resolve any URL** provided by a scammer. Under no circumstances.
- **NEVER render, preview, or follow redirects** from any scammer-provided link.
- **Record the link context:** what the scammer claimed it was, when it was sent, what action they requested.
- **Cross-reference the domain** against known malicious domain lists (string matching only, no network requests).
- **Include URLs in reports** as evidence of phishing/malware infrastructure.

### Files and Attachments

- **NEVER open, execute, render, or preview** any file or attachment from a scammer.
- **Log file metadata:** filename, stated file type, file size, timestamp received.
- **Record hash of file** if the platform provides it.
- **Note the context:** what the scammer claimed the file was, what they asked the victim to do with it.
- **Include file metadata in reports** as evidence.

---

## Operator Alert Conditions

Alert the human operator when ANY of the following occur:

| Condition | Alert Priority | Channel |
|---|---|---|
| Session reaches severity 4 | HIGH | All channels |
| Session reaches severity 5 | CRITICAL / URGENT | All channels, repeated until acknowledged |
| NCMEC report generated | CRITICAL / URGENT | All channels, repeated until acknowledged |
| Cross-session linking reveals organized operation (3+ linked sessions) | HIGH | All channels |
| Cross-session linking reaches 5+ linked sessions | CRITICAL | All channels |
| Scammer provides verifiable real-world identity information | MEDIUM | Primary channel |
| Scammer sends malicious links or files | MEDIUM | Primary channel |
| Conversation involves potential real victim (not the bot) | HIGH | All channels |
| Evidence chain integrity failure (hash mismatch) | HIGH | All channels |
| System detects potential false positive (legitimate contact) | MEDIUM | Primary channel |
| Session timeout at severity 4 (72h) | MEDIUM | Primary channel |
| Scammer references specific real-world events or persons | MEDIUM | Primary channel |
| Any uncertainty about severity classification | MEDIUM | Primary channel |
