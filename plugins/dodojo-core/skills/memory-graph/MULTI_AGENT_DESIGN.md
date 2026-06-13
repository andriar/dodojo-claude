# Multi-Agent Memory Collaboration — Design Spec

Status: DRAFT (design-only, 2026-06-13). No code yet. Builds on the `memory-graph` skill.

## 1. Goal & non-goals

**Goal.** Turn the memory graph from a passive knowledge store into the shared substrate for a team of role-specialized agents (PM, QA, Engineer, …) that:
- read memory scoped to their role + shared context (a *retrieval lens*),
- reason and produce an output (a decision, spec, verdict, design),
- write that output back as a new graph node linked to the inputs it consumed (provenance),
- so the next agent can retrieve it and continue — collaboration happens *through the graph*, not through ad-hoc prompt passing.

**Non-goals (v1).**
- No real-time concurrency / agents running simultaneously. Turn-based handoff only.
- No new LLM runtime — agents are Claude Code subagents (Agent tool / `~/.claude/agents/*.md`).
- No distributed store — flat markdown files under `~/.claude/memory/`, same as today.
- No auto-merge of conflicting decisions — conflicts are surfaced, a human (or a designated arbiter agent) resolves.

## 2. Core model

A **node** = one markdown memory file (unchanged format). New facets via frontmatter:

| field | meaning | example |
|---|---|---|
| `agent` | owner role that authored it (absent = legacy/shared knowledge) | `pm`, `qa`, `eng` |
| `scope` | visibility | `private` (only owner retrieves) \| `shared` (any agent) |
| `kind` | node type | `knowledge` (fact), `decision`, `spec`, `verdict`, `design`, `task` |
| `from` | provenance — slugs of input nodes consumed to produce this | `[release-1-2-spec, flaky-login-test]` |
| `run` | collaboration-run id that produced it (groups a session) | `run_20260613_1` |
| `status` | for actionable nodes | `open`, `accepted`, `rejected`, `superseded` |

**Edges** (3 kinds, all already in the graph engine):
- `Related:` / wikilinks — topical association (semantic or manual).
- `Linked from:` backlinks — auto reciprocal.
- **provenance** = `from:` → rendered as wikilinks to inputs. This is the *new* edge type that records *who derived what from what*.

Existing topical memory (the 80 files) = `scope: shared, kind: knowledge, agent: (none)`. No migration needed; absence of `agent` means shared knowledge readable by all.

## 3. Directory layout

```
~/.claude/memory/
  <existing topical dirs>/        # shared knowledge (kind:knowledge)
  agents/
    pm/      *.md                 # agent:pm nodes (decisions, specs)
    qa/      *.md                 # agent:qa nodes (verdicts, bug notes)
    eng/     *.md                 # agent:eng nodes (designs)
  runs/
    run_20260613_1.md            # run ledger: ordered list of node slugs + handoffs
```

`scope:private` is enforced by the `retrieve` filter, not the filesystem (files stay readable for audit).

## 4. Engine additions (`memory_graph.py`)

Reuse embeddings + cache + canonical resolver already built.

### `retrieve --agent <role> --query "<text>" [-k 8] [--shared-only] [--kind decision]`
The agent's working-context fetch. Algorithm:
1. visible set = nodes where `scope==shared` OR `agent==role` (private of others excluded).
2. optional filter by `kind`.
3. embed the query, cosine-rank visible set, return top-k as `slug + path + 1-line desc + score`.
4. fallback to keyword `dup`-style ranking if Ollama down.
Output is compact (designed to be pasted into a subagent prompt).

### `emit --agent <role> --kind <kind> --title "<t>" [--from a,b,c] [--run <id>] --body -`
1. read body from stdin (or `--body-file`).
2. **dedup-gate**: semantic-dup the body vs visible set; if ≥0.85 → refuse, print the match, suggest `--supersede <slug>` or update.
3. slugify title → path under `agents/<role>/`.
4. write frontmatter (`agent, scope, kind, from, run, created, status:open`) + body + `Related:` links built from `--from`.
5. run `backlink --apply` so inputs gain a `Linked from:` to this output → bidirectional provenance.
6. append a line to `runs/<id>.md`.

