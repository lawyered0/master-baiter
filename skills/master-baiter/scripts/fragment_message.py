# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Split a single message into realistic multi-message fragments.

Real people — especially on SMS/WhatsApp — don't send one perfect paragraph.
Brad fires off staccato bursts. Edna sends a message, then a correction,
then "sorry dear I hit send too early." This script takes a composed message
and breaks it into fragments with inter-fragment delays.

This is anti-bot-detection layer #3: message cadence patterns.
"""

import argparse
import json
import random
import re
import sys

# --- Persona fragmentation profiles ---

PROFILES = {
    "confused_edna": {
        "fragment_probability": 0.35,      # 35% chance of fragmenting at all
        "max_fragments": 3,
        "style": "ramble_and_correct",
        # Edna sends one long message, then maybe a correction or afterthought
        "inter_delay": (8, 25),            # seconds between fragments
        "correction_phrases": [
            "Oh wait I meant to say",
            "Sorry dear, what I meant was",
            "Hold on let me fix that",
            "Oh silly me, I meant",
            "*",
        ],
        "afterthought_phrases": [
            "Oh and also dear",
            "I forgot to mention",
            "Oh one more thing",
            "Also Mr. Whiskers says hello!",
            "Sorry, Tommy always tells me to say everything in one message but I never remember",
        ],
    },
    "eager_investor": {
        "fragment_probability": 0.70,      # Brad almost always sends multiple short msgs
        "max_fragments": 5,
        "style": "staccato_burst",
        # Brad fires off rapid short messages like a group chat
        "inter_delay": (2, 8),             # Very fast between bursts
        "excitement_interjections": [
            "Bro",
            "Dude",
            "Wait",
            "OK so",
            "Yo",
            "Listen",
            "Hold up",
            "Ngl",
            "Fr fr",
            "No cap",
        ],
    },
    "lonely_heart": {
        "fragment_probability": 0.30,
        "max_fragments": 3,
        "style": "emotional_overflow",
        # Diane writes one long message, sometimes splits when emotions overflow
        "inter_delay": (10, 40),
        "overflow_phrases": [
            "Sorry, I just...",
            "I don't even know why I'm telling you all this lol",
            "Ugh ignore me I'm being silly",
            "Anyway...",
            "💕",
            "I just feel like we really connect you know?",
        ],
    },
    "counter_scammer": {
        "fragment_probability": 0.25,
        "max_fragments": 2,
        "style": "calculated_pause",
        # Viktor sends one message, then a pointed follow-up
        "inter_delay": (15, 45),
        "follow_up_patterns": [
            "Actually, one more question.",
            "By the way.",
            "Also I am curious about something.",
            "Hmm.",
        ],
    },
    "helpful_clueless": {
        "fragment_probability": 0.55,
        "max_fragments": 4,
        "style": "course_correct",
        # Pat sends, realizes mistake, sends correction, then gets confused again
        "inter_delay": (5, 15),
        "correction_phrases": [
            "Wait no that's not right",
            "Oops wrong button lol",
            "Actually hold on",
            "Hmm that doesn't look right",
            "Oh shoot I think I did the wrong thing",
            "Wait lemme try again",
        ],
    },
    "wealthy_cautious": {
        "fragment_probability": 0.15,      # Richard rarely fragments — he composes carefully
        "max_fragments": 2,
        "style": "measured_addendum",
        "inter_delay": (30, 90),           # Long pause before the addendum
        "addendum_phrases": [
            "One additional point.",
            "I should also mention",
            "My counsel would want me to add",
            "For the record",
            "Separately",
        ],
    },
}

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


def resolve_persona(name: str) -> str:
    key = name.lower().strip().replace("-", "_")
    if key in PROFILES:
        return key
    if key in ALIASES:
        return ALIASES[key]
    for alias, profile_key in ALIASES.items():
        if alias.startswith(key):
            return profile_key
    return key


_ABBREVS = re.compile(
    r'\b(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|St|vs|etc|Inc|Ltd|Corp|Rev|Gen|Gov|Sgt|Cpl|Pvt|Capt|Col|Maj|Lt|Cmdr|Adm|Ave|Blvd|Dept|Est|Fig|Mt|No|Vol|approx|dept|est)\.'
)

# Sentinel that won't appear in real text
_ABBREV_GUARD = '\x01ABBR\x01'


def _split_at_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping punctuation attached.

    Handles common abbreviations (Dr., Mr., Mrs., etc.) so they
    don't get treated as sentence boundaries.
    """
    # Temporarily mask abbreviation periods so they don't trigger a split
    guarded = _ABBREVS.sub(lambda m: m.group().replace('.', _ABBREV_GUARD), text)

    # Split on sentence-ending punctuation followed by a space
    parts = re.split(r'(?<=[.!?])\s+', guarded)

    # Restore masked periods
    restored = [p.replace(_ABBREV_GUARD, '.').strip() for p in parts]
    return [p for p in restored if p]


