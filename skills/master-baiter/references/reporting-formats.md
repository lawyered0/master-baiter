# Report Format Specifications

Field-by-field specifications for each reporting destination. Report scripts populate these from session state, evidence chain, and intel database.

## FBI IC3 (Internet Crime Complaint Center)

**URL:** https://www.ic3.gov/
**Purpose:** Federal reporting for internet-enabled crime

### Required Fields

| Field | Source | Notes |
|---|---|---|
| Complaint Type | session.scam_type → IC3 code | See mapping below |
| Victim Info | REDACTED / anonymized | Never include real victim PII |
| Subject Name(s) | intel: type=name | All names extracted from conversation |
| Subject Email(s) | intel: type=email | All email addresses |
| Subject Phone(s) | intel: type=phone | All phone numbers |
| Incident Description | evidence chain summary | Narrative of scam progression |
| Date of Incident | session.created_at | First contact date |
| Financial Loss | $0 (no real money sent) | Note: AI scam baiter, no actual loss |

### IC3 Complaint Type Mapping

| Scam Type | IC3 Category |
|---|---|
| ROMANCE_SCAM | Romance/Confidence Fraud |
| ADVANCE_FEE | Advance Fee Fraud |
| CRYPTO_PIG_BUTCHERING | Cryptocurrency Fraud |
| TECH_SUPPORT | Tech Support Fraud |
| PHISHING | Phishing/Spoofing |
| SEXTORTION | Extortion |
| GOV_IMPERSONATION | Government Impersonation |
| MONEY_MULE | Money Laundering/Mule |
| EMPLOYMENT_SCAM | Employment Fraud |
| LOTTERY_SCAM | Lottery/Sweepstakes Fraud |

### Optional Fields

- Subject IP address (if available from platform metadata)
- Subject cryptocurrency wallets (intel: type=wallet)
- Subject bank accounts (intel: type=bank_account)
- Associated websites/URLs (logged but never visited)
- Method of initial contact (session.channel)

### Report Format Note
IC3 submission is done via their web form. Our report generates a structured markdown that maps 1:1 to the form fields for easy copy-paste submission.

---

## FTC (Federal Trade Commission)

**URL:** https://reportfraud.ftc.gov/
**Purpose:** Consumer fraud and unfair business practices

### Required Fields

| Field | Source | Notes |
|---|---|---|
| What Happened | evidence chain narrative | 3-5 paragraph summary |
| How Were You Contacted | session.channel | Platform/method |
| Person or Company | intel: names, aliases | Scammer's claimed identity |
| Contact Info Provided | intel: phone, email | Scammer's contact details |
| Amount Requested | extracted from messages | What the scammer asked for |
| Payment Method Requested | extracted from messages | Gift cards, wire, crypto, etc. |
| Did You Pay | No | AI baiter, no real payment |

### FTC Category Mapping

| Scam Type | FTC Category |
|---|---|
| ROMANCE_SCAM | Romance Scams |
| TECH_SUPPORT | Tech Support Scams |
| GOV_IMPERSONATION | Impersonator Scams → Government |
| EMPLOYMENT_SCAM | Job Scams |
| LOTTERY_SCAM | Prizes, Sweepstakes, Lotteries |
| CRYPTO_PIG_BUTCHERING | Investment Scams → Cryptocurrency |
| PHISHING | Identity Theft & Online Security |

---

## NCMEC CyberTipline

**URL:** https://report.cybertip.org/
**Purpose:** Reporting child sexual exploitation. MANDATORY for certain categories.

### ⚠️ CRITICAL CONSTRAINTS
- ONLY generate for predator detection cases (session.mode == "passive")
- ONLY generate at severity 4-5
- NEVER include actual CSAM — use text descriptions of content only
- This report triggers real law enforcement response

### Required Fields

| Field | Source | Notes |
|---|---|---|
| Incident Type | Classification | See types below |
| Date/Time of Incident | evidence chain timestamps | First predatory indicator |
| Reported Person Info | intel: all types | Everything extracted about subject |
| Platform/ESP | session.channel | Messaging platform used |
| Incident Narrative | evidence summary | Factual, clinical description |
| Content Description | evidence entries | TEXT ONLY — describe, never quote CSAM |

### NCMEC Incident Types

- Online Enticement (including sextortion of minors)
- Child Sexual Abuse Material (CSAM)
- Child Sex Trafficking
- Misleading Domain/URL
- Unsolicited Obscene Material Sent to a Child

