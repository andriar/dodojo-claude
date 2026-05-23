#!/usr/bin/env python3
"""
dj audit-stack — measure passive context cost of installed plugins + base layer.

Pure script. Zero Claude tokens. Output: Markdown report.
"""
from __future__ import annotations
import json, os, re, sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
PLUGIN_CACHE = HOME / ".claude/plugins/cache"
SETTINGS = HOME / ".claude/settings.json"
TELEMETRY = HOME / ".claude/dodojo/telemetry"
REPORTS = HOME / ".claude/dodojo/reports"
CHARS_PER_TOKEN = 4

BASE_LAYER_FILES = [
    HOME / ".claude/CLAUDE.md",
    HOME / ".claude/RTK.md",
    HOME / ".claude/memory/INDEX.md",
    HOME / ".claude/skills/README.md",
    HOME / ".claude/hooks/README.md",
]


def tok(byte_count: int) -> int:
    return byte_count // CHARS_PER_TOKEN


def read_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text())
    except Exception:
        return {}


def latest_version_dir(plugin_root: Path) -> Path | None:
    """Find the deepest dir containing skills/ or .claude-plugin/ — most-recent by mtime."""
    candidates = []
    for p in plugin_root.rglob(".claude-plugin"):
        if p.is_dir():
            candidates.append(p.parent)
    if not candidates:
        # fallback: any dir with skills/ subdir
        for p in plugin_root.rglob("skills"):
            if p.is_dir():
                candidates.append(p.parent)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def measure_skill_frontmatter(skill_md: Path) -> tuple[str, str, int]:
    """Return (name, description, frontmatter_bytes_estimate_in_system_reminder)."""
    try:
        text = skill_md.read_text()
    except Exception:
        return ("", "", 0)
    name = ""
    desc = ""
    in_fm = False
    fm_lines = 0
    fm_bytes = 0
    for i, line in enumerate(text.splitlines()):
        if i == 0 and line.strip() == "---":
            in_fm = True
            continue
        if in_fm:
            if line.strip() == "---":
                break
            fm_lines += 1
            fm_bytes += len(line) + 1
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
    # System reminder line per skill is roughly: "- <plugin>:<name>: <description>"
    # which is shorter than full frontmatter. Estimate the reminder line.
    reminder_line_bytes = len(name) + len(desc) + 6
    return (name, desc, reminder_line_bytes)


def measure_plugin(plugin_root: Path) -> dict:
    """Measure a single plugin's passive cost."""
    name = plugin_root.name
    version_dir = latest_version_dir(plugin_root)
    if version_dir is None:
        return {
            "name": name, "version_dir": None, "skill_count": 0,
            "reminder_bytes": 0, "reminder_tokens": 0,
            "skills": [], "commands_count": 0, "disk_mb": 0,
            "version_count": 0,
        }

    skill_md_files = list(version_dir.rglob("SKILL.md"))
    skills = []
    total_bytes = 0
    for s in skill_md_files:
        sn, sd, b = measure_skill_frontmatter(s)
        skills.append({"name": sn, "desc": sd, "bytes": b, "path": str(s.relative_to(HOME))})
        total_bytes += b

    cmd_dir = version_dir / "commands"
    cmd_count = len(list(cmd_dir.glob("*"))) if cmd_dir.is_dir() else 0

    # Disk usage (parent plugin_root, not just version)
    disk_kb = 0
    for f in plugin_root.rglob("*"):
        try:
            if f.is_file():
                disk_kb += f.stat().st_size
        except Exception:
            pass

    # Count cached versions
    version_count = len([d for d in plugin_root.iterdir() if d.is_dir()]) if plugin_root.is_dir() else 0

    return {
        "name": name,
        "version_dir": str(version_dir.relative_to(HOME)),
        "skill_count": len(skills),
        "reminder_bytes": total_bytes,
        "reminder_tokens": tok(total_bytes),
        "skills": skills,
        "commands_count": cmd_count,
        "disk_mb": round(disk_kb / 1024 / 1024, 1),
        "version_count": version_count,
    }


def measure_base_layer() -> list[dict]:
    out = []
    for f in BASE_LAYER_FILES:
        if f.exists():
            b = f.stat().st_size
            out.append({
                "file": str(f.relative_to(HOME)),
                "bytes": b,
                "tokens": tok(b),
                "lines": sum(1 for _ in f.open()),
            })
    return out


def measure_project_memory(cwd: Path) -> list[dict]:
    """Look for project-specific MEMORY.md (used by warungku, etc.)."""
    out = []
    # User's project memory dir convention
    project_slug = str(cwd).replace("/", "-")
    proj_mem = HOME / f".claude/projects/{project_slug}/memory/MEMORY.md"
    if proj_mem.exists():
        b = proj_mem.stat().st_size
        out.append({
            "file": str(proj_mem.relative_to(HOME)),
            "bytes": b,
            "tokens": tok(b),
            "lines": sum(1 for _ in proj_mem.open()),
        })
    # In-repo CLAUDE.md / AGENTS.md
    for name in ("CLAUDE.md", "AGENTS.md"):
        p = cwd / name
        if p.exists():
            b = p.stat().st_size
            out.append({
                "file": str(p),
                "bytes": b,
                "tokens": tok(b),
                "lines": sum(1 for _ in p.open()),
            })
    return out


