import os
from pathlib import Path

from conftest import run_hook


def _make_skills_dir(tmp: Path) -> Path:
    sk = tmp / "skills" / "pr-describe"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        '---\nname: pr-describe\ndescription: Generate Pull Request title and summary from git diff\n---\n\nbody\n',
        encoding="utf-8",
    )
    return tmp


def test_silent_no_match(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_skills_dir(tmp_path))
    r = run_hook("skill-suggest.py", {"prompt": "completely unrelated topic xyz"}, env=env)
    assert r.returncode == 0
    assert "skill-suggest" not in r.stdout


def test_hints_on_match(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_skills_dir(tmp_path))
    r = run_hook(
        "skill-suggest.py",
        {"prompt": "draft a pull request title summary from git diff"},
        env=env,
    )
    assert r.returncode == 0
    assert "pr-describe" in r.stdout


def test_too_short_silent(tmp_path):
    env = os.environ.copy()
    env["DODOJO_DATA"] = str(_make_skills_dir(tmp_path))
    r = run_hook("skill-suggest.py", {"prompt": "pr"}, env=env)
    assert r.stdout.strip() == ""
