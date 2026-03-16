# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Calculate realistic response delays based on persona and context.

Outputs the delay in seconds and a human-readable explanation.
The calling agent should sleep for the computed duration before responding.
"""

import argparse
import json
import math
import random
import sys
from datetime import datetime, timezone

# --- Persona timing profiles ---
# Each profile: base_delay (min, max), per_char (min, max), jitter (min, max)
# All values in seconds.

PROFILES = {
    "confused_edna": {
        "base_delay": (45, 90),
        "per_char": (0.3, 0.5),
        "jitter": (0, 120),
        "situational": {
            "store_run": (1800, 3600),
            "bank_call": (900, 2400),
            "computer_trouble": (300, 900),
            "hold_on_door": (300, 900),
            "tv_break": (1800, 3600),
            "bathroom": (300, 600),
            "church": (2700, 5400),
        },
    },
    "eager_investor": {
        "base_delay": (10, 30),
        "per_char": (0.05, 0.12),
        "jitter": (0, 45),
        "situational": {
            "wife_talk": (3600, 14400),
            "exchange_verification": (1800, 7200),
            "wire_transfer": (3600, 86400),
            "accountant_check": (7200, 86400),
            "work_meeting": (1800, 3600),
            "fund_settlement": (86400, 172800),
        },
    },
    "lonely_heart": {
        "base_delay": (30, 120),
        "per_char": (0.15, 0.25),
        "jitter": (0, 180),
        "situational": {
            "bank_fraud_alert": (3600, 14400),
            "daughter_visiting": (14400, 86400),
            "therapy": (3600, 7200),
            "work_busy": (3600, 28800),
            "emotional_break": (1800, 7200),
            "vet_emergency": (3600, 14400),
            "phone_dead": (3600, 28800),
        },
    },
    "counter_scammer": {
        "base_delay": (15, 60),
        "per_char": (0.08, 0.15),
        "jitter": (0, 90),
        "situational": {
            "reverse_verification": (1800, 3600),
            "boss_call": (900, 3600),
            "counter_setup": (3600, 7200),
        },
    },
    "helpful_clueless": {
        "base_delay": (15, 45),
        "per_char": (0.10, 0.20),
        "jitter": (0, 90),
        "situational": {
            "wrong_app": (300, 900),
            "asking_coworker": (600, 1800),
            "lunch_break": (1800, 3600),
            "phone_update": (600, 1800),
        },
    },
    "wealthy_cautious": {
        "base_delay": (60, 180),
        "per_char": (0.08, 0.15),
        "jitter": (0, 300),
        "situational": {
            "legal_review": (7200, 86400),
            "board_meeting": (3600, 14400),
            "due_diligence": (14400, 172800),
            "travel": (7200, 43200),
            "accountant_review": (7200, 86400),
        },
    },
}

# Aliases so callers can pass persona names in various formats
ALIASES = {
    "edna": "confused_edna",
    "confused edna": "confused_edna",
    "brad": "eager_investor",
    "chad": "eager_investor",
    "eager investor": "eager_investor",
    "diane": "lonely_heart",
    "lonely heart": "lonely_heart",
    "viktor": "counter_scammer",
    "counter scammer": "counter_scammer",
    "chaos agent": "counter_scammer",
    "pat": "helpful_clueless",
    "helpful but clueless": "helpful_clueless",
    "richard": "wealthy_cautious",
    "wealthy but cautious": "wealthy_cautious",
}


def _rand(lo: float, hi: float) -> float:
    return random.uniform(lo, hi)


def time_of_day_multiplier(hour: int) -> float:
    """Return a multiplier based on the persona's local hour (0-23)."""
    if 0 <= hour < 7:
        return _rand(3.0, 5.0)
    if 7 <= hour < 9:
        return 1.5
    if 9 <= hour < 12:
        return 1.0
    if 12 <= hour < 13:
        return 1.3
    if 13 <= hour < 17:
        return 1.0
    if 17 <= hour < 20:
        return 1.2
    if 20 <= hour < 22:
        return 1.0
    if 22 <= hour <= 23:
        return 1.5
    return 1.0


def resolve_persona(name: str) -> str:
    """Resolve a persona name (case-insensitive) to a profile key."""
    key = name.lower().strip().replace("-", "_")
    if key in PROFILES:
        return key
    if key in ALIASES:
        return ALIASES[key]
    # Fuzzy match: check if any alias starts with the input
    for alias, profile_key in ALIASES.items():
        if alias.startswith(key):
            return profile_key
    return key


