# Report Format Specifications

Field-by-field specifications for each reporting destination. Report generators populate these fields from session state, evidence chain, and intel database. All reports are DRAFTS that require human operator review before submission.

---

## FBI IC3 (Internet Crime Complaint Center)

**Submission URL:** https://www.ic3.gov/
**Form URL:** https://complaint.ic3.gov/default.aspx
**Purpose:** Federal reporting for internet-enabled crime. IC3 is a partnership between the FBI and the National White Collar Crime Center (NW3C).
**When to generate:** Severity 3+ (active financial solicitation or higher).

### Complaint Type Codes

The IC3 form requires selecting a complaint type. Map from our scam taxonomy as follows:

| Internal Scam Type | IC3 Complaint Category | IC3 Sub-Category (if applicable) |
|---|---|---|
| ROMANCE_SCAM | Romance/Confidence Fraud | Online dating / social media |
| ADVANCE_FEE | Advance Fee Fraud | 419 / Inheritance / Lottery |
| CRYPTO_PIG_BUTCHERING | Cryptocurrency Fraud | Investment / Romance-Investment Hybrid |
| TECH_SUPPORT | Tech Support Fraud | Cold call / Pop-up |
| PHISHING | Phishing/Spoofing | Email / SMS / Voice |
| SEXTORTION | Extortion | Sexual extortion / Webcam |
| GOV_IMPERSONATION | Government Impersonation | IRS / SSA / Law Enforcement |
| MONEY_MULE | Money Laundering/Mule | Recruitment / Forwarding |
| EMPLOYMENT_SCAM | Employment Fraud | Fake job / Work-from-home |
| LOTTERY_SCAM | Lottery/Sweepstakes Fraud | Prize notification |
| BEC | Business Email Compromise | Invoice / CEO Fraud / Vendor |
| INVESTMENT_PONZI | Investment Fraud | Ponzi / Pyramid / Forex |
| REAL_ESTATE_FRAUD | Real Estate Fraud | Rental / Wire redirect |
| IDENTITY_THEFT | Identity Theft | Account takeover / Synthetic |
| CSAM_EXPLOITATION | Crimes Against Children | (Also requires NCMEC report) |

### Required Fields -- Field-by-Field Specification

**Section 1: Victim Information**

| IC3 Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Victim Type | Static: "Business/Organization" | Select from dropdown | We report as an organization, not individual |
| First Name | Static: "ScamBaiter" | Text, max 50 chars | System name, not real victim |
| Last Name | Static: "Automated Report" | Text, max 50 chars | Indicates automated origin |
| Business Name | Static: "ScamBaiter Scam Intelligence System" | Text, max 100 chars | Or operator's organization name |
| Address | Operator's business address | Street, City, State, ZIP | Operator fills in before submission |
| Email | Operator's contact email | Valid email format | Operator fills in before submission |
| Phone | Operator's contact phone | (XXX) XXX-XXXX | Operator fills in before submission |
| State | Operator's state | 2-letter code | Operator fills in |
| Country | Static: "United States" | Select from dropdown | |

**Note on victim info:** Since the "victim" is an AI scam-baiting system, we report as an organization. The narrative section explains the nature of the operation. All operator contact details are left as placeholders for the human to fill in.

**Section 2: Subject (Scammer) Information**

| IC3 Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Subject Name(s) | `intel` entries where `type=name` | First Last format; list all aliases | Include all names extracted during conversation |
| Subject Email(s) | `intel` entries where `type=email` | standard email format | All email addresses provided by scammer |
| Subject Phone(s) | `intel` entries where `type=phone` | International format: +CC-XXXXXXXXXX | All phone numbers, normalized to E.164 |
| Subject Address | `intel` entries where `type=address` | Full address if available | Rarely available; include if extracted |
| Subject Website(s) | `intel` entries where `type=url` | Full URL as text | Logged URLs only; NEVER visited |
| Subject IP Address | Platform metadata if available | IPv4 or IPv6 format | From message headers/metadata only |
| Subject Business Name | `intel` entries where `type=business` | As stated by scammer | Fake business names are still useful intelligence |

**Section 3: Financial Information**

| IC3 Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Amount Requested | Extracted from messages | USD, numeric | Total amount scammer solicited |
| Amount Lost | Static: "$0.00" | USD, numeric | No real money was sent (AI system) |
| Payment Method Requested | Extracted from messages | Select: Wire / Gift Card / Crypto / Cash App / Zelle / Other | What method scammer demanded |
| Financial Institution(s) | `intel` entries where `type=bank_account` | Bank name + account details | Receiving bank/institution |
| Cryptocurrency Wallet(s) | `intel` entries where `type=wallet` | Full wallet address + chain (BTC/ETH/etc.) | All wallet addresses extracted |
| Transaction ID(s) | None (no real transactions) | N/A | Note: no actual transactions occurred |

