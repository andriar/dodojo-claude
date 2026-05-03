import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "model-route.py"


def run_hook(prompt: str, tmp_home: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(REPO)
    env["HOME"] = str(tmp_home)
    env["DODOJO_DATA"] = str(tmp_home / ".claude")
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"prompt": prompt}),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_refactor_routes_to_hard(tmp_path):
    r = run_hook("refactor the user service into modules", tmp_path)
    assert r.returncode == 0
    assert "verdict=hard" in r.stdout
    assert "model=opus" in r.stdout


def test_lookup_routes_to_trivial(tmp_path):
    r = run_hook("where is the auth middleware defined", tmp_path)
    assert r.returncode == 0
    assert "verdict=trivial" in r.stdout
    assert "model=haiku" in r.stdout


def test_empty_prompt_silent(tmp_path):
    r = run_hook("", tmp_path)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_user_override_shadows_plugin(tmp_path):
    user_routing = tmp_path / ".claude" / "memory" / "routing"
    user_routing.mkdir(parents=True)
    (user_routing / "refactor_hard.md").write_text(
        "---\nname: override\ntype: routing\n"
        "pattern: refactor\nverdict: trivial\nwhy: test\n---\n"
    )
    r = run_hook("refactor the user service", tmp_path)
    assert r.returncode == 0
    assert "verdict=trivial" in r.stdout
    assert "src:user:refactor_hard.md" in r.stdout


def test_log_written(tmp_path):
    run_hook("where is the auth middleware", tmp_path)
    log = tmp_path / ".claude" / "hooks" / "model-route.log"
    assert log.exists()
    rec = json.loads(log.read_text().strip().splitlines()[0])
    assert rec["verdict"] == "trivial"
    assert "prompt_head" in rec
