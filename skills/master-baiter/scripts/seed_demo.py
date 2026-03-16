# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Seed the workspace with realistic demo data for the dashboard.

Run once to populate the dashboard with sample sessions so new users
can see the full UI immediately.

Usage:
    uv run seed_demo.py
    uv run seed_demo.py --clean   # Remove demo data first
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Import from sibling modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_logger import log_evidence, update_session_state, extract_intel

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
BASE_DIR = WORKSPACE / "master-baiter"

DEMO_SESSIONS = [
    {
        "id": "demo-romance-001",
        "channel": "whatsapp",
        "sender_id": "+1-555-SCAM-01",
        "scam_type": "ROMANCE_SCAM",
        "severity": 3,
        "persona": "Lonely Heart",
        "mode": "bait",
        "messages": [
            ("inbound", "Hi there! I found your profile and you seem like a really wonderful person. My name is Jennifer."),
            ("outbound", "Oh hello! That's so sweet of you to say. I don't get many messages like this. I'm Margaret. Where are you from?"),
            ("inbound", "I'm from California but I'm working overseas as an oil rig engineer. It gets very lonely out here. I would love someone to talk to."),
            ("outbound", "Oh my, an engineer! That sounds so interesting but also very lonely. My late husband was an engineer too. What kind of work do you do on the rig?"),
            ("inbound", "I manage the drilling operations. But enough about work! Tell me about yourself Margaret. Do you have any hobbies?"),
            ("outbound", "Well I love gardening and I go to church on Sundays. Do you have a picture? I'd love to see who I'm talking to!"),
            ("inbound", "Of course! I'll send one soon. Margaret, I feel like we have a real connection. I've been thinking about you all day."),
            ("outbound", "Oh my, that's so sweet! Nobody has said anything like that to me since Harold passed. Tell me more about California!"),
            ("inbound", "I want to visit you when I get leave next month. But I have a small problem - my company card is blocked and I need to buy a plane ticket. Could you help?"),
            ("outbound", "Oh dear, that sounds terrible! How much would a ticket cost? I might be able to help... let me check with my bank first."),
        ],
        "intel": [
            ("phone", "+1-555-0191", "whatsapp"),
            ("name", "Jennifer (fake)", "whatsapp"),
            ("email", "jennifer.oilrig@gmail.com", ""),
        ],
    },
    {
        "id": "demo-crypto-002",
        "channel": "telegram",
        "sender_id": "@crypto_wealth_99",
        "scam_type": "CRYPTO_PIG_BUTCHERING",
        "severity": 3,
        "persona": "Eager Investor",
        "mode": "bait",
        "messages": [
            ("inbound", "Hello! I noticed you're interested in cryptocurrency. I've been making amazing returns with a new platform."),
            ("outbound", "Really?? I've been wanting to get into crypto but I don't know where to start! What kind of returns are we talking about?"),
            ("inbound", "I've been making 15-20% weekly! Let me show you my portfolio. The platform is called CryptoMaxPro."),
            ("outbound", "15-20% WEEKLY? That's incredible! My financial advisor says 8% annually is good. How do I sign up??"),
            ("inbound", "It's very simple. First deposit $500 to start. Here's my referral link: cryptomaxpro.io/ref/jenny99"),
            ("outbound", "OK I'm looking at the website now. It looks very professional! Should I use my Coinbase account to transfer? I have about $2000 in Bitcoin."),
            ("inbound", "Yes! Transfer to this wallet address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa. Start with $1000 for the best returns."),
            ("outbound", "Exciting!! I just need to figure out how to send from Coinbase. My nephew set it up for me. Can you walk me through it step by step?"),
        ],
        "intel": [
            ("wallet", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin"),
            ("url", "cryptomaxpro.io", "telegram"),
            ("username", "@crypto_wealth_99", "telegram"),
        ],
    },
    {
        "id": "demo-techsupport-003",
        "channel": "discord",
        "sender_id": "MicrosoftSupport#4521",
        "scam_type": "TECH_SUPPORT",
        "severity": 2,
        "persona": "Confused Edna",
        "mode": "bait",
        "messages": [
            ("inbound", "⚠️ ALERT: Your Windows license has expired. Your computer will be locked in 24 hours. Call us immediately or click here to renew."),
            ("outbound", "Oh dear! My computer is going to be locked?? My grandson Tommy usually helps me with these things but he's away at college. What do I do??"),
            ("inbound", "Don't worry ma'am. We're Microsoft certified technicians. We can fix this remotely. First, press Windows key + R and type 'cmd'."),
            ("outbound", "OK I'm looking at my keyboard... which one is the Windows key? Is it the one with the little flag? Hold on let me get my reading glasses."),
            ("inbound", "Yes, the flag key. Press it and the R key at the same time."),
            ("outbound", "I pressed it but nothing happened. Oh wait, I think I pressed the wrong R. There's two of them on my keyboard! Let me try again... OK something popped up but it's very small. I can barely read it."),
            ("inbound", "Type 'cmd' in the box and press Enter."),
            ("outbound", "C... M... D... OK I typed it but my cat Mr. Whiskers just walked across the keyboard and now it says something else. Let me start over. Actually, can you hold on? Someone's at the door."),
        ],
        "intel": [
            ("username", "MicrosoftSupport#4521", "discord"),
        ],
    },
    {
        "id": "demo-advance-fee-004",
        "channel": "email",
        "sender_id": "barrister.williams@outlook.com",
        "scam_type": "ADVANCE_FEE",
        "severity": 2,
        "persona": "Competing Scammer",
        "mode": "bait",
        "messages": [
            ("inbound", "Dear Sir/Madam, I am Barrister Williams from the Bank of England. You have been selected as the beneficiary of $4.5 million USD from a deceased client. Reply to claim."),
            ("outbound", "What a coincidence! I am ALSO a barrister and I TOO have an unclaimed $4.5 million! Perhaps we can help each other? I just need a small processing fee from you first."),
            ("inbound", "Sir, this is a legitimate inheritance. I need your full name, address, and phone number to process the claim. There is a small transfer fee of $850."),
            ("outbound", "Absolutely! But first, I should mention that MY $4.5 million requires a processing fee of only $750. Much better deal! Send me YOUR details and I'll process your inheritance AND mine."),
            ("inbound", "I do not understand. This is your money. You only need to pay the transfer fee."),
            ("outbound", "And YOUR money from MY deceased client is ready too! Tell you what — let's pool our fees. Send me $425 and I'll send you $425 and we BOTH get our $4.5 million. Sound fair?"),
        ],
        "intel": [
            ("email", "barrister.williams@outlook.com", "email"),
            ("name", "Barrister Williams (fake)", ""),
        ],
    },
    {
        "id": "demo-sextortion-005",
        "channel": "signal",
        "sender_id": "+44-7911-XXXX",
        "scam_type": "SEXTORTION",
        "severity": 4,
        "persona": "Helpful But Clueless",
        "mode": "bait",
        "messages": [
            ("inbound", "I have compromising photos of you. Send $2000 in Bitcoin to this address or I will send them to all your contacts."),
            ("outbound", "Oh no! Which photos? I take so many photos. Is it the one from my vacation? My mom really liked that one."),
            ("inbound", "Don't play games. You know exactly what photos. You have 48 hours. BTC: 3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5"),
            ("outbound", "I'm not playing games! I genuinely don't know which ones. Could you send me a preview so I know which photos you mean? Also what's a Bitcoin? Is that like Venmo?"),
        ],
        "intel": [
            ("phone", "+44-7911-XXXX", "signal"),
            ("wallet", "3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5", "bitcoin"),
        ],
    },
]


def clean_demo_data():
    """Remove all demo sessions."""
    for session in DEMO_SESSIONS:
        sid = session["id"]
        for subdir in ["sessions", "evidence", "reports"]:
            d = BASE_DIR / subdir / sid
            if d.exists():
                shutil.rmtree(d)
    print(f"Cleaned {len(DEMO_SESSIONS)} demo sessions.")


def seed():
    """Create demo data using the real evidence_logger functions."""
    for session in DEMO_SESSIONS:
        sid = session["id"]

        # Log each message
        for direction, content in session["messages"]:
            log_evidence(
                session_id=sid,
                channel=session["channel"],
                sender_id=session["sender_id"],
                direction=direction,
                content=content,
            )

        # Set session state
        update_session_state(
            session_id=sid,
            channel=session["channel"],
            sender_id=session["sender_id"],
            scam_type=session["scam_type"],
            severity=session["severity"],
            persona=session["persona"],
            mode=session["mode"],
        )
        # Fix message count to match actual messages
        state_file = BASE_DIR / "sessions" / sid / "state.json"
        state = json.loads(state_file.read_text())
        state["message_count"] = len(session["messages"])
        state_file.write_text(json.dumps(state, indent=2))

        # Extract intel
        for intel_type, value, platform in session.get("intel", []):
            extract_intel(
                session_id=sid,
                intel_type=intel_type,
                value=value,
                platform=platform,
            )

        print(f"  ✓ {sid}: {session['scam_type']} on {session['channel']} ({len(session['messages'])} messages, {len(session.get('intel', []))} intel items)")

    print(f"\nSeeded {len(DEMO_SESSIONS)} demo sessions.")
    print(f"Launch dashboard: uv run {Path(__file__).resolve().parent.parent}/server/main.py")
    print(f"Open: http://localhost:8147")


def main():
    parser = argparse.ArgumentParser(description="Seed demo data for master-baiter dashboard")
    parser.add_argument("--clean", action="store_true", help="Remove demo data before seeding")
    args = parser.parse_args()

    if args.clean:
        clean_demo_data()

    seed()


if __name__ == "__main__":
    main()
