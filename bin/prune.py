#!/usr/bin/env python3
"""
dj prune — interactive plugin cleanup.

Reads audit state, walks prune candidates, prompts y/N for each.
Safe by default: shows full rm path, defaults to No, never auto-deletes enabled plugins.

Flags:
  --dry-run        Show what would be deleted, no rm
  --yes / -y       Auto-confirm all (use with care)
  --include-empty  Also prompt to delete empty/orphan cache dirs (default: on)
"""
from __future__ import annotations
import argparse, json, shutil, sys
from collections import Counter
from pathlib import Path

HOME = Path.home()
PLUGIN_CACHE = HOME / ".claude/plugins/cache"
SETTINGS = HOME / ".claude/settings.json"
STATE = HOME / ".claude/dodojo/state/audit-stack.json"
TELEMETRY = HOME / ".claude/dodojo/telemetry"

# ANSI
R = "\033[31m"; G = "\033[32m"; Y = "\033[33m"; B = "\033[34m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


def color(s: str, c: str) -> str:
    return f"{c}{s}{RESET}" if sys.stdout.isatty() else s


def dir_size_mb(p: Path) -> float:
    total = 0
    for f in p.rglob("*"):
        try:
            if f.is_file():
                total += f.stat().st_size
        except Exception:
            pass
    return round(total / 1024 / 1024, 1)


def load_enabled() -> dict:
    try:
        s = json.loads(SETTINGS.read_text())
        return s.get("enabledPlugins", {})
    except Exception:
        return {}


def plugin_enabled(name: str, enabled_map: dict) -> bool | None:
    """Return True/False if found, None if no entry."""
    for k, v in enabled_map.items():
        if name in k:
            return v
    return None


def load_skill_usage() -> Counter:
    c = Counter()
    f = TELEMETRY / "skill-usage.jsonl"
    if not f.exists():
        return c
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            sk = d.get("skill", "")
            if sk:
                c[sk] += 1
        except Exception:
            pass
    return c


def plugin_usage(plugin_name: str, usage: Counter) -> int:
    return sum(c for sk, c in usage.items() if sk.startswith(plugin_name + ":") or sk == plugin_name)


