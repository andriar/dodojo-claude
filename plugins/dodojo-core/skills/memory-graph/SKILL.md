---
name: memory-graph
description: Audit & maintain the relation graph across ~/.claude/memory — resolve [[wikilinks]] canonically, find rot/islands, suggest links from keyword overlap, inject backlinks, and dedup-guard new memories before writing. Use when user asks "memory relations", "are my memories connected", "dedup memory", "link graph", "before saving a new memory", or memory feels redundant/disconnected.
domain: meta
category: ops
---

# memory-graph

Grouping (folder + INDEX) tells you *where* a memory lives. This skill tells you *how memories relate* and *whether a new one is redundant*. Engine: `memory_graph.py` (pure stdlib, no deps).

## The core problem it solves

Memories accumulate as islands. The `[[name]]` wikilink convention exists in CLAUDE.md but:
- links get written kebab-case while files are snake_case → false "rot"
- nobody injects backlinks → graph is one-directional / invisible
- nothing checks similarity *before* writing → duplicates pile up

This skill makes the graph **live**: canonical resolution, bidirectional backlinks, and a dedup gate at write time.

## Canonical resolution (the key trick)

A `[[target]]` resolves by normalizing to `lowercase`, stripping path + `.md`, and collapsing `-`/`_`/space → `-`. It matches against each memory's **filename stem**, **`id:`**, or slugified **`name:`**. This alone recovered 5/9 false-rot links in the live corpus. Use `fix-rot --apply` to rewrite valid-but-mismatched links to the canonical filename stem.

## Commands

```bash
S=~/.claude/skills/memory-graph/memory_graph.py
python3 $S report          # health: edges, rot, islands, dup candidates (default)
python3 $S resolve         # debug: every [[link]] -> resolved file or ROT
python3 $S fix-rot [--apply]   # rewrite kebab/path links to canonical stem
python3 $S backlink [--apply]  # inject "Linked from:" footer from inbound links
python3 $S suggest         # propose links via keyword overlap (0.20-0.35)
python3 $S mermaid         # emit graph as mermaid flowchart
python3 $S dup --file X.md # OR pipe text via stdin: dedup check vs corpus
# --- semantic (needs Ollama) ---
python3 $S semantic              # embedding link suggestions (catches paraphrase)
python3 $S semantic-dup --file X.md  # embedding dedup check (falls back to keyword if down)
```

## Multi-agent layer (P0+P1 built)

Memory graph as substrate for role agents (PM/QA/Eng) that retrieve a scoped lens, reason, and emit provenance-linked decisions. Full design: `MULTI_AGENT_DESIGN.md`.

```bash
# agent retrieval lens — semantic top-k over (own ∪ shared), optional --kind filter
python3 $S retrieve --agent qa --query "ship decision X" --kind decision -k 8
# emit an output node (reads body from stdin); --from = provenance inputs actually used
echo "BODY" | python3 $S emit --agent pm --kind decision --title "T" --from a,b --run run_x
# render one collaboration run as a provenance DAG
python3 $S run-graph --run run_x
# conflict/lifecycle
python3 $S set-status --node <slug> --status accepted|rejected|superseded
echo BODY | python3 $S emit ... --supersede <old_slug>   # flips old node to superseded
python3 $S retrieve ... --include-dead                    # include superseded nodes
```

