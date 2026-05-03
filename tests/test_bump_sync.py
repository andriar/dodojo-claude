"""bump.sh keeps plugin.json + marketplace.json (metadata + plugins[]) in lock-step."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUMP = REPO / "scripts" / "bump.sh"


def test_bump_updates_all_version_locations(tmp_path):
    fake = tmp_path / "repo"
    shutil.copytree(REPO, fake, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"))
    subprocess.run(["git", "init", "-q"], cwd=fake, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=fake, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=fake, check=True)
    subprocess.run(["git", "add", "-A"], cwd=fake, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=fake, check=True)

    res = subprocess.run(
        ["bash", str(fake / "scripts" / "bump.sh"), "9.9.9", "--no-tag", "--no-sync"],
        cwd=fake, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr

    plug = json.loads((fake / ".claude-plugin" / "plugin.json").read_text())
    mkt = json.loads((fake / ".claude-plugin" / "marketplace.json").read_text())
    assert plug["version"] == "9.9.9"
    assert mkt["metadata"]["version"] == "9.9.9"
    for p in mkt["plugins"]:
        assert p["version"] == "9.9.9", f"plugin {p['name']} version not bumped"


def test_bump_rejects_non_semver(tmp_path):
    res = subprocess.run(
        ["bash", str(BUMP), "v1.2"],
        capture_output=True, text=True,
    )
    assert res.returncode != 0
    assert "semver" in res.stderr.lower()
