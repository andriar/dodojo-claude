"""Unit tests for greeter renderer helpers.

These freeze behavior of small pure functions so the upcoming v0.3.4 split
of dodojo-greet.py into modules can be verified mechanically.

Each function is imported from the monolith via importlib (the file uses a
hyphen so it is not a regular module name).
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GREET = REPO / "hooks" / "dodojo-greet.py"


def _greet_module():
    # Force color OFF so renderers return plain glyphs (test assertions assume this).
    for k in ("KAGAMI_COLOR", "KAGAMI_THEME", "KAGAMI_ICONS"):
        os.environ.pop(k, None)
    os.environ["KAGAMI_COLOR"] = "0"
    spec = importlib.util.spec_from_file_location("greet", GREET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G = _greet_module()


def test_sparkline_known_sequence():
    # 7-step ramp (▁▂▃▄▅▆▇), peak capped at ▇ (no full block).
    # values=[1..5], peak=5, len(bars)-1=6 → indices 1,2,3,4,6 → ▂▃▄▅▇.
    assert G.sparkline([1, 2, 3, 4, 5], color=False) == "▂▃▄▅▇"


def test_sparkline_no_full_block():
    # Regression: full block U+2588 (█) bleeds — must be excluded from ramp.
    assert "█" not in G.sparkline([1, 5, 10, 100], color=False)


def test_sparkline_empty_returns_empty():
    assert G.sparkline([], color=False) == ""


def test_sparkline_all_zero_uses_lowest_bar():
    assert G.sparkline([0, 0, 0], color=False) == "▁▁▁"


def test_sparkline_peak_is_top_of_ramp():
    # Peak value renders as ▇ (last char of "▁▂▃▄▅▆▇").
    out = G.sparkline([1, 1, 100], color=False)
    assert out.endswith("▇")


def test_progress_bar_partial():
    assert G.progress_bar(7, 10, w=10) == "▰" * 7 + "▱" * 3


def test_progress_bar_full():
    assert G.progress_bar(10, 10, w=5) == "▰" * 5


def test_progress_bar_empty():
    assert G.progress_bar(0, 10, w=5) == "▱" * 5


def test_progress_bar_overflow_clamps_to_full():
    # Guard: cur > total must NOT produce extra chars / negative remainder.
    assert G.progress_bar(100, 10, w=5) == "▰" * 5


def test_trend_arrow_up():
    assert G.trend_arrow(10, 5) == "↑"


def test_trend_arrow_down():
    assert G.trend_arrow(2, 10) == "↓"


def test_trend_arrow_flat():
    assert G.trend_arrow(5, 5) == "→"


def test_fmt_tok_under_1k():
    assert G.fmt_tok(950) == "950"


def test_fmt_tok_thousand():
    assert G.fmt_tok(50_000) == "50K"


def test_fmt_tok_million():
    assert G.fmt_tok(1_234_567) == "1.2M"


def test_fmt_tok_zero():
    assert G.fmt_tok(0) == "0"


def test_section_contains_title_and_emoji():
    s = G.section("Pulse", "⚡")
    assert "Pulse" in s
    assert "⚡" in s
