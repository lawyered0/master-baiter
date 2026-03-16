# Contributing to Master-Baiter

Thanks for wanting to help fight scammers. Here's how to get involved.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/master-baiter.git
cd master-baiter

# Install uv (if you don't have it)
brew install uv  # or: curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the tests
cd skills/master-baiter/scripts
uv run pytest test_evidence_logger.py -v

# Start the dashboard (for development)
cd ../server
uv run main.py
# Open http://localhost:8147
```

## Project Structure

```
skills/master-baiter/
├── SKILL.md                 # OpenClaw skill definition (frontmatter + LLM instructions)
├── scripts/                 # Python scripts called by the LLM at runtime
│   ├── evidence_logger.py   # Forensic evidence capture with SHA-256 hash chain
│   ├── hash_verify.py       # Evidence chain integrity verification
│   ├── report_*.py          # Law enforcement report generators
│   └── test_*.py            # Tests
├── references/              # Domain knowledge docs loaded on-demand by the LLM
│   ├── scam-taxonomy.md     # Scam type classification
│   ├── predator-indicators.md
│   ├── persona-strategies.md
│   ├── escalation-framework.md
│   └── reporting-formats.md
└── server/                  # Dashboard backend + frontend
    ├── main.py              # FastAPI server
    ├── models.py            # SQLAlchemy models
    ├── db.py                # Database setup
    ├── ingest.py            # File watcher (workspace JSON → SQLite)
    ├── ws.py                # WebSocket manager
    ├── routes/              # API endpoints
    └── frontend/            # SPA dashboard (vanilla JS + Chart.js)
```

## What You Can Work On

### Good First Issues

- **Add a new scam type** to `references/scam-taxonomy.md` — document the opening patterns, progression stages, and indicators
- **Add a new persona** to `references/persona-strategies.md` — create a character with delay tactics and extraction techniques
- **Improve report templates** — make IC3/FTC/NCMEC reports more accurate to the actual submission formats
- **Dashboard polish** — CSS improvements, mobile responsiveness, accessibility

### Intermediate

- **New report script** — add a report generator for a new agency or platform
- **Platform abuse reports** — add support for more platforms (Facebook, Instagram, X, etc.)
- **Intel correlation** — improve cross-session linking (same scammer, different channels)
- **Dashboard charts** — add new analytics visualizations

### Advanced

- **Conversation analysis** — improve the `references/scam-taxonomy.md` patterns for better LLM classification
- **Evidence export** — add evidence export in formats courts accept
- **Multi-language support** — scams happen in every language
- **Integration tests** — test the full skill → evidence → report pipeline

## Guidelines

### Code

- Python scripts use PEP 723 inline metadata (`# /// script`) so `uv run` works without setup
- No external dependencies in scripts unless absolutely necessary (stdlib preferred)
- The server uses FastAPI + SQLAlchemy + uvicorn
- Frontend is vanilla JS — no build step, no frameworks (keeps it simple for contributors)

### Reference Documents

These are the LLM's domain knowledge. They should be:
- **Actionable** — the LLM reads these to make decisions, not for background info
- **Structured** — use consistent headers, bullet points, tables
- **Concise** — the LLM has limited context; every paragraph must justify its tokens
- **Accurate** — wrong information here means wrong decisions in conversations

### SKILL.md

The SKILL.md body is injected directly into the LLM's context. Changes here affect behavior immediately. Be very careful with:
- Hard constraints (the NEVER rules)
- Escalation thresholds
- Persona selection logic

### Tests

- All scripts should have corresponding test files
- Use `pytest` with `tmp_path` fixture for filesystem tests
- Test both happy paths and edge cases (tampered evidence, missing files, etc.)

## Pull Request Process

1. Fork the repo and create a feature branch
2. Make your changes
3. Run the tests: `uv run pytest`
4. Open a PR with a clear description of what and why
5. Reference any related issues

## Legal Note

This tool is designed for legitimate scam baiting and predator detection. By contributing, you agree that your contributions will be used in accordance with the project's [Code of Conduct](CODE_OF_CONDUCT.md). All predator detection must remain passive (detect and report only, never entrap). All generated reports are drafts requiring human review before submission.