def read_telemetry() -> dict:
    skill_usage = Counter()
    plugin_usage = Counter()
    session_count = 0
    sessions_with_data = []

    s_file = TELEMETRY / "skill-usage.jsonl"
    if s_file.exists():
        for line in s_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                sk = d.get("skill", "")
                if sk:
                    skill_usage[sk] += 1
                pl = d.get("plugin", "") or ("_custom" if sk and ":" not in sk else "")
                if pl:
                    plugin_usage[pl] += 1
            except Exception:
                pass

    sess_file = TELEMETRY / "sessions.jsonl"
    if sess_file.exists():
        session_count = sum(1 for line in sess_file.read_text().splitlines() if line.strip())

    summary_file = TELEMETRY / "session-summary.jsonl"
    if summary_file.exists():
        for line in summary_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                sessions_with_data.append(json.loads(line))
            except Exception:
                pass

    return {
        "skill_usage": dict(skill_usage),
        "plugin_usage": dict(plugin_usage),
        "session_count": session_count,
        "sessions_with_data": sessions_with_data,
    }


def recommendation(plugin: dict, enabled_map: dict, usage: dict) -> str:
    """Pick a one-word recommendation per plugin."""
    name = plugin["name"]
    # Match settings.json plugin keys ("<plugin>@<marketplace>")
    enabled = None
    for key, val in enabled_map.items():
        # key like "caveman@caveman" — plugin part is before @
        if name in key:
            enabled = val
            break

    usage_count = sum(c for sk, c in usage.get("skill_usage", {}).items()
                      if sk.startswith(name + ":") or sk in (p.get("name", "") for p in plugin["skills"]))

    if plugin["skill_count"] == 0 and plugin["commands_count"] == 0:
        return "🗑 EMPTY (delete cache)"
    if enabled is False:
        return "🟡 disabled in settings (verify still in context?)"
    if plugin["version_count"] > 2:
        return f"🧹 prune {plugin['version_count']-1} old versions ({plugin['disk_mb']}MB)"
    if usage_count == 0:
        return "🔴 0 invocations — candidate for uninstall"
    if usage_count < 3:
        return f"🟡 only {usage_count} uses — review"
    return f"🟢 keep ({usage_count} uses)"