### `run-show <id>` / `run-graph <id>`
Render a single collaboration run as an ordered ledger / mermaid DAG (who emitted what, from which inputs). This is the audit + "what did the team decide" view.

## 5. Agent definitions (`~/.claude/agents/<role>.md`)

Claude Code custom agents. Each frontmatter sets name/description/tools; the body is the role contract. **Shared contract every role follows:**

```
1. RETRIEVE first: run `memory_graph.py retrieve --agent <me> --query "<task>"`.
   Treat the returned nodes as your working memory. Do not invent facts already there.
2. REASON in role: produce exactly one output of your kind.
3. EMIT: pipe your output through `emit --agent <me> --kind <k> --from <the slugs you actually used>`.
   The --from list is mandatory and must reflect real inputs (provenance integrity).
4. HANDOFF: state which role should act next and why (one line).
```

Role specifics (v1):
- **pm** — kind `spec`/`decision`. Input: shared knowledge + user goal. Output: a spec or a ship decision with acceptance criteria.
- **qa** — kind `verdict`. Input: a spec/design + relevant knowledge. Output: pass/fail + missing states/risks, linked to what it reviewed.
- **eng** — kind `design`. Input: a spec + code-pattern knowledge. Output: an implementation design linked to the spec.

## 6. Handoff protocol (turn-based)

A **run** is an ordered sequence of (agent, action) steps sharing a `run` id. Two driving modes:

- **Scripted pipeline** — a fixed chain, e.g. `pm → eng → qa`. The orchestrator (an `orchestrate` skill subcommand or a small driver) spawns each subagent in order via the Agent tool, passing only the `run` id + the task; each agent self-retrieves and self-emits. The graph carries state between them — the driver passes almost nothing inline.
- **Router-driven** — after each emit, the agent's "HANDOFF" line names the next role; the driver dispatches accordingly until someone emits a terminal `decision status:accepted` or a max-step cap is hit.

Conflict / disagreement: if QA emits a `verdict status:rejected` against a PM `decision`, the driver routes back to PM (or to an `arbiter` role in v2). No silent overwrite — the rejected node stays, the new decision `supersede`s it (edge preserved).

## 7. Provenance & audit

Every derived node records `from:` (inputs) + `agent` (author) + `run`. This yields:
- **Why did the team decide X?** → walk `from:` edges backward to the knowledge/specs consumed.
- **What did agent QA contribute this run?** → filter `agent==qa, run==id`.
- **Dead reasoning** → a `decision` whose `from:` inputs were later `superseded` → flag for re-review.
`run-graph` renders this as a DAG; `dodojo:recall` / memory-graph `report` already surface orphans & rot across it.

## 8. Reuse map (nothing rebuilt)

| Need | Existing piece |
|---|---|
| agent retrieval lens | semantic embeddings + cache (`semantic`/`embed_corpus`) |
| cross-agent sharing edge | `Related:` + `backlink` |
| provenance edge | `from:` rendered as wikilinks + canonical resolver |
| anti-redundant decisions | dedup-gate (`gate` / `semantic-dup`) |
| task routing | `orchestrate route` |
| run audit / recall | `memory-graph report`, `dodojo:recall` |
| spawning roles | Claude Code Agent tool / `~/.claude/agents/` |

## 9. Roadmap (phased)