def _rand_delay(lo: float, hi: float) -> float:
    return round(random.uniform(lo, hi), 1)


def fragment_staccato(text: str, profile: dict) -> list[dict]:
    """Brad-style: break into rapid short bursts."""
    sentences = _split_at_sentences(text)

    if len(sentences) <= 1:
        # Try splitting on commas or "and" for short texts
        parts = re.split(r',\s+|\s+and\s+|\s+but\s+', text)
        if len(parts) <= 1:
            return [{"text": text, "delay_before": 0}]
        sentences = [p.strip() for p in parts if p.strip()]

    # Group sentences into fragments (1-2 sentences each)
    fragments = []
    i = 0
    while i < len(sentences):
        # Sometimes grab 2 sentences, sometimes just 1
        grab = 1 if random.random() < 0.6 else min(2, len(sentences) - i)
        chunk = " ".join(sentences[i:i + grab])
        fragments.append(chunk)
        i += grab

    # Cap at max_fragments
    max_f = profile["max_fragments"]
    if len(fragments) > max_f:
        # Merge excess into the last fragment
        merged = fragments[:max_f - 1]
        merged.append(" ".join(fragments[max_f - 1:]))
        fragments = merged

    # Maybe add an interjection at the start
    if random.random() < 0.3 and "excitement_interjections" in profile:
        interjection = random.choice(profile["excitement_interjections"])
        fragments.insert(0, interjection)
        if len(fragments) > max_f:
            fragments = fragments[:max_f]

    result = []
    for i, frag in enumerate(fragments):
        delay = 0 if i == 0 else _rand_delay(*profile["inter_delay"])
        result.append({"text": frag, "delay_before": delay})

    return result


def fragment_ramble_and_correct(text: str, profile: dict) -> list[dict]:
    """Edna-style: send the message, then maybe a correction or afterthought."""
    result = [{"text": text, "delay_before": 0}]

    # Maybe add an afterthought
    if random.random() < 0.5:
        phrase = random.choice(profile["afterthought_phrases"])
        delay = _rand_delay(*profile["inter_delay"])
        result.append({"text": phrase, "delay_before": delay})

    return result


def fragment_emotional_overflow(text: str, profile: dict) -> list[dict]:
    """Diane-style: one long message, sometimes an emotional overflow follow-up."""
    result = [{"text": text, "delay_before": 0}]

    if random.random() < 0.4:
        phrase = random.choice(profile["overflow_phrases"])
        delay = _rand_delay(*profile["inter_delay"])
        result.append({"text": phrase, "delay_before": delay})

    return result


def fragment_calculated_pause(text: str, profile: dict) -> list[dict]:
    """Viktor-style: one message, then a pointed follow-up."""
    sentences = _split_at_sentences(text)

    if len(sentences) <= 2:
        result = [{"text": text, "delay_before": 0}]
        if random.random() < 0.5:
            phrase = random.choice(profile["follow_up_patterns"])
            delay = _rand_delay(*profile["inter_delay"])
            result.append({"text": phrase, "delay_before": delay})
        return result

    # Split off the last sentence as a separate "pointed" message
    main = " ".join(sentences[:-1])
    follow = sentences[-1]
    return [
        {"text": main, "delay_before": 0},
        {"text": follow, "delay_before": _rand_delay(*profile["inter_delay"])},
    ]


