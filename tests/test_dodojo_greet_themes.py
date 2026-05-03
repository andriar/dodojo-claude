"""All declared themes render greeter without crash + /dev/tty fallback path."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import HOOKS, REPO

GREET = HOOKS / "dodojo-greet.py"


def _theme_keys() -> list[str]:
    src = GREET.read_text()
    block = re.search(r"^THEMES\s*=\s*\{(.+?)^\}", src, re.M | re.S).group(1)
    return re.findall(r'^\s{4}"([a-z_]+)":\s*\{', block, re.M)


@pytest.mark.parametrize("theme", _theme_keys())
def test_theme_renders_without_crash(theme, tmp_path):
    env = {**os.environ, "KAGAMI_THEME": theme, "DODOJO_DATA": str(tmp_path), "KAGAMI_COLOR": "1"}
    res = subprocess.run(
        [sys.executable, str(GREET)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        capture_output=True, text=True, timeout=10, env=env,
    )
    assert res.returncode == 0, f"theme {theme} crashed: {res.stderr}"


@pytest.mark.parametrize("icons", ["nerd", "unicode", "emoji"])
def test_icon_modes_render(icons, tmp_path):
    env = {**os.environ, "KAGAMI_ICONS": icons, "DODOJO_DATA": str(tmp_path)}
    res = subprocess.run(
        [sys.executable, str(GREET)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        capture_output=True, text=True, timeout=10, env=env,
    )
    assert res.returncode == 0, f"icon mode {icons} crashed: {res.stderr}"


def test_dev_tty_unwritable_falls_back_to_stdout(tmp_path):
    """Simulate container/CI: /dev/tty unavailable → banner must reach stdout, no crash."""
    # Seed one session so greeter doesn't auto-suppress on zero-state.
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    from datetime import date
    (sessions / f"{date.today()}.jsonl").write_text(
        '{"ts":1,"tool_total":3,"files_touched_count":1}\n'
    )
    env = {**os.environ, "DODOJO_DATA": str(tmp_path)}
    wrapper = tmp_path / "no_tty.py"
    wrapper.write_text(
        "import builtins, runpy\n"
        "_orig = builtins.open\n"
        "def patched(path, *a, **k):\n"
        "    if str(path) == '/dev/tty':\n"
        "        raise OSError('no tty')\n"
        "    return _orig(path, *a, **k)\n"
        "builtins.open = patched\n"
        f"runpy.run_path({str(GREET)!r}, run_name='__main__')\n"
    )
    res = subprocess.run(
        [sys.executable, str(wrapper)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        capture_output=True, text=True, timeout=10, env=env,
    )
    assert res.returncode == 0, res.stderr
    assert len(res.stdout) > 50, "banner did not reach stdout fallback"
