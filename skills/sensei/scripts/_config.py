"""Sensei path resolution — env-driven, plugin-portable.

Defaults assume plugin install. Override any var to relocate state, vault,
shell history, or repo roots. Read-only `HOME` (skill sources, templates) is
auto-inferred from `${CLAUDE_PLUGIN_ROOT}` if the script lives inside a plugin
cache, otherwise falls back to the script parent.
"""
from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # .../skills/sensei/scripts
_DEFAULT_HOME = _HERE.parent  # .../skills/sensei

HOME = Path(os.environ.get("SENSEI_HOME") or _DEFAULT_HOME).resolve()
STATE = Path(os.environ.get("SENSEI_STATE") or Path.home() / ".claude" / "dodojo" / "sensei").resolve()
VAULT = Path(os.environ.get("SENSEI_VAULT") or Path.home() / "Documents" / "Obsidian Vault" / "Sensei").resolve()
HISTORY = Path(os.environ.get("SENSEI_HISTORY") or Path.home() / ".zsh_history").resolve()
REPOS = [Path(p).expanduser().resolve() for p in (os.environ.get("SENSEI_REPOS") or str(Path.home() / "Development")).split(":") if p]

# Standard files
RAW = STATE / "raw.tsv"
WEIGHTS = STATE / "weights.json"
FEEDBACK = STATE / "feedback.jsonl"
PATTERNS_SEEN = STATE / "patterns_seen.json"
LAST_SCORED = STATE / "last_scored.json"
RULES = STATE / "rules.json"
EXCLUSIONS = STATE / "exclusions.txt"

TEMPLATES = HOME / "templates"
SCRIPTS = HOME / "scripts"


def ensure_state_dir() -> None:
    STATE.mkdir(parents=True, exist_ok=True)


def seed_state_from_home() -> None:
    """Copy default state files (weights.json, exclusions.txt, rules.json) from
    plugin HOME into user STATE if missing. Lets first run work without manual setup.
    """
    ensure_state_dir()
    home_state = HOME / "state"
    if not home_state.is_dir():
        return
    for fname in ("weights.json", "rules.json", "exclusions.txt"):
        src = home_state / fname
        dst = STATE / fname
        if src.is_file() and not dst.exists():
            dst.write_bytes(src.read_bytes())
