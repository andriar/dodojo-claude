#!/usr/bin/env python3
"""Generate assets/theme-previews.json from DECORATIONS dict in hooks/dodojo-greet.py.

Output: 3-line ASCII preview per theme, distinguishable by bullet + tagline + divider + sig.
Color stripped — AskUserQuestion preview renders monospace markdown, not ANSI.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GREETER = REPO / "hooks" / "dodojo-greet.py"
OUT = REPO / "assets" / "theme-previews.json"


def extract_decorations() -> dict[str, dict[str, str]]:
    tree = ast.parse(GREETER.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DECORATIONS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("DECORATIONS not found in greeter")


def render(name: str, deco: dict[str, str]) -> str:
    bullet = deco["bullet"]
    tagline = deco["tagline"]
    div = deco["div"]
    sig = deco["sig"]
    bar = div * 28
    bullets = (bullet + " ") * 6
    sig_line = f"  {sig}" if sig else ""
    lines = [
        bullets.rstrip(),
        f"DODOJO · {name}",
        f"  {tagline}",
        bar,
    ]
    if sig_line:
        lines.append(sig_line)
    return "\n".join(lines)


def main() -> int:
    decos = extract_decorations()
    previews = {name: render(name, d) for name, d in decos.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(previews, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(previews)} previews → {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
