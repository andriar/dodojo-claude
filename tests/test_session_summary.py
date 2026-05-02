import json
import os
from pathlib import Path

from conftest import run_hook


def _make_transcript(tmp: Path) -> Path:
    p = tmp / "transcript.jsonl"
    records = [
        {"type": "user", "message": {"role": "user", "content": "hi"}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "ok"},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/a.txt"}},
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/tmp/b.txt"}},
        ]}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def test_writes_session_record(tmp_path):
    transcript = _make_transcript(tmp_path)
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(tmp_path / "data")
    r = run_hook(
        "session-summary.py",
        {"transcript_path": str(transcript), "session_id": "s1", "cwd": str(tmp_path)},
        env=env,
    )
    assert r.returncode == 0
    sessions = list((tmp_path / "data" / "sessions").glob("*.jsonl"))
    assert len(sessions) == 1
    rec = json.loads(sessions[0].read_text().strip().splitlines()[-1])
    assert rec["tool_total"] == 2
    assert rec["files_touched_count"] == 2


def test_missing_transcript_silent(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(tmp_path / "data")
    r = run_hook(
        "session-summary.py",
        {"transcript_path": "/nonexistent.jsonl", "session_id": "x", "cwd": "/tmp"},
        env=env,
    )
    assert r.returncode == 0
    assert not (tmp_path / "data" / "sessions").exists()
