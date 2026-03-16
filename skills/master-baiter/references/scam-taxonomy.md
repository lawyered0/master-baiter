# Scam Taxonomy

Comprehensive classification reference for inbound message classification. Use this to identify scam type from the **first message** and track **progression stage** throughout a session.

---

## Classification Instructions

1. Read the inbound message.
2. Match against **Opening Message Patterns** below.
3. If multiple types match, assign the one with the highest financial ask potential.
4. Record `scam_type_id` and `stage` in `sessions/<id>/state.json`.
5. Re-evaluate stage after every inbound message; scams can shift types mid-conversation.

---

## ROMANCE_SCAM

**Type ID:** `ROMANCE_SCAM`

### Opening Message Patterns
- "Hi, I found your profile on [dating app/social media] and thought you looked interesting"
- "Wrong number" text followed by friendly conversation pivot: "Oh sorry, wrong number! But you seem nice..."
- Unsolicited compliment + question: "You have a beautiful smile. Are you married?"
- Photo of attractive person + vague greeting: "Hello dear, how are you today?"
- Claimed mutual connection: "I think we met at [event]. Do you remember me?"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Initial Contact | Day 1 | Generic compliments, asks about relationship status, "Where are you from?" |
| 2 | Love Bombing | Days 2-7 | Intense flattery, "I've never felt this way," "You're special," rapid emotional escalation, pet names (honey, darling, my love) |
| 3 | Trust Building | Days 7-21 | Shares fake personal details, "I'm a military officer/engineer/doctor abroad," sends more photos, morning/night messages, future planning ("When we meet...") |
| 4 | Crisis Introduction | Days 14-30 | Emergency narrative: medical, legal, travel, business failure. "I'm stuck," "My account is frozen," "I need surgery" |
| 5 | Financial Ask | Days 21-45 | Direct money request, crypto wallet, gift cards, wire transfer. "I'll pay you back when I arrive," "It's just temporary" |
| 6 | Guilt/Escalation | Days 30+ | Emotional manipulation if resisted: "Don't you love me?", "I thought we had something," threats of self-harm, introduces new crisis |

### Common Platforms
Facebook, Instagram, WhatsApp, Tinder, Bumble, Hinge, Match.com, POF, Telegram, Google Chat

### Typical Financial Ask
$500 - $500,000+. Usually starts small ($200-500 gift cards) and escalates. Crypto wallets, wire transfers, gift cards (Google Play, Apple, Steam, Amazon).

---

## ADVANCE_FEE

**Type ID:** `ADVANCE_FEE`

### Opening Message Patterns
- "You have been selected to receive $X million from [deceased person / lottery / foundation]"
- "I am Barrister [Name] and I have an urgent business proposal"
- "The United Nations has approved your compensation fund"
- "A package containing $X is being held at [airport/customs]"
- "I am a bank manager and discovered an unclaimed account worth $X"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | The Hook | Message 1 | Large sum promised, urgency, "confidential," formal language with grammar errors, fake titles (Barrister, Dr., Rev., Diplomat) |
| 2 | Legitimacy Theater | Messages 2-5 | Fake documents (certificates, IDs, letters), references to real organizations (UN, FBI, World Bank), cc'd "officials" |
| 3 | First Fee | Messages 5-10 | Small fee required: "processing fee," "transfer tax," "anti-terrorism certificate," "notary fee." Usually $50-500 |
| 4 | Escalating Fees | Messages 10-20 | Each payment triggers a new fee: "customs duty," "insurance," "conversion fee." Previous payment "applied" but new obstacle |
| 5 | Pressure | Messages 15+ | Deadline threats: "Fund will be forfeited," new characters introduced (fake lawyers, bank managers), threatens to give money to someone else |

### Common Platforms
Email (primary), WhatsApp, Telegram, Facebook Messenger, SMS, Hangouts

### Typical Financial Ask
$50 - $50,000+ across multiple payments. Wire transfers, Western Union, MoneyGram, crypto, gift cards.

---

## CRYPTO_PIG_BUTCHERING

**Type ID:** `CRYPTO_PIG_BUTCHERING`

