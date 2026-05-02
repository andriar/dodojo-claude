from conftest import run_hook


def test_silent_on_plain_prompt():
    r = run_hook("memory-trigger.py", {"prompt": "fix the bug in auth"})
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_fires_on_remember():
    r = run_hook("memory-trigger.py", {"prompt": "remember this for next time"})
    assert r.returncode == 0
    assert "memory-trigger" in r.stdout


def test_fires_on_indo_ingat():
    r = run_hook("memory-trigger.py", {"prompt": "ingat ini ya bro"})
    assert "memory-trigger" in r.stdout


def test_fires_on_from_now_on():
    r = run_hook("memory-trigger.py", {"prompt": "from now on use tabs"})
    assert "memory-trigger" in r.stdout


def test_too_short_prompt_silent():
    r = run_hook("memory-trigger.py", {"prompt": "hi"})
    assert r.stdout.strip() == ""