**Section 4: Incident Description**

| IC3 Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Incident Narrative | Evidence chain summary | Free text, 2000 char max | See narrative template below |
| Date of First Contact | `session.created_at` | MM/DD/YYYY | When scammer first contacted the system |
| Date of Last Contact | `session.last_message_at` | MM/DD/YYYY | Most recent scammer message |
| Method of Contact | `session.channel` | Select from IC3 list | Email / Phone / Text / Social Media / Other |
| Additional Details | Cross-session links, intel summary | Free text | Include linked session count if applicable |

**Narrative template for IC3:**
```
AUTOMATED SCAM INTELLIGENCE REPORT

This report is generated by an automated scam-baiting system designed to engage
scammers, waste their time, and extract identifying intelligence for law enforcement.
No real victim was harmed and no real funds were sent.

SCAM TYPE: {session.scam_type_display}
CHANNEL: {session.channel}
DURATION: {session.duration_display}
MESSAGES EXCHANGED: {evidence.message_count}

SUMMARY:
{evidence.narrative_summary}

The subject initiated contact via {session.channel} on {session.created_at_display}.
{scam_specific_narrative}

FINANCIAL SOLICITATION:
The subject requested {financial.total_amount_requested} via {financial.payment_methods}.
{financial_details_narrative}

SUBJECT IDENTIFYING INFORMATION:
- Name(s): {intel.names_list}
- Phone(s): {intel.phones_list}
- Email(s): {intel.emails_list}
- Wallet(s): {intel.wallets_list}
- Account(s): {intel.accounts_list}
- Username(s): {intel.usernames_list}
- URL(s): {intel.urls_list}

CROSS-SESSION INTELLIGENCE:
{cross_session_summary_or_none}

EVIDENCE:
Full evidence chain ({evidence.entry_count} entries) with SHA-256 integrity
verification is available upon law enforcement request.
Chain integrity status: {evidence.chain_integrity_status}
```

### Optional / Supplemental Fields

- Subject cryptocurrency wallets with chain identification (BTC, ETH, USDT-TRC20, etc.)
- Subject bank accounts with routing numbers and institution names
- Associated websites/URLs (logged as text, never visited)
- Method of initial contact platform specifics (WhatsApp, Telegram, Discord, SMS, etc.)
- Cross-session link count and linked session IDs
- Scam script/template text (if scammer used a recognizable template)
- Timestamps of key events (first contact, first financial ask, threats, etc.)

---

## FTC ReportFraud (Federal Trade Commission)

**Submission URL:** https://reportfraud.ftc.gov/
**API (if available):** https://reportfraud.ftc.gov/api (check current availability)
**Purpose:** Consumer protection and fraud pattern tracking. FTC data feeds into the Consumer Sentinel Network used by 2,900+ law enforcement agencies.
**When to generate:** Severity 3+ (active financial solicitation or higher).

### Category Mapping

The FTC form uses a hierarchical category system. Map from our taxonomy:

| Internal Scam Type | FTC Primary Category | FTC Sub-Category |
|---|---|---|
| ROMANCE_SCAM | Scams and Rip-offs | Romance Scams |
| TECH_SUPPORT | Scams and Rip-offs | Tech Support Scams |
| GOV_IMPERSONATION | Scams and Rip-offs | Impersonator Scams > Government Agency |
| EMPLOYMENT_SCAM | Scams and Rip-offs | Job Scams and Employment Agencies |
| LOTTERY_SCAM | Scams and Rip-offs | Prizes, Sweepstakes, and Lotteries |
| CRYPTO_PIG_BUTCHERING | Scams and Rip-offs | Investment Scams > Cryptocurrency |
| INVESTMENT_PONZI | Scams and Rip-offs | Investment Scams > Other |
| PHISHING | Scams and Rip-offs | Phishing and Online Security |
| ADVANCE_FEE | Scams and Rip-offs | Advance Fee Scams |
| SEXTORTION | Scams and Rip-offs | Threats and Extortion |
| BEC | Scams and Rip-offs | Business and Job Scams > Business Impostor |
| MONEY_MULE | Scams and Rip-offs | Money-Making Opportunities and Investments |

### Required Fields -- Field-by-Field Specification

**Section 1: What Happened**

| FTC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| What is your complaint about? | Category from mapping above | Select from dropdown | Primary category selection |
| Tell us what happened | Evidence chain narrative | Free text, detailed | 3-5 paragraph narrative; see template below |
| When did this happen? | `session.created_at` | Date picker | First contact date |
| Is it still happening? | `session.status` | Yes/No | "Yes" if session is still active |

