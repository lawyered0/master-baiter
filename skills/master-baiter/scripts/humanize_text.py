# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Inject persona-appropriate typos, autocorrect artifacts, and natural imperfections.

Takes clean AI-generated text and returns a humanized version that matches
the persona's typing style. This is the #2 anti-bot-detection layer after
response delays — too-clean text is a dead giveaway.
"""

import argparse
import json
import random
import re
import sys

# Adjacent keys on a QWERTY keyboard for realistic fat-finger typos
ADJACENT_KEYS = {
    "a": "sqwz", "b": "vghn", "c": "xdfv", "d": "sfcxer",
    "e": "wrsdf", "f": "dgcvrt", "g": "fhbvty", "h": "gjbnyu",
    "i": "ujkol", "j": "hknmui", "k": "jlmio", "l": "kop",
    "m": "njk", "n": "bhjm", "o": "iklp", "p": "ol",
    "q": "wa", "r": "etdf", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc",
    "y": "tghu", "z": "xsa",
    "1": "2q", "2": "13qw", "3": "24we", "4": "35er",
    "5": "46rt", "6": "57ty", "7": "68yu", "8": "79ui",
    "9": "80io", "0": "9op",
}

# Common autocorrect substitutions (word -> what autocorrect might "fix" it to)
AUTOCORRECT_SWAPS = {
    "well": "we'll",
    "ill": "I'll",
    "hell": "he'll",
    "were": "we're",
    "its": "it's",
    "cant": "can't",
    "wont": "won't",
    "dont": "don't",
    "form": "from",
    "teh": "the",
    "adn": "and",
    "hte": "the",
    "yuor": "your",
    "thier": "their",
    "recieve": "receive",
    "definately": "definitely",
}
# NOTE: removed "but"->"buy", "now"->"not", "duck", "shot", "sit"
# because they change meaning drastically and break the conversation.
# Real autocorrect fixes typos into real words, not swaps common words.

# Edna's tech malapropisms — she uses these instead of the real terms
EDNA_MALAPROPISMS = {
    "browser": "the Google",
    "google": "the Google",
    "chrome": "the Google",
    "email": "the email machine",
    "facebook": "the Face-space",
    "instagram": "the Insta-thingy",
    "app": "the little picture thingy",
    "download": "put it on the computer",
    "upload": "send it up to the cloud thing",
    "password": "the secret code",
    "username": "my screen name",
    "wifi": "the wi-fis",
    "internet": "the interwebs",
    "website": "the web page thingy",
    "link": "the blue clicky words",
    "screenshot": "a picture of my screen",
    "click": "push the button",
    "laptop": "my computer machine",
    "phone": "my telephone",
    "text": "the little message",
    "notification": "the ding-ding",
}

# --- Persona error profiles ---

PERSONA_PROFILES = {
    "confused_edna": {
        "typo_rate": 0.06,            # 6% of words get typos
        "double_space_rate": 0.04,     # random double spaces
        "missing_space_rate": 0.02,    # words run together
        "caps_error_rate": 0.03,       # random caps or missing caps
        "punctuation_chaos": 0.05,     # wrong punctuation, extra periods
        "autocorrect_rate": 0.0,       # Edna doesn't use autocorrect (types on a desktop)
        "malapropism_rate": 0.7,       # 70% chance of replacing tech terms
        "ellipsis_abuse": 0.15,        # replaces periods with "..."
        "trailing_space": 0.3,         # leaves trailing spaces
        "send_typo_correction": 0.2,   # chance of a "*correction" follow-up
    },
    "eager_investor": {
        "typo_rate": 0.02,
        "double_space_rate": 0.01,
        "missing_space_rate": 0.01,
        "caps_error_rate": 0.06,       # TYPES IN CAPS when excited
        "punctuation_chaos": 0.02,
        "autocorrect_rate": 0.04,
        "malapropism_rate": 0.0,
        "ellipsis_abuse": 0.0,
        "trailing_space": 0.05,
        "send_typo_correction": 0.05,
    },
    "lonely_heart": {
        "typo_rate": 0.02,
        "double_space_rate": 0.02,
        "missing_space_rate": 0.01,
        "caps_error_rate": 0.02,
        "punctuation_chaos": 0.03,
        "autocorrect_rate": 0.03,
        "malapropism_rate": 0.0,
        "ellipsis_abuse": 0.20,        # lots of "..." for emotional pauses
        "trailing_space": 0.1,
        "send_typo_correction": 0.08,
    },
    "counter_scammer": {
        "typo_rate": 0.03,
        "double_space_rate": 0.01,
        "missing_space_rate": 0.02,
        "caps_error_rate": 0.02,
        "punctuation_chaos": 0.02,
        "autocorrect_rate": 0.01,
        "malapropism_rate": 0.0,
        "ellipsis_abuse": 0.05,
        "trailing_space": 0.05,
        "send_typo_correction": 0.03,
    },
    "helpful_clueless": {
        "typo_rate": 0.05,
        "double_space_rate": 0.03,
        "missing_space_rate": 0.03,
        "caps_error_rate": 0.03,
        "punctuation_chaos": 0.04,
        "autocorrect_rate": 0.05,
        "malapropism_rate": 0.0,
        "ellipsis_abuse": 0.05,
        "trailing_space": 0.15,
        "send_typo_correction": 0.15,  # Pat corrects a lot
    },
    "wealthy_cautious": {
        "typo_rate": 0.01,            # Richard is careful
        "double_space_rate": 0.01,
        "missing_space_rate": 0.005,
        "caps_error_rate": 0.01,
        "punctuation_chaos": 0.01,
        "autocorrect_rate": 0.02,
        "malapropism_rate": 0.0,
        "ellipsis_abuse": 0.02,
        "trailing_space": 0.05,
        "send_typo_correction": 0.02,
    },
}

# Reuse aliases from delay_calculator
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
    if key in PERSONA_PROFILES:
        return key
    if key in ALIASES:
        return ALIASES[key]
    for alias, profile_key in ALIASES.items():
        if alias.startswith(key):
            return profile_key
    return key


# Patterns that should NEVER get typos injected (would break the bait)
PROTECTED_PATTERNS = re.compile(
    r'^('
    r'0x[0-9a-fA-F]{6,}'         # Crypto wallet addresses (0x...)
    r'|[13][a-km-zA-HJ-NP-Z1-9]{25,34}'  # Bitcoin addresses
    r'|[A-Z]{2,4}-\d{6,}'        # Confirmation codes (REF-12345678, WT-1234567890)
    r'|TXN-[A-Za-z0-9]{8,}'      # Transaction IDs
    r'|\d{3}[-.]?\d{3}[-.]?\d{4}'  # Phone numbers
    r'|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'  # Email addresses
    r'|\$[\d,.]+\d'               # Dollar amounts ($500.00)
    r'|\d{4,}'                    # Long number sequences (account numbers, PINs)
    r')$'
)


def _is_protected(word: str) -> bool:
    """Check if a word should be protected from typo injection."""
    clean = word.strip(".,!?;:'\"()-")
    return bool(PROTECTED_PATTERNS.match(clean))


# --- Error injection functions ---

def _adjacent_key_typo(char: str) -> str:
    """Replace a character with an adjacent key."""
    lower = char.lower()
    if lower in ADJACENT_KEYS:
        replacement = random.choice(ADJACENT_KEYS[lower])
        return replacement.upper() if char.isupper() else replacement
    return char


def _transpose(word: str) -> str:
    """Swap two adjacent characters in a word."""
    if len(word) < 3:
        return word
    # Don't transpose the first character (too obvious / unreadable)
    idx = random.randint(1, len(word) - 2)
    chars = list(word)
    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    return "".join(chars)


def _double_char(word: str) -> str:
    """Double a random character (fat finger held too long)."""
    if len(word) < 2:
        return word
    idx = random.randint(0, len(word) - 1)
    return word[:idx] + word[idx] + word[idx:]


def _drop_char(word: str) -> str:
    """Drop a random character (missed keystroke)."""
    if len(word) < 4:
        return word
    idx = random.randint(1, len(word) - 2)  # Don't drop first/last
    return word[:idx] + word[idx + 1:]


def inject_word_typo(word: str) -> str:
    """Apply a random typo to a single word."""
    if len(word) < 3:
        return word

    mutation = random.choices(
        ["adjacent", "transpose", "double", "drop"],
        weights=[0.4, 0.3, 0.15, 0.15],
        k=1,
    )[0]

    if mutation == "adjacent":
        idx = random.randint(1, len(word) - 1)  # Skip first char
        return word[:idx] + _adjacent_key_typo(word[idx]) + word[idx + 1:]
    elif mutation == "transpose":
        return _transpose(word)
    elif mutation == "double":
        return _double_char(word)
    elif mutation == "drop":
        return _drop_char(word)
    return word


def apply_autocorrect(word: str) -> str:
    """Simulate autocorrect mangling a word."""
    lower = word.lower().strip(".,!?;:'\"")
    if lower in AUTOCORRECT_SWAPS:
        replacement = AUTOCORRECT_SWAPS[lower]
        # Preserve original casing of first letter
        if word[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        # Preserve trailing punctuation
        trailing = ""
        for c in reversed(word):
            if c in ".,!?;:'\"":
                trailing = c + trailing
            else:
                break
        return replacement + trailing
    return word


def apply_malapropisms(text: str, rate: float) -> str:
    """Replace tech terms with Edna-style malapropisms.

    Handles the double-article problem: if the replacement starts with "the"
    (e.g., "the Google") and the original text has "the browser", we match
    "the browser" as a unit and replace it — avoiding "the the Google".

    Uses placeholders to prevent cascading replacements (e.g., "browser" →
    "the Google", then "google" matching the just-inserted "Google").
    """
    if rate <= 0:
        return text

    # Use placeholder tokens to prevent cascade: replacement text from one
    # malapropism shouldn't be matched by a later one.
    placeholders: dict[str, str] = {}
    counter = 0

    for term, replacement in EDNA_MALAPROPISMS.items():
        if random.random() < rate:
            placeholder = f"\x00MALAP{counter}\x00"
            counter += 1

            matched = False
            # If replacement starts with an article/possessive, first try to
            # match "the/a/an/my/your/her/his <term>" as a unit to avoid
            # "the the Google" or "your my telephone"
            if replacement.lower().startswith(("the ", "my ", "a ")):
                article_pattern = re.compile(
                    r'\b(?:the|a|an|my|your|her|his|our|their)\s+'
                    + re.escape(term) + r'\b',
                    re.IGNORECASE,
                )
                if article_pattern.search(text):
                    text = article_pattern.sub(placeholder, text)
                    matched = True

            # Replace any remaining bare occurrences
            bare_pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            if bare_pattern.search(text):
                text = bare_pattern.sub(placeholder, text)
                matched = True

            if matched:
                placeholders[placeholder] = replacement

    # Substitute all placeholders with their actual replacement text
    for placeholder, replacement in placeholders.items():
        text = text.replace(placeholder, replacement)

    return text


def humanize(text: str, persona: str, message_number: int = 1) -> dict:
    """Apply persona-appropriate imperfections to clean text.

    Args:
        text: Clean AI-generated text
        persona: Persona name
        message_number: How far into the conversation (higher = sloppier for degradation)

    Returns:
        dict with 'original', 'humanized', 'corrections', 'mutations_applied'
    """
    persona_key = resolve_persona(persona)
    profile = PERSONA_PROFILES.get(persona_key)

    if not profile:
        available = ", ".join(sorted(PERSONA_PROFILES.keys()))
        return {"error": f"Unknown persona '{persona}'. Available: {available}"}

    mutations = []

    # --- Degradation over time ---
    # After message 20+, everyone gets sloppier
    degradation_mult = 1.0
    if message_number > 20:
        degradation_mult = 1.0 + min((message_number - 20) * 0.03, 0.6)  # Up to 60% more errors
        mutations.append(f"degradation_multiplier: {degradation_mult:.2f} (message #{message_number})")

    # --- Apply malapropisms first (before word-level processing) ---
    result = apply_malapropisms(text, profile["malapropism_rate"])
    if result != text:
        mutations.append("malapropisms_applied")

    # --- Word-level processing ---
    words = result.split(" ")
    processed = []

    for i, word in enumerate(words):
        if not word:
            processed.append(word)
            continue

        # Skip very short words and words that are already "messy"
        clean_word = word.strip(".,!?;:'\"()-")

        # Skip contractions — typos on "don't" produce unnatural "dont'" artifacts
        is_contraction = "'" in clean_word

        # Typo injection (skip protected patterns like wallets, phones, emails)
        if (len(clean_word) >= 3
                and not _is_protected(word)
                and not is_contraction
                and random.random() < profile["typo_rate"] * degradation_mult):
            original_word = word
            # Find the clean part within the word to preserve surrounding punctuation
            start = word.find(clean_word)
            if start >= 0:
                prefix = word[:start]
                suffix = word[start + len(clean_word):]
            else:
                prefix = ""
                suffix = ""
            word = prefix + inject_word_typo(clean_word) + suffix
            if word != original_word:
                mutations.append(f"typo: '{original_word}' → '{word}'")

        # Autocorrect artifacts
        elif random.random() < profile["autocorrect_rate"] * degradation_mult:
            original_word = word
            word = apply_autocorrect(word)
            if word != original_word:
                mutations.append(f"autocorrect: '{original_word}' → '{word}'")

        # Random CAPS for excited personas (Brad)
        if (persona_key == "eager_investor"
                and len(clean_word) >= 3
                and random.random() < profile["caps_error_rate"]):
            word = word.upper()
            mutations.append(f"caps_excitement: '{clean_word}' → '{word}'")

        processed.append(word)

        # Double space injection
        if random.random() < profile["double_space_rate"] * degradation_mult:
            processed.append("")  # Creates a double space when joined
            mutations.append("double_space")

    result = " ".join(processed)

    # --- Sentence-level mutations ---

    # Ellipsis abuse (replace some periods with "...")
    if profile["ellipsis_abuse"] > 0:
        sentences = result.split(". ")
        if len(sentences) > 1:
            # Only attempt mid-sentence ellipsis if there are multiple sentences
            new_sentences = []
            for idx, s in enumerate(sentences):
                new_sentences.append(s)
                # Replace the ". " joiner with "... " between sentences
                if (idx < len(sentences) - 1
                        and random.random() < profile["ellipsis_abuse"] * degradation_mult):
                    # We'll rejoin with "... " instead of ". "
                    new_sentences[-1] = s.rstrip(".") + "..."
                    mutations.append("ellipsis")
            result = ". ".join(new_sentences)
        # Randomly replace trailing period with "..."
        if (random.random() < profile["ellipsis_abuse"] * degradation_mult
                and result.endswith(".")):
            result = result.rstrip(".")
            result += "..."
            mutations.append("trailing_ellipsis")

    # Missing capitalization at start (degradation effect)
    if (message_number > 15
            and random.random() < 0.15 * degradation_mult
            and result and result[0].isupper()):
        result = result[0].lower() + result[1:]
        mutations.append("dropped_initial_cap")

    # Trailing space (sloppy)
    if random.random() < profile["trailing_space"]:
        result += " "
        mutations.append("trailing_space")

    # --- Corrections ---
    # Some personas send a "*correction" as a follow-up
    correction = None
    if mutations and random.random() < profile["send_typo_correction"]:
        # Pick a random typo we made and "correct" it
        typo_mutations = [m for m in mutations if m.startswith("typo:")]
        if typo_mutations:
            # Extract the corrected word from a random typo
            m = random.choice(typo_mutations)
            # Parse "typo: 'original' → 'mangled'"
            parts = m.split("'")
            if len(parts) >= 4:
                original = parts[1]
                correction = f"*{original}"
                mutations.append(f"self_correction: {correction}")

    return {
        "original": text,
        "humanized": result,
        "correction": correction,  # Send as a follow-up message if not None
        "mutations_applied": mutations,
        "mutation_count": len(mutations),
        "persona_key": persona_key,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Inject persona-appropriate typos and imperfections into AI text",
    )
    parser.add_argument(
        "--persona", required=True,
        help="Persona name (e.g., confused_edna, eager_investor, diane)",
    )
    parser.add_argument(
        "--text", default="",
        help="Text to humanize (or pass via stdin)",
    )
    parser.add_argument(
        "--message-number", type=int, default=1,
        help="Message number in conversation (higher = sloppier). Default: 1",
    )

    args = parser.parse_args()

    text = args.text
    if not text:
        text = sys.stdin.read().strip()

    if not text:
        print(json.dumps({"error": "No text provided. Use --text or pipe via stdin."}))
        sys.exit(1)

    result = humanize(text, args.persona, args.message_number)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
