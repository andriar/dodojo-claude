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


def test_tool_result_not_counted_as_user_prompt(tmp_path):
    # Regression: tool_result records have role=user but are not real prompts.
    # Old logic landed last_user_idx on the tool_result, slicing scan past the
    # assistant tool_use → tool_total wrongly reported as 0.
    p = tmp_path / "transcript.jsonl"
    records = [
        {"type": "user", "message": {"role": "user", "content": "do work"}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/a.txt"}},
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/tmp/b.txt"}},
            {"type": "tool_use", "name": "Bash", "input": {}},
        ]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "x", "content": "ok"},
        ]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "done"},
        ]}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(tmp_path / "data")
    r = run_hook(
        "session-summary.py",
        {"transcript_path": str(p), "session_id": "s2", "cwd": str(tmp_path)},
        env=env,
    )
    assert r.returncode == 0
    rec = json.loads(
        next((tmp_path / "data" / "sessions").glob("*.jsonl")).read_text().strip().splitlines()[-1]
    )
    assert rec["tool_total"] == 3, f"expected 3 tool calls, got {rec['tool_total']}"
    assert rec["files_touched_count"] == 2


def test_multi_turn_fixture_only_counts_last_turn(tmp_path):
    # Use the multi-turn fixture with mixed tool_use / tool_result blocks.
    # Last user prompt = "now patch file_a"; only the Edit after it counts.
    fixture = Path(__file__).parent / "fixtures" / "multi_turn_transcript.jsonl"
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(tmp_path / "data")
    r = run_hook(
        "session-summary.py",
        {"transcript_path": str(fixture), "session_id": "s3", "cwd": str(tmp_path)},
        env=env,
    )
    assert r.returncode == 0
    rec = json.loads(
        next((tmp_path / "data" / "sessions").glob("*.jsonl")).read_text().strip().splitlines()[-1]
    )
    assert rec["tool_total"] == 1, rec
    assert rec["tool_counts"] == {"Edit": 1}
    assert rec["files_touched"] == ["/repo/file_a.py"]


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