- **P0 (foundation)** — ✅ DONE 2026-06-13. `agent/scope/kind/from/run` frontmatter + `retrieve`/`emit`/`run-graph` in engine. dedup-gate scoped to same-kind (decision≈source-knowledge is provenance, not dup). emit embeds+caches new node.
- **P1 (MVP loop)** — ✅ VALIDATED via CLI hand-run 2026-06-13: PM emit decision (from 2 knowledge nodes) → QA `retrieve --kind decision` → QA emit verdict `--from` decision → `run-graph run_demo_1` rendered knowledge→decision→verdict DAG with bidirectional provenance. Agent *definitions* (`~/.claude/agents/*.md`) NOT yet written — loop proven manually, next is wrapping it in subagent prompts.
- **P2 (collaboration)** — ✅ DONE & validated 2026-06-13. Agent defs `~/.claude/agents/{pm,qa,eng}.md` + `DRIVER.md` (main-thread spawns subagents pm→eng→qa via Agent tool; state flows through graph). Live run `run_p2_1` on a real task ("wire semantic-dup into the gate?"): PM decision → ENG design → QA verdict, each self-retrieved + self-emitted with honest `from:` provenance; 3-node DAG rendered. QA caught a real bug (advisory path would inherit embed()'s hardcoded 30s timeout, not 2s) — system produced genuinely useful analysis of its own codebase. NOTE: custom agents spawned via general-purpose reading the agent .md (custom subagent_type may need session reload to register).
- **P3 (router + conflict)** — ✅ DONE & validated 2026-06-13. Engine: `set-status`, `--supersede` flips old node to `status:superseded`, `retrieve` hides superseded (unless `--include-dead`). Arbiter agent `~/.claude/agents/arbiter.md` (UPHOLD_QA / OVERRULE_QA / NEEDS_REDESIGN). Live: run_p2_1 continued — QA blocking verdict → router→arbiter ruled NEEDS_REDESIGN (decision sound, design flaw vs its own AC2) → ENG emitted design v2 `--supersede`ing v1 → QA re-verdict PASS → decision set `accepted`. 6-node DAG with superseded v1 design+verdict marked dead. Router dispatched on each HANDOFF line; terminated at DONE (terminal = decision accepted). Cap respected (1 redesign round).
- **P4 (operationalize + fold-in)** — partially 2026-06-13.
  - ✅ Demo artifacts cleaned (agent nodes + runs removed, dangling refs stripped, 0 new rot).
  - ✅ Agent registration: `~/.claude/agents/{pm,eng,qa,arbiter}.md` use standard frontmatter (name/description/tools/model) → callable as `subagent_type` after a session reload; until then spawn via general-purpose+Read (validated).
  - ✅ GPU embedding path documented (ROCm `ollama/ollama:rocm` + `HSA_OVERRIDE_GFX_VERSION=10.3.0` for RX 6600) — deferred until corpus large (CPU does 80 files/26s).
  - ⏳ DEFERRED: folding the engine into `dodojo:memory-curator`/`orchestrate`. Per the orchestrator_migrate_to_dodojo memory, migrate only after 2-3 weeks of standalone validation — do NOT fold prematurely. Trigger: sustained real use of retrieve/emit across multiple runs.

## 10. Open questions / risks

1. **Private scope leakage** — retrieve filters it, but files are world-readable for audit. Acceptable for a single-user homelab; revisit if multi-user.
2. **Embedding staleness** — emit writes new nodes; their embeddings must be added to cache at emit time (else first retrieve re-embeds). `emit` should embed-and-cache its own body.
3. **Hub explosion** — auto-`from` links could make a few decision nodes into mega-hubs. Cap `--from` to the k nodes actually used; don't dump the whole retrieve result.
4. **Provenance honesty** — agents might list `from:` they didn't truly use. Mitigation: prompt contract demands it reflect real inputs; spot-check in `run-graph`.
5. **Ollama availability** — collaboration depends on retrieval; if the daemon is down, `retrieve` falls back to keyword (degraded but functional). Document the dependency.
6. **Termination** — router mode needs a hard max-step + terminal-kind to avoid infinite agent ping-pong.

## 11. First concrete artifact when we build

`retrieve` + `emit` in `memory_graph.py`, the `agent/scope/kind/from/run` frontmatter convention, and a single hand-run example: PM emits one decision, QA retrieves and emits one verdict — then `run-graph <id>` shows the 2-node DAG with the provenance edge. That validates the whole thesis cheaply.