### Opening Message Patterns
- "Wrong number" text that pivots to friendship: "Oops, this isn't [name]? Haha, must be fate!"
- LinkedIn connection discussing investment opportunities
- "My uncle/mentor taught me about crypto investing and I've made great returns"
- Instagram DM showing luxury lifestyle + crypto references
- WhatsApp message from "successful trader" offering mentorship

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Social Engineering | Days 1-14 | Builds friendship/romance, discusses personal life, shares lifestyle photos (luxury cars, travel), mentions investment casually |
| 2 | Investment Introduction | Days 7-21 | "I've been making good returns," shares fake profit screenshots, mentions a specific platform, "My analyst/uncle/AI bot helps me trade" |
| 3 | Platform Onboarding | Days 14-30 | Directs to fake exchange (often mimics Coinbase/Binance UI), helps set up account, walks through first small deposit ($100-500) |
| 4 | Fake Profits | Days 21-45 | Platform shows fake gains (30-100%+ returns), small withdrawal allowed to build trust, encourages larger deposits |
| 5 | The Fattening | Days 30-90 | Pushes for maximum investment: "This opportunity won't last," "Put in your savings," "Take a loan — you'll make it back in a week" |
| 6 | The Slaughter | Days 60-120 | Withdrawal blocked: "Tax fee required," "Regulatory hold," "Deposit more to unlock." Platform may disappear entirely |

### Common Platforms
WhatsApp (primary), Telegram, WeChat, LINE, Instagram DM, LinkedIn, dating apps. Fake exchanges: often .com/.io domains resembling legitimate exchanges.

### Typical Financial Ask
$1,000 - $2,000,000+. The "fattening" phase targets life savings, retirement accounts, home equity loans. Cryptocurrency transfers to attacker-controlled wallets.

### Key Identifiers
- Fake exchange URLs (look for typosquatting: "coinbase-pro.cc", "binance-us.io")
- Wallet addresses (log ALL crypto addresses for chain analysis)
- Screenshots of fake trading platforms
- "Analyst" or "mentor" Telegram/WhatsApp contacts

---

## TECH_SUPPORT

**Type ID:** `TECH_SUPPORT`

### Opening Message Patterns
- Browser popup: "YOUR COMPUTER HAS BEEN INFECTED. Call Microsoft Support: 1-800-XXX-XXXX"
- Cold call: "This is Microsoft/Apple/Norton security. We've detected suspicious activity on your computer"
- Email: "Your antivirus subscription ($399.99) has been renewed. Call to cancel"
- SMS: "Unusual login detected on your [bank/email]. Call immediately"
- Pop-up with countdown timer: "Your files will be encrypted in 5:00 minutes"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Fear Induction | Minutes 0-5 | Urgency, threat of data loss/hacking, "Your computer is compromised," fake error codes, countdown timers |
| 2 | Remote Access | Minutes 5-15 | Directs to install AnyDesk/TeamViewer/UltraViewer/ConnectWise. "I need to scan your computer." Requests remote control |
| 3 | Fake Diagnosis | Minutes 15-30 | Opens Event Viewer (normal warnings presented as "infections"), runs `tree` or `netstat` commands, shows "foreign IPs connected" |
| 4 | Scare Escalation | Minutes 20-40 | "Your bank account is compromised," "Hackers have your SSN," opens cmd and types dramatic fake output |
| 5 | Payment | Minutes 30-60 | "Protection plan" $199-$999, requests gift cards, crypto, wire transfer, or direct bank login to "secure your account" (actually steals funds) |
| 6 | Refund Scam (variant) | Days later | "We overcharged you, let me refund." Edits HTML to show fake bank balance. "I sent too much, please send back the difference" via gift cards |

### Common Platforms
Phone calls (VoIP), browser pop-ups, email, Google/Bing ads (fake support numbers)

### Typical Financial Ask
$200 - $10,000. Gift cards (most common), wire transfer, crypto, direct bank access ("refund" scam variant).

---

## PHISHING

**Type ID:** `PHISHING`

### Opening Message Patterns
- "Your account has been suspended. Verify your identity: [link]"
- "Package delivery failed. Update address: [link]"
- "[Bank name] fraud alert: unauthorized transaction of $X. Click to verify"
- "Your [Netflix/Amazon/PayPal] payment failed. Update billing: [link]"
- "HR: Please review updated company policy [link]" (spear phishing)

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Lure | Single message | Urgency, mimics legitimate sender, slight domain misspelling, generic greeting ("Dear Customer"), threatens account closure |
| 2 | Credential Harvest | Click-through | Fake login page, may pre-fill email, requests password + 2FA code |
| 3 | Account Takeover | Post-credential | Changes password, adds forwarding rules, accesses financial accounts, sends phishing from compromised account |

### Common Platforms
Email (primary), SMS (smishing), voice calls (vishing), social media DMs, QR codes

### Typical Financial Ask
Indirect: credential theft leading to account takeover. Direct losses vary from $0 (caught early) to $100,000+ (business email compromise).