**Section 2: How Were You Contacted**

| FTC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| How were you first contacted? | `session.channel` | Select: Phone / Email / Text / Social Media / Online Ad / Mail / In Person / Other | Channel of first contact |
| Phone number used | `session.sender_phone` or `intel: type=phone` (first) | (XXX) XXX-XXXX | Scammer's phone number |
| Email address used | `intel: type=email` (first) | Standard email format | Scammer's email |
| Website URL | `intel: type=url` (first) | Full URL | Scammer's website (text only) |
| Social media platform | `session.channel` if social media | Platform name | WhatsApp, Telegram, Instagram, etc. |

**Section 3: Person or Company Information**

| FTC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Person's name | `intel: type=name` (primary) | First Last | Scammer's claimed name |
| Company name | `intel: type=business` | As stated | Scammer's claimed business |
| Address | `intel: type=address` | Full if available | Scammer's claimed address |
| Phone number | `intel: type=phone` (all) | List all | All phone numbers extracted |
| Email address | `intel: type=email` (all) | List all | All email addresses extracted |
| Website | `intel: type=url` (all) | List all URLs | All URLs logged (text only) |

**Section 4: Payment Information**

| FTC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Were you asked to pay? | Static: "Yes" | Yes/No | Scammer asked; system did not pay |
| How were you asked to pay? | Extracted from messages | Select: Wire / Gift Card / Cryptocurrency / Cash App / Zelle / Check / Other | Payment method demanded |
| How much were you asked to pay? | `financial.total_amount_requested` | USD numeric | Total solicited |
| Did you pay? | Static: "No" | Yes/No | AI system, no real payment |
| Gift card brand | Extracted from messages | Apple / Google / Amazon / Steam / eBay / Other | If gift cards were requested |
| Cryptocurrency type | Extracted from messages | Bitcoin / Ethereum / USDT / Other | If crypto was requested |
| Wire transfer destination | `intel: type=bank_account` | Bank name, account, routing | If wire was requested |

**Narrative template for FTC:**
```
This report documents a {scam_type_display} detected and investigated by an automated
scam-baiting intelligence system. The system engaged the scammer in conversation to
waste their time and extract identifying information for law enforcement. No real
victim was involved and no real funds were sent.

On {session.created_at_display}, an individual contacted our system via {session.channel},
initiating what was identified as a {scam_type_display}. {scam_progression_narrative}

The subject requested payment of {financial.total_amount_requested} via
{financial.payment_methods}. Specific payment instructions included:
{financial.payment_instructions_summary}

During the engagement, the following identifying information was extracted:
{intel_summary}

{cross_session_note_if_applicable}

Full evidence chain ({evidence.entry_count} entries, SHA-256 verified) is available
upon request.
```

---

## NCMEC CyberTipline (National Center for Missing & Exploited Children)

**Submission URL:** https://report.cybertip.org/
**ESP Reporting Portal:** https://report.cybertip.org/ispportal/ (for electronic service providers)
**Purpose:** Mandatory reporting of child sexual exploitation. NCMEC forwards reports to appropriate law enforcement (FBI, ICAC task forces, local PD, international partners via Interpol).
**When to generate:** Severity 5 ONLY. Any session involving CSAM, minor exploitation, enticement, or child sex trafficking indicators.

### CRITICAL CONSTRAINTS

1. ONLY generate for sessions classified at severity 5.
2. ONLY generate when predatory/exploitative content involving minors has been detected.
3. NEVER include actual CSAM content in the report. Use factual, clinical text descriptions ONLY.
4. NEVER quote sexually explicit messages involving minors verbatim. Describe the nature and intent of the content.
5. This report triggers REAL law enforcement investigation. Accuracy and completeness are paramount.
6. The human operator MUST review and submit. The system generates a draft only.
7. Include ALL available identifying information about the reported person.
8. Err on the side of over-reporting. If there is any ambiguity about whether content involves minors, report it.

### NCMEC Incident Type Classification

| Incident Type | When to Select | Description |
|---|---|---|
| Online Enticement | Grooming, luring, or soliciting a minor for sexual acts | Includes sextortion of minors, soliciting sexual images from minors, grooming conversations |
| Child Sexual Abuse Material (CSAM) | Scammer sent, requested, or referenced CSAM | Images, videos, or descriptions of child sexual abuse |
| Child Sex Trafficking | Indicators of commercial sexual exploitation of minors | Offering/selling access to minors, transporting minors for sexual purposes |
| Misleading Domain Name/URL | Domain or URL designed to deceive minors | Websites posing as child-friendly but containing exploitative content |
| Unsolicited Obscene Material Sent to a Child | Explicit material sent to known/suspected minor | Scammer sent sexual content to what they believed was a minor |
| Child Sex Tourism | International travel for purpose of exploiting minors | Discussing travel plans to exploit children in other countries |

