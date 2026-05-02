from conftest import run_hook


def test_allows_normal_push():
    r = run_hook("force-push-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "git push origin feature-branch"}})
    assert r.returncode == 0


def test_blocks_force_push_main():
    r = run_hook("force-push-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}})
    assert r.returncode == 2


def test_blocks_force_push_master_short_flag():
    r = run_hook("force-push-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "git push -f origin master"}})
    assert r.returncode == 2


def test_blocks_force_with_lease_develop():
    r = run_hook("force-push-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "git push --force-with-lease origin develop"}})
    assert r.returncode == 2


def test_allows_force_push_feature():
    r = run_hook("force-push-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "git push -f origin my-feature"}})
    assert r.returncode == 0