def fragment_course_correct(text: str, profile: dict) -> list[dict]:
    """Pat-style: send, realize mistake, correct, get confused again."""
    sentences = _split_at_sentences(text)
    result = [{"text": text, "delay_before": 0}]

    # Pat often sends a correction follow-up
    if random.random() < 0.5 and "correction_phrases" in profile:
        phrase = random.choice(profile["correction_phrases"])
        delay = _rand_delay(*profile["inter_delay"])
        result.append({"text": phrase, "delay_before": delay})

    return result


def fragment_measured_addendum(text: str, profile: dict) -> list[dict]:
    """Richard-style: one composed message, rarely a formal addendum."""
    sentences = _split_at_sentences(text)
    result = [{"text": text, "delay_before": 0}]

    # Richard very rarely adds a follow-up, and when he does it's formal
    if len(sentences) > 3 and random.random() < 0.3:
        # Pull the last sentence out as a separate formal addendum
        main = " ".join(sentences[:-1])
        addendum_intro = random.choice(profile["addendum_phrases"])
        addendum = f"{addendum_intro} {sentences[-1]}"
        return [
            {"text": main, "delay_before": 0},
            {"text": addendum, "delay_before": _rand_delay(*profile["inter_delay"])},
        ]

    return result


# Map styles to fragmenter functions
FRAGMENTERS = {
    "staccato_burst": fragment_staccato,
    "ramble_and_correct": fragment_ramble_and_correct,
    "emotional_overflow": fragment_emotional_overflow,
    "calculated_pause": fragment_calculated_pause,
    "course_correct": fragment_course_correct,
    "measured_addendum": fragment_measured_addendum,
}


def fragment_message(text: str, persona: str) -> dict:
    """Fragment a message into realistic multi-message chunks.

    Args:
        text: The complete message to potentially fragment
        persona: Persona name

    Returns:
        dict with:
          - fragments: list of {text, delay_before} dicts
          - should_fragment: whether fragmentation was applied
          - total_inter_delay: sum of all inter-fragment delays
          - persona_key: resolved persona key
    """
    persona_key = resolve_persona(persona)
    profile = PROFILES.get(persona_key)

    if not profile:
        available = ", ".join(sorted(PROFILES.keys()))
        return {"error": f"Unknown persona '{persona}'. Available: {available}"}

    # Decide whether to fragment at all
    should_fragment = random.random() < profile["fragment_probability"]

    if not should_fragment or len(text) < 30:
        return {
            "fragments": [{"text": text, "delay_before": 0}],
            "should_fragment": False,
            "total_inter_delay": 0,
            "fragment_count": 1,
            "persona_key": persona_key,
        }

    # Apply the persona's fragmentation style
    style = profile["style"]
    fragmenter = FRAGMENTERS.get(style)

    if not fragmenter:
        return {
            "fragments": [{"text": text, "delay_before": 0}],
            "should_fragment": False,
            "total_inter_delay": 0,
            "fragment_count": 1,
            "persona_key": persona_key,
        }

    fragments = fragmenter(text, profile)

    # If the fragmenter produced only 1 fragment, it means the text
    # couldn't be split (e.g., single sentence with no commas).
    # Report should_fragment=False so the caller doesn't log misleading metadata.
    actually_fragmented = len(fragments) > 1

    # Calculate total inter-fragment delay
    total_inter = sum(f["delay_before"] for f in fragments)

    return {
        "fragments": fragments,
        "should_fragment": actually_fragmented,
        "total_inter_delay": round(total_inter, 1),
        "fragment_count": len(fragments),
        "persona_key": persona_key,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Split a message into realistic multi-message fragments",
    )
    parser.add_argument(
        "--persona", required=True,
        help="Persona name (e.g., confused_edna, eager_investor, diane)",
    )
    parser.add_argument(
        "--text", default="",
        help="Message to fragment (or pass via stdin)",
    )

    args = parser.parse_args()

    text = args.text
    if not text:
        text = sys.stdin.read().strip()

    if not text:
        print(json.dumps({"error": "No text provided. Use --text or pipe via stdin."}))
        sys.exit(1)

    result = fragment_message(text, args.persona)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
