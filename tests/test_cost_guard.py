from conftest import run_hook


def test_allows_safe_bash():
    r = run_hook("cost-guard.py", {"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
    assert r.returncode == 0


def test_blocks_find_root():
    r = run_hook("cost-guard.py", {"tool_name": "Bash", "tool_input": {"command": "find / -name foo"}})
    assert r.returncode == 2
    assert "find" in r.stderr.lower()


def test_blocks_rm_rf_home():
    r = run_hook("cost-guard.py", {"tool_name": "Bash", "tool_input": {"command": "rm -rf $HOME"}})
    assert r.returncode == 2


def test_blocks_read_var_log_no_limit():
    r = run_hook("cost-guard.py", {"tool_name": "Read", "tool_input": {"file_path": "/var/log/syslog"}})
    assert r.returncode == 2


def test_allows_read_var_log_with_limit():
    r = run_hook("cost-guard.py", {"tool_name": "Read", "tool_input": {"file_path": "/var/log/syslog", "limit": 200}})
    assert r.returncode == 0


def test_malformed_json_exits_zero():
    import subprocess, sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, str(repo / "hooks/cost-guard.py")], input="not-json", capture_output=True, text=True)
    assert r.returncode == 0
