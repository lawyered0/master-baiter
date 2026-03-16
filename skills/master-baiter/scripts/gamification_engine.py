# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Gamification engine — XP scoring, leveling, and achievement tracking.

Calculates XP for baiting events, manages level progression, and checks
achievement conditions. All state is stored in the dashboard's SQLite DB
via the server's ingest pipeline; this script is the scoring brain.

Usage:
    uv run gamification_engine.py --event message_sent --session SESSION_ID --severity 3
    uv run gamification_engine.py --check-achievements --session SESSION_ID
    uv run gamification_engine.py --level-info --total-xp 5000
    uv run gamification_engine.py --recalculate --sessions-json '[...]'
"""

import argparse
import json
import math
import sys


# ─── XP Events ───────────────────────────────────────────────────────────────

XP_EVENTS = {
    "message_sent":      5,
    "message_received":  3,
    "time_wasted_min":   1,     # per minute of scammer time wasted
    "intel_extracted":   50,
    "report_generated":  100,
    "report_submitted":  200,
    "session_started":   10,
}

# Session milestones: (threshold, xp_bonus, label)
MESSAGE_MILESTONES = [
    (10,  25,   "10 messages"),
    (25,  75,   "25 messages"),
    (50,  200,  "50 messages"),
    (100, 500,  "100 messages"),
    (200, 1000, "200 messages"),
]

TIME_MILESTONES = [
    (3600,    100,  "1 hour wasted"),
    (14400,   500,  "4 hours wasted"),
    (28800,   1000, "8 hours wasted"),
    (86400,   5000, "24 hours wasted"),
]


# ─── Level System ────────────────────────────────────────────────────────────

LEVEL_TITLES = [
    (1,  "Bait Apprentice"),
    (5,  "Hook Setter"),
    (10, "Line Tangler"),
    (15, "Reel Master"),
    (20, "Scam Sinker"),
    (30, "Time Thief"),
    (40, "Intel Operative"),
    (50, "Master Baiter"),
]


def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    if level <= 0:
        return 0
    return round(100 * level ** 1.5)


def level_from_xp(total_xp: int) -> dict:
    """Calculate level info from total XP."""
    level = 0
    while xp_for_level(level + 1) <= total_xp:
        level += 1
        if level > 200:  # safety cap
            break

    title = "Bait Apprentice"
    for min_level, t in reversed(LEVEL_TITLES):
        if level >= min_level:
            title = t
            break

    current_level_xp = xp_for_level(level)
    next_level_xp = xp_for_level(level + 1)
    progress = 0
    if next_level_xp > current_level_xp:
        progress = round((total_xp - current_level_xp) / (next_level_xp - current_level_xp) * 100, 1)

    return {
        "level": level,
        "title": title,
        "total_xp": total_xp,
        "xp_for_current_level": current_level_xp,
        "xp_for_next_level": next_level_xp,
        "progress_percent": progress,
    }


# ─── Multipliers ─────────────────────────────────────────────────────────────

def compute_multipliers(
    severity: int = 1,
    persona_variety: bool = False,
    intel_combo: bool = False,
    rapid_extraction: bool = False,
) -> tuple[float, list[str]]:
    """Calculate XP multiplier from context."""
    mult = 1.0
    reasons = []

    # Severity bonus: 1.0 + (severity * 0.2)
    if severity > 1:
        sev_mult = 1.0 + severity * 0.2
        mult *= sev_mult
        reasons.append(f"severity_{severity} ({sev_mult}x)")

    if persona_variety:
        mult *= 1.5
        reasons.append("persona_variety (1.5x)")

    if intel_combo:
        mult *= 2.0
        reasons.append("intel_combo (2x)")

    if rapid_extraction:
        mult *= 1.5
        reasons.append("rapid_extraction (1.5x)")

    return round(mult, 2), reasons


def score_event(
    event_type: str,
    severity: int = 1,
    count: int = 1,
    **kwargs,
) -> dict:
    """Score a single XP event."""
    base = XP_EVENTS.get(event_type, 0) * count
    mult, reasons = compute_multipliers(
        severity=severity,
        persona_variety=kwargs.get("persona_variety", False),
        intel_combo=kwargs.get("intel_combo", False),
        rapid_extraction=kwargs.get("rapid_extraction", False),
    )
    awarded = round(base * mult)

    return {
        "event_type": event_type,
        "xp_base": base,
        "multiplier": mult,
        "multiplier_reasons": reasons,
        "xp_awarded": awarded,
    }


# ─── Achievements ────────────────────────────────────────────────────────────

ACHIEVEMENTS = [
    # Time Wasting
    {
        "id": "first_blood",
        "name": "First Blood",
        "description": "Waste your first minute of a scammer's time",
        "icon": "🩸",
        "category": "time_wasting",
        "xp_reward": 50,
        "condition": {"type": "global_time", "gte": 60},
    },
    {
        "id": "coffee_break",
        "name": "Coffee Break",
        "description": "Keep a scammer on the hook for 15 minutes",
        "icon": "☕",
        "category": "time_wasting",
        "xp_reward": 100,
        "condition": {"type": "session_time", "gte": 900},
    },
    {
        "id": "lunch_hour",
        "name": "Lunch Hour Thief",
        "description": "Waste a full hour of a scammer's day",
        "icon": "🍕",
        "category": "time_wasting",
        "xp_reward": 250,
        "condition": {"type": "session_time", "gte": 3600},
    },
    {
        "id": "half_day",
        "name": "Half-Day Hero",
        "description": "Burn through 4 hours of scammer time in one session",
        "icon": "🦸",
        "category": "time_wasting",
        "xp_reward": 1000,
        "condition": {"type": "session_time", "gte": 14400},
    },
    {
        "id": "full_shift",
        "name": "Full Shift Waster",
        "description": "8 hours. You just cost them a whole work day.",
        "icon": "💼",
        "category": "time_wasting",
        "xp_reward": 2500,
        "condition": {"type": "session_time", "gte": 28800},
    },
    {
        "id": "overtime",
        "name": "Mandatory Overtime",
        "description": "12+ hours in a single session. The scammer should be getting time-and-a-half.",
        "icon": "🕐",
        "category": "time_wasting",
        "xp_reward": 5000,
        "condition": {"type": "session_time", "gte": 43200},
    },
    {
        "id": "centurion",
        "name": "The Centurion",
        "description": "100 total hours wasted across all sessions",
        "icon": "🏛️",
        "category": "time_wasting",
        "xp_reward": 10000,
        "condition": {"type": "global_time", "gte": 360000},
    },

    # Intel Extraction
    {
        "id": "first_catch",
        "name": "First Catch",
        "description": "Extract your first piece of scammer intel",
        "icon": "🐟",
        "category": "intel",
        "xp_reward": 50,
        "condition": {"type": "total_intel", "gte": 1},
    },
    {
        "id": "phone_phisher",
        "name": "Phone Phisher",
        "description": "Extract 5 phone numbers from scammers",
        "icon": "📱",
        "category": "intel",
        "xp_reward": 200,
        "condition": {"type": "intel_by_type", "intel_type": "phone", "gte": 5},
    },
    {
        "id": "wallet_inspector",
        "name": "Wallet Inspector",
        "description": "Extract 5 crypto wallet addresses",
        "icon": "👛",
        "category": "intel",
        "xp_reward": 300,
        "condition": {"type": "intel_by_type", "intel_type": "wallet", "gte": 5},
    },
    {
        "id": "email_harvester",
        "name": "Email Harvester",
        "description": "Extract 10 scammer email addresses",
        "icon": "📧",
        "category": "intel",
        "xp_reward": 250,
        "condition": {"type": "intel_by_type", "intel_type": "email", "gte": 10},
    },
    {
        "id": "identity_crisis",
        "name": "Identity Crisis",
        "description": "Extract 3+ different intel types from a single session",
        "icon": "🪪",
        "category": "intel",
        "xp_reward": 500,
        "condition": {"type": "session_intel_types", "gte": 3},
    },
    {
        "id": "intelligence_agency",
        "name": "Intelligence Agency",
        "description": "Collect 50 total unique intel items",
        "icon": "🕵️",
        "category": "intel",
        "xp_reward": 2000,
        "condition": {"type": "total_intel", "gte": 50},
    },
    {
        "id": "follow_the_money",
        "name": "Follow the Money",
        "description": "Extract both a wallet AND a bank account in one session",
        "icon": "💰",
        "category": "intel",
        "xp_reward": 750,
        "condition": {"type": "session_has_intel_types", "required": ["wallet", "bank_account"]},
    },

    # Reports & Justice
    {
        "id": "paper_pusher",
        "name": "Paper Pusher",
        "description": "Generate your first law enforcement report",
        "icon": "📝",
        "category": "reports",
        "xp_reward": 100,
        "condition": {"type": "total_reports", "gte": 1},
    },
    {
        "id": "by_the_book",
        "name": "By the Book",
        "description": "Submit a report to law enforcement",
        "icon": "📚",
        "category": "reports",
        "xp_reward": 500,
        "condition": {"type": "reports_submitted", "gte": 1},
    },
    {
        "id": "federal_case",
        "name": "Federal Case",
        "description": "File an IC3 complaint with the FBI",
        "icon": "🏛️",
        "category": "reports",
        "xp_reward": 300,
        "condition": {"type": "report_type_count", "report_type": "ic3", "gte": 1},
    },
    {
        "id": "full_dossier",
        "name": "Full Dossier",
        "description": "Generate all 5 report types for a single session",
        "icon": "📂",
        "category": "reports",
        "xp_reward": 2000,
        "condition": {"type": "session_report_types", "gte": 5},
    },
    {
        "id": "serial_reporter",
        "name": "Serial Reporter",
        "description": "Submit 10 reports to authorities",
        "icon": "🏆",
        "category": "reports",
        "xp_reward": 2500,
        "condition": {"type": "reports_submitted", "gte": 10},
    },

    # Persona Mastery
    {
        "id": "edna_fan",
        "name": "Bless Your Heart",
        "description": "Complete 5 sessions as Confused Edna",
        "icon": "👵",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "confused_edna", "gte": 5},
    },
    {
        "id": "brad_fan",
        "name": "To The Moon",
        "description": "Complete 5 sessions as Eager Investor Brad",
        "icon": "🚀",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "eager_investor", "gte": 5},
    },
    {
        "id": "diane_fan",
        "name": "Heartbreaker",
        "description": "Complete 5 sessions as Lonely Heart Diane",
        "icon": "💔",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "lonely_heart", "gte": 5},
    },
    {
        "id": "viktor_fan",
        "name": "Reverse Uno",
        "description": "Complete 5 sessions as Counter-Scammer Viktor",
        "icon": "🔄",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "counter_scammer", "gte": 5},
    },
    {
        "id": "pat_fan",
        "name": "Helpful Hindrance",
        "description": "Complete 5 sessions as Helpful But Clueless Pat",
        "icon": "🤷",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "helpful_clueless", "gte": 5},
    },
    {
        "id": "richard_fan",
        "name": "Due Diligence",
        "description": "Complete 5 sessions as Wealthy But Cautious Richard",
        "icon": "🎩",
        "category": "personas",
        "xp_reward": 300,
        "condition": {"type": "persona_sessions", "persona": "wealthy_cautious", "gte": 5},
    },
    {
        "id": "method_actor",
        "name": "Method Actor",
        "description": "Use all 6 personas at least once",
        "icon": "🎭",
        "category": "personas",
        "xp_reward": 1000,
        "condition": {"type": "unique_personas", "gte": 6},
    },
    {
        "id": "chameleon",
        "name": "The Chameleon",
        "description": "Use 3 different personas in a single day",
        "icon": "🦎",
        "category": "personas",
        "xp_reward": 500,
        "condition": {"type": "daily_unique_personas", "gte": 3},
    },

    # Session & Engagement
    {
        "id": "chatterbox",
        "name": "Chatterbox",
        "description": "Exchange 50 messages in a single session",
        "icon": "💬",
        "category": "engagement",
        "xp_reward": 250,
        "condition": {"type": "session_messages", "gte": 50},
    },
    {
        "id": "novelist",
        "name": "The Novelist",
        "description": "Exchange 100 messages in a single session",
        "icon": "📖",
        "category": "engagement",
        "xp_reward": 750,
        "condition": {"type": "session_messages", "gte": 100},
    },
    {
        "id": "war_and_peace",
        "name": "War and Peace",
        "description": "Exchange 200 messages in a single session. Tolstoy would be proud.",
        "icon": "📕",
        "category": "engagement",
        "xp_reward": 2000,
        "condition": {"type": "session_messages", "gte": 200},
    },
    {
        "id": "multi_tasker",
        "name": "Multi-Tasker",
        "description": "Have 3+ sessions active simultaneously",
        "icon": "🤹",
        "category": "engagement",
        "xp_reward": 500,
        "condition": {"type": "concurrent_active", "gte": 3},
    },
    {
        "id": "scam_spotter",
        "name": "Scam Spotter",
        "description": "Encounter 5 different scam types",
        "icon": "🔎",
        "category": "engagement",
        "xp_reward": 400,
        "condition": {"type": "unique_scam_types", "gte": 5},
    },
    {
        "id": "streak_3",
        "name": "Hat Trick",
        "description": "Complete 3 sessions in a row with intel extracted",
        "icon": "🎯",
        "category": "engagement",
        "xp_reward": 300,
        "condition": {"type": "intel_streak", "gte": 3},
    },
    {
        "id": "streak_7",
        "name": "Lucky Seven",
        "description": "7-session intel extraction streak",
        "icon": "🍀",
        "category": "engagement",
        "xp_reward": 1000,
        "condition": {"type": "intel_streak", "gte": 7},
    },

    # Hidden/Rare
    {
        "id": "boomerang",
        "name": "Boomerang",
        "description": "A scammer tries the same scam on you twice",
        "icon": "🪃",
        "category": "hidden",
        "xp_reward": 1000,
        "condition": {"type": "repeat_scammer", "gte": 1},
    },
    {
        "id": "night_owl",
        "name": "Night Owl",
        "description": "Keep a session active past midnight",
        "icon": "🦉",
        "category": "hidden",
        "xp_reward": 200,
        "condition": {"type": "session_spans_midnight", "gte": 1},
    },
    {
        "id": "mr_whiskers",
        "name": "Mr. Whiskers Award",
        "description": "Use Confused Edna and waste 2+ hours in one session",
        "icon": "🐱",
        "category": "hidden",
        "xp_reward": 500,
        "condition": {"type": "persona_time", "persona": "confused_edna", "gte": 7200},
    },
]


def check_achievement(achievement: dict, stats: dict) -> bool:
    """Check if an achievement condition is met given current stats.

    Stats dict expected keys (all optional, default 0):
        global_time, session_time, total_intel, total_reports,
        reports_submitted, session_messages, concurrent_active,
        unique_scam_types, unique_personas, daily_unique_personas,
        intel_streak, session_intel_types, repeat_scammer,
        session_spans_midnight,
        intel_by_type: {phone: N, email: N, wallet: N, ...},
        session_intel_type_set: [type1, type2, ...],
        persona_sessions: {persona_key: N, ...},
        persona_time: {persona_key: seconds, ...},
        report_type_count: {ic3: N, ftc: N, ...},
        session_report_types: N,
    """
    cond = achievement["condition"]
    ctype = cond["type"]

    if ctype == "global_time":
        return stats.get("global_time", 0) >= cond["gte"]
    elif ctype == "session_time":
        return stats.get("session_time", 0) >= cond["gte"]
    elif ctype == "total_intel":
        return stats.get("total_intel", 0) >= cond["gte"]
    elif ctype == "total_reports":
        return stats.get("total_reports", 0) >= cond["gte"]
    elif ctype == "reports_submitted":
        return stats.get("reports_submitted", 0) >= cond["gte"]
    elif ctype == "session_messages":
        return stats.get("session_messages", 0) >= cond["gte"]
    elif ctype == "concurrent_active":
        return stats.get("concurrent_active", 0) >= cond["gte"]
    elif ctype == "unique_scam_types":
        return stats.get("unique_scam_types", 0) >= cond["gte"]
    elif ctype == "unique_personas":
        return stats.get("unique_personas", 0) >= cond["gte"]
    elif ctype == "daily_unique_personas":
        return stats.get("daily_unique_personas", 0) >= cond["gte"]
    elif ctype == "intel_streak":
        return stats.get("intel_streak", 0) >= cond["gte"]
    elif ctype == "session_intel_types":
        return stats.get("session_intel_types", 0) >= cond["gte"]
    elif ctype == "repeat_scammer":
        return stats.get("repeat_scammer", 0) >= cond["gte"]
    elif ctype == "session_spans_midnight":
        return stats.get("session_spans_midnight", 0) >= cond["gte"]
    elif ctype == "intel_by_type":
        intel_map = stats.get("intel_by_type", {})
        return intel_map.get(cond["intel_type"], 0) >= cond["gte"]
    elif ctype == "session_has_intel_types":
        session_types = set(stats.get("session_intel_type_set", []))
        return all(t in session_types for t in cond["required"])
    elif ctype == "persona_sessions":
        persona_map = stats.get("persona_sessions", {})
        return persona_map.get(cond["persona"], 0) >= cond["gte"]
    elif ctype == "persona_time":
        time_map = stats.get("persona_time", {})
        return time_map.get(cond["persona"], 0) >= cond["gte"]
    elif ctype == "report_type_count":
        report_map = stats.get("report_type_count", {})
        return report_map.get(cond["report_type"], 0) >= cond["gte"]
    elif ctype == "session_report_types":
        return stats.get("session_report_types", 0) >= cond["gte"]

    return False


def check_all_achievements(stats: dict, already_unlocked: set[str] | None = None) -> list[dict]:
    """Check all achievements, returning newly unlocked ones."""
    if already_unlocked is None:
        already_unlocked = set()

    newly_unlocked = []
    for ach in ACHIEVEMENTS:
        if ach["id"] in already_unlocked:
            continue
        if check_achievement(ach, stats):
            newly_unlocked.append(ach)

    return newly_unlocked


def get_all_achievements() -> list[dict]:
    """Return all achievement definitions."""
    return ACHIEVEMENTS


# ─── Fun Stats ───────────────────────────────────────────────────────────────

BREAKING_BAD_RUNTIME = 62 * 3600  # ~62 hours for the full series

FUN_COMPARISONS = [
    (60,       "enough time to microwave a burrito"),
    (300,      "enough time to brew a proper cup of tea"),
    (1800,     "an entire episode of The Office"),
    (3600,     "enough time to watch an episode of Breaking Bad"),
    (7200,     "a full movie's worth of scammer misery"),
    (14400,    "a transatlantic flight's worth of wasted scammer time"),
    (28800,    "an entire work shift of scammer suffering"),
    (86400,    "a full 24 hours of scammer agony"),
    (BREAKING_BAD_RUNTIME, "the entire run of Breaking Bad"),
    (360000,   "more time than it takes to fly to the Moon"),
]


def fun_comparison(total_seconds: int) -> str:
    """Generate a fun time comparison."""
    best = None
    for threshold, desc in FUN_COMPARISONS:
        if total_seconds >= threshold:
            best = desc
    if not best:
        return "Keep going! Every second counts."

    # For large amounts, use multiples
    for threshold, desc in reversed(FUN_COMPARISONS):
        if total_seconds >= threshold:
            times = total_seconds / threshold
            if times >= 2:
                return f"enough to {desc} {times:.0f} times over"
            return desc

    return best


def format_duration_human(seconds: int) -> str:
    """Format seconds into human-friendly duration."""
    if seconds < 60:
        return f"{seconds} seconds"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m != 1 else ''}"
    if seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        if m:
            return f"{h} hour{'s' if h != 1 else ''} and {m} minute{'s' if m != 1 else ''}"
        return f"{h} hour{'s' if h != 1 else ''}"

    d = seconds // 86400
    h = (seconds % 86400) // 3600
    if h:
        return f"{d} day{'s' if d != 1 else ''}, {h} hour{'s' if h != 1 else ''}"
    return f"{d} day{'s' if d != 1 else ''}"


def scammer_salary_wasted(seconds: int) -> str:
    """Estimate how much scammer salary was wasted. Uses $5/hr estimate."""
    dollars = (seconds / 3600) * 5
    return f"${dollars:,.2f}"


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gamification engine for Master-Baiter")

    parser.add_argument("--event", help="Score an XP event (message_sent, intel_extracted, etc.)")
    parser.add_argument("--session", help="Session ID for context")
    parser.add_argument("--severity", type=int, default=1, help="Scam severity (1-5)")
    parser.add_argument("--count", type=int, default=1, help="Event count multiplier")

    parser.add_argument("--level-info", action="store_true", help="Get level info from total XP")
    parser.add_argument("--total-xp", type=int, default=0, help="Total XP for level calculation")

    parser.add_argument("--check-achievements", action="store_true", help="Check achievements against stats")
    parser.add_argument("--stats-json", default="", help="JSON stats for achievement checking")
    parser.add_argument("--unlocked-json", default="", help="JSON list of already-unlocked achievement IDs")

    parser.add_argument("--list-achievements", action="store_true", help="List all achievement definitions")

    args = parser.parse_args()

    if args.event:
        result = score_event(
            event_type=args.event,
            severity=args.severity,
            count=args.count,
        )
        print(json.dumps(result, indent=2))

    elif args.level_info:
        result = level_from_xp(args.total_xp)
        print(json.dumps(result, indent=2))

    elif args.check_achievements:
        stats = json.loads(args.stats_json) if args.stats_json else {}
        unlocked = set(json.loads(args.unlocked_json)) if args.unlocked_json else set()
        newly = check_all_achievements(stats, unlocked)
        print(json.dumps({"newly_unlocked": newly}, indent=2))

    elif args.list_achievements:
        print(json.dumps({"achievements": ACHIEVEMENTS}, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