### Required ESP (Electronic Service Provider) Information

| Field | Source |
|---|---|
| Service Name | session.channel (WhatsApp, Telegram, etc.) |
| URL of Content | Message links if available |
| User Account ID | session.sender_id |
| User Display Name | intel: type=name or type=username |
| Geographic Info | Any location data from conversation |

---

## Local Law Enforcement

**Purpose:** Direct tip to local police department with jurisdiction

### Email Format

**Subject line:** `[CYBER TIP] {scam_type} — Evidence of Internet {crime_category} via {channel}`

**Body structure:**

```
To: [Department] Cyber Crime Unit / Detective Division
From: [Operator name — filled in by human before sending]
Date: {generated_at}
Re: Internet {crime_category} — Suspect Communication via {channel}

INCIDENT SUMMARY
[2-3 paragraph narrative: what happened, how detected, why reporting]

SUSPECT IDENTIFYING INFORMATION
- Name(s): {intel: type=name}
- Phone(s): {intel: type=phone}
- Email(s): {intel: type=email}
- Online Handle(s): {intel: type=username}
- Cryptocurrency Wallet(s): {intel: type=wallet}
- Bank Account(s): {intel: type=bank_account}
- Platform Account: {channel} — {sender_id}

DIGITAL EVIDENCE SUMMARY
- Evidence chain: {evidence_count} entries, SHA-256 verified
- Date range: {first_entry} to {last_entry}
- Chain integrity: VERIFIED / BROKEN AT SEQ {n}
- Full transcript available upon request

RELEVANT STATUTES
[Based on scam type — see statute mapping below]

RECOMMENDED NEXT STEPS
[Based on evidence strength and scam type]
```

### Statute Mapping (Federal)

| Scam Type | Primary Statute |
|---|---|
| Wire/Bank Fraud | 18 U.S.C. § 1343 (Wire Fraud) |
| Romance Scam | 18 U.S.C. § 1343 + § 1028 (Identity Theft) |
| Crypto Fraud | 18 U.S.C. § 1343 + § 1956 (Money Laundering) |
| Sextortion | 18 U.S.C. § 873 (Extortion) |
| Gov Impersonation | 18 U.S.C. § 912 (Impersonating Federal Officer) |
| CSAM/Exploitation | 18 U.S.C. § 2251-2252 (Sexual Exploitation of Children) |
| Money Mule | 18 U.S.C. § 1956-1957 (Money Laundering) |
| Phishing | 18 U.S.C. § 1030 (Computer Fraud and Abuse Act) |

---

## Platform Abuse Reports

### WhatsApp
**URL:** In-app report or https://www.whatsapp.com/contact/
**Fields:** Phone number, conversation screenshots, description
**Note:** WhatsApp's report mechanism is in-app. Our report generates a summary suitable for email to abuse@whatsapp.com or Meta's law enforcement request portal.

### Telegram
**URL:** https://telegram.org/support or @notoscam bot
**Fields:** Username, chat ID, description, evidence
**Note:** Reports can go to abuse@telegram.org or via @notoscam in-app.

### Discord
**URL:** https://support.discord.com/hc/en-us/requests/new
**Fields:** User ID, server ID (if applicable), message links, description
**Report Type:** Trust & Safety → Harassment, Scams, or Child Safety

### Coinbase
**URL:** https://help.coinbase.com/en/contact-us
**Fields:** Wallet address, transaction hashes, description
**Compliance email:** compliance@coinbase.com
**Note:** For suspected fraud involving Coinbase wallets. Include all wallet addresses and any transaction IDs.

### Kraken
**URL:** https://support.kraken.com/
**Fields:** Wallet address, description, evidence
**Compliance email:** compliance@kraken.com

### Binance
**URL:** https://www.binance.com/en/support
**Fields:** Wallet address, transaction ID, description
**Law enforcement:** https://www.binance.com/en/support/law-enforcement

---

## Evidence Packaging Standards

All reports should reference:
1. **Evidence chain file path** (for operator to verify/attach)
2. **Chain integrity status** (verified by hash_verify.py)
3. **Entry count and date range**
4. **Intel items linked to this session**
5. **Cross-session links** (if applicable)

Reports are DRAFTS. The human operator must:
- Review for accuracy
- Redact any accidentally captured real PII
- Add their own contact information
- Submit via the appropriate channel (web form, email, etc.)
