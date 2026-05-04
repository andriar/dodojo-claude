#!/usr/bin/env python3
"""
Test suite for Q3 Smart Tips + Sensei Phase 2 + M2 integration
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
SENSEI_DIR = Path.home() / ".claude" / "sensei"
FEEDBACK_DIR = Path.home() / ".claude" / "dodojo"

def test_tips_data():
    """Test tips.json structure"""
    print("✓ Test 1: Tips data structure")

    tips_file = PROJECT_ROOT / "data" / "tips.json"
    assert tips_file.exists(), "tips.json not found"

    with open(tips_file) as f:
        data = json.load(f)

    assert 'tips' in data, "No 'tips' key"
    assert len(data['tips']) >= 25, f"Expected 25+ tips, got {len(data['tips'])}"

    # Check each tip has required fields
    for tip in data['tips']:
        assert 'id' in tip, f"Tip {tip} missing 'id'"
        assert 'text' in tip, f"Tip {tip} missing 'text'"
        assert 'category' in tip, f"Tip {tip} missing 'category'"
        assert 'helpfulness' in tip, f"Tip {tip} missing 'helpfulness'"

    # Check categories
    categories = set(t['category'] for t in data['tips'])
    expected = {'code-review', 'search', 'memory', 'workflow', 'sensei', 'general'}
    assert categories == expected, f"Category mismatch: {categories} vs {expected}"

    print(f"  ✅ PASS ({len(data['tips'])} tips, {len(categories)} categories)")

def test_tips_selector():
    """Test tips selector script"""
    print("✓ Test 2: Tips selector script")

    selector = Path.home() / ".claude" / "scripts" / "tips-selector.py"
    assert selector.exists(), "tips-selector.py not found"

    # Test basic execution
    result = subprocess.run(
        [sys.executable, str(selector), "general"],
        capture_output=True,
        text=True,
        timeout=5
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "💡" in result.stdout, "No tip emoji in output"

    print(f"  ✅ PASS (output: {result.stdout.split(chr(10))[0][:50]}...)")

def test_sensei_analyzer():
    """Test Sensei analyzer"""
    print("✓ Test 3: Sensei analyzer")

    analyzer = Path.home() / ".claude" / "scripts" / "sensei-analyzer.py"
    assert analyzer.exists(), "sensei-analyzer.py not found"

    # Run analyzer
    result = subprocess.run(
        [sys.executable, str(analyzer)],
        capture_output=True,
        text=True,
        timeout=10
    )

    assert result.returncode == 0, f"Analyzer failed: {result.stderr}"

    # Check analysis.json created
    analysis_file = SENSEI_DIR / "analysis.json"
    assert analysis_file.exists(), "analysis.json not created"

    with open(analysis_file) as f:
        analysis = json.load(f)

    assert 'patterns' in analysis, "No patterns in analysis"
    assert len(analysis['patterns']) > 0, "No patterns detected"

    print(f"  ✅ PASS (detected {len(analysis['patterns'])} patterns)")

def test_feedback_tracking():
    """Test feedback tracking"""
    print("✓ Test 4: Feedback tracking")

    selector = Path.home() / ".claude" / "scripts" / "tips-selector.py"
    feedback_file = FEEDBACK_DIR / "tips-feedback.jsonl"

    # Clear feedback file
    if feedback_file.exists():
        feedback_file.unlink()

    # Log a feedback
    result = subprocess.run(
        [sys.executable, str(selector), "--feedback", "tip_test_001", "👍"],
        capture_output=True,
        text=True,
        timeout=5
    )

    assert result.returncode == 0, f"Feedback logging failed: {result.stderr}"
    assert feedback_file.exists(), "Feedback file not created"

    # Check feedback recorded
    with open(feedback_file) as f:
        lines = f.readlines()

    assert len(lines) > 0, "No feedback recorded"

    feedback = json.loads(lines[-1])
    assert feedback['tip_id'] == 'tip_test_001', "Wrong tip ID"
    assert feedback['rating'] == '👍', "Wrong rating"

    print(f"  ✅ PASS (feedback recorded)")

def test_greeter_hooks():
    """Test greeter hooks registration"""
    print("✓ Test 5: Greeter hooks registered")

    settings = Path.home() / ".claude" / "settings.json"
    assert settings.exists(), "settings.json not found"

    with open(settings) as f:
        config = json.load(f)

    # Check SessionStart hooks
    hooks = config.get('hooks', {}).get('SessionStart', [])
    assert len(hooks) > 0, "No SessionStart hooks"

    hook_commands = []
    for hook_group in hooks:
        for hook in hook_group.get('hooks', []):
            hook_commands.append(hook['command'])

    # Check our hooks are registered
    assert any('sensei-greeter.sh' in cmd for cmd in hook_commands), "sensei-greeter.sh not registered"
    assert any('tips-display.sh' in cmd for cmd in hook_commands), "tips-display.sh not registered"

    print(f"  ✅ PASS ({len(hook_commands)} SessionStart hooks registered)")

def test_sensei_telemetry():
    """Test Sensei telemetry collection"""
    print("✓ Test 6: Sensei telemetry")

    telemetry_file = SENSEI_DIR / "telemetry.jsonl"
    assert telemetry_file.exists(), "telemetry.jsonl not created"

    with open(telemetry_file) as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) > 0, "No telemetry records"

    # Check record structure
    sample = records[0]
    assert 'timestamp' in sample, "Missing timestamp"
    assert 'prompt' in sample, "Missing prompt"
    assert 'response' in sample, "Missing response"

    print(f"  ✅ PASS ({len(records)} telemetry records)")

def test_m2_milestone():
    """Test M2 milestone components"""
    print("✓ Test 7: M2 milestone components")

    components = {
        'Phase 5c: Categorized Memory': Path.home() / ".claude" / "memory",
        'Phase 5: Smart Context': Path.home() / ".claude" / "scripts" / "sensei-summary.py",
        'Phase 4: Auto-Archival': Path.home() / ".claude" / "scripts" / "sensei-adoption.py",
        'Phase 2: Sensei Optimizer': SENSEI_DIR / "analysis.json",
        'Q3: Smart Tips': PROJECT_ROOT / "data" / "tips.json"
    }

    passed = 0
    for name, path in components.items():
        if path.exists():
            print(f"    ✅ {name}")
            passed += 1
        else:
            print(f"    ❌ {name}")

    assert passed == len(components), f"Missing {len(components) - passed} components"
    print(f"  ✅ PASS ({passed}/{len(components)} components ready)")

def test_end_to_end():
    """End-to-end flow test"""
    print("✓ Test 8: End-to-end flow")

    print("    Simulating: SessionStart → Greeter output")

    # Step 1: Run analyzer
    analyzer = Path.home() / ".claude" / "scripts" / "sensei-analyzer.py"
    result = subprocess.run([sys.executable, str(analyzer)], capture_output=True, timeout=10)
    print(f"    1. Analyzer: {'✅' if result.returncode == 0 else '❌'}")

    # Step 2: Get Sensei summary
    summary = Path.home() / ".claude" / "scripts" / "sensei-summary.py"
    result = subprocess.run([sys.executable, str(summary)], capture_output=True, text=True, timeout=5)
    has_sensei = "SENSEI" in result.stdout
    print(f"    2. Sensei tip: {'✅' if has_sensei else '❌'}")

    # Step 3: Get daily tip
    selector = Path.home() / ".claude" / "scripts" / "tips-selector.py"
    result = subprocess.run([sys.executable, str(selector), "general"], capture_output=True, text=True, timeout=5)
    has_tip = "💡" in result.stdout
    print(f"    3. Daily tip: {'✅' if has_tip else '❌'}")

    assert has_sensei and has_tip, "Missing greeter elements"
    print(f"  ✅ PASS (full greeter flow working)")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TEST SUITE: Q3 + Sensei Phase 2 + M2 Complete")
    print("="*60 + "\n")

    tests = [
        test_tips_data,
        test_tips_selector,
        test_sensei_analyzer,
        test_feedback_tracking,
        test_greeter_hooks,
        test_sensei_telemetry,
        test_m2_milestone,
        test_end_to_end
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("✅ All tests passed. Ready to ship!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed. Fix before shipping.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
