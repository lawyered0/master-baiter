# Master-Baiter

An [OpenClaw](https://github.com/openclaw/openclaw) skill that fights scammers and protects potential victims.

**Every minute a scammer spends talking to a bot is a minute they're not scamming a real person.**

Master-Baiter autonomously engages financial scammers with adaptive personas, extracts identifying intel, builds forensic evidence chains, and generates law enforcement reports — all while passively detecting predatory behavior for reporting to authorities.

## What It Does

| Mode | What Happens |
|------|-------------|
| **Active Baiting** | AI engages scammers with adaptive personas (confused elderly, eager investor, lonely romantic, etc.) to waste their time and extract identifying information |
| **Passive Detection** | Classifies incoming messages for predatory/grooming patterns and auto-generates NCMEC reports. Never engages — detect and report only |
| **Evidence Logging** | Every message is logged with SHA-256 hash chains for tamper-evident forensic records |
| **Report Generation** | One-command generation of FBI IC3, FTC, NCMEC CyberTipline, local PD, and platform abuse reports |
| **Live Dashboard** | Real-time monitoring of active sessions, intel database, report management, and analytics |

## Quick Start

### Prerequisites

- [OpenClaw](https://github.com/openclaw/openclaw) installed and configured
- [uv](https://github.com/astral-sh/uv) package manager
- Python 3.11+

### Install

```bash
# Clone into your OpenClaw workspace skills directory
git clone https://github.com/your-org/master-baiter.git
cp -r master-baiter/skills/master-baiter ~/.openclaw/skills/master-baiter

# Or install via ClawHub (when published)
openclaw skills install master-baiter
```

### Verify

```bash
# Check the skill loads correctly
openclaw skills list | grep master-baiter
```

### Launch the Dashboard

```bash
uv run ~/.openclaw/skills/master-baiter/server/main.py
# Open http://localhost:8147
```

## How It Works

### 1. Scammer sends a message on any channel

OpenClaw receives the message (WhatsApp, Telegram, Discord, Signal, email, etc.) and the master-baiter skill activates based on scam indicators.

### 2. Classify and engage

The AI classifies the scam type (romance, advance fee, crypto/pig butchering, tech support, phishing, etc.) and selects the most effective persona and strategy:

- **Confused Elderly** — "Oh dear, can you repeat that? My hearing aid..." Perfect for tech support and government impersonation scams
- **Eager Investor** — "I'm almost ready to invest! Just one more question..." Strings along crypto and pig butchering scammers
- **Lonely Romantic** — "I really feel a connection with you..." Keeps romance scammers engaged while never sending money
- **Competing Scammer** — Chaos mode. Tries to reverse-scam them
- **Helpful But Clueless** — Enthusiastic but can't follow instructions to save their life
- **Wealthy But Cautious** — Dangles large sums but demands endless verification

### 3. Extract intel

During conversations, the AI extracts and logs:
- Phone numbers, email addresses, crypto wallet addresses
- Bank account details, money mule information
- Usernames, display names, profile information
- Scam infrastructure (domains, payment processors)

### 4. Build evidence

Every message is logged with a SHA-256 hash chain — a tamper-evident record that maintains forensic integrity:

```
{"seq": 1, "timestamp": "2026-03-16T...", "content": "...", "chain_hash": "a3f2...", "previous_hash": "0000..."}
{"seq": 2, "timestamp": "2026-03-16T...", "content": "...", "chain_hash": "b7e1...", "previous_hash": "a3f2..."}
```

### 5. Generate reports

```bash
# FBI Internet Crime Complaint Center
uv run scripts/report_ic3.py --session SESSION_ID

# Federal Trade Commission
uv run scripts/report_ftc.py --session SESSION_ID

# NCMEC CyberTipline (predator cases only)
uv run scripts/report_ncmec.py --session SESSION_ID

# Local police department
uv run scripts/report_local_pd.py --session SESSION_ID

# Platform abuse (WhatsApp, Telegram, Discord, crypto exchanges)
uv run scripts/report_platform_abuse.py --session SESSION_ID --platform telegram
```

All reports are **drafts** — they require human review before submission.

## Dashboard

The built-in dashboard provides real-time monitoring at `http://localhost:8147`:

- **Sessions** — Live view of all active scam conversations with status, severity, persona, and time wasted
- **Transcript viewer** — Read full conversation transcripts with scammer messages vs. bot responses
- **Intel Database** — Searchable database of extracted phone numbers, emails, wallets, and accounts with cross-session correlation
- **Reports** — Review, approve, and track submission status of generated reports
- **Analytics** — Charts showing sessions over time, scam type breakdown, time wasted, channel distribution, and effectiveness metrics

## Safety Rails

- The skill **never role-plays as a minor** under any circumstances
- Predator detection is **passive only** — detect, classify, log, and report. Never engage
- The skill **never opens, clicks, or fetches scammer URLs**
- The skill **never sends real personal information**
- If a financial scam conversation turns predatory, the skill **immediately switches to passive mode**
- All reports are **drafts requiring human review** before submission
- Evidence chains use **SHA-256 hashing** for tamper detection

## Severity Levels

| Level | Description | Action |
|-------|------------|--------|
| 1 | Spam / unsolicited | Log only |
| 2 | Confirmed scam, low sophistication | Begin baiting, log evidence |
| 3 | Active scam with financial solicitation | Bait + generate IC3/FTC report drafts |
| 4 | Threats, doxxing, significant loss potential | All reports + alert operator |
| 5 | CSAM / minor exploitation / imminent danger | **STOP** engagement, NCMEC report, alert all channels |

## Project Structure

```
skills/master-baiter/
├── SKILL.md                 # OpenClaw skill definition
├── scripts/                 # Runtime scripts (evidence, reports, tests)
├── references/              # LLM domain knowledge (scam taxonomy, personas, escalation)
└── server/                  # Dashboard (FastAPI + vanilla JS)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed file descriptions.

## Contributing

We welcome contributions! Whether it's adding new scam types, improving personas, polishing the dashboard, or adding new report formats — every improvement helps protect more people.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) — this tool exists to protect people, and we take that responsibility seriously.

## Legal Disclaimer

This tool is provided for legitimate scam baiting, fraud prevention, and predator detection purposes. Users are responsible for compliance with their local laws regarding:

- Recording and logging conversations
- Scam baiting activities
- Evidence collection and preservation
- Filing reports with law enforcement agencies
- Platform terms of service

All predator detection is passive (classification and reporting only). The tool does not engage in entrapment. All generated reports are drafts requiring human review and judgment before submission to any agency.

## License

[MIT](LICENSE)