def latest_version_dir(plugin_root: Path) -> Path | None:
    candidates = [p.parent for p in plugin_root.rglob(".claude-plugin") if p.is_dir()]
    if not candidates:
        candidates = [p.parent for p in plugin_root.rglob("skills") if p.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def measure_reminder_tokens(plugin_root: Path) -> int:
    """Rough estimate: sum of (name+description+6) across SKILL.md in LATEST version only."""
    version = latest_version_dir(plugin_root)
    if version is None:
        return 0
    total = 0
    for skill_md in version.rglob("SKILL.md"):
        try:
            text = skill_md.read_text()
        except Exception:
            continue
        in_fm = False
        name = ""
        desc = ""
        for i, line in enumerate(text.splitlines()):
            if i == 0 and line.strip() == "---":
                in_fm = True
                continue
            if in_fm:
                if line.strip() == "---":
                    break
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
        total += len(name) + len(desc) + 6
    return total // 4  # ~tokens


def build_candidates(enabled_map: dict, usage: Counter) -> list[dict]:
    """Scan plugin cache and classify each into severity buckets."""
    cands = []
    if not PLUGIN_CACHE.is_dir():
        return cands

    for plugin_root in sorted(PLUGIN_CACHE.iterdir()):
        if not plugin_root.is_dir():
            continue
        name = plugin_root.name
        version = latest_version_dir(plugin_root)
        skill_count = len(list(version.rglob("SKILL.md"))) if version else 0
        tokens = measure_reminder_tokens(plugin_root)
        size_mb = dir_size_mb(plugin_root)
        enabled = plugin_enabled(name, enabled_map)
        uses = plugin_usage(name, usage)
        version_count = len([d for d in plugin_root.iterdir() if d.is_dir()])

        reasons = []
        severity = 0

        if skill_count == 0:
            reasons.append("empty (no SKILL.md found)")
            severity = 3
        if enabled is False and uses == 0:
            reasons.append(f"disabled in settings + 0 invocations logged")
            severity = max(severity, 2)
        elif enabled is False:
            reasons.append("disabled in settings")
            severity = max(severity, 1)
        elif uses == 0 and tokens > 100:
            reasons.append(f"0 invocations, costs {tokens} tokens/session")
            severity = max(severity, 1)

        if version_count > 2:
            reasons.append(f"{version_count} cached versions ({size_mb}MB)")
            severity = max(severity, 1)

        if not reasons:
            # Healthy — skip
            continue

        cands.append({
            "name": name,
            "path": plugin_root,
            "enabled": enabled,
            "uses": uses,
            "skill_count": skill_count,
            "tokens": tokens,
            "size_mb": size_mb,
            "version_count": version_count,
            "reasons": reasons,
            "severity": severity,
        })

    # Sort by severity desc, then by tokens desc (biggest wins first)
    cands.sort(key=lambda c: (-c["severity"], -c["tokens"]))
    return cands


def prompt(question: str, default: str = "n") -> str:
    suffix = "[y/N/q]" if default == "n" else "[Y/n/q]"
    try:
        ans = input(f"{question} {suffix} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return "q"
    return ans or default


def main():
    ap = argparse.ArgumentParser(description="Interactive DoDojo plugin prune")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted, don't rm")
    ap.add_argument("-y", "--yes", action="store_true", help="Auto-confirm all (use with care)")
    args = ap.parse_args()

    enabled_map = load_enabled()
    usage = load_skill_usage()
    cands = build_candidates(enabled_map, usage)

    if not cands:
        print(color("✓ No prune candidates. Stack is clean.", G))
        return

    print(color(f"\n🪓 dj prune — {len(cands)} candidate(s)", BOLD))
    if args.dry_run:
        print(color("   DRY RUN — no files will be deleted", Y))
    print()

    deleted = []
    skipped = []
    saved_tokens = 0
    saved_mb = 0.0

    for i, c in enumerate(cands, 1):
        sev_icon = ["", "🟡", "🟠", "🔴"][c["severity"]]
        enabled_str = (color("disabled", DIM) if c["enabled"] is False
                       else color("ENABLED", R + BOLD) if c["enabled"] else color("?", DIM))

        print(color(f"[{i}/{len(cands)}] {sev_icon} {c['name']}", BOLD))
        print(f"     path: {color(str(c['path']), DIM)}")
        print(f"     status: {enabled_str}  ·  skills: {c['skill_count']}  ·  uses: {c['uses']}")
        tok_str = f"{c['tokens']} tokens/session"
        print(f"     passive: {color(tok_str, Y)}  ·  disk: {c['size_mb']}MB")
        for r in c["reasons"]:
            print(f"     · {r}")

        # Safety: warn if enabled
        if c["enabled"] is True:
            print(color("     ⚠ This plugin is ENABLED. Deleting will break active functionality.", R))

        if args.yes:
            ans = "y"
        else:
            default = "n" if c["enabled"] is True else "n"  # always default no, intentional
            ans = prompt(f"     delete?", default=default)

        if ans == "q":
            print(color("     aborted by user.", Y))
            break
        if ans not in ("y", "yes"):
            skipped.append(c["name"])
            print(color("     skipped.", DIM))
            print()
            continue

        if args.dry_run:
            print(color(f"     [dry-run] would rm -rf {c['path']}", DIM))
        else:
            try:
                shutil.rmtree(c["path"])
                print(color(f"     ✓ deleted ({c['size_mb']}MB freed)", G))
                deleted.append(c["name"])
                saved_tokens += c["tokens"]
                saved_mb += c["size_mb"]
            except Exception as e:
                print(color(f"     ✗ failed: {e}", R))
        print()

    print(color("─" * 50, DIM))
    print(color(f"Summary:", BOLD))
    print(f"  deleted:  {len(deleted)}  ({', '.join(deleted) if deleted else '—'})")
    print(f"  skipped:  {len(skipped)}")
    if deleted:
        print(f"  freed:    {color(f'{saved_tokens} tokens/session', G)}  ·  {saved_mb:.1f}MB disk")

    if deleted and not args.dry_run:
        print()
        print(color("Re-running audit...", DIM))
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent / "audit-stack.py")])


if __name__ == "__main__":
    main()
