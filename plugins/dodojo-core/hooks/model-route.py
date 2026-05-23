#!/usr/bin/env python3
"""model-route: classify UserPromptSubmit prompt → emit routing hint.

Loads rules from two locations (user wins on conflict):
  1. ${HOME}/.claude/memory/routing/*.md  (user overrides)
  2. ${CLAUDE_PLUGIN_ROOT}/routing/*.md   (plugin defaults)

Falls back to built-in heuristics if no rule matches.
Emits one-line hint to stdout (becomes additionalContext).
Logs decisions to ${DODOJO_DATA:-~/.claude}/hooks/model-route.log (jsonl)
for the route-tune skill / Sensei to mine.
"""
from __future__ import annotations
import json, os, re, sys, time
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or "")

USER_RULES = HOME / ".claude" / "memory" / "routing"
PLUGIN_RULES = PLUGIN_ROOT / "routing" if PLUGIN_ROOT else None
LOG = DODOJO_DATA / "hooks" / "model-route.log"

VERDICTS = {
    "trivial": ("haiku", "light", "spawn Agent(haiku) instead of working in main thread"),
    "medium":  ("sonnet", "normal", "current model fine; proceed"),
    "hard":    ("opus", "deep", "task heavy — consider /model opus before deep work"),
}

BUILTIN = [
    (r"\b(refactor|architect|design|migrat|rewrite|untangle|redesign)\b", "hard"),
    (r"\b(plan|strategy|tradeoff|decide|approach|deep dive)\b",            "hard"),
    (r"\b(security|auth flow|cryptograph|exploit|threat model)\b",         "hard"),
    (r"\b(typo|rename|format|lint|fix import|comment)\b",                  "trivial"),
    (r"\b(what is|where is|find|locate|grep|show me)\b",                   "trivial"),
    (r"\b(list|cat|read file|print)\b",                                    "trivial"),
]


def parse_rule(path: Path) -> dict | None:
    try:
        text = path.read_text()
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    try:
        _, fm, _ = text.split("---", 2)
    except ValueError:
        return None
    meta: dict = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    if "pattern" not in meta or "verdict" not in meta:
        return None
    try:
        meta["_re"] = re.compile(meta["pattern"], re.IGNORECASE)
    except re.error:
        return None
    meta["_file"] = path.name
    meta["_src"] = "user" if USER_RULES in path.parents else "plugin"
    return meta


def load_rules() -> list[dict]:
    rules: list[dict] = []
    seen_names: set[str] = set()
    # User first (override priority)
    for d in [USER_RULES, PLUGIN_RULES]:
        if not d or not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name.upper() == "INDEX.MD":
                continue
            r = parse_rule(f)
            if not r:
                continue
            # Dedup by filename — user file shadows plugin file of same name
            if r["_file"] in seen_names:
                continue
            seen_names.add(r["_file"])
            rules.append(r)
    return rules


def classify(prompt: str) -> tuple[str, str]:
    p = prompt.strip()
    for rule in load_rules():
        if rule["_re"].search(p):
            return rule["verdict"], f"{rule['_src']}:{rule['_file']}"
    for pat, verdict in BUILTIN:
        if re.search(pat, p, re.IGNORECASE):
            return verdict, "builtin"
    n = len(p)
    if n < 80:
        return "trivial", "len-default"
    if n > 600:
        return "hard", "len-default"
    return "medium", "default"


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    prompt = payload.get("prompt") or payload.get("user_prompt") or ""
    if not prompt:
        return 0

    verdict, source = classify(prompt)
    model, effort, advice = VERDICTS[verdict]

    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({
                "ts": int(time.time()),
                "verdict": verdict, "source": source,
                "model": model, "effort": effort,
                "prompt_len": len(prompt),
                "prompt_head": prompt[:120],
            }) + "\n")
    except Exception:
        pass

    print(f"[model-route] verdict={verdict} → suggest model={model} effort={effort} ({advice}) [src:{source}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