- Frontmatter facets: `agent` (owner), `scope` (private|shared, default shared), `kind` (knowledge|decision|spec|verdict|design), `from` (inputs), `run`, `status`. Legacy memories = shared knowledge (no migration).
- Agent nodes live under `memory/agents/<role>/`; run ledgers under `memory/runs/<id>.md`.
- `emit` dedup-gates **only against the same `kind`** (a decision is *meant* to resemble its source knowledge — that's provenance, not duplication). Use `--supersede <slug>` to replace.
- `emit` embeds+caches the new node immediately so the next `retrieve` doesn't re-embed.
- After a run, `backlink --apply` makes provenance bidirectional (inputs learn who consumed them).
- Validated loop: PM emit decision → QA `retrieve --kind decision` → QA emit verdict `--from <decision>` → `run-graph` shows knowledge→decision→verdict DAG.

## Agents (the collaboration roles)

Role definitions live at `~/.claude/agents/{pm,eng,qa,arbiter}.md` + `DRIVER.md`. They are Claude Code custom agents — once the session reloads they are callable directly via the Agent tool (`subagent_type: pm|eng|qa|arbiter`). Until a reload registers them, spawn via `general-purpose` with a prompt that says "Read ~/.claude/agents/<role>.md and follow it" (the validated workaround). The main thread is the driver: spawn roles in order, route on each `HANDOFF:` line, stop at `DONE`.

## GPU embeddings (deferred optimization)

CPU embeds the whole corpus in ~26s (cached after), so GPU is unnecessary until the corpus is large. When needed, run Ollama on the RX 6600 (ROCm) instead of CPU:
```bash
docker run -d --name ollama --device /dev/kfd --device /dev/dri \
  -e HSA_OVERRIDE_GFX_VERSION=10.3.0 \
  -p 127.0.0.1:11434:11434 -v ollama:/root/.ollama ollama/ollama:rocm
```
(RX 6600 = gfx1032; the HSA override makes ROCm treat it as gfx1030. See homelab_ai_stack_gotchas memory for ROCm GID pitfalls.)

## Semantic pass (Ollama embeddings)

Keyword jaccard only catches *shared vocabulary* — it misses paraphrase and is noisy on islands (proven: island suggest returned mostly template noise). The semantic pass embeds each memory body via Ollama and links by cosine similarity (meaning, not words).

```bash
# one-time on a machine with the daemon:
ollama pull nomic-embed-text
# point the skill at your daemon (default localhost:11434):
export OLLAMA_HOST=http://zorin-server:11434      # tailnet prod-ollama
export OLLAMA_EMBED_MODEL=nomic-embed-text        # optional override
python3 $S semantic                                # cosine>=0.80 STRONG, 0.62-0.80 weak
```

- Embeddings cached at `.embed_cache.json` (keyed by `sha1(model+body)`) — re-runs are free; only changed/new bodies re-embed.
- `routing/*` excluded (template siblings); already-linked pairs skipped.
- Graceful: if the daemon is unreachable, prints the fix hint and exits 0; `semantic-dup` falls back to keyword `dup`.
- Thresholds tuned for `nomic-embed-text` cosine; override with `--threshold`. Re-tune if you swap models (e.g. `mxbai-embed-large`).
- The dedup **gate hook stays on keyword** (fast, offline, no network on every Write); semantic is the interactive/periodic pass.

## Workflows

**Periodic graph audit** → `report`. Triage rot (real missing target vs slug mismatch), review islands (link or accept standalone), check dup candidates.

**Make graph bidirectional** → `fix-rot --apply` then `backlink --apply`. Backlinks append a `<!-- backlinks -->` footer (idempotent — re-run overwrites, never stacks).

**Dedup-at-write (the gate)** → before saving any new memory, pipe the draft body through `dup`. If top jaccard ≥ 0.35 → **update the existing file instead of creating a new one** (matches CLAUDE.md "check for existing file before saving"). This is the hulu guard the rule always wanted but couldn't enforce.

## Notes & tuning

- `routing/*` are template siblings (shared model-route schema) — excluded from dup detection by design; don't try to merge them.
- Token overlap ignores YAML frontmatter (titles/ids/dates inflate false matches).
- Forward-references to not-yet-written memories (e.g. `[[ui-kit-guardian-agent]]`) show as rot — that's intended; they mark work to do, per CLAUDE.md "link liberally".
- Read-only by default; every mutating command needs `--apply`.

## Future (not built)

Auto-apply semantic STRONG pairs as `Related:` links (currently advisory — you review then cluster manually). Fold into `dodojo:memory-curator` after validation — see orchestrator_migrate_to_dodojo memory for the dodojo migration path.