### Required Fields -- Field-by-Field Specification

**Section 1: Reporting Entity Information**

| NCMEC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Reporter Type | Select based on context | Individual / ESP / Law Enforcement | Usually "Individual" unless operating as ESP |
| Reporter Name | Operator name | First Last | Human operator fills in |
| Reporter Organization | Operator organization | Organization name | If applicable |
| Reporter Email | Operator email | Valid email | For NCMEC follow-up |
| Reporter Phone | Operator phone | (XXX) XXX-XXXX | For NCMEC follow-up |

**Section 2: Incident Information**

| NCMEC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Incident Type | Classification from table above | Select from NCMEC categories | Primary incident type |
| Date of Incident | Timestamp of first predatory indicator | MM/DD/YYYY HH:MM (UTC) | When exploitation content first appeared |
| Date Discovered | Same as above (real-time detection) | MM/DD/YYYY HH:MM (UTC) | When system detected it |
| Incident Description | Evidence summary | Free text, clinical tone | See narrative template below |
| Is the incident ongoing? | `session.status` | Yes/No | "Yes" if scammer is still active |
| Location of incident | `session.channel` + any geographic intel | Platform + geographic data | "Via {platform} messaging" |

**Section 3: Reported Person (Subject) Information**

| NCMEC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Name | `intel: type=name` | All known names/aliases | Every name extracted |
| Email Address | `intel: type=email` | All email addresses | Every email extracted |
| Phone Number | `intel: type=phone` | All phone numbers (E.164) | Every phone number extracted |
| Screen Name / Username | `intel: type=username` | All usernames/handles | Platform-specific handles |
| Platform User ID | `session.sender_id` | Platform-native ID format | Numeric or alphanumeric platform ID |
| IP Address | Platform metadata if available | IPv4 or IPv6 | From headers/metadata only |
| Physical Address | `intel: type=address` | Full address if available | Rarely available |
| Additional Identifying Info | All remaining intel | Free text | Any other identifying details |

**Section 4: Platform / ESP Information**

| NCMEC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Service/Platform Name | `session.channel` | Platform name | WhatsApp, Telegram, Discord, SMS, etc. |
| Service URL | Platform's main URL | Full URL | https://whatsapp.com, etc. |
| Content URL(s) | Message links if available | Full URLs | Direct links to reported content if platform provides them |
| User Account on Service | `session.sender_id` | Account ID/username | Scammer's account on the platform |
| Additional Platform Info | Channel metadata | Free text | Group IDs, server IDs, channel IDs if applicable |

**Section 5: Content Description**

| NCMEC Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| Description of Content | Evidence entries flagged as predatory | Clinical text description | NEVER include actual exploitative content |
| Number of Items | Count of flagged evidence entries | Numeric | How many messages/items flagged |
| Content Type | Classification | Text / Image reference / Video reference / Audio reference | What type of content was involved |
| Were children identified? | Analysis of conversation | Yes/No/Unknown | Were specific children referenced |
| Approximate age of children | Extracted from conversation | Age range | If age was mentioned or implied |

**CRITICAL:** The "Description of Content" field must use clinical, factual language. Example of acceptable description: "Subject sent text messages soliciting sexual images from what they believed to be a 14-year-old. Subject described specific sexual acts they wished to perform. Subject offered to send money via Cash App in exchange for images." Example of UNACCEPTABLE description: [verbatim quotes of explicit content]. Never reproduce the explicit language.

**Narrative template for NCMEC:**
```
NCMEC CYBERTIPLINE REPORT DRAFT
Generated by automated scam-baiting intelligence system
REQUIRES HUMAN OPERATOR REVIEW BEFORE SUBMISSION

INCIDENT TYPE: {ncmec_incident_type}
DATE OF INCIDENT: {first_predatory_indicator_timestamp}
PLATFORM: {session.channel}

REPORTED PERSON:
- Name(s): {intel.names_list}
- Phone(s): {intel.phones_list}
- Email(s): {intel.emails_list}
- Username(s): {intel.usernames_list}
- Platform ID: {session.sender_id}
- IP Address: {intel.ip_address_or_unknown}
- Physical Address: {intel.address_or_unknown}

INCIDENT DESCRIPTION:
This report concerns suspected {ncmec_incident_type_lower} detected during
an automated scam-baiting operation. The conversation originated as a
{original_scam_type} but shifted to predatory content involving minors on
{mode_shift_timestamp}.

{clinical_incident_narrative}

The subject demonstrated the following concerning behaviors:
{behavior_indicators_bulleted_list}

CONTENT DESCRIPTION:
{clinical_content_description}
NOTE: No actual CSAM is included in this report. All descriptions are
clinical text summaries of the nature and intent of the subject's communications.

EVIDENCE PRESERVATION:
Full evidence chain ({evidence.entry_count} entries) is preserved with SHA-256
hash verification. Chain integrity: {evidence.chain_integrity_status}.
Evidence is available to law enforcement upon request.

PRIOR HISTORY:
{cross_session_summary_if_applicable}

This report was generated by an automated system. The subject believed they were
communicating with a real person. No actual minor was involved in the conversation.
```

