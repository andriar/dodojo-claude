"""Sensei analyzer against the session-summary telemetry store.

The old input — `sensei/telemetry.jsonl`, written by `sensei-telemetry.sh` —
was never registered as a hook and could not write even when run directly
(its heredoc `python3` received no argv, so the transcript path was always
None). Sensei now reads the session records that `session-summary.py`
already writes on every Stop.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANALYZER = REPO / "scripts" / "sensei-analyzer.py"


def _sessions_dir(data_root: Path) -> Path:
    return data_root / "plugins" / "data" / "dodojo-core" / "sessions"


def _write_sessions(data_root: Path, records: list[dict]) -> None:
    d = _sessions_dir(data_root)
    d.mkdir(parents=True, exist_ok=True)
    with (d / (time.strftime("%Y-%m-%d") + ".jsonl")).open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _record(**over) -> dict:
    rec = {
        "v": 3,
        "ts": int(time.time()),
        "session_id": "s1",
        "cwd": "/tmp",
        "tool_counts": {"Read": 3},
        "tool_total": 3,
        "files_touched": [],
        "file_reads": {},
        "tokens": {"input": 500, "output": 250, "cache_read": 0, "cache_write": 0},
        "prompt_intents": [],
        "prompt_category": "general",
        "user_chars": 40,
        "assistant_chars": 80,
        "memories_injected": [],
    }
    rec.update(over)
    return rec


def _run(data_root: Path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(data_root)
    r = subprocess.run([sys.executable, str(ANALYZER)], capture_output=True, text=True,
                       timeout=10, env=env)
    assert r.returncode == 0, r.stderr
    return json.loads((data_root / "sensei" / "analysis.json").read_text())


def _types(analysis) -> set[str]:
    return {p["type"] for p in analysis.get("patterns", [])}


def test_detects_repeated_file_reads(tmp_path):
    _write_sessions(tmp_path, [
        _record(file_reads={"/tmp/hot.py": 2}),
        _record(session_id="s2", file_reads={"/tmp/hot.py": 3}),
    ])
    analysis = _run(tmp_path)
    assert "repeated-file-reads" in _types(analysis)
    hit = next(p for p in analysis["patterns"] if p["type"] == "repeated-file-reads")
    assert hit["file"] == "/tmp/hot.py"
    assert hit["reads_count"] == 5


def test_detects_tool_misuse_from_intent(tmp_path):
    _write_sessions(tmp_path, [
        _record(prompt_intents=["search"], tool_counts={"Read": 4}),
    ])
    assert "tool-misuse" in _types(_run(tmp_path))


def test_detects_follow_up_chain(tmp_path):
    _write_sessions(tmp_path, [
        _record(session_id="s1", prompt_intents=[]),
        _record(session_id="s2", prompt_intents=["clarify"]),
        _record(session_id="s3", prompt_intents=["clarify"]),
        _record(session_id="s4", prompt_intents=["clarify"]),
    ])
    assert "follow-up-chain" in _types(_run(tmp_path))


def test_ignores_records_older_than_window(tmp_path):
    old = int(time.time()) - 60 * 60 * 24 * 30
    _write_sessions(tmp_path, [_record(ts=old, file_reads={"/tmp/hot.py": 9})])
    analysis = _run(tmp_path)
    assert analysis.get("patterns", []) == []


def test_still_reads_legacy_telemetry(tmp_path):
    # Historical sensei/telemetry.jsonl must not be orphaned.
    sensei = tmp_path / "sensei"
    sensei.mkdir(parents=True)
    (sensei / "telemetry.jsonl").write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "prompt": {"text": "where is routing", "text_length": 16, "category": "search"},
        "response": {"input": 500, "output": 250},
        "files_accessed": [{"path": "/tmp/legacy.py", "reads": 4}],
        "tools_used": [{"name": "Read", "count": 4}],
    }) + "\n", encoding="utf-8")
    analysis = _run(tmp_path)
    assert "repeated-file-reads" in _types(analysis)
