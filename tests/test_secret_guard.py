from conftest import run_hook


def test_allows_clean_command():
    r = run_hook("secret-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "echo hello"}})
    assert r.returncode == 0


def test_blocks_aws_key():
    fake = "AKIA" + "IOSFODNN7EXAMPL"  # synthesize at runtime to dodge own guard during edit
    r = run_hook("secret-guard.sh", {"tool_name": "Write", "tool_input": {"content": fake + "X"}})
    assert r.returncode == 2
    assert "secret" in r.stderr.lower()


def test_blocks_github_pat():
    fake = "ghp_" + "a" * 36
    r = run_hook("secret-guard.sh", {"tool_name": "Write", "tool_input": {"content": "token=" + fake}})
    assert r.returncode == 2


def test_blocks_anthropic_key():
    fake = "sk-" + "ant-" + "x" * 40
    r = run_hook("secret-guard.sh", {"tool_name": "Bash", "tool_input": {"command": "export KEY=" + fake}})
    assert r.returncode == 2


def test_allows_placeholder():
    r = run_hook("secret-guard.sh", {"tool_name": "Write", "tool_input": {"content": "API_KEY=your-token-here"}})
    assert r.returncode == 0