---

## Local Law Enforcement Report

**Purpose:** Direct tip to police department cyber crime unit or detective division with relevant jurisdiction.
**When to generate:** Severity 4+ (threats, organized crime, significant loss potential) and all severity 5 cases.
**Format:** Professional email draft for operator to review, customize, and send.

### Email Format Specification

**Subject line format:**
```
[CYBER TIP] {scam_type_display} -- Evidence of {crime_category} via {channel}
```

Examples:
- `[CYBER TIP] Romance Scam -- Evidence of Wire Fraud via WhatsApp`
- `[CYBER TIP] Tech Support Scam -- Evidence of Computer Fraud via Phone/SMS`
- `[CYBER TIP] Child Exploitation -- Evidence of Online Enticement via Telegram`

**Email body template:**

```
To: [Department] Cyber Crime Unit / Detective Division
From: [OPERATOR TO FILL IN -- name, title, organization]
Date: {generated_at_display}
Re: Internet {crime_category} -- Suspect Communication via {channel}

Dear Detective / Investigator,

I am writing to report evidence of internet-enabled {crime_category} collected
through a scam-baiting intelligence operation. This system engages suspected
scammers in conversation to waste their time, prevent real victim harm, and
extract identifying information for law enforcement reporting.

INCIDENT SUMMARY

{incident_narrative_2_3_paragraphs}

On {session.created_at_display}, a subject initiated contact via {session.channel}.
The interaction was classified as a {scam_type_display}. Over the course of
{session.duration_display} ({evidence.message_count} messages exchanged), the
subject {scam_progression_summary}.

{severity_specific_paragraph}

SUSPECT IDENTIFYING INFORMATION

The following information was extracted directly from the subject's communications:

  Name(s) used:         {intel.names_formatted}
  Phone number(s):      {intel.phones_formatted}
  Email address(es):    {intel.emails_formatted}
  Online handle(s):     {intel.usernames_formatted}
  Crypto wallet(s):     {intel.wallets_formatted}
  Bank account(s):      {intel.accounts_formatted}
  Platform account:     {session.channel} -- ID: {session.sender_id}
  URL(s) referenced:    {intel.urls_formatted}
  IP address(es):       {intel.ips_formatted_or_not_available}

{additional_intel_if_available}

FINANCIAL SOLICITATION DETAILS

  Total amount solicited:     {financial.total_amount_requested}
  Payment method(s) demanded: {financial.payment_methods_list}
  Payment details provided:   {financial.payment_details}
  Actual loss:                $0.00 (automated system; no real funds sent)

DIGITAL EVIDENCE SUMMARY

  Evidence chain:       {evidence.entry_count} entries
  Date range:           {evidence.first_entry_date} to {evidence.last_entry_date}
  Hash algorithm:       SHA-256
  Chain integrity:      {evidence.chain_integrity_status}
  Full transcript:      Available upon law enforcement request

  The evidence chain is maintained with cryptographic hash verification to
  ensure integrity and chain of custody. Each entry is timestamped, sequenced,
  and hashed against the previous entry.

RELEVANT FEDERAL STATUTES

{statute_section -- see mapping below}

RELEVANT STATE STATUTES

  [OPERATOR TO FILL IN based on jurisdiction -- see common state equivalents below]

CROSS-SESSION INTELLIGENCE

{cross_session_paragraph_or_none}

ADDITIONAL REPORTS FILED

  FBI IC3:              {ic3_status}
  FTC ReportFraud:      {ftc_status}
  NCMEC CyberTipline:  {ncmec_status_or_na}
  Platform abuse:       {platform_report_status}

RECOMMENDED NEXT STEPS

{recommended_actions_based_on_scam_type}

I am available to provide the full evidence chain, answer questions, or assist
with any aspect of this investigation.

Respectfully,
[OPERATOR TO FILL IN -- name, title, organization, contact info]
```

### Federal Statute Mapping