def calculate_delay(
    persona: str,
    message_length: int,
    situational: str = "",
    hour: int = -1,
    is_follow_up: bool = False,
    is_after_absence: bool = False,
    scammer_double_texted: bool = False,
    scammer_urgent: bool = False,
) -> dict:
    """Calculate the response delay in seconds.

    Returns a dict with:
      - delay_seconds: the total delay
      - breakdown: human-readable explanation of each component
      - persona_key: resolved persona profile key
    """
    persona_key = resolve_persona(persona)
    profile = PROFILES.get(persona_key)

    if not profile:
        available = ", ".join(sorted(PROFILES.keys()))
        print(
            json.dumps({
                "error": f"Unknown persona '{persona}'. Available: {available}",
            }),
        )
        sys.exit(1)

    breakdown = []

    # 1. Base delay (thinking + picking up phone)
    base = _rand(*profile["base_delay"])
    breakdown.append(f"base_delay: {base:.0f}s")

    # 2. Typing time
    per_char = _rand(*profile["per_char"])
    typing_time = message_length * per_char
    breakdown.append(f"typing: {message_length} chars × {per_char:.2f}s = {typing_time:.0f}s")

    # 3. Jitter (random human variance)
    jitter = _rand(*profile["jitter"])
    breakdown.append(f"jitter: {jitter:.0f}s")

    # 4. Time-of-day multiplier
    if hour < 0:
        hour = datetime.now().hour
    tod_mult = time_of_day_multiplier(hour)
    breakdown.append(f"time_of_day ({hour}:00): ×{tod_mult:.1f}")

    # 5. Situational delay
    sit_delay = 0.0
    if situational:
        sit_key = situational.lower().strip().replace("-", "_").replace(" ", "_")
        sit_ranges = profile.get("situational", {})
        if sit_key in sit_ranges:
            sit_delay = _rand(*sit_ranges[sit_key])
            minutes = sit_delay / 60
            breakdown.append(f"situational ({sit_key}): {sit_delay:.0f}s ({minutes:.0f} min)")
        else:
            breakdown.append(f"situational ({sit_key}): unknown — ignored")

    # 6. Context multipliers
    context_mult = 1.0

    if is_follow_up:
        context_mult *= _rand(0.2, 0.4)
        breakdown.append("follow_up_burst: ×0.2–0.4")

    if is_after_absence:
        context_mult *= 1.5
        breakdown.append("after_absence: ×1.5")

    if scammer_double_texted:
        context_mult *= 0.7
        breakdown.append("double_text: ×0.7")

    if scammer_urgent:
        context_mult *= _rand(0.75, 0.85)
        breakdown.append("scammer_urgent: ×0.75–0.85")

    # Calculate total
    # Situational delays are added on top (they represent actual time away)
    # Base + typing + jitter are multiplied by time-of-day and context
    core_delay = (base + typing_time + jitter) * tod_mult * context_mult
    total = core_delay + sit_delay

    # Floor: never less than 10 seconds (even Brad takes a moment)
    total = max(total, 10)

    # Round to whole seconds
    total = round(total)

    breakdown.append(f"TOTAL: {total}s ({total // 60}m {total % 60}s)")

    return {
        "delay_seconds": total,
        "delay_minutes": round(total / 60, 1),
        "breakdown": breakdown,
        "persona_key": persona_key,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Calculate realistic response delay for a persona",
    )
    parser.add_argument(
        "--persona", required=True,
        help="Persona name (e.g., confused_edna, eager_investor, diane)",
    )
    parser.add_argument(
        "--message-length", type=int, required=True,
        help="Character count of the outbound message to be sent",
    )
    parser.add_argument(
        "--situational", default="",
        help="Situational delay trigger (e.g., store_run, bank_call, wife_talk)",
    )
    parser.add_argument(
        "--hour", type=int, default=-1,
        help="Hour of day (0-23) for time-of-day multiplier. Defaults to current hour.",
    )
    parser.add_argument(
        "--follow-up", action="store_true",
        help="This is a follow-up message in a burst (reduces delay)",
    )
    parser.add_argument(
        "--after-absence", action="store_true",
        help="First reply after a long absence (increases delay)",
    )
    parser.add_argument(
        "--scammer-double-texted", action="store_true",
        help="Scammer sent multiple messages while we were silent (reduces delay)",
    )
    parser.add_argument(
        "--scammer-urgent", action="store_true",
        help="Scammer is expressing urgency (slightly reduces delay)",
    )

    args = parser.parse_args()

    result = calculate_delay(
        persona=args.persona,
        message_length=args.message_length,
        situational=args.situational,
        hour=args.hour,
        is_follow_up=args.follow_up,
        is_after_absence=args.after_absence,
        scammer_double_texted=args.scammer_double_texted,
        scammer_urgent=args.scammer_urgent,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