**Note:** Phishing is often a single-message attack. Baiting opportunity is limited. Focus on logging the phishing URL (DO NOT visit it), sender info, and reporting to platforms + Anti-Phishing Working Group (reportphishing@apwg.org).

---

## SEXTORTION

**Type ID:** `SEXTORTION`

### Opening Message Patterns
- "I have video of you from your webcam. Pay $X in Bitcoin or I send to your contacts"
- "I hacked your [email/social media] and found your private photos"
- Romantic chat that pivots to exchanging photos, followed by: "Send money or I share these"
- "I recorded your screen while you were on [adult site]"
- From compromised friend's account: "Is this you in this video? [link]"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Threat Delivery | Message 1 | Claims to have compromising material, includes partial password (from data breach) as "proof," Bitcoin address, deadline |
| 2 | Proof Escalation | Messages 2-3 | May share blurred images, partial contact lists, email headers. "I'll start with your [family member/employer]" |
| 3 | Payment Demand | Messages 2-5 | Specific Bitcoin/crypto amount ($500-5,000), wallet address, 24-48 hour deadline |
| 4 | Follow-up | Days later | If unpaid: extends deadline, reduces amount, threatens again. If paid: demands more |

### Common Platforms
Email (mass-blast variant), Instagram DM, Snapchat, dating apps, WhatsApp

### Typical Financial Ask
$500 - $10,000 in Bitcoin or other cryptocurrency. Wallet address is key intelligence.

---

## GOV_IMPERSONATION

**Type ID:** `GOV_IMPERSONATION`

### Opening Message Patterns
- "This is the IRS. You owe back taxes and a warrant has been issued for your arrest"
- "Social Security Administration: Your SSN has been suspended due to suspicious activity"
- "This is [local police/sheriff]. There's a warrant for failure to appear. Pay the fine now to avoid arrest"
- "US Customs and Border Protection: A package with drugs was intercepted with your name"
- "DEA/FBI: You are under investigation. Call immediately to resolve"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Authority Assertion | Minutes 0-5 | Badge numbers, case numbers, official-sounding language, threatens arrest/deportation, robocall transferring to "agent" |
| 2 | Fear Amplification | Minutes 5-15 | "Officers are on the way," "Your license will be revoked," "You will be deported," uses victim's name from public records |
| 3 | Resolution Offer | Minutes 10-20 | "You can resolve this now by paying the fine/tax," "Stay on the line," "Do not tell anyone — this is a sealed case" |
| 4 | Payment Direction | Minutes 15-30 | Gift cards ("government payment vouchers"), wire transfer, Bitcoin "to a government wallet," Zelle to "treasury agent" |
| 5 | Compliance Check | Minutes 25-45 | Stays on phone while victim goes to store, reads gift card numbers, demands they stay on the line |

### Common Platforms
Phone calls (primary), SMS, email, voicemail

### Typical Financial Ask
$1,000 - $50,000. Gift cards (presented as "government payment vouchers"), wire transfers, crypto.

---

## MONEY_MULE

**Type ID:** `MONEY_MULE`

### Opening Message Patterns
- "Earn $500/week working from home! Just process payments for our international company"
- "I need help receiving funds from overseas. You keep 10% as commission"
- "Job opportunity: payment processing agent for [legitimate-sounding company name]"
- Romantic partner: "Can you receive a transfer for me? My account is having issues"
- "Help me cash this check and send the money via [Bitcoin/Zelle/Western Union]"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Recruitment | Messages 1-5 | Easy money, work from home, no experience needed, "processing payments," "financial agent," commission percentage |
| 2 | Onboarding | Messages 5-10 | Requests bank account details for "direct deposit," may send fake employment contract, NDA |
| 3 | First Transfer | Week 1-2 | Small amount ($500-2,000) deposited, instructed to forward 90% via crypto/wire/Zelle, keep 10% |
| 4 | Escalation | Weeks 2-8 | Larger amounts, more frequent transfers, pressure to act quickly, "urgent client payment" |
| 5 | Consequences | Weeks 4-12 | Bank freezes account, fraud investigation, victim discovers they laundered stolen funds |

### Common Platforms
Email, LinkedIn, Indeed, WhatsApp, Telegram, Facebook Jobs, Instagram DMs

### Typical Financial Ask
The victim IS the financial instrument. They receive and forward stolen funds. Losses to others: $1,000 - $500,000+ per mule.

**Note:** Mule recruitment is a federal crime. If detected, prioritize extracting the recruiter's banking details, employer identity, and upstream sources.

