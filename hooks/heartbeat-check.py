#!/usr/bin/env python3
"""Heartbeat check for dodojo telemetry pipeline.

SessionStart hook. Detects silent outage: if Claude transcripts are newer than
the most recent sessions/*.jsonl entry by more than HEARTBEAT_STALE_HOURS, the
Stop hook isn't firing. Writes one alert per outage window to alerts.jsonl so
the greeter surfaces it.

Idempotent: skips if an unread heartbeat alert already exists.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
SESSIONS = DODOJO_DATA / "sessions"
PROJECTS = DODOJO_DATA / "projects"
ALERTS = DODOJO_DATA / "alerts.jsonl"

STALE_HOURS = float(os.environ.get("DODOJO_HEARTBEAT_STALE_HOURS", "12"))
ALERT_SOURCE = "heartbeat"


def _latest_mtime(root: Path, glob: str) -> float:
    latest = 0.0
    if not root.is_dir():
        return latest
    for p in root.glob(glob):
        try:
            mt = p.stat().st_mtime
            if mt > latest:
                latest = mt
        except OSError:
            continue
    return latest


def _has_unread_heartbeat() -> bool:
    if not ALERTS.is_file():
        return False
    try:
        for line in ALERTS.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("source") == ALERT_SOURCE and not r.get("read"):
                return True
    except OSError:
        pass
    return False


def main() -> int:
    # Drain stdin so hook payload doesn't break Claude
    try:
        sys.stdin.read()
    except OSError:
        pass

    sessions_mt = _latest_mtime(SESSIONS, "*.jsonl")
    transcripts_mt = _latest_mtime(PROJECTS, "**/*.jsonl")

    if transcripts_mt == 0:
        return 0  # fresh install, nothing to compare

    gap_h = (transcripts_mt - sessions_mt) / 3600.0
    if gap_h < STALE_HOURS:
        return 0

    if _has_unread_heartbeat():
        return 0

    alert = {
        "ts": int(time.time()),
        "severity": "warn",
        "source": ALERT_SOURCE,
        "message": (
            f"Stop hook silent for {gap_h:.0f}h "
            f"(transcripts newer than sessions log) — run dj heartbeat or check plugin"
        ),
        "read": False,
    }

    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ALERTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert) + "\n")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
