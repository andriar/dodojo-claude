# Collaboration Driver — pm → eng → qa

How the **main Claude thread** orchestrates a run. A standalone script cannot spawn Claude subagents, so the driver IS the main thread calling the Agent tool sequentially. State flows through the memory graph (each agent self-retrieves and self-emits); the driver passes only the task + run id.

## Procedure

1. **Mint a run id**: `run_<YYYYMMDD>_<n>` (or `dj mg run-new`).
2. **Spawn PM** (Agent subagent_type `pm`): prompt = the user goal + the run id. Wait for it. It returns an emitted slug + `HANDOFF:` line.
3. **Route on HANDOFF**: if `eng`, spawn Engineer with the same run id + a one-line task pointer; if `qa`, skip to QA; if `DONE`, stop.
4. **Spawn ENG** (subagent_type `eng`): same run id. Returns design slug + `HANDOFF: qa`.
5. **Spawn QA** (subagent_type `qa`): same run id. Returns verdict + `HANDOFF:`.
6. **On QA HANDOFF: pm** (FAIL / blocking) → optionally re-spawn PM to supersede; cap at N rounds to avoid ping-pong.
7. **Wire + render**: `backlink --apply` then `run-graph --run <id>` for the provenance DAG.

## Invariants

- Each agent gets ONLY task + run id inline — never the previous agent's prose. Context comes from `retrieve`.
- `--from` provenance must reflect real inputs; spot-check via `run-graph`.
- Hard cap on rounds (default 2 PM↔QA cycles) + terminal kind (`verdict PASS` or `decision accepted`) = termination.
- Ollama must be reachable (retrieve depends on it); degrades to keyword if down.

## Modes

- **Scripted** (default): fixed pm→eng→qa chain as above.
- **Router**: after each agent, dispatch to whatever role its `HANDOFF:` names, until DONE or cap.
