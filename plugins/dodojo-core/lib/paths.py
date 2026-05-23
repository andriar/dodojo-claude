"""Canonical paths for dodojo plugin.

Separates user-owned data (`~/.claude/memory/`, `~/.claude/skills/_drafts/`,
themes, alerts) from plugin-owned telemetry (sessions/, hook logs, audit state).

Plugin telemetry should live under `plugins/data/dodojo-dodojo/` per Claude Code
plugin conventions. Historically these were written directly under `~/.claude/`,
which made dodojo a namespace squatter. This module provides the new
canonical location plus legacy fallback paths so readers stay compatible
during the migration window.

Override via `DODOJO_DATA` (user-data root) and `DODOJO_TELEMETRY_HOME`
(plugin telemetry root). Default split:

    DODOJO_DATA            = ~/.claude
    DODOJO_TELEMETRY_HOME  = ~/.claude/plugins/data/dodojo-dodojo

Helpers return the *write* path (always canonical) and a list of *read* paths
(canonical first, then legacy). Writers should always use the canonical path;
readers should iterate over the legacy list to merge historical data.
"""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
USER_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
TELEMETRY_HOME = Path(
    os.environ.get("DODOJO_TELEMETRY_HOME")
    or str(USER_DATA / "plugins" / "data" / "dodojo-dodojo")
)


def sessions_dir_write() -> Path:
    return TELEMETRY_HOME / "sessions"


def sessions_dirs_read() -> list[Path]:
    return [TELEMETRY_HOME / "sessions", USER_DATA / "sessions"]


def hook_log_write(name: str) -> Path:
    return TELEMETRY_HOME / "hooks" / name


def hook_log_reads(name: str) -> list[Path]:
    return [TELEMETRY_HOME / "hooks" / name, USER_DATA / "hooks" / name]


def alerts_file() -> Path:
    # Alerts stay user-facing (read by greeter, written by heartbeat).
    return USER_DATA / "alerts.jsonl"


def memory_dir() -> Path:
    # User-owned. Never moves.
    return USER_DATA / "memory"