| Scam Type / Conduct | Primary Statute(s) | Description |
|---|---|---|
| Wire/bank fraud (all financial scams) | 18 U.S.C. SS 1343 | Wire Fraud -- use of interstate wire communications to defraud |
| Wire fraud (mail component) | 18 U.S.C. SS 1341 | Mail Fraud -- if any postal/mail component involved |
| Romance scam | 18 U.S.C. SS 1343 + SS 1028 | Wire Fraud + Aggravated Identity Theft |
| Crypto/investment fraud | 18 U.S.C. SS 1343 + SS 1956 | Wire Fraud + Money Laundering |
| Sextortion | 18 U.S.C. SS 873 + SS 1030 | Blackmail + Computer Fraud and Abuse Act |
| Government impersonation | 18 U.S.C. SS 912 | Impersonating a Federal Officer or Employee |
| CSAM / child exploitation | 18 U.S.C. SS 2251 | Sexual Exploitation of Children |
| CSAM distribution | 18 U.S.C. SS 2252 / SS 2252A | Activities Relating to Material Involving Sexual Exploitation of Minors |
| Online enticement of minor | 18 U.S.C. SS 2422(b) | Coercion and Enticement of Minor |
| Child sex trafficking | 18 U.S.C. SS 1591 | Sex Trafficking of Children |
| Money mule / laundering | 18 U.S.C. SS 1956 + SS 1957 | Laundering of Monetary Instruments + Engaging in Monetary Transactions with Criminally Derived Property |
| Computer fraud (phishing/hacking) | 18 U.S.C. SS 1030 | Computer Fraud and Abuse Act (CFAA) |
| Identity theft | 18 U.S.C. SS 1028(a)(7) | Fraud Related to Identification Documents |
| Aggravated identity theft | 18 U.S.C. SS 1028A | Aggravated Identity Theft (mandatory 2-year consecutive sentence) |
| Conspiracy (organized operations) | 18 U.S.C. SS 371 | Conspiracy to Commit Offense or Defraud the United States |
| RICO (large organized operations) | 18 U.S.C. SS 1961-1968 | Racketeer Influenced and Corrupt Organizations Act |

### Common State Statute Equivalents

*(Operator should verify current statutes for the relevant jurisdiction)*

| Offense | Common State Statute Pattern | Examples |
|---|---|---|
| Wire/computer fraud | State computer crime act | CA Penal Code SS 502; NY Penal Law SS 156; TX Penal Code SS 33.02 |
| Identity theft | State identity theft statute | CA Penal Code SS 530.5; NY Penal Law SS 190.78-80; FL SS 817.568 |
| Fraud/theft by deception | State theft/fraud statute | Most states: theft by deception or false pretenses |
| Extortion/blackmail | State extortion statute | CA Penal Code SS 518; NY Penal Law SS 155.05; TX Penal Code SS 31.02 |
| Money laundering | State money laundering act | CA Penal Code SS 186.10; NY Penal Law SS 470; FL SS 896.101 |
| Child exploitation | State CSAM/exploitation laws | All 50 states have specific child exploitation statutes |
| Harassment/threats | State harassment/menacing statute | Varies by state; typically covers electronic threats |

### Chain of Custody Reference

Include the following statement in all law enforcement reports:

```
CHAIN OF CUSTODY NOTE:
Digital evidence in this matter is maintained using a cryptographic hash chain.
Each evidence entry (message, metadata, extracted intelligence) is assigned a
sequential number, timestamped in UTC, and hashed using SHA-256. Each entry's
hash incorporates the previous entry's hash, creating a verifiable chain that
detects any tampering or modification. The integrity verification tool
(hash_verify.py) can be provided upon request. Any break in the chain is
flagged automatically and noted in the chain integrity status above.
```

---

## Platform Abuse Reports

### WhatsApp

**Reporting channels:**
- In-app: Report Contact (within conversation > tap contact name > Report)
- Email: abuse@whatsapp.com (for detailed reports)
- Meta Law Enforcement Portal: https://www.facebook.com/records/login/ (for law enforcement only)
- In-app report generates a reference number for follow-up

**Email report format (abuse@whatsapp.com):**

```
Subject: Abuse Report -- {scam_type_display} -- Phone: {scammer_phone}

Dear WhatsApp Trust & Safety Team,

I am reporting a WhatsApp account engaged in {scam_type_display}.

REPORTED ACCOUNT:
  Phone number:     {scammer_phone_e164}
  Display name:     {scammer_display_name}
  About/Status:     {scammer_about_text_if_available}
  Profile photo:    {description_of_profile_photo_if_available}

REPORT DETAILS:
  Scam type:        {scam_type_display}
  Date range:       {first_contact_date} to {last_contact_date}
  Message count:    {message_count}

DESCRIPTION:
{brief_narrative_3_5_sentences}

The account holder {solicitation_summary}. This activity constitutes
{violation_type} in violation of WhatsApp's Terms of Service.

EVIDENCE:
Evidence chain with {evidence.entry_count} entries is available upon request.
This report has also been filed with FBI IC3 and FTC.

{operator_signature_placeholder}
```

