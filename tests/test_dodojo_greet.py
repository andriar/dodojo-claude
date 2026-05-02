"""Greeter regression tests — guard against v2.1.126 IO breakage.

Bugs to never let return:
  1. Greeter wrapping output in {"systemMessage": ...} JSON envelope (raw dump)
  2. Greeter emitting valid JSON at all (it must be plain text + ANSI)
  3. .sh wrapper double-printing or re-wrapping python stdout
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"


def _run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=json.dumps({"session_id": "test", "cwd": str(REPO)}),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )


def _seed_minimal_state(data_dir: Path) -> None:
    # Greeter auto-suppresses when ALL state sources are empty (zero-state mode).
    # Seed one session record so it has something to render — enough to exercise
    # banner formatting paths without coupling to user's real ~/.claude.
    sessions = data_dir / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": 1700000000,
        "iso": "2026-04-30T00:00:00+0000",
        "session_id": "fixture",
        "cwd": "/tmp",
        "tool_counts": {"Read": 3, "Edit": 1},
        "tool_total": 4,
        "files_touched": ["/tmp/x.py"],
        "files_touched_count": 1,
        "user_chars": 100,
        "assistant_chars": 200,
    }
    (sessions / "2026-04-30.jsonl").write_text(json.dumps(rec) + "\n")


def _greet_env(tmp: Path) -> dict:
    data = tmp / "data"
    _seed_minimal_state(data)
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(data)
    env["KAGAMI_COLOR"] = "1"
    return env


def test_py_stdout_is_not_json_envelope(tmp_path):
    # Stdout must NOT parse as JSON object with systemMessage / hookSpecificOutput.
    r = _run([sys.executable, str(HOOKS / "dodojo-greet.py")], env=_greet_env(tmp_path))
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert out.strip(), "greeter produced empty stdout"
    try:
        parsed = json.loads(out)
        assert not (isinstance(parsed, dict) and ("systemMessage" in parsed or "hookSpecificOutput" in parsed)), (
            "greeter regressed — output wrapped in JSON envelope"
        )
    except json.JSONDecodeError:
        pass  # plain text expected


def test_py_stdout_contains_ansi(tmp_path):
    r = _run([sys.executable, str(HOOKS / "dodojo-greet.py")], env=_greet_env(tmp_path))
    assert r.returncode == 0
    assert "\x1b[" in r.stdout, "expected ANSI escape sequences when KAGAMI_COLOR=1"


def test_sh_passthrough_single_print(tmp_path):
    # .sh wrapper must exec python directly, NOT re-wrap output.
    sh = HOOKS / "dodojo-greet.sh"
    r = _run([str(sh)], env=_greet_env(tmp_path))
    assert r.returncode == 0, r.stderr
    out = r.stdout
    # Must not contain JSON envelope markers
    assert '"systemMessage"' not in out, "sh wrapper regressed — wrapping output in JSON"
    assert '"hookSpecificOutput"' not in out, "sh wrapper regressed — adding additionalContext"
    # Must not double-print: banner header should appear at most once
    assert out.count("D O D O J O") <= 1, "banner duplicated — double-print regression"


def test_sh_matches_py_output(tmp_path):
    # .sh exec passthrough: stdout must equal python's stdout byte-for-byte.
    env = _greet_env(tmp_path)
    py = _run([sys.executable, str(HOOKS / "dodojo-greet.py")], env=env)
    sh = _run([str(HOOKS / "dodojo-greet.sh")], env=env)
    assert py.stdout == sh.stdout, "sh wrapper diverged from python output — should be exec passthrough"
