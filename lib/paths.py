"""Canonical paths for dodojo plugin.

Separates user-owned data (`~/.claude/memory/`, `~/.claude/skills/_drafts/`,
themes, alerts) from plugin-owned telemetry (sessions/, hook logs, audit state).

Plugin telemetry should live under `plugins/data/dodojo-dodojo/` per Claude Code
plugin conventions. Historically these were written directly under `~/.claude/`,
which made dodojo a namespace squatter. This module provides the new
canonical location plus legacy fallback paths so readers stay compatible
during the migration window.

Override via `DODOJO_DATA` (user-data root) and `DODOJO_TELEMETRY_HOME`
(plugin telemetry root). Default split (Phase 4 onward):

    DODOJO_DATA            = ~/.claude
    DODOJO_TELEMETRY_HOME  = ~/.claude/plugins/data/dodojo-core

Helpers return the *write* path (always canonical) and a list of *read* paths
(canonical first, then legacy). Writers should always use the canonical path;
readers should iterate over the legacy list to merge historical data.

Read-compat chain (most-recent-canonical first):

    1. plugins/data/dodojo-core/   (Phase 4 canonical)
    2. plugins/data/dodojo-dodojo/ (Phase 1–3 canonical; pre-split plugin name)
    3. ~/.claude/sessions, ~/.claude/hooks (pre-namespace-migration, v0.4.3 and earlier)
"""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
USER_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
TELEMETRY_HOME = Path(
    os.environ.get("DODOJO_TELEMETRY_HOME")
    or str(USER_DATA / "plugins" / "data" / "dodojo-core")
)
# Legacy telemetry dir from Phase 1–3 (before plugin rename). Readers still
# pick it up so historical data is not orphaned by the dir rename.
LEGACY_TELEMETRY_HOMES = [
    USER_DATA / "plugins" / "data" / "dodojo-dodojo",
]


def sessions_dir_write() -> Path:
    return TELEMETRY_HOME / "sessions"


def sessions_dirs_read() -> list[Path]:
    dirs = [TELEMETRY_HOME / "sessions"]
    dirs.extend(legacy / "sessions" for legacy in LEGACY_TELEMETRY_HOMES)
    dirs.append(USER_DATA / "sessions")
    return dirs


def hook_log_write(name: str) -> Path:
    return TELEMETRY_HOME / "hooks" / name


def hook_log_reads(name: str) -> list[Path]:
    paths = [TELEMETRY_HOME / "hooks" / name]
    paths.extend(legacy / "hooks" / name for legacy in LEGACY_TELEMETRY_HOMES)
    paths.append(USER_DATA / "hooks" / name)
    return paths


def alerts_file() -> Path:
    # Alerts stay user-facing (read by greeter, written by heartbeat).
    return USER_DATA / "alerts.jsonl"


def memory_dir() -> Path:
    # User-owned. Never moves.
    return USER_DATA / "memory"