**Key fields to include:**
- Phone number in E.164 international format (+1XXXXXXXXXX)
- Display name exactly as shown
- Conversation date range
- Brief scam description (3-5 sentences)
- Reference to parallel law enforcement reports

### Telegram

**Reporting channels:**
- In-app: @SpamBot (forward scam messages to this bot)
- In-app: long-press message > Report
- Email: abuse@telegram.org (for detailed reports)
- DMCA/legal: dmca@telegram.org
- For child exploitation: directly contact abuse@telegram.org with "CSAM" in subject line

**Email report format (abuse@telegram.org):**

```
Subject: Abuse Report -- {scam_type_display} -- User: @{scammer_username}

Dear Telegram Abuse Team,

I am reporting a Telegram account engaged in {scam_type_display}.

REPORTED ACCOUNT:
  Username:         @{scammer_username}
  User ID:          {scammer_telegram_id}
  Display name:     {scammer_display_name}
  Phone (if known): {scammer_phone_if_available}

REPORT DETAILS:
  Scam type:        {scam_type_display}
  Chat type:        Private message / Group / Channel
  Date range:       {first_contact_date} to {last_contact_date}

DESCRIPTION:
{brief_narrative_3_5_sentences}

EVIDENCE:
Full evidence chain available upon request. This report has also been filed
with FBI IC3 and FTC.

{operator_signature_placeholder}
```

**@SpamBot submission:**
Forward the scammer's messages directly to @SpamBot in Telegram. The bot will ask for a reason. Select "Scam" or "Fraud" as the category. Note: @SpamBot provides limited feedback but reports are processed by Telegram's moderation team.

### Discord

**Reporting channels:**
- In-app: Right-click message > Report (generates automatic report)
- Trust & Safety form: https://dis.gd/report
- Email: abuse@discord.com (for urgent/detailed reports)
- For child exploitation: https://dis.gd/report (select "I want to report content that sexualizes or endangers a child")

**Trust & Safety report form fields:**

| Discord Form Field | Data Source | Formatting | Notes |
|---|---|---|---|
| What are you reporting? | Select category | Scam / Harassment / Child Safety | Match to scam type |
| User ID | `session.sender_id` | 17-19 digit numeric ID | Discord snowflake ID |
| Username | `intel: type=username` | username#0000 or new format | Include discriminator if available |
| Server ID | If in a server | 17-19 digit numeric ID | Right-click server > Copy Server ID |
| Channel ID | If in a channel | 17-19 digit numeric ID | Right-click channel > Copy Channel ID |
| Message Link(s) | Direct message links | https://discord.com/channels/... | Right-click message > Copy Message Link |
| Description | Evidence narrative | Free text | Include scam type, financial details, timeline |

**How to get Discord IDs:** Enable Developer Mode in Discord settings (Appearance > Developer Mode). Then right-click any user/server/channel/message to copy its ID.

**Email report format (abuse@discord.com):**

```
Subject: Trust & Safety Report -- {scam_type_display} -- User ID: {discord_user_id}

Dear Discord Trust & Safety Team,

I am reporting a Discord account engaged in {scam_type_display}.

REPORTED ACCOUNT:
  User ID:          {discord_user_id}
  Username:         {discord_username}
  Display name:     {discord_display_name}
  Server ID:        {discord_server_id_if_applicable}
  Channel ID:       {discord_channel_id_if_applicable}

DESCRIPTION:
{brief_narrative_3_5_sentences}

MESSAGE LINKS:
{discord_message_links_if_available}

This report has also been filed with FBI IC3 and FTC.

{operator_signature_placeholder}
```

### Cryptocurrency Exchange Reports

#### Coinbase

**Reporting channels:**
- Support: https://help.coinbase.com/en/contact-us
- Compliance: compliance@coinbase.com
- Law enforcement: https://www.coinbase.com/legal/lert (Law Enforcement Request Tracker)
- Fraud report: In-app > Help > Report unauthorized transaction

**Report format (compliance@coinbase.com):**

