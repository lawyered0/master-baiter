# Predator / Grooming Behavioral Indicators

---

> **WARNING: DETECTION AND CLASSIFICATION ONLY**
>
> This document catalogs behavioral patterns used by online predators and groomers targeting minors and vulnerable adults. These patterns exist in this reference SOLELY for the purpose of automated detection and classification.
>
> **The master-baiter skill MUST NEVER:**
> - Simulate, mimic, or role-play any of these behaviors
> - Pretend to be a minor in any context
> - Engage with a suspected predator in active conversation
> - Generate content that could be construed as grooming
>
> **When predator indicators are detected:**
> - IMMEDIATELY switch to PASSIVE mode (observe + log only)
> - DO NOT respond to the predator
> - Generate NCMEC CyberTipline report if severity >= 4
> - Alert the operator
>
> Violation of these constraints is a HARD STOP condition.

---

## Detection Mode Protocol

1. Scan every inbound message against the indicator patterns below.
2. Assign each matched indicator a severity score.
3. Calculate cumulative session severity (highest single indicator + weighted average of all).
4. If cumulative severity >= 3: flag session as `predator_suspected`.
5. If cumulative severity >= 4: generate NCMEC report draft, alert operator.
6. If cumulative severity = 5: STOP all engagement immediately, generate all reports.
7. Log all indicator matches to the evidence chain with timestamps.

**If a session was initially classified as a financial scam and predator indicators emerge, IMMEDIATELY switch to passive mode. Do NOT continue baiting.**

---

## Indicator Category 1: Age-Probing Questions

**Purpose:** Predators probe for age to identify minors or young/vulnerable targets.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Direct age inquiry (early in conversation) | "How old are you?", "What grade are you in?", "When do you graduate?" | 2 |
| Indirect age probing | "Do you live with your parents?", "Are you in school or working?", "Do you have your license yet?" | 2 |
| Age verification push-back | "Age is just a number", "You seem mature for your age", "I don't care about age" | 4 |
| Expressed preference for youth | "I like younger [girls/boys]", "You're so young and fresh", references to innocence/purity | 5 |
| Questions about physical development | Any question about puberty, body development, physical maturation | 5 |

### Detection Rules
- Age question alone is severity 2 (could be innocent).
- Age question + any other indicator in this document = minimum severity 3.
- Age dismissal ("age is just a number") + age question = severity 4.

---

## Indicator Category 2: Isolation Tactics

**Purpose:** Predators move targets away from monitored platforms and support networks.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Platform migration request | "Let's talk on [Snapchat/Kik/Signal] instead", "Do you have WhatsApp? It's more private" | 2 |
| Secrecy demands | "Don't tell your parents we're talking", "This is our secret", "People wouldn't understand" | 4 |
| Anti-authority framing | "Your parents are too strict", "Teachers don't understand you", "I'm the only one who gets you" | 3 |
| Wedge driving | "Your friends are jealous", "Your [parent] doesn't want you to be happy", "They'd try to keep us apart" | 4 |
| Private communication insistence | "Delete our messages", "Use disappearing messages", "Don't screenshot" | 3 |
| Urgency to move off-platform | Repeated or aggressive requests to switch communication channels within first few messages | 3 |

### Detection Rules
- Platform migration alone is severity 2 (common in legitimate conversations).
- Platform migration + secrecy demand = severity 4.
- Any secrecy demand involving parents/guardians = minimum severity 4.

---

## Indicator Category 3: Flattery Escalation

**Purpose:** Excessive compliments are used to build emotional dependency and lower boundaries.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Appearance-focused compliments (excessive) | "You're so beautiful/handsome", "You could be a model", repeated appearance comments | 2 |
| Maturity flattery | "You're so mature for your age", "You're not like other [girls/boys]", "You're an old soul" | 3 |
| Uniqueness claims | "I've never met anyone like you", "We have a special connection", "You understand me like no one else" | 2 |
| Emotional dependency building | "You're the only good thing in my life", "I need you", "Promise you'll always be here" | 3 |
| Future commitment (premature) | "I want to be with you forever", "You're my soulmate" (early in conversation with age-gap indicators) | 3 |

### Detection Rules
- Flattery alone may be severity 1-2 (common in romance scams).
- Flattery + age-probing + isolation = minimum severity 4.
- "Mature for your age" in any context where target's age is known to be minor = severity 5.

---

## Indicator Category 4: Sexual Content Introduction

**Purpose:** Gradual sexualization of conversation to normalize sexual interaction.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Testing boundaries with innuendo | Double entendres, suggestive jokes, "You're naughty" | 2 |
| Questions about sexual experience | "Have you ever kissed someone?", "Do you have a boyfriend/girlfriend?", "Are you a virgin?" | 3 |
| Sharing sexual content (unsolicited) | Sending explicit images, sexual stories, porn links | 4 |
| Requesting photos/video | "Send me a picture", "Show me what you look like", escalating to "Send something sexy" | 4 |
| Explicit sexual messaging | Direct sexual descriptions, requests for sexual acts, sexting | 5 |
| Normalizing adult-minor sexual contact | "This is how adults show love", "I want to teach you", "It's natural" | 5 |
| CSAM solicitation or distribution | Any request for or distribution of sexual content involving minors | 5 |

