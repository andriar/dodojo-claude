import os
import tempfile
from pathlib import Path

from conftest import run_hook


def _make_data_dir(tmp: Path) -> Path:
    mem = tmp / "memory"
    mem.mkdir(parents=True)
    (mem / "docker_bridge_ufw.md").write_text(
        "---\nname: docker bridge ufw block\ndescription: UFW blocks docker bridge to host port\n---\n\nUFW default-deny silently drops bridge traffic to host ports.\n",
        encoding="utf-8",
    )
    (mem / "INDEX.md").write_text("- pointer only, should be excluded\n", encoding="utf-8")
    return tmp


def test_silent_on_short_prompt(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_data_dir(tmp_path))
    r = run_hook("smart-context.py", {"prompt": "hi", "cwd": "/tmp"}, env=env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_matches_relevant_memory(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_data_dir(tmp_path))
    r = run_hook(
        "smart-context.py",
        {"prompt": "docker bridge ufw blocking host port", "cwd": "/tmp"},
        env=env,
    )
    assert r.returncode == 0
    assert "smart-context" in r.stdout
    assert "docker" in r.stdout.lower()


def test_excludes_index_files(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_data_dir(tmp_path))
    r = run_hook(
        "smart-context.py",
        {"prompt": "pointer only excluded", "cwd": "/tmp"},
        env=env,
    )
    assert "INDEX" not in r.stdout