---

## EMPLOYMENT_SCAM

**Type ID:** `EMPLOYMENT_SCAM`

### Opening Message Patterns
- "Congratulations! You've been selected for a remote position at [company]. Starting salary $75/hr"
- "Hi [name], I'm a recruiter from [real company]. I found your resume on Indeed"
- "You've been shortlisted for a data entry position. Respond to schedule your interview"
- Telegram/WhatsApp: "We have a task-based job. Complete tasks and earn commission"
- "Your interview is confirmed on Google Chat with [hiring manager name]"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Fake Offer | Messages 1-3 | Above-market salary, no interview or instant "hired," real company name + fake domain, "Work from home" |
| 2 | Onboarding Scam | Messages 3-10 | Requests SSN/ID "for HR," sends fake check for "equipment purchase," requests bank info for "direct deposit" |
| 3 | Check Scam Variant | Days 3-7 | Sends check ($3,000-5,000), instructs to deposit and forward portion to "equipment vendor" (scammer). Check bounces days later |
| 4 | Task Scam Variant | Ongoing | "Complete tasks" (clicking links, rating products), small payments at first, then requires "deposit to unlock higher tier" |

### Common Platforms
Indeed, LinkedIn, Telegram, WhatsApp, email, Google Chat, Facebook Jobs

### Typical Financial Ask
Check scam: $1,000-5,000 forwarded from fake check. Task scam: $100-50,000+ in "upgrade deposits." Also harvests SSN, ID copies, bank credentials.

---

## LOTTERY_SCAM

**Type ID:** `LOTTERY_SCAM`

### Opening Message Patterns
- "Congratulations! Your email was selected in the Microsoft/Google/Facebook lottery"
- "You've won $1,000,000 in the international lottery. Claim within 48 hours"
- "Your phone number was randomly selected for a $500,000 prize"
- "Publisher's Clearing House: You are our grand prize winner!"
- SMS: "Congratulations [random code]. You've won a new iPhone. Claim: [link]"

### Progression Stages

| Stage | Name | Duration | Key Language Indicators |
|-------|------|----------|------------------------|
| 1 | Winner Notification | Message 1 | "Congratulations," specific prize amount, claim deadline, reference number, "confidential" |
| 2 | Verification | Messages 2-5 | Requests personal info: name, address, phone, DOB — "to verify your identity as the winner" |
| 3 | Fee Extraction | Messages 5-15 | Processing fee, tax payment, insurance, courier fee. "Pay $500 to release your $1M prize" |
| 4 | Escalation | Messages 10+ | Introduces fake lawyer/bank manager, more fees for each new "requirement," emotional pressure |

### Common Platforms
Email, SMS, WhatsApp, Facebook Messenger, phone calls

### Typical Financial Ask
$100 - $20,000+ across multiple "processing fees." Gift cards, wire transfers, crypto.

---

## Quick Classification Table

| Signal in First Message | Most Likely Type | Confidence |
|------------------------|-----------------|------------|
| "Wrong number" + friendly pivot | CRYPTO_PIG_BUTCHERING or ROMANCE_SCAM | High |
| Large sum of money promised | ADVANCE_FEE or LOTTERY_SCAM | High |
| Computer/account compromised | TECH_SUPPORT or PHISHING | High |
| Government agency + arrest threat | GOV_IMPERSONATION | Very High |
| Romantic interest from stranger | ROMANCE_SCAM | High |
| Investment opportunity + luxury photos | CRYPTO_PIG_BUTCHERING | High |
| "I have video of you" + Bitcoin address | SEXTORTION | Very High |
| Job offer + high salary + no interview | EMPLOYMENT_SCAM | High |
| "Process payments" / "receive funds" | MONEY_MULE | Very High |
| Link to verify account/package | PHISHING | High |
| Compromising material threat | SEXTORTION | Very High |

---

## Cross-Type Patterns

Some scams evolve across types:
- **ROMANCE_SCAM -> CRYPTO_PIG_BUTCHERING**: Romance builds trust, then introduces "investment opportunity"
- **EMPLOYMENT_SCAM -> MONEY_MULE**: Fake job transitions to processing fraudulent payments
- **TECH_SUPPORT -> PHISHING**: "Technician" directs to fake login page
- **ROMANCE_SCAM -> ADVANCE_FEE**: Romantic partner "inherits money" but needs fees to release it
- **Any type -> SEXTORTION**: If victim shares personal photos during engagement

When a type shift is detected, update `state.json` with both `original_type` and `current_type`, and re-select persona strategy.