def render_report(plugins: list[dict], base: list[dict], proj_mem: list[dict],
                  enabled_map: dict, usage: dict, cwd: Path) -> str:
    total_base = sum(f["tokens"] for f in base)
    total_proj = sum(f["tokens"] for f in proj_mem)
    total_plugin = sum(p["reminder_tokens"] for p in plugins)
    total_passive = total_base + total_proj + total_plugin

    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

    lines = []
    lines.append(f"# DoDojo Stack Audit\n")
    lines.append(f"Generated: `{ts}` · cwd: `{cwd}`\n")
    lines.append("---\n")
    lines.append(f"## Headline\n")
    lines.append(f"**Total passive load per session: ~{total_passive:,} tokens**\n")
    lines.append(f"- Base layer (CLAUDE.md + @-refs): **{total_base:,} tokens**")
    lines.append(f"- Project layer (in-repo): **{total_proj:,} tokens**")
    lines.append(f"- Plugin layer (skill descriptions): **{total_plugin:,} tokens**\n")
    sessions = usage.get("session_count", 0)
    if sessions:
        monthly = total_passive * sessions * 30 // max(sessions, 1)
        lines.append(f"_Telemetry: {sessions} sessions logged so far._\n")

    lines.append("\n## Base layer (auto-loaded every session)\n")
    lines.append("| File | Lines | ~Tokens |")
    lines.append("|---|---:|---:|")
    for f in sorted(base, key=lambda x: -x["tokens"]):
        lines.append(f"| `~/{f['file']}` | {f['lines']} | {f['tokens']:,} |")
    lines.append(f"| **Subtotal** | | **{total_base:,}** |\n")

    if proj_mem:
        lines.append("\n## Project layer (loaded when in this cwd)\n")
        lines.append("| File | Lines | ~Tokens |")
        lines.append("|---|---:|---:|")
        for f in sorted(proj_mem, key=lambda x: -x["tokens"]):
            lines.append(f"| `{f['file']}` | {f['lines']} | {f['tokens']:,} |")
        lines.append(f"| **Subtotal** | | **{total_proj:,}** |\n")

    lines.append("\n## Plugin layer (skill descriptions in system reminder)\n")
    lines.append("| Plugin | Enabled | Skills | Cmds | ~Tokens | Disk | Versions | Recommendation |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for p in sorted(plugins, key=lambda x: -x["reminder_tokens"]):
        rec = recommendation(p, enabled_map, usage)
        enabled = "?"
        for key, val in enabled_map.items():
            if p["name"] in key:
                enabled = "✓" if val else "✗"
                break
        lines.append(
            f"| `{p['name']}` | {enabled} | {p['skill_count']} | {p['commands_count']} | "
            f"{p['reminder_tokens']:,} | {p['disk_mb']}MB | {p['version_count']} | {rec} |"
        )
    lines.append(f"| **Subtotal** | | | | **{total_plugin:,}** | | | |\n")

    # Usage telemetry summary
    sk_usage = usage.get("skill_usage", {})
    if sk_usage:
        lines.append("\n## Skill usage (from telemetry)\n")
        lines.append("| Skill | Invocations |")
        lines.append("|---|---:|")
        for sk, c in sorted(sk_usage.items(), key=lambda x: -x[1]):
            lines.append(f"| `{sk}` | {c} |")
    else:
        lines.append("\n## Skill usage\n")
        lines.append("_No skill invocations logged yet. Telemetry just turned on._\n")

    # Session summary
    sessions_data = usage.get("sessions_with_data", [])
    if sessions_data:
        lines.append("\n## Recent session token cost (real data)\n")
        lines.append("| Session ts | Repo | Prompts | Input | Output | Cache Read | Cache Write |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for s in sessions_data[-10:]:
            t = s.get("tokens", {})
            lines.append(
                f"| {s.get('ts','')[:19]} | {s.get('repo','')} | {s.get('prompts',0)} | "
                f"{t.get('input',0):,} | {t.get('output',0):,} | "
                f"{t.get('cache_read',0):,} | {t.get('cache_write',0):,} |"
            )

    # Prune list
    lines.append("\n## 🪓 Prune candidates (ordered by impact)\n")
    cands = []
    for p in plugins:
        if p["skill_count"] == 0 and p["commands_count"] == 0:
            cands.append((9999, p, "empty plugin cache"))
            continue
        usage_count = sum(c for sk, c in sk_usage.items() if sk.startswith(p["name"] + ":"))
        if usage_count == 0 and p["reminder_tokens"] > 100:
            cands.append((p["reminder_tokens"], p, f"unused, costs {p['reminder_tokens']} tokens/session"))
        if p["version_count"] > 2:
            est_saved = (p["version_count"] - 1) * (p["disk_mb"] / max(p["version_count"], 1))
            cands.append((int(est_saved * 100), p, f"{p['version_count']-1} stale versions, ~{est_saved:.1f}MB"))

    cands.sort(key=lambda x: -x[0])
    if cands:
        for _, p, why in cands[:10]:
            lines.append(f"- **{p['name']}** — {why}")
    else:
        lines.append("_None — your stack is lean._")

    lines.append("\n---\n")
    lines.append(f"_Run again: `~/.claude/dodojo/bin/dj audit`_")
    return "\n".join(lines)


def main():
    cwd = Path.cwd()
    settings = read_settings()
    enabled_map = settings.get("enabledPlugins", {})

    plugins = []
    if PLUGIN_CACHE.is_dir():
        for plugin_root in sorted(PLUGIN_CACHE.iterdir()):
            if plugin_root.is_dir():
                plugins.append(measure_plugin(plugin_root))

    base = measure_base_layer()
    proj_mem = measure_project_memory(cwd)
    usage = read_telemetry()

    report = render_report(plugins, base, proj_mem, enabled_map, usage, cwd)

    REPORTS.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    dated = REPORTS / f"audit-stack-{today}.md"
    latest = REPORTS / "audit-stack-latest.md"
    dated.write_text(report)
    latest.write_text(report)

    # Also write a JSON state file for the statusline to read
    state = {
        "ts": datetime.now().astimezone().isoformat(),
        "total_passive_tokens": sum(f["tokens"] for f in base) + sum(f["tokens"] for f in proj_mem) + sum(p["reminder_tokens"] for p in plugins),
        "base_tokens": sum(f["tokens"] for f in base),
        "plugin_tokens": sum(p["reminder_tokens"] for p in plugins),
        "plugin_count": len(plugins),
        "prune_candidates": len([p for p in plugins if p["skill_count"] == 0 or (sum(c for sk, c in usage["skill_usage"].items() if sk.startswith(p["name"] + ":")) == 0 and p["reminder_tokens"] > 100)]),
    }
    state_dir = HOME / ".claude/dodojo/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "audit-stack.json").write_text(json.dumps(state, indent=2))

    # Print quick summary to stdout
    print(f"DoDojo Stack Audit · {state['total_passive_tokens']:,} passive tokens/session")
    print(f"  base: {state['base_tokens']:,}  plugins: {state['plugin_tokens']:,}")
    print(f"  prune candidates: {state['prune_candidates']}")
    print(f"  full report: {latest}")


if __name__ == "__main__":
    main()
