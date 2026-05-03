#!/usr/bin/env python3
"""Audit companion plugins recommended alongside DoDojo.

Read-only — never writes settings.json. Detects via installed_plugins.json.
Exit 0 always (advisory).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

INSTALLED = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

COMPANIONS = [
    {
        "name": "caveman",
        "role": "Output compression — ~75% token saving on long sessions",
        "install": "/plugin install caveman@caveman",
        "marketplace_hint": "caveman",
    },
    {
        "name": "claude-mem",
        "role": "Cross-session deep recall + AST code nav + multi-phase planner",
        "install": "/plugin install claude-mem@thedotmack",
        "marketplace_hint": "thedotmack",
    },
    {
        "name": "poke",
        "alias": "pokemon-buddy-claude",
        "role": "Gamification — XP, badges, raids on dev work",
        "install": "/plugin install poke@pokemon-buddy-claude",
        "marketplace_hint": "pokemon-buddy",
    },
]

C_OK = "\033[32m"
C_WARN = "\033[33m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def color(text: str, code: str) -> str:
    return f"{code}{text}{C_RESET}" if use_color() else text


def load_installed() -> dict[str, str]:
    """Return {plugin_name: full_key} from installed_plugins.json."""
    if not INSTALLED.exists():
        return {}
    try:
        data = json.loads(INSTALLED.read_text())
    except json.JSONDecodeError:
        return {}
    out = {}
    for full_key in data.get("plugins", {}).keys():
        name = full_key.split("@", 1)[0]
        out[name] = full_key
    return out


def main() -> int:
    installed = load_installed()
    print(color("DoDojo companion plugins audit", C_BOLD))
    print("=" * 60)

    present = 0
    for c in COMPANIONS:
        names = [c["name"]] + ([c["alias"]] if "alias" in c else [])
        match = next((installed[n] for n in names if n in installed), None)
        label = c["name"].ljust(14)
        if match:
            present += 1
            print(f"  {color('✓', C_OK)} {label} {color('installed', C_DIM)} ({match})")
        else:
            print(f"  {color('✗', C_WARN)} {label} {color('missing', C_WARN)} — {c['role']}")
            print(f"       {color(c['install'], C_DIM)}")

    total = len(COMPANIONS)
    print()
    summary = f"{present}/{total} recommended companions present"
    print(color(summary, C_BOLD if present == total else C_WARN))
    if present < total:
        print(color("Optional — DoDojo works fully standalone.", C_DIM))
    return 0


if __name__ == "__main__":
    sys.exit(main())
