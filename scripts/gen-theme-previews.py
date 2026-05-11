#!/usr/bin/env python3
"""Generate assets/theme-previews.json from hooks/dodojo-greet.py.

Each preview = ASCII bullet/tagline/divider/sig + emoji color swatch line
mapped from the theme's xterm-256 palette. Emoji squares render in
AskUserQuestion's monospace markdown box, giving real per-theme color
distinction (raw ANSI escapes would render as garbage).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GREETER = REPO / "hooks" / "dodojo-greet.py"
OUT = REPO / "assets" / "theme-previews.json"

SWATCH_KEYS = ("primary", "accent", "success", "warn", "crit", "info")
RESET = "\033[0m"


def _ansi(rgb: tuple[int, int, int] | None) -> str:
    if rgb is None:
        return ""
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m"


def _wrap(rgb: tuple[int, int, int] | None, text: str) -> str:
    code = _ansi(rgb)
    return f"{code}{text}{RESET}" if code else text


def _xterm_to_rgb(n: int) -> tuple[int, int, int]:
    if n < 16:
        base = [
            (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
            (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
            (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
            (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
        ]
        return base[n]
    if n < 232:
        n -= 16
        steps = [0, 95, 135, 175, 215, 255]
        return steps[n // 36], steps[(n // 6) % 6], steps[n % 6]
    g = 8 + (n - 232) * 10
    return g, g, g


# Emoji swatches — RGB anchors picked so binning lands on the visually closest hue.
SWATCHES = {
    "🟥": (220, 40, 40),
    "🟧": (230, 130, 30),
    "🟨": (240, 220, 60),
    "🟩": (60, 200, 80),
    "🟦": (60, 130, 230),
    "🟪": (170, 80, 220),
    "🟫": (140, 90, 50),
    "⬛": (20, 20, 20),
    "⬜": (235, 235, 235),
}


def _nearest_emoji(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    sat = max(rgb) - min(rgb)
    # Saturated colors must not collapse to ⬜/⬛ (loses the hue).
    skip_neutrals = sat >= 50
    best = None
    best_d = 10**9
    for emoji, (er, eg, eb) in SWATCHES.items():
        if skip_neutrals and emoji in ("⬜", "⬛"):
            continue
        d = (r - er) ** 2 + (g - eg) ** 2 + (b - eb) ** 2
        if d < best_d:
            best_d = d
            best = emoji
    return best  # type: ignore[return-value]


def _extract_rgb(node: ast.AST) -> tuple[int, int, int] | None:
    """Return RGB if node is `_c(N)` or `_rgb(r,g,b)` call, else None."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        return None
    args = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, int)]
    if node.func.id == "_c" and len(args) == 1:
        return _xterm_to_rgb(args[0])
    if node.func.id == "_rgb" and len(args) == 3:
        return args[0], args[1], args[2]
    return None


def _extract_themes(tree: ast.Module) -> dict[str, dict[str, tuple[int, int, int] | None]]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "THEMES" for t in node.targets
        ):
            assert isinstance(node.value, ast.Dict)
            out: dict[str, dict[str, tuple[int, int, int] | None]] = {}
            for k, v in zip(node.value.keys, node.value.values):
                if not (isinstance(k, ast.Constant) and isinstance(v, ast.Dict)):
                    continue
                palette: dict[str, tuple[int, int, int] | None] = {}
                for pk, pv in zip(v.keys, v.values):
                    if isinstance(pk, ast.Constant):
                        palette[pk.value] = _extract_rgb(pv)
                out[k.value] = palette
            return out
    raise RuntimeError("THEMES not found in greeter")


def _extract_decorations(tree: ast.Module) -> dict[str, dict[str, str]]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DECORATIONS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("DECORATIONS not found in greeter")


def _swatch_line(palette: dict[str, tuple[int, int, int] | None]) -> str:
    cells = []
    for key in SWATCH_KEYS:
        rgb = palette.get(key)
        cells.append(_nearest_emoji(rgb) if rgb is not None else "⬜")
    return " ".join(cells)


def render(name: str, deco: dict[str, str], palette: dict[str, tuple[int, int, int] | None]) -> str:
    bullet = deco["bullet"]
    tagline = deco["tagline"]
    div = deco["div"]
    sig = deco["sig"]
    bar_raw = div * 36
    primary = palette.get("primary")
    accent = palette.get("accent")
    success = palette.get("success")
    warn = palette.get("warn")
    crit = palette.get("crit")
    info = palette.get("info")

    bar = _wrap(accent, bar_raw)
    section = lambda label: f"  {_wrap(accent, bullet)} {_wrap(primary, label)}"
    sig_tail = f"   {_wrap(crit, sig)}" if sig else ""

    lines = [
        _swatch_line(palette),
        bar,
        f"  {_wrap(accent, bullet)} {_wrap(primary, f'D O D O J O · {name}')}{sig_tail}",
        f"     {_wrap(info, tagline)}",
        bar,
        "",
        section("Memory health"),
        f"     {_wrap(success, '78 files')} · {_wrap(success, '12 reused')} this week (saved ~{_wrap(warn, '6.2k tok')})",
        f"     INDEX 142 lines · {_wrap(success, '0 orphans')} · {_wrap(warn, '1 expiring')} soon",
        "",
        section("Buddy"),
        f"     {_wrap(accent, 'Pidgey Lv.24')} · {_wrap(success, '506/800 XP')} · combo {_wrap(crit, '×3 🔥')}",
        f"     Quest: ship to production {_wrap(success, '[✓ DONE]')}",
        "",
        section("Quick actions"),
        f"     {_wrap(info, '/recall <query>')} — cross-silo search",
        f"     {_wrap(info, '/dodojo:audit')}  — context budget check",
        f"     {_wrap(info, '/poke:status')}   — buddy card",
        "",
        section("Tip"),
        f"     {_wrap(warn, 'theme-picker.sh')} runs in shell — {_wrap(success, '0 tokens')} per switch",
        bar,
    ]
    return "\n".join(lines)


def main() -> int:
    tree = ast.parse(GREETER.read_text())
    themes = _extract_themes(tree)
    decos = _extract_decorations(tree)
    previews = {
        name: render(name, d, themes.get(name, {}))
        for name, d in decos.items()
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(previews, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(previews)} previews → {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
