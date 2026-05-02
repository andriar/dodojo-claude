import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "inject-git-context.sh"


def test_emits_branch_in_git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "trunk"], cwd=tmp_path, check=True)
    (tmp_path / "f").write_text("x")
    subprocess.run(["git", "add", "f"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "i"], cwd=tmp_path, check=True)

    r = subprocess.run([str(HOOK)], cwd=tmp_path, input="{}", capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    assert "branch=trunk" in r.stdout


def test_silent_outside_git(tmp_path):
    r = subprocess.run([str(HOOK)], cwd=tmp_path, input="{}", capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