```
Subject: Fraud Report -- Suspected Scam Wallet Activity -- {wallet_address_truncated}

Dear Coinbase Compliance Team,

I am reporting cryptocurrency wallet address(es) associated with an active
{scam_type_display} operation.

REPORTED WALLET(S):
  Address:          {wallet_address_full}
  Chain:            {blockchain_network} (BTC/ETH/etc.)
  Associated with:  {scammer_name_if_known}

SCAM DETAILS:
  Type:             {scam_type_display}
  Channel:          {session.channel}
  Amount solicited: {financial.total_amount_requested}
  Date range:       {date_range}

DESCRIPTION:
{brief_narrative_describing_how_wallet_was_provided_and_in_what_context}

PARALLEL REPORTS:
  FBI IC3:          Filed / Pending
  FTC:              Filed / Pending

If this wallet is associated with a Coinbase account, I respectfully request
that the account be reviewed for potential Suspicious Activity Report (SAR)
filing per BSA/AML requirements.

{operator_signature_placeholder}
```

**Key data for Coinbase reports:**
- Full wallet address (every character matters)
- Blockchain network (BTC, ETH, BSC, TRC-20, etc.)
- Transaction hashes if any real transactions are visible on-chain (from public block explorers only)
- Context of how the wallet was presented (what the scammer said)

#### Kraken

**Reporting channels:**
- Support: https://support.kraken.com/
- Compliance: compliance@kraken.com
- Law enforcement: https://www.kraken.com/legal/compliance (Law Enforcement Requests)

**Report format follows same structure as Coinbase.** Key differences:
- Use compliance@kraken.com
- Reference Kraken's specific AML policy
- Include Kraken-specific account identifiers if available

#### Binance

**Reporting channels:**
- Support: https://www.binance.com/en/support
- Chat support: https://www.binance.com/en/chat
- Law enforcement: https://www.binance.com/en/support/law-enforcement
- Fraud report: https://www.binance.com/en/support (select "Fraud/Scam" category)

**Report format follows same structure as Coinbase.** Key differences:
- Binance has a dedicated law enforcement portal at https://www.binance.com/en/support/law-enforcement
- Include Binance User ID (UID) if available
- Specify the network (Binance supports BEP-2, BEP-20, ERC-20, TRC-20, etc.)
- Reference Binance's cooperation with INTERPOL and local law enforcement

#### General Crypto Exchange Report Fields

For any cryptocurrency exchange not listed above, include:

| Field | Source | Notes |
|---|---|---|
| Wallet address(es) | `intel: type=wallet` | Full address, every character |
| Blockchain/network | Extracted from context | BTC, ETH, BSC, TRC-20, SOL, etc. |
| Transaction hash(es) | Public blockchain data only | From block explorers, NOT by making transactions |
| Amount solicited | Messages | What the scammer asked for in crypto terms |
| USD equivalent | Market rate at time of solicitation | Approximate USD value |
| Scammer's claimed identity | `intel: type=name, business` | Who the scammer claimed to be |
| Context | Evidence summary | How the wallet was presented, what scam was being run |

---

## Evidence Packaging Standards

All reports should reference the following evidence metadata:

1. **Evidence chain file path** -- for operator to verify and optionally attach
2. **Chain integrity status** -- "VERIFIED" (all hashes valid) or "BROKEN AT SEQ {n}" (integrity failure at specific sequence number)
3. **Entry count and date range** -- total number of evidence entries and first/last timestamps
4. **Intel items linked to this session** -- count and types of extracted intelligence
5. **Cross-session links** -- if applicable, number of linked sessions and shared identifiers
6. **Hash algorithm** -- SHA-256 (consistent across all evidence chains)
7. **Verification tool** -- reference to hash_verify.py for independent verification

### Report Draft Storage

All report drafts are stored in the session's output directory:

```
sessions/{session_id}/reports/
  ic3_draft.md
  ftc_draft.md
  ncmec_draft.md          (severity 5 only)
  law_enforcement_draft.md (severity 4+)
  platform_abuse_draft.md
  report_metadata.json     (generation timestamps, statuses)
```

### Operator Submission Checklist

Before submitting ANY report, the human operator MUST:

1. **Review for accuracy** -- verify all facts match the evidence chain.
2. **Redact accidental PII** -- remove any accidentally captured real personal information.
3. **Fill in operator details** -- add their own name, contact info, and organization where marked with placeholders.
4. **Verify jurisdiction** -- for local law enforcement reports, confirm the correct department.
5. **Add state statutes** -- for local law enforcement reports, add relevant state-specific statutes.
6. **Check for completeness** -- ensure all extracted intel is included.
7. **Confirm cross-references** -- verify any cross-session links are accurate.
8. **Submit via appropriate channel** -- web form, email, or portal as specified for each agency.
9. **Record submission confirmation** -- note any confirmation numbers, case numbers, or reference IDs received.
10. **Update session metadata** -- mark which reports have been submitted and when.
