"""hooks.json: every registered command resolves to an executable file under hooks/."""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO / "hooks.json"
PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"


def _commands() -> list[tuple[str, str]]:
    cfg = json.loads(HOOKS_JSON.read_text())
    out = []
    for event, arr in cfg.get("hooks", {}).items():
        for matcher in arr:
            for h in matcher.get("hooks", []):
                cmd = h.get("command", "")
                out.append((event, cmd))
    return out


def test_hooks_json_parses():
    json.loads(HOOKS_JSON.read_text())


def test_every_command_uses_plugin_root_token():
    for event, cmd in _commands():
        assert cmd.startswith(PLUGIN_ROOT_TOKEN), (
            f"{event}: {cmd!r} must start with {PLUGIN_ROOT_TOKEN}"
        )


def test_every_command_resolves_and_executable():
    for event, cmd in _commands():
        rel = cmd.replace(PLUGIN_ROOT_TOKEN + "/", "")
        path = REPO / rel
        assert path.is_file(), f"{event}: {path} missing"
        assert os.access(path, os.X_OK), f"{event}: {path} not executable"


def test_every_hook_has_timeout():
    cfg = json.loads(HOOKS_JSON.read_text())
    for event, arr in cfg.get("hooks", {}).items():
        for matcher in arr:
            for h in matcher.get("hooks", []):
                assert "timeout" in h, f"{event}: {h.get('command')} missing timeout"
                assert 1000 <= h["timeout"] <= 30000
