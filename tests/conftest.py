"""Shared test helpers — run hook scripts as subprocesses with stdin JSON."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"


def run_hook(script: str, payload: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    path = HOOKS / script
    return subprocess.run(
        [sys.executable, str(path)] if script.endswith(".py") else [str(path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