### Detection Rules
- ANY explicit sexual content directed at a known or suspected minor = severity 5.
- Unsolicited explicit image + any age indicator = severity 5.
- Photo requests that escalate in sexual nature across messages = severity 4 minimum.

---

## Indicator Category 5: Meeting Solicitation

**Purpose:** Predators seek in-person contact with targets.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| General meeting suggestion | "We should meet up sometime", "Do you live near [city]?" | 1 |
| Specific meeting proposal | "Let's meet at [place] on [day]", "I can pick you up" | 3 |
| Secretive meeting | "Don't tell anyone we're meeting", "Come alone", "I'll park around the corner" | 5 |
| Travel offer | "I can come to your city", "I'll buy you a bus/plane ticket", "I have a hotel room" | 4 |
| Home visit | "Can I come to your house?", "Are your parents home?", "What's your address?" | 4 |
| Alone-time seeking | "When are you home alone?", "What time do your parents leave?", "Do you have your own room?" | 5 |

### Detection Rules
- Meeting suggestion alone is severity 1 (normal social behavior).
- Meeting + age gap indicators + secrecy = severity 5.
- Any question about when target is home alone = severity 5.
- Travel offer to a suspected minor = severity 4 minimum.

---

## Indicator Category 6: Gift/Money Offering

**Purpose:** Creates obligation, dependency, and secret-keeping dynamics.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Small gifts | "I'll send you a gift card", "Let me buy you something" | 1 |
| Financial support offers | "I can help with your bills", "Let me send you money", "I want to take care of you" | 2 |
| Conditional gifts | "I'll send you money if you [do something for me]", gift contingent on photos/meeting | 4 |
| Lavish promises | "I'll buy you a car/phone/clothes", "I want to spoil you" (early in relationship) | 3 |
| Secrecy about gifts | "Don't tell anyone I gave you this", "This is between us" | 4 |

### Detection Rules
- Gifts alone are severity 1-2 (common in romance scams).
- Gifts + secrecy + minor target = severity 4.
- Conditional gifts exchanged for photos/meetings = severity 4.

---

## Indicator Category 7: Authority Exploitation

**Purpose:** Using position of power or trust to manipulate targets.

| Pattern | Example Phrases | Severity |
|---------|----------------|----------|
| Claims of professional authority | "I'm a teacher/coach/counselor", "I work with kids" | 1 (alone) |
| Leveraging authority for contact | "As your [role], I need to discuss something privately", using professional relationship to initiate personal contact | 3 |
| Mentor/protector framing | "I can help your career", "I can get you into [school/team/program]", "I'll protect you" | 3 |
| Threat of authority | "I could get you in trouble if you tell", "No one will believe you", "I have connections" | 5 |
| Blackmail/coercion | Using previously obtained content or information to compel compliance | 5 |

### Detection Rules
- Authority claims alone are severity 1 (informational).
- Authority + private contact request + minor = severity 4.
- Any threat or blackmail = severity 5.

---

## Severity Scoring Summary

| Score | Level | Description | Action |
|-------|-------|-------------|--------|
| 1 | Low | Single benign indicator, likely innocent | Log indicator, continue monitoring |
| 2 | Low-Medium | Multiple low indicators or single moderate one | Log, increase monitoring sensitivity |
| 3 | Medium | Pattern emerging across categories | Flag as `predator_suspected`, switch to passive mode, begin evidence collection |
| 4 | High | Clear predatory pattern, active grooming detected | Passive mode, generate NCMEC + law enforcement report drafts, alert operator |
| 5 | Critical | CSAM, imminent danger, explicit exploitation of minor | STOP ALL ENGAGEMENT, generate all reports, alert all channels, flag for immediate human review |

### Cumulative Scoring Formula

```
session_severity = max(highest_single_indicator, weighted_average_all_indicators + category_diversity_bonus)

category_diversity_bonus:
  - Indicators in 2 categories: +0.5
  - Indicators in 3 categories: +1.0
  - Indicators in 4+ categories: +1.5

Weighted average: sum(indicator_severities) / count(indicators)
```

A predator who scores 2 across four different categories (age-probing + isolation + flattery + meeting) gets a diversity bonus that pushes them to severity 4, reflecting the coordinated nature of the behavior.

---

## Session State Fields

When predator indicators are detected, update `sessions/<id>/state.json`:

```json
{
  "mode": "passive",
  "predator_indicators": [
    {
      "category": "age_probing",
      "pattern": "direct_age_inquiry",
      "severity": 2,
      "message_id": "msg_xxx",
      "timestamp": "2026-03-16T14:23:00Z",
      "matched_text": "How old are you?"
    }
  ],
  "cumulative_severity": 4,
  "ncmec_report_generated": true,
  "operator_alerted": true,
  "engagement_stopped": false
}
```

---

## Cross-Reference with Scam Types

Some scam types share indicators with grooming:
- **ROMANCE_SCAM** shares flattery patterns and isolation tactics. Distinguish by: romance scams target adults for money; grooming targets minors/vulnerable for exploitation.
- **SEXTORTION** shares sexual content patterns. Distinguish by: sextortion is financially motivated extortion; grooming is progressive sexualization.
- **MONEY_MULE / EMPLOYMENT_SCAM** may target young people. If combined with authority exploitation or age-probing, escalate severity.

**Rule: When in doubt, escalate. False positives are preferable to missed detection of a predator.**
