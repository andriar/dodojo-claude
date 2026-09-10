import json
import os
from pathlib import Path

from conftest import run_hook


def _sessions_dir(data_root: Path) -> Path:
    """Canonical telemetry dir for a given DODOJO_DATA root.

    Telemetry moved out of `<DODOJO_DATA>/sessions` into
    `<DODOJO_DATA>/plugins/data/dodojo-core/sessions` (lib/paths.py) so dodojo
    stops squatting the ~/.claude namespace. Mirrors that layout rather than
    importing lib/paths, which reads the env at import time.
    """
    return data_root / "plugins" / "data" / "dodojo-core" / "sessions"


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
    sessions = list(_sessions_dir(tmp_path / "data").glob("*.jsonl"))
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
        next(_sessions_dir(tmp_path / "data").glob("*.jsonl")).read_text().strip().splitlines()[-1]
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
        next(_sessions_dir(tmp_path / "data").glob("*.jsonl")).read_text().strip().splitlines()[-1]
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
    assert not _sessions_dir(tmp_path / "data").exists()


def _turn(prompt: str, tools: list[tuple[str, str]], usage: dict | None = None) -> list[dict]:
    """One user prompt + one assistant reply issuing `tools` as (name, file_path)."""
    blocks = [
        {"type": "tool_use", "name": name, "input": ({"file_path": path} if path else {})}
        for name, path in tools
    ]
    assistant = {"type": "assistant", "message": {"role": "assistant", "content": blocks}}
    if usage is not None:
        assistant["message"]["usage"] = usage
    return [
        {"type": "user", "message": {"role": "user", "content": prompt}},
        assistant,
    ]


def _run(tmp_path: Path, records: list[dict], session_id: str = "sx"):
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(tmp_path / "data")
    r = run_hook(
        "session-summary.py",
        {"transcript_path": str(p), "session_id": session_id, "cwd": str(tmp_path)},
        env=env,
    )
    assert r.returncode == 0, r.stderr
    return json.loads(
        next(_sessions_dir(tmp_path / "data").glob("*.jsonl")).read_text().strip().splitlines()[-1]
    )


def test_counts_reads_per_file(tmp_path):
    # Sensei's repeated-file-reads pattern needs per-file read COUNTS; the
    # `files_touched` set only says a path was seen at least once.
    rec = _run(tmp_path, _turn("look at it", [
        ("Read", "/tmp/hot.py"),
        ("Read", "/tmp/hot.py"),
        ("Read", "/tmp/cold.py"),
        ("Edit", "/tmp/hot.py"),
    ]))
    assert rec["file_reads"] == {"/tmp/hot.py": 2, "/tmp/cold.py": 1}


def test_records_token_usage(tmp_path):
    rec = _run(tmp_path, _turn("do it", [("Read", "/tmp/a.py")], usage={
        "input_tokens": 500,
        "output_tokens": 250,
        "cache_read_input_tokens": 100,
        "cache_creation_input_tokens": 40,
    }))
    assert rec["tokens"] == {"input": 500, "output": 250, "cache_read": 100, "cache_write": 40}


def test_classifies_prompt_intent(tmp_path):
    # Raw prompt text is deliberately NOT stored — Sensei only needs the
    # intent buckets its heuristics key off.
    rec = _run(tmp_path, _turn("where is the router defined", [("Read", "/tmp/a.py")]))
    assert "search" in rec["prompt_intents"]
    assert "text" not in rec.get("prompt", {})
    assert rec["prompt_category"]

    rec2 = _run(tmp_path, _turn("can you explain what you mean", [("Read", "/tmp/a.py")]), "sy")
    assert "clarify" in rec2["prompt_intents"]
