#!/usr/bin/env python3
"""Consolidated SessionStart greeter — polished edition.

Plain text via hook (silent context to Claude).
Same script renders ANSI-colored variant when called via launcher (terminal stdout).

Color enabled via env var KAGAMI_COLOR=1 (set by launcher).
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))

ALERTS = DODOJO_DATA / "alerts.jsonl"
XP_QUEUE = DODOJO_DATA / "buddy-xp-pending.jsonl"
SENSEI_STATE = Path(os.environ.get("SENSEI_STATE") or DODOJO_DATA / "dodojo" / "sensei")
SENSEI_LAST = SENSEI_STATE / "last_scored.json"
SENSEI_FB = SENSEI_STATE / "feedback.jsonl"
DRAFTS = DODOJO_DATA / "skills" / "_drafts"
SC_LOG = DODOJO_DATA / "hooks" / "smart-context.log"
SESSIONS = DODOJO_DATA / "sessions"
MEM_DIR = DODOJO_DATA / "memory"
BUDDY_POKE = DODOJO_DATA / "buddy-pokemon.md"
BUDDY_STATS = DODOJO_DATA / "buddy-stats.md"

USE_COLOR = os.environ.get("KAGAMI_COLOR", "0") == "1"

# Theme: env var KAGAMI_THEME, fallback to file ~/.claude/.kagami-theme, default "default"
def _resolve_theme() -> str:
    env = os.environ.get("KAGAMI_THEME", "").strip()
    if env:
        return env
    f = DODOJO_DATA / ".kagami-theme"
    if f.is_file():
        try:
            return f.read_text(errors="replace").strip() or "default"
        except OSError:
            pass
    return "default"


# 256-color palette via \033[38;5;Nm where N is xterm color index
def _c(idx: int) -> str:
    return f"\033[38;5;{idx}m" if USE_COLOR else ""


# Truecolor (24-bit) when terminal supports it; else nearest 256-color fallback.
USE_TRUECOLOR = USE_COLOR and os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def _rgb_to_256(r: int, g: int, b: int) -> int:
    """Approximate RGB to xterm 256-color index (6x6x6 cube + grayscale ramp)."""
    if abs(r - g) < 8 and abs(g - b) < 8:
        v = (r + g + b) // 3
        if v < 8:
            return 16
        if v > 248:
            return 231
        return 232 + (v - 8) // 10
    return 16 + 36 * (r * 5 // 255) + 6 * (g * 5 // 255) + (b * 5 // 255)


def _rgb(r: int, g: int, b: int) -> str:
    if not USE_COLOR:
        return ""
    if USE_TRUECOLOR:
        return f"\033[38;2;{r};{g};{b}m"
    return f"\033[38;5;{_rgb_to_256(r, g, b)}m"


# Icon sets: nerd (Nerd Font glyphs), unicode (universal geometric), emoji (legacy).
# Override via env KAGAMI_ICONS=nerd|unicode|emoji. Default: nerd.
ICON_SETS = {
    "nerd": {
        "brand":  "",   # nf-fa-image
        "sensei": "",   # nf-fa-graduation_cap
        "pulse":  "",   # nf-fa-bar_chart
        "memory": "",   # nf-fa-book
        "buddy":  "",   # nf-fa-smile
        "tip":    "",   # nf-fa-lightbulb
        "saved":  "",   # nf-fa-money
        "spark":  "",   # nf-fa-star
        "fire":   "",   # nf-fa-fire
        "bolt":   "",   # nf-fa-bolt
        "rocket": "",   # nf-fa-rocket
    },
    "unicode": {
        "brand":  "◆",
        "sensei": "△",
        "pulse":  "▰",
        "memory": "▢",
        "buddy":  "●",
        "tip":    "※",
        "saved":  "◈",
        "spark":  "✦",
        "fire":   "◉",
        "bolt":   "↯",
        "rocket": "▲",
    },
    "emoji": {
        "brand":  "🪞",
        "sensei": "🎓",
        "pulse":  "📊",
        "memory": "💾",
        "buddy":  "🐭",
        "tip":    "💡",
        "saved":  "💰",
        "spark":  "✨",
        "fire":   "🔥",
        "bolt":   "⚡",
        "rocket": "🚀",
    },
}

def _resolve_icon_mode() -> str:
    env = os.environ.get("KAGAMI_ICONS", "").strip().lower()
    if env in ICON_SETS:
        return env
    f = DODOJO_DATA / ".dodojo-icons"
    if f.exists():
        v = f.read_text().strip().lower()
        if v in ICON_SETS:
            return v
    # Auto-detect: env hints from terminal / Nerd Font installs
    if os.environ.get("NERD_FONT") or os.environ.get("KAGAMI_NERD"):
        return "nerd"
    try:
        import subprocess
        r = subprocess.run(["fc-list"], capture_output=True, text=True, timeout=1)
        if r.returncode == 0 and "nerd" in r.stdout.lower():
            return "nerd"
    except Exception:
        pass
    # Safe default — unicode renders on every modern terminal
    return "unicode"

ICON_MODE = _resolve_icon_mode()


def _icon(name: str) -> str:
    return ICON_SETS[ICON_MODE].get(name, "")


# Each theme: (primary, accent, success, warn, crit, info, subtle, gray)
THEMES = {
    "default": {
        "primary": _c(38),    # bold cyan
        "accent":  _c(213),   # bright magenta
        "success": _c(82),    # bright green
        "warn":    _c(220),   # gold
        "crit":    _c(196),   # red
        "info":    _c(75),    # sky blue
        "subtle":  _c(244),   # mid gray
        "gray":    _c(240),   # dim gray
    },
    "pastel": {
        "primary": _c(117),   # baby blue
        "accent":  _c(218),   # pink
        "success": _c(157),   # mint
        "warn":    _c(222),   # peach
        "crit":    _c(204),   # rose
        "info":    _c(189),   # lavender
        "subtle":  _c(252),   # light gray
        "gray":    _c(247),   # warm gray
    },
    "neon": {
        "primary": _c(51),    # electric cyan
        "accent":  _c(201),   # hot magenta
        "success": _c(118),   # lime
        "warn":    _c(226),   # neon yellow
        "crit":    _c(199),   # hot pink
        "info":    _c(45),    # bright teal
        "subtle":  _c(141),   # purple
        "gray":    _c(238),   # near-black
    },
    "retro": {
        "primary": _c(46),    # phosphor green
        "accent":  _c(82),    # bright green
        "success": _c(118),   # lime
        "warn":    _c(34),    # forest
        "crit":    _c(40),    # green-3
        "info":    _c(48),    # spring
        "subtle":  _c(28),    # dark green
        "gray":    _c(22),    # darker green
    },
    "mono": {
        "primary": "\033[1m" if USE_COLOR else "",
        "accent":  "\033[1m" if USE_COLOR else "",
        "success": "\033[1m" if USE_COLOR else "",
        "warn":    "\033[1m" if USE_COLOR else "",
        "crit":    "\033[1m" if USE_COLOR else "",
        "info":    "",
        "subtle":  "\033[2m" if USE_COLOR else "",
        "gray":    "\033[2m" if USE_COLOR else "",
    },
    "dracula": {
        "primary": _c(141),   # purple
        "accent":  _c(212),   # pink
        "success": _c(84),    # green
        "warn":    _c(228),   # yellow
        "crit":    _c(203),   # red
        "info":    _c(117),   # cyan
        "subtle":  _c(103),   # comment
        "gray":    _c(60),    # bg
    },
    "gruvbox": {
        "primary": _c(208),   # orange
        "accent":  _c(214),   # yellow-orange
        "success": _c(142),   # aqua
        "warn":    _c(214),   # yellow
        "crit":    _c(167),   # red
        "info":    _c(108),   # blue-aqua
        "subtle":  _c(245),   # gray
        "gray":    _c(239),   # dark gray
    },
    "tokyo-night": {
        "primary": _c(111),   # indigo
        "accent":  _c(176),   # coral
        "success": _c(151),   # teal
        "warn":    _c(180),   # peach
        "crit":    _c(168),   # rose
        "info":    _c(110),   # blue
        "subtle":  _c(248),   # cool gray
        "gray":    _c(238),
    },
    # === Popular dev themes (truecolor with 256-color fallback) ===
    "catppuccin": {           # soothing pastel — mocha variant
        "primary": _rgb(203, 166, 247),  # mauve
        "accent":  _rgb(245, 194, 231),  # pink
        "success": _rgb(166, 227, 161),  # green
        "warn":    _rgb(249, 226, 175),  # yellow
        "crit":    _rgb(243, 139, 168),  # red
        "info":    _rgb(137, 180, 250),  # blue
        "subtle":  _rgb(186, 194, 222),  # subtext
        "gray":    _rgb(108, 112, 134),  # overlay
    },
    "nord": {                 # arctic minimal — frost + aurora
        "primary": _rgb(136, 192, 208),  # frost cyan
        "accent":  _rgb(180, 142, 173),  # aurora purple
        "success": _rgb(163, 190, 140),  # aurora green
        "warn":    _rgb(235, 203, 139),  # aurora yellow
        "crit":    _rgb(191, 97, 106),   # aurora red
        "info":    _rgb(129, 161, 193),  # frost blue
        "subtle":  _rgb(216, 222, 233),  # snow storm
        "gray":    _rgb(76, 86, 106),    # polar night
    },
    "rose-pine": {            # soho vibes — soft mauve + gold
        "primary": _rgb(235, 188, 186),  # rose
        "accent":  _rgb(196, 167, 231),  # iris
        "success": _rgb(156, 207, 216),  # foam
        "warn":    _rgb(246, 193, 119),  # gold
        "crit":    _rgb(235, 111, 146),  # love
        "info":    _rgb(49, 116, 143),   # pine
        "subtle":  _rgb(224, 222, 244),  # text
        "gray":    _rgb(110, 106, 134),  # muted
    },
    "one-dark": {             # atom classic
        "primary": _rgb(97, 175, 239),   # blue
        "accent":  _rgb(198, 120, 221),  # magenta
        "success": _rgb(152, 195, 121),  # green
        "warn":    _rgb(229, 192, 123),  # yellow
        "crit":    _rgb(224, 108, 117),  # red
        "info":    _rgb(86, 182, 194),   # cyan
        "subtle":  _rgb(171, 178, 191),  # text
        "gray":    _rgb(92, 99, 112),    # comment
    },
    "solarized-dark": {       # low contrast, high focus
        "primary": _rgb(38, 139, 210),   # blue
        "accent":  _rgb(211, 54, 130),   # magenta
        "success": _rgb(133, 153, 0),    # green
        "warn":    _rgb(181, 137, 0),    # yellow
        "crit":    _rgb(220, 50, 47),    # red
        "info":    _rgb(42, 161, 152),   # cyan
        "subtle":  _rgb(147, 161, 161),  # base1
        "gray":    _rgb(88, 110, 117),   # base01
    },
    "monokai": {              # sublime classic
        "primary": _rgb(249, 38, 114),   # pink
        "accent":  _rgb(174, 129, 255),  # purple
        "success": _rgb(166, 226, 46),   # green
        "warn":    _rgb(230, 219, 116),  # yellow
        "crit":    _rgb(253, 151, 31),   # orange
        "info":    _rgb(102, 217, 239),  # cyan
        "subtle":  _rgb(248, 248, 242),  # fg
        "gray":    _rgb(117, 113, 94),   # comment
    },
    "github-dark": {          # default familiar
        "primary": _rgb(88, 166, 255),   # blue
        "accent":  _rgb(188, 140, 255),  # purple
        "success": _rgb(63, 185, 80),    # green
        "warn":    _rgb(210, 153, 34),   # yellow
        "crit":    _rgb(248, 81, 73),    # red
        "info":    _rgb(118, 227, 234),  # cyan
        "subtle":  _rgb(201, 209, 217),  # text
        "gray":    _rgb(139, 148, 158),  # subtle
    },

    # === Anime themes ===
    "sakura": {              # 🌸 cherry blossom — soft pink + cream
        "primary": _c(218),   # sakura pink
        "accent":  _c(225),   # blossom highlight
        "success": _c(157),   # spring green
        "warn":    _c(223),   # cream
        "crit":    _c(204),   # deep rose
        "info":    _c(189),   # sky lavender
        "subtle":  _c(254),   # rice paper
        "gray":    _c(247),   # ash
    },
    "shounen": {             # 🔥 battle vibe — bold orange/blue/red
        "primary": _c(202),   # naruto orange
        "accent":  _c(33),    # shonen blue
        "success": _c(46),    # power-up green
        "warn":    _c(214),   # gold
        "crit":    _c(196),   # dragon ball red
        "info":    _c(39),    # sky blue
        "subtle":  _c(245),   # smoke
        "gray":    _c(240),
    },
    "ghibli": {              # 🌳 studio ghibli — soft green/cream/sky
        "primary": _c(108),   # totoro green
        "accent":  _c(180),   # cream
        "success": _c(150),   # spring leaf
        "warn":    _c(186),   # haystack
        "crit":    _c(173),   # rust
        "info":    _c(116),   # mononoke sky
        "subtle":  _c(187),   # parchment
        "gray":    _c(101),   # forest shadow
    },
    "mecha": {               # 🤖 gundam — metallic gray + red + cyan
        "primary": _c(45),    # cockpit cyan
        "accent":  _c(160),   # zaku red
        "success": _c(48),    # HUD green
        "warn":    _c(220),   # caution gold
        "crit":    _c(196),   # warning red
        "info":    _c(81),    # display blue
        "subtle":  _c(244),   # steel
        "gray":    _c(238),   # gunmetal
    },
    "kawaii": {              # 🍡 pastel rainbow happy
        "primary": _c(219),   # candy pink
        "accent":  _c(159),   # mint
        "success": _c(157),   # pastel lime
        "warn":    _c(228),   # butter yellow
        "crit":    _c(217),   # peach
        "info":    _c(189),   # baby blue
        "subtle":  _c(255),   # cotton
        "gray":    _c(249),
    },
    "evangelion": {          # 🩸 NGE — purple/green/orange
        "primary": _c(99),    # eva purple
        "accent":  _c(46),    # core green
        "success": _c(82),    # AT-field
        "warn":    _c(208),   # angel orange
        "crit":    _c(160),   # blood
        "info":    _c(141),   # light purple
        "subtle":  _c(245),   # nerv gray
        "gray":    _c(238),
    },
    "demon-slayer": {        # ⚔️ Kimetsu — black/red/teal water-pattern
        "primary": _c(30),    # water-breath teal
        "accent":  _c(160),   # tanjiro red
        "success": _c(34),    # green leaf
        "warn":    _c(214),   # zenitsu yellow
        "crit":    _c(196),   # nezuko red
        "info":    _c(80),    # water
        "subtle":  _c(244),
        "gray":    _c(237),
    },
    "jjk": {                 # 🟣 Jujutsu Kaisen — domain expansion
        "primary": _c(91),    # cursed purple
        "accent":  _c(33),    # gojo blue
        "success": _c(82),    # cursed green
        "warn":    _c(214),   # binding gold
        "crit":    _c(196),   # sukuna red
        "info":    _c(75),
        "subtle":  _c(245),
        "gray":    _c(237),
    },
    "aot": {                 # ⚔ Attack on Titan — military earth
        "primary": _c(58),    # survey corps brown
        "accent":  _c(124),   # blood red
        "success": _c(28),    # forest
        "warn":    _c(178),   # wheat
        "crit":    _c(160),   # titan red
        "info":    _c(108),
        "subtle":  _c(244),
        "gray":    _c(238),
    },
    "one-piece": {           # 🏴‍☠️ pirate flag colors
        "primary": _c(196),   # luffy red
        "accent":  _c(220),   # treasure gold
        "success": _c(46),    # adventure green
        "warn":    _c(214),
        "crit":    _c(160),
        "info":    _c(33),    # ocean blue
        "subtle":  _c(252),
        "gray":    _c(240),
    },
    "chainsaw-man": {        # 🪚 chainsaw — grimy orange/red/black
        "primary": _c(202),   # chainsaw orange
        "accent":  _c(124),   # blood red
        "success": _c(70),    # power green
        "warn":    _c(214),
        "crit":    _c(196),
        "info":    _c(95),    # gritty
        "subtle":  _c(241),
        "gray":    _c(236),   # near-black
    },
    "frieren": {             # ❄ frost — purple/silver/teal
        "primary": _c(141),   # mage purple
        "accent":  _c(123),   # frost cyan
        "success": _c(157),   # spring teal
        "warn":    _c(229),   # candle gold
        "crit":    _c(168),   # rose
        "info":    _c(189),   # ice
        "subtle":  _c(252),
        "gray":    _c(244),
    },
    "madoka": {              # 🌸 magical girl — pastel pink/white/gold
        "primary": _c(218),   # madoka pink
        "accent":  _c(228),   # soul gem yellow
        "success": _c(159),   # mami green
        "warn":    _c(222),   # kyoko peach
        "crit":    _c(204),   # walpurgis rose
        "info":    _c(189),   # homura purple
        "subtle":  _c(255),   # white
        "gray":    _c(248),
    },
}

# === Decorations per theme (bullets, tagline, divider char, signature) ===
DECORATIONS = {
    "default":      {"bullet": "▸", "tagline": "mirror of work",            "div": "─", "section_div": "·", "sig": ""},
    "pastel":       {"bullet": "♡", "tagline": "soft signals",              "div": "─", "section_div": "·", "sig": ""},
    "neon":         {"bullet": "▸", "tagline": "cyber pulse",               "div": "━", "section_div": "═", "sig": "◢◤"},
    "retro":        {"bullet": ">", "tagline": "phosphor terminal",         "div": "=", "section_div": "-", "sig": "[ok]"},
    "mono":         {"bullet": "·", "tagline": "minimal",                   "div": "─", "section_div": "·", "sig": ""},
    "dracula":      {"bullet": "▸", "tagline": "after dark",                "div": "─", "section_div": "·", "sig": ""},
    "gruvbox":      {"bullet": "▸", "tagline": "warm signals",              "div": "─", "section_div": "·", "sig": ""},
    "tokyo-night":  {"bullet": "▸", "tagline": "city lights",               "div": "─", "section_div": "·", "sig": ""},

    # Popular dev themes
    "catppuccin":     {"bullet": "▸", "tagline": "soothing pastel",           "div": "─", "section_div": "·", "sig": ""},
    "nord":           {"bullet": "▸", "tagline": "arctic minimal",            "div": "─", "section_div": "·", "sig": ""},
    "rose-pine":      {"bullet": "▸", "tagline": "soho vibes",                "div": "─", "section_div": "·", "sig": ""},
    "one-dark":       {"bullet": "▸", "tagline": "atom classic",              "div": "─", "section_div": "·", "sig": ""},
    "solarized-dark": {"bullet": "▸", "tagline": "low contrast, high focus",  "div": "─", "section_div": "·", "sig": ""},
    "monokai":        {"bullet": "▸", "tagline": "sublime classic",           "div": "─", "section_div": "·", "sig": ""},
    "github-dark":    {"bullet": "▸", "tagline": "default familiar",          "div": "─", "section_div": "·", "sig": ""},

    # Anime
    "sakura":       {"bullet": "❀", "tagline": "petals on the wind",        "div": "·", "section_div": "❀", "sig": "🌸"},
    "shounen":      {"bullet": "▶", "tagline": "never give up",             "div": "━", "section_div": "═", "sig": "🔥"},
    "ghibli":       {"bullet": "✿", "tagline": "tonari no kagami",          "div": "─", "section_div": "·", "sig": "🌳"},
    "mecha":        {"bullet": "▸", "tagline": "system online",             "div": "═", "section_div": "─", "sig": "[ARM-OK]"},
    "kawaii":       {"bullet": "★", "tagline": "ganbatte yo",               "div": "·", "section_div": "♡", "sig": "(⌒‿⌒)"},
    "evangelion":   {"bullet": "►", "tagline": "AT-field engaged",          "div": "═", "section_div": "─", "sig": "NERV"},
    "demon-slayer": {"bullet": "⚔", "tagline": "total concentration",       "div": "≋", "section_div": "─", "sig": "全集中"},
    "jjk":          {"bullet": "▸", "tagline": "domain expansion",          "div": "─", "section_div": "·", "sig": "領域展開"},
    "aot":          {"bullet": "⚔", "tagline": "shinzou wo sasageyo",       "div": "─", "section_div": "·", "sig": "🪽"},
    "one-piece":    {"bullet": "☠", "tagline": "set sail",                  "div": "═", "section_div": "·", "sig": "🏴‍☠"},
    "chainsaw-man": {"bullet": "🪚", "tagline": "wake up denji",            "div": "≡", "section_div": "·", "sig": ""},
    "frieren":      {"bullet": "❄", "tagline": "1000 years of magic",       "div": "·", "section_div": "❄", "sig": "✨"},
    "madoka":       {"bullet": "✦", "tagline": "make a contract",           "div": "·", "section_div": "✧", "sig": "💫"},
}

THEME_NAME = _resolve_theme()
T = THEMES.get(THEME_NAME, THEMES["default"])
D = DECORATIONS.get(THEME_NAME, DECORATIONS["default"])

RESET = "\033[0m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""

# Semantic aliases (used in render below)
PRIMARY = T["primary"]
ACCENT = T["accent"]
GREEN = T["success"]
YELLOW = T["warn"]
RED = T["crit"]
CYAN = T["info"]
BLUE = T["info"]
MAGENTA = T["accent"]
GRAY = T["gray"]

TIPS = [
    "/audit-context — token budget snapshot",
    "/hook-health — smoke-test all hooks",
    "/recall <query> — cross-silo search (memory + git + vault)",
    "/new-skill — scaffold skill, auto-register in 5s",
    "/archive-orphans — prune unused memories (dry-run default)",
    "smart-context boosts cwd-matching memories 2× score",
    "cost-guard auto-blocks `find /` and `rm -rf ~`",
    "Sensei ingests hook telemetry — weekly digest is richer",
    "/caveman cuts response tokens ~75%",
]


def load_jsonl_n(path: Path, max_lines: int = 500) -> list[dict]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


import platform as _platform

_OS = _platform.system().lower()  # 'linux' | 'darwin' | 'windows'

# Per-OS glyph profiles. Windows fallback uses ASCII for terminals
# without proper monospace + unicode block coverage (cmd.exe, default
# Cascadia weights). macOS keeps unicode blocks (Menlo/SFMono OK).
GLYPHS = {
    # Sparkline glyphs must stay strictly within cell baseline. Lower-block
    # Unicode chars (U+2581-U+2588) bleed into adjacent rows in most popular
    # monospace fonts (JetBrains Mono, Hack, SFMono, Cascadia, MonaSpace).
    # ASCII shading set is ugly but font-safe everywhere. Bar fill / divider
    # chars stay Unicode since they only render on a single dedicated row.
    # Sparkline uses lower-block glyphs U+2581..U+2587. Drop full block
    # U+2588 — its 8/8 cell height bleeds into adjacent rows in many fonts.
    # Banner adds a blank line between sessions and tools rows for breathing
    # room; the ramp itself stays bounded to 7/8 cell height.
    "linux":   {"bars": "▁▂▃▄▅▆▇", "fill": "▰", "empty": "▱", "div": "─", "dot": "·"},
    "darwin":  {"bars": "▁▂▃▄▅▆▇", "fill": "█", "empty": "░", "div": "─", "dot": "·"},
    "windows": {"bars": "_.-=+*#@", "fill": "#", "empty": "-", "div": "-", "dot": "."},
}
G = GLYPHS.get(_OS, GLYPHS["linux"])


def sparkline(values: list[int], color: bool = True) -> str:
    """Vertical bar sparkline — magnitude via ▁▂▃▄▅▆▇ glyphs.

    Caller must give breathing room around the row (blank line above and
    below) — these glyphs visually extend slightly above the cell baseline
    in some monospace fonts and crowd adjacent rows without spacing.
    """
    bars = G["bars"]
    if not values:
        return ""
    if max(values) == 0:
        return DIM + bars[0] * len(values) + RESET
    peak = max(values)
    s = "".join(bars[min(len(bars) - 1, int(c / peak * (len(bars) - 1)))] for c in values)
    return CYAN + s + RESET if color else s


def progress_bar(cur: int, total: int, w: int = 16) -> str:
    fill, empty = G["fill"], G["empty"]
    if total <= 0:
        return DIM + empty * w + RESET
    pct = min(1.0, cur / total)
    f = int(round(pct * w))
    color = GREEN if pct >= 0.6 else YELLOW if pct >= 0.3 else RED
    return color + fill * f + RESET + DIM + empty * (w - f) + RESET


def trend_arrow(this_w: int, last_w: int) -> str:
    if last_w == 0:
        if this_w == 0:
            return DIM + "→" + RESET
        return GREEN + "↑" + RESET
    d = (this_w - last_w) / last_w
    if d > 0.20:
        return GREEN + "↑" + RESET
    if d < -0.20:
        return RED + "↓" + RESET
    return DIM + "→" + RESET


def savings_7d() -> int:
    """Quick estimate of tokens saved last 7 days."""
    # claude-mem savings
    cmem_now = 50
    try:
        cfg = json.loads((HOME / ".claude-mem" / "settings.json").read_text())
        cmem_now = int(cfg.get("CLAUDE_MEM_CONTEXT_OBSERVATIONS", 50))
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    save_per_session = max(0, (50 - cmem_now) * 250)

    # session count last 7d
    today = datetime.now().date()
    sess_count = 0
    for i in range(7):
        f = SESSIONS / f"{today - timedelta(days=i)}.jsonl"
        if f.is_file():
            sess_count += sum(1 for _ in load_jsonl_n(f, 500))
    cmem_save = save_per_session * sess_count

    # smart-context savings
    cutoff = int(time.time()) - 7 * 86400
    matched = 0
    if SC_LOG.is_file():
        for r in load_jsonl_n(SC_LOG, 1000):
            if r.get("ts", 0) >= cutoff and r.get("matched_count", 0) > 0:
                matched += 1
    smart_save = matched * 1900

    return cmem_save + smart_save


def fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def buddy_summary() -> dict:
    out = {"name": None, "level": None, "xp": None, "xp_max": None,
           "streak": 0, "total_xp": 0, "ships": 0}
    if BUDDY_POKE.is_file():
        try:
            text = BUDDY_POKE.read_text(errors="replace")
        except OSError:
            text = ""
        if text:
            m = re.search(r"\*\*Name\*\*:\s*(\S+)", text)
            if m:
                out["name"] = m.group(1)
            m = re.search(r"\*\*Level\*\*:\s*(\d+)", text)
            if m:
                out["level"] = int(m.group(1))
            m = re.search(r"\*\*XP\*\*:\s*(\d+)\s*/\s*(\d+)", text)
            if m:
                out["xp"] = int(m.group(1))
                out["xp_max"] = int(m.group(2))
    if BUDDY_STATS.is_file():
        try:
            text = BUDDY_STATS.read_text(errors="replace")
        except OSError:
            text = ""
        for k, key in [("streak", "streak"), ("total_xp_ever", "total_xp"), ("ships", "ships")]:
            m = re.search(rf"\*\*{k}\*\*:\s*(\d+)", text)
            if m:
                out[key] = int(m.group(1))
    return out


def section(title: str, emoji: str = "") -> str:
    label = f"{emoji}  {title}" if emoji else title
    return f"{BOLD}{PRIMARY}{label}{RESET}"


def main() -> int:
    now = int(time.time())
    cutoff_7d = now - 7 * 86400

    # --- Telemetry ---
    sc_recent = load_jsonl_n(SC_LOG, max_lines=300)
    sc_7d = sum(1 for r in sc_recent if r.get("ts", 0) >= cutoff_7d)

    today = datetime.now().date()
    sess_14: list[int] = []
    tools_14: list[int] = []
    files_7d = 0
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        f = SESSIONS / f"{day}.jsonl"
        records = load_jsonl_n(f) if f.is_file() else []
        sess_14.append(len(records))
        tools_14.append(sum(r.get("tool_total", 0) for r in records))
        if i <= 6:
            files_7d += sum(r.get("files_touched_count", 0) for r in records)

    sess_7 = sess_14[7:]
    tool_7 = tools_14[7:]
    sess_total = sum(sess_7)
    tool_total = sum(tool_7)
    sess_trend = trend_arrow(sum(sess_14[7:]), sum(sess_14[:7]))
    tool_trend = trend_arrow(sum(tools_14[7:]), sum(tools_14[:7]))

    # --- Memory ---
    mem_files = []
    if MEM_DIR.is_dir():
        mem_files = [f for f in MEM_DIR.glob("*.md") if f.name != "INDEX.md"]
    mem_total = len(mem_files)
    hit_paths: set[str] = set()
    for r in sc_recent:
        for m in r.get("matches", []):
            hit_paths.add(m.get("file", ""))
    mem_active = sum(1 for f in mem_files if str(f).replace(str(HOME), "~") in hit_paths)
    mem_orphans = mem_total - mem_active

    # --- Alerts ---
    alerts = [r for r in load_jsonl_n(ALERTS, 200) if not r.get("read")]
    sev = {"crit": 0, "warn": 0, "info": 0}
    for r in alerts:
        sev[r.get("severity", "info")] = sev.get(r.get("severity", "info"), 0) + 1

    # --- XP ---
    xp = [r for r in load_jsonl_n(XP_QUEUE, 200) if not r.get("claimed")]

    # --- Sensei ---
    sensei_pending = 0
    sensei_top = None
    if SENSEI_LAST.is_file():
        try:
            ls = json.loads(SENSEI_LAST.read_text())
        except (json.JSONDecodeError, OSError):
            ls = {}
        decided: set[str] = set()
        if SENSEI_FB.is_file():
            for line in SENSEI_FB.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    decided.add(json.loads(line).get("pattern_id"))
                except json.JSONDecodeError:
                    continue
        acts = [p for p in ls.get("patterns", [])
                if not p.get("informational") and p.get("id") not in decided]
        sensei_pending = len(acts)
        if acts:
            sensei_top = acts[0]
    drafts = []
    if DRAFTS.is_dir():
        drafts = [p.name for p in DRAFTS.iterdir() if p.is_dir()]

    bd = buddy_summary()

    # Auto-suppress if zero state
    if (sess_total == 0 and not alerts and not xp and sensei_pending == 0
            and not drafts and sc_7d == 0 and not bd.get("name")):
        return 0

    # === Render ===
    width = 60
    bullet = D["bullet"]
    tagline = D["tagline"]
    sig = D["sig"]
    # On Windows, force ASCII fallback for dividers regardless of theme
    div_char = G["div"] if _OS == "windows" else D["div"]
    sec_char = G["dot"] if _OS == "windows" else D["section_div"]
    sep_thin = DIM + div_char * width + RESET
    sep_dot = DIM + sec_char * width + RESET

    out: list[str] = []

    # Header
    timestamp = time.strftime("%a · %b %d · %H:%M")
    sig_part = f"  {ACCENT}{sig}{RESET}" if sig else ""
    # Read plugin version from sibling .claude-plugin/plugin.json — lets the
    # banner advertise which build is rendering, exposing stale-cache cases.
    plugin_version = "?"
    try:
        pj = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
        plugin_version = json.loads(pj.read_text()).get("version", "?")
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    out.append("")
    out.append(f"  {BOLD}{ACCENT}{_icon('brand')}  D O D O J O{RESET}   {DIM}{tagline}{RESET}  {GRAY}{DIM}[{THEME_NAME}]{RESET}{sig_part}")
    out.append(f"  {GRAY}{timestamp}{RESET}  {DIM}v{plugin_version}{RESET}")
    out.append(f"  {sep_thin}")
    out.append("")

    # Pulse
    out.append(f"  {section('Pulse', _icon('pulse'))}  {DIM}last 7 days{RESET}")
    out.append("")
    # Vertical sparkline glyphs need breathing room — insert a blank line
    # between sessions and tools so the ramps don't crowd each other.
    out.append(f"     {GRAY}sessions{RESET}   {sparkline(sess_7)}   {BOLD}{sess_total:>4}{RESET} total  {sess_trend}")
    out.append("")
    out.append(f"     {GRAY}tools   {RESET}   {sparkline(tool_7)}   {BOLD}{tool_total:>4}{RESET} calls  {tool_trend}")
    if files_7d or sc_7d:
        out.append(f"     {GRAY}also{RESET}        {files_7d} files touched · {sc_7d} memory matches")
    out.append("")

    # Memory health
    if mem_total:
        bar = progress_bar(mem_active, mem_total)
        pct = int(mem_active / mem_total * 100) if mem_total else 0
        out.append(f"  {section('Memory health', _icon('memory'))}")
        out.append("")
        out.append(f"     {bar}   {BOLD}{mem_active}{RESET}/{mem_total}  ({pct}% active)")
        if mem_orphans:
            color = YELLOW if mem_orphans > 5 else GRAY
            out.append(f"     {color}{mem_orphans} orphan{RESET}  {DIM}— /archive-orphans after telemetry warms{RESET}")
        out.append("")

    # Buddy
    if bd["name"]:
        out.append(f"  {section('Buddy', _icon('buddy'))}")
        out.append("")
        lvl = f"Lv.{bd['level']}" if bd["level"] else ""
        if bd["xp"] is not None and bd["xp_max"]:
            xpbar = progress_bar(bd["xp"], bd["xp_max"], 16)
            out.append(f"     {BOLD}{bd['name']}{RESET} {lvl}  {xpbar}  {DIM}{bd['xp']:,}/{bd['xp_max']:,}{RESET}")
        else:
            out.append(f"     {BOLD}{bd['name']}{RESET} {lvl}")
        bits = []
        if bd["streak"]:
            bits.append(f"{_icon('fire')} {bd['streak']}d")
        if bd["total_xp"]:
            bits.append(f"⚡ {bd['total_xp']:,} XP")
        if bd["ships"]:
            bits.append(f"{_icon('rocket')} {bd['ships']}")
        if bits:
            out.append(f"     {DIM}{'  ·  '.join(bits)}{RESET}")
        out.append("")

    # Alerts
    if alerts:
        if sev["crit"]:
            sym, color = "🔴", RED
        elif sev["warn"]:
            sym, color = "🟡", YELLOW
        else:
            sym, color = "🔵", BLUE
        out.append(f"  {sym}  {color}{BOLD}Alerts{RESET}  {color}{len(alerts)} unread{RESET}  {DIM}c{sev['crit']}/w{sev['warn']}/i{sev['info']}{RESET}")
        out.append("")
        for r in alerts[-3:]:
            sv = r.get("severity", "info").upper()[:4]
            src = r.get("source", "?")[:20]
            msg = r.get("message", "")[:50]
            dot = "●" if sv == "CRIT" else "○" if sv == "WARN" else "·"
            out.append(f"     {color}{dot}{RESET} [{sv}] {src}: {DIM}{msg}{RESET}")
        out.append("")

    # Sensei
    if sensei_pending or drafts:
        out.append(f"  {section('Sensei', _icon('sensei'))}")
        out.append("")
        bits = []
        if sensei_pending:
            bits.append(f"{BOLD}{sensei_pending}{RESET} pending recs")
        if drafts:
            bits.append(f"{BOLD}{len(drafts)}{RESET} draft{'s' if len(drafts) > 1 else ''}")
        out.append(f"     {' · '.join(bits)}")
        if sensei_top:
            rid = sensei_top.get("id", "?")[:28]
            sug = sensei_top.get("suggestion", "")[:40]
            score = sensei_top.get("score", 0)
            out.append(f"     {DIM}▸{RESET} [{score:.1f}] {YELLOW}{rid}{RESET}  {DIM}{sug}{RESET}")
        out.append("")

    # XP
    if xp:
        out.append(f"  {section('Pending XP', _icon('bolt'))}")
        out.append("")
        out.append(f"     {BOLD}{len(xp)}{RESET} unclaimed grant{'s' if len(xp) > 1 else ''}  {DIM}— /poke:xp <description>{RESET}")
        out.append("")

    # Quick actions
    actions = []
    if alerts:
        actions.append("review alerts")
    if xp:
        actions.append("/poke:xp")
    if sensei_pending:
        actions.append("/sensei")
    if mem_orphans > 5 and sc_7d >= 50:
        actions.append("/archive-orphans")
    if actions:
        out.append(f"  {section('Quick actions', _icon('tip'))}")
        out.append("")
        for a in actions[:4]:
            out.append(f"     {GREEN}{bullet}{RESET} {a}")
        out.append("")

    # Tip
    seed = int(datetime.now().strftime("%Y%j"))
    tip = random.Random(seed).choice(TIPS)
    out.append(f"  {sep_dot}")
    saved = savings_7d()
    if saved > 0:
        out.append(f"  {DIM}{_icon('saved')}  saved{RESET}  {GREEN}{BOLD}~{fmt_tok(saved)}{RESET} {DIM}tokens last 7d (DoDojo stack){RESET}")
    out.append(f"  {DIM}{_icon('spark')}  tip{RESET}  {tip}")
    out.append("")

    banner = "\n".join(out)
    try:
        with open("/dev/tty", "w") as tty:
            tty.write(banner + "\n")
            tty.flush()
    except OSError:
        print(banner)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
