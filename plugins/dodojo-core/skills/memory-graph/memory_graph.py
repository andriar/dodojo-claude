#!/usr/bin/env python3
"""memory-graph — relasi + dedup engine untuk ~/.claude/memory.

Subcommands:
  report     graph health: rot, islands, clusters, dup candidates (default)
  resolve    canonical resolve of every [[link]] -> file (debug)
  fix-rot    rewrite [[link]] yang valid-tapi-mismatch ke slug kanonik (--apply)
  backlink   inject/update "Linked from" footer dari inbound links (--apply)
  suggest    usulkan link berdasar keyword overlap (read-only)
  mermaid    cetak graph sebagai mermaid flowchart
  dup        cek 1 file/teks vs corpus (dedup-at-write guard)

Canonical key: lowercase, strip path & .md, '-'/'_'/' ' -> '-'.
Resolusi target [[x]] cocok ke: filename stem | id: frontmatter | slug(name:).
"""
import re, sys, pathlib, argparse, collections, os as _os

# ROOT = the user's memory dir (NOT the plugin dir). Env-overridable for non-standard layouts.
ROOT = pathlib.Path(_os.environ.get("MEMGRAPH_ROOT",
                                    str(pathlib.Path.home() / ".claude" / "memory")))
LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
STOP = set("the a an and or of to in on for with is are be this that it as by at from into your you our we i".split())


def canon(s: str) -> str:
    s = s.strip().split('|', 1)[0].split('#', 1)[0].strip()  # drop [[x|alias]] / [[x#anchor]]
    s = s.rsplit('/', 1)[-1]                                  # drop [[dir/x]] path prefix
    if s.endswith('.md'):
        s = s[:-3]
    return re.sub(r'[\s_-]+', '-', s.lower()).strip('-')


def fm(txt, key):
    m = re.search(rf'^{key}:\s*(.+)$', txt, re.M)
    return m.group(1).strip() if m else None


def load():
    def _keep(p):
        return '_archive' not in p.parts and p.name not in ('INDEX.md', 'MEMORY.md')
    files = [p for p in ROOT.rglob('*.md') if _keep(p)]
    # rglob does NOT descend symlinked dirs (e.g. memory/_project -> project memory);
    # scan them explicitly so cross-vault [[links]] resolve instead of showing as rot.
    seen = {p.resolve() for p in files}
    for d in ROOT.iterdir():
        if d.is_symlink() and d.is_dir():
            for p in d.rglob('*.md'):
                if _keep(p) and p.resolve() not in seen:
                    seen.add(p.resolve())
                    files.append(p)
    docs = {}
    for p in files:
        txt = p.read_text()
        keys = {canon(p.stem)}
        for k in ('id', 'name'):
            v = fm(txt, k)
            if v:
                keys.add(canon(v))
        docs[p] = {'txt': txt, 'keys': keys,
                   'links': [t.strip() for t in LINK_RE.findall(txt)],
                   'desc': fm(txt, 'description') or ''}
    # canonical key -> file
    index = {}
    for p, d in docs.items():
        for k in d['keys']:
            index.setdefault(k, p)
    return docs, index


def resolve_target(t, index):
    return index.get(canon(t))


def strip_fm(txt):
    # drop YAML frontmatter block so titles/ids/dates don't pollute token overlap
    m = re.match(r'^---\n.*?\n---\n', txt, re.S)
    return txt[m.end():] if m else txt


def tokens(txt):
    body = strip_fm(txt)
    return set(w for w in re.findall(r'[a-z][a-z0-9]{3,}', body.lower())
               if w not in STOP and not w.isdigit())


# ---------- semantic (Ollama embeddings) ----------
import os, json, hashlib, urllib.request

OLLAMA = os.environ.get('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')
if not OLLAMA.startswith('http'):
    OLLAMA = 'http://' + OLLAMA
EMODEL = os.environ.get('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
# Cache lives in user data space, NOT the plugin dir — plugin dirs get nuked on update.
CACHE = pathlib.Path(os.environ.get(
    'MEMGRAPH_CACHE',
    str(pathlib.Path.home() / '.claude' / '.cache' / 'memory-graph' / 'embed_cache.json')))
CACHE.parent.mkdir(parents=True, exist_ok=True)


def _load_cache():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def _ollama_embed(text):
    """POST to Ollama; try /api/embed (new) then /api/embeddings (old). Returns vector or None."""
    for path, key, outkey in (('/api/embed', 'input', 'embeddings'),
                              ('/api/embeddings', 'prompt', 'embedding')):
        try:
            body = json.dumps({'model': EMODEL, key: text}).encode()
            req = urllib.request.Request(OLLAMA + path, data=body,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
            v = d.get(outkey)
            if v and isinstance(v[0], list):   # /api/embed returns [[...]]
                v = v[0]
            if v:
                return v
        except Exception:
            continue
    return None


def embed(text, cache):
    h = hashlib.sha1((EMODEL + '\x00' + text).encode()).hexdigest()
    if h in cache:
        return cache[h]
    v = _ollama_embed(text)
    if v is not None:
        cache[h] = v
    return v


def cosine(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return s / (na * nb) if na and nb else 0.0


def embed_corpus(docs):
    """Returns (vecs dict p->vector, cache). Skips files that fail to embed."""
    cache = _load_cache()
    vecs = {}
    fail = 0
    for p, d in docs.items():
        v = embed(strip_fm(d['txt'])[:4000], cache)
        if v:
            vecs[p] = v
        else:
            fail += 1
    CACHE.write_text(json.dumps(cache))
    if not vecs:
        sys.stderr.write(
            f"[semantic] no embeddings — is Ollama up at {OLLAMA} with model '{EMODEL}'?\n"
            f"  start daemon, then: ollama pull {EMODEL}\n"
            f"  override host: OLLAMA_HOST=http://zorin-server:11434 (env)\n")
    elif fail:
        sys.stderr.write(f"[semantic] {fail} files failed to embed (skipped)\n")
    return vecs


# ---------- subcommands ----------

def cmd_report(docs, index, args):
    edges = collections.defaultdict(set)   # p -> set(target file)
    rot = []
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            if tgt:
                edges[p].add(tgt)
            else:
                rot.append((p, t))
    inbound = collections.defaultdict(set)
    for p, tgts in edges.items():
        for t in tgts:
            inbound[t].add(p)
    connected = set(edges) | set(inbound)
    islands = [p for p in docs if p not in connected]

    print(f"# memory-graph report  ({len(docs)} memories)")
    print(f"  edges resolved : {sum(len(v) for v in edges.values())}")
    print(f"  rot (unresolvable) : {len(rot)}")
    print(f"  islands (no in/out): {len(islands)}")
    print()
    if rot:
        print("## ROT (run `fix-rot --apply` if these are slug mismatches)")
        for p, t in rot:
            guess = ''
            # nearest by canon prefix
            ck = canon(t)
            cand = [k for k in index if ck in k or k in ck]
            if cand:
                guess = f"  ~ maybe -> {index[cand[0]].relative_to(ROOT)}"
            print(f"  {p.relative_to(ROOT)}  [[{t}]]{guess}")
        print()
    print(f"## ISLANDS ({len(islands)}) — kandidat di-link atau memang standalone")
    for p in islands:
        print(f"  {p.relative_to(ROOT)}")
    print()
    # dup candidates via token jaccard on description+body
    print("## DUP CANDIDATES (jaccard>=0.35 on tokens)")
    items = [(p, tokens(d['txt'])) for p, d in docs.items()]
    seen = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            if not a or not b:
                continue
            # routing/* are template siblings (same model-route schema) -> not real dups
            if items[i][0].parent.name == 'routing' and items[j][0].parent.name == 'routing':
                continue
            jac = len(a & b) / len(a | b)
            if jac >= 0.35:
                seen += 1
                print(f"  {jac:.2f}  {items[i][0].relative_to(ROOT)}  <>  {items[j][0].relative_to(ROOT)}")
    if not seen:
        print("  (none)")


def cmd_resolve(docs, index, args):
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            mark = tgt.relative_to(ROOT) if tgt else "*** ROT ***"
            print(f"{p.relative_to(ROOT)}  [[{t}]] -> {mark}")


def cmd_fix_rot(docs, index, args):
    changes = []
    for p, d in docs.items():
        new = d['txt']
        for t in d['links']:
            if resolve_target(t, index):
                slug = resolve_target(t, index).stem
                if t != slug and canon(t) == canon(slug):
                    new = new.replace(f"[[{t}]]", f"[[{slug}]]")
                    changes.append((p, t, slug))
        if new != d['txt'] and args.apply:
            p.write_text(new)
    for p, t, slug in changes:
        print(f"{'FIXED' if args.apply else 'WOULD FIX'}  {p.relative_to(ROOT)}  [[{t}]] -> [[{slug}]]")
    if not changes:
        print("no slug-mismatch rot to fix (remaining rot = truly missing targets)")
    elif not args.apply:
        print("\n(dry-run; pass --apply to write)")


def cmd_backlink(docs, index, args):
    inbound = collections.defaultdict(set)
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            if tgt and tgt != p:
                inbound[tgt].add(p.stem)
    MARK = "<!-- backlinks -->"
    for p, srcs in inbound.items():
        line = MARK + "\n*Linked from:* " + ", ".join(f"[[{s}]]" for s in sorted(srcs))
        txt = docs[p]['txt']
        txt = re.sub(MARK + r".*?(?=\n#|\Z)", "", txt, flags=re.S).rstrip()
        new = txt + "\n\n" + line + "\n"
        if args.apply:
            p.write_text(new)
        print(f"{'WROTE' if args.apply else 'WOULD WRITE'} backlinks -> {p.relative_to(ROOT)} ({len(srcs)})")
    if not args.apply:
        print("\n(dry-run; pass --apply to write)")


def cmd_suggest(docs, index, args):
    items = [(p, tokens(d['txt'])) for p, d in docs.items()]
    existing = set()
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            if tgt:
                existing.add(frozenset((p, tgt)))
    print("# Suggested links (overlap 0.20-0.35, not yet linked)")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pa, a = items[i]; pb, b = items[j]
            if not a or not b or frozenset((pa, pb)) in existing:
                continue
            jac = len(a & b) / len(a | b)
            if 0.20 <= jac < 0.35:
                shared = ", ".join(sorted(a & b)[:6])
                print(f"  {jac:.2f}  {pa.relative_to(ROOT)} <> {pb.relative_to(ROOT)}  [{shared}]")


def cmd_mermaid(docs, index, args):
    print("```mermaid\nflowchart LR")
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            if tgt:
                print(f"  {p.stem} --> {tgt.stem}")
    print("```")


def cmd_dup(docs, index, args):
    if args.file:
        probe = tokens(pathlib.Path(args.file).read_text())
        label = args.file
    else:
        probe = tokens(sys.stdin.read())
        label = "(stdin)"
    scored = []
    for p, d in docs.items():
        b = tokens(d['txt'])
        if b:
            scored.append((len(probe & b) / len(probe | b), p))
    scored.sort(reverse=True)
    print(f"# dedup check for {label}")
    for jac, p in scored[:5]:
        flag = "  <-- LIKELY DUP, update instead" if jac >= 0.35 else ""
        print(f"  {jac:.2f}  {p.relative_to(ROOT)}{flag}")


def cmd_gate(docs, index, args):
    """PreToolUse hook entry: read Write tool JSON from stdin, block on high dup.
    exit 0 = allow, exit 2 = block (stderr fed back to model)."""
    import json
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return  # malformed → allow
    ti = payload.get('tool_input', {})
    fp = ti.get('file_path', '')
    content = ti.get('content', '')
    rp = pathlib.Path(fp).resolve()
    # only gate NEW memory files (Edit/overwrite of existing = legit update)
    if ROOT not in rp.parents or rp.suffix != '.md':
        return
    if rp.name in ('INDEX.md', 'MEMORY.md') or rp.exists():
        return
    probe = tokens(content)
    if not probe:
        return
    best = []
    for p, d in docs.items():
        b = tokens(d['txt'])
        if b:
            j = len(probe & b) / len(probe | b)
            if j >= 0.35:
                best.append((j, p))
    if best:
        best.sort(reverse=True)
        msg = ["[memory-dedup-gate] New memory looks redundant with existing:"]
        for j, p in best[:3]:
            msg.append(f"  {j:.2f}  [[{p.stem}]]  ({p.relative_to(ROOT)})")
        msg.append("Consider UPDATING the existing file instead of creating a new one.")
        msg.append("If genuinely distinct, add a [[link]] to the related memory and retry.")
        sys.stderr.write("\n".join(msg) + "\n")
        sys.exit(2)


# ---------- multi-agent layer (P0) ----------
def node_meta(d):
    """scope/agent/kind for a doc dict. Legacy (no agent) = shared knowledge."""
    txt = d['txt']
    return {'agent': fm(txt, 'agent'),
            'scope': fm(txt, 'scope') or 'shared',
            'kind': fm(txt, 'kind') or 'knowledge'}


def visible(docs, role, shared_only=False):
    """Nodes an agent may retrieve: scope==shared OR owned by role. Excludes others' private."""
    out = []
    for p, d in docs.items():
        m = node_meta(d)
        if m['scope'] == 'private' and m['agent'] != role:
            continue
        if shared_only and m['agent'] == role and m['scope'] != 'shared':
            continue
        out.append((p, d, m))
    return out


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '_', t.lower()).strip('_')[:60]


def cmd_retrieve(docs, index, args):
    if not args.agent or not args.query:
        sys.stderr.write("retrieve needs --agent and --query\n"); sys.exit(1)
    pool = visible(docs, args.agent, args.shared_only)
    if args.kind:
        pool = [x for x in pool if x[2]['kind'] == args.kind]
    if not args.include_dead:
        pool = [x for x in pool if fm(x[1]['txt'], 'status') != 'superseded']
    if not pool:
        print("# (no visible nodes for this scope/kind)"); return
    cache = _load_cache()
    qv = embed(args.query, cache)
    k = args.topk or 8
    if qv is None:
        # keyword fallback
        sys.stderr.write(f"[retrieve] Ollama down at {OLLAMA}; keyword fallback\n")
        q = tokens(args.query)
        scored = sorted(((len(q & tokens(d['txt'])) / (len(q | tokens(d['txt'])) or 1), p, d)
                         for p, d, _ in pool), reverse=True)
    else:
        scored = []
        for p, d, _ in pool:
            v = embed(strip_fm(d['txt'])[:4000], cache)
            if v:
                scored.append((cosine(qv, v), p, d))
        scored.sort(reverse=True)
    CACHE.write_text(json.dumps(cache))
    print(f"# retrieve agent={args.agent} k={k} :: \"{args.query}\"")
    for s, p, d in scored[:k]:
        print(f"  [{s:.3f}] [[{p.stem}]]  ({p.relative_to(ROOT)})")
        print(f"          {d['desc'][:100]}")


AGENT_DIR = ROOT / 'agents'
RUN_DIR = ROOT / 'runs'


def cmd_emit(docs, index, args):
    for req in ('agent', 'kind', 'title'):
        if not getattr(args, req):
            sys.stderr.write(f"emit needs --{req}\n"); sys.exit(1)
    body = pathlib.Path(args.body_file).read_text() if args.body_file else sys.stdin.read()
    body = body.strip()
    if not body:
        sys.stderr.write("emit: empty body\n"); sys.exit(1)
    # dedup-gate vs visible set
    cache = _load_cache()
    pv = embed(body[:4000], cache)
    if pv is not None:
        # only dedup against SAME kind — a decision naturally resembles its source knowledge (provenance, not dup)
        for p, d, m in visible(docs, args.agent):
            if m['kind'] != args.kind:
                continue
            v = embed(strip_fm(d['txt'])[:4000], cache)
            if v and cosine(pv, v) >= 0.85 and not args.supersede:
                sys.stderr.write(
                    f"[emit] body ~{cosine(pv,v):.2f} similar to [[{p.stem}]] "
                    f"({p.relative_to(ROOT)}). Use --supersede {p.stem} or update it.\n")
                sys.exit(2)
    slug = slugify(args.title)
    dest = AGENT_DIR / args.agent / f"{slug}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        slug = f"{slug}_{__import__('datetime').datetime.now():%H%M%S}"
        dest = AGENT_DIR / args.agent / f"{slug}.md"
    froms = [f.strip() for f in (args.from_nodes or '').split(',') if f.strip()]
    run = args.run or f"run_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}"
    today = __import__('datetime').date.today().isoformat()
    fms = [f"agent: {args.agent}", "scope: shared", f"kind: {args.kind}",
           f"run: {run}", f"created: {today}", "status: open", f"name: {slug}",
           f"description: {args.title}"]
    if froms:
        fms.append("from: [" + ", ".join(froms) + "]")
    out = "---\n" + "\n".join(fms) + "\n---\n\n" + body + "\n"
    if args.supersede:
        out += f"\n*Supersedes:* [[{args.supersede}]]\n"
    if froms:
        out += "\n<!-- related -->\n*Related:* " + ", ".join(f"[[{f}]]" for f in froms) + "\n"
    dest.write_text(out)
    # supersede: flip the old node's status so retrieve/run-graph show it as dead
    if args.supersede:
        old = resolve_target(args.supersede, index)
        if old:
            ot = old.read_text()
            if re.search(r'^status:', ot, re.M):
                ot = re.sub(r'^status:.*$', 'status: superseded', ot, count=1, flags=re.M)
            else:
                ot = re.sub(r'\n---\n', '\nstatus: superseded\n---\n', ot, count=1)
            old.write_text(ot)
            print(f"  superseded [[{old.stem}]] -> status: superseded")
    # embed+cache the new node now (avoid first-retrieve re-embed) — P0 risk #2
    nv = embed(strip_fm(out)[:4000], cache)
    CACHE.write_text(json.dumps(cache))
    # run ledger
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ledger = RUN_DIR / f"{run}.md"
    if not ledger.exists():
        ledger.write_text(f"# {run}\n\n")
    with ledger.open('a') as fh:
        fh.write(f"- {args.agent} emit `{args.kind}` [[{slug}]]"
                 + (f" from {froms}" if froms else "") + "\n")
    print(f"emitted [[{slug}]] -> {dest.relative_to(ROOT)}  (run={run}"
          + (", embedded)" if nv else ", NOT embedded — Ollama down)"))
    print(f"run `python3 memory_graph.py backlink --apply` to wire provenance backlinks")


def _existing_links(docs, index):
    pairs = set()
    for p, d in docs.items():
        for t in d['links']:
            tgt = resolve_target(t, index)
            if tgt and tgt != p:
                pairs.add(frozenset((p, tgt)))
    return pairs


def cmd_semantic(docs, index, args):
    """Embedding-based link suggestions — catches paraphrase keyword jaccard misses.
    routing/* excluded (template siblings). Skips pairs already linked."""
    vecs = embed_corpus(docs)
    if not vecs:
        return
    existing = _existing_links(docs, index)
    items = list(vecs.items())
    hi = args.threshold or 0.80   # nomic cosine: ~.80+ = strongly related
    lo = 0.62                      # below this = unrelated
    scored = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pa, va = items[i]; pb, vb = items[j]
            if pa.parent.name == 'routing' and pb.parent.name == 'routing':
                continue
            if frozenset((pa, pb)) in existing:
                continue
            c = cosine(va, vb)
            if c >= lo:
                scored.append((c, pa, pb))
    scored.sort(reverse=True)
    print(f"# semantic links ({EMODEL} @ {OLLAMA}) — cosine>={lo:.2f}, not yet linked")
    print(f"#   >= {hi:.2f} STRONG (consider Related:)   {lo:.2f}-{hi:.2f} weak\n")
    for c, pa, pb in scored[:40]:
        tag = "STRONG" if c >= hi else "weak  "
        print(f"  {c:.3f} {tag}  {pa.relative_to(ROOT)} <> {pb.relative_to(ROOT)}")
    if not scored:
        print("  (no pairs above threshold)")


def cmd_semantic_dup(docs, index, args):
    """Embedding dedup check for a draft (--file or stdin) vs corpus."""
    if args.file:
        probe_txt = pathlib.Path(args.file).read_text()
        label = args.file
    else:
        probe_txt = sys.stdin.read(); label = "(stdin)"
    cache = _load_cache()
    pv = embed(strip_fm(probe_txt)[:4000], cache)
    CACHE.write_text(json.dumps(cache))
    if pv is None:
        sys.stderr.write(f"[semantic] Ollama unreachable at {OLLAMA}; falling back to keyword\n")
        return cmd_dup(docs, index, args)
    vecs = embed_corpus(docs)
    scored = sorted(((cosine(pv, v), p) for p, v in vecs.items()), reverse=True)
    print(f"# semantic dedup for {label} ({EMODEL})")
    for c, p in scored[:5]:
        flag = "  <-- LIKELY DUP, update instead" if c >= (args.threshold or 0.85) else ""
        print(f"  {c:.3f}  {p.relative_to(ROOT)}{flag}")


def cmd_set_status(docs, index, args):
    if not args.node or not args.status:
        sys.stderr.write("set-status needs --node <slug> --status <s>\n"); sys.exit(1)
    tgt = resolve_target(args.node, index)
    if not tgt:
        sys.stderr.write(f"node not found: {args.node}\n"); sys.exit(1)
    t = tgt.read_text()
    if re.search(r'^status:', t, re.M):
        t = re.sub(r'^status:.*$', f'status: {args.status}', t, count=1, flags=re.M)
    else:
        t = re.sub(r'\n---\n', f'\nstatus: {args.status}\n---\n', t, count=1)
    tgt.write_text(t)
    print(f"[[{tgt.stem}]] status -> {args.status}")


def cmd_run_graph(docs, index, args):
    rid = args.run
    if not rid:
        sys.stderr.write("run-graph needs --run <id>\n"); sys.exit(1)
    members = [(p, d, node_meta(d)) for p, d in docs.items()
               if fm(d['txt'], 'run') == rid]
    if not members:
        print(f"# no nodes for run {rid}"); return
    members.sort(key=lambda x: fm(x[1]['txt'], 'created') or '')
    print(f"# run {rid} — {len(members)} nodes")
    print("```mermaid\nflowchart LR")
    for p, d, m in members:
        froms = fm(d['txt'], 'from') or ''
        for f in re.findall(r'[\w-]+', froms):
            tgt = resolve_target(f, index)
            if tgt:
                print(f"  {tgt.stem} --> {p.stem}")
        print(f"  {p.stem}[\"{m['agent']}:{m['kind']}<br/>{p.stem}\"]")
    print("```")
    for p, d, m in members:
        print(f"  {m['agent']:>4} {m['kind']:<9} [[{p.stem}]]  status={fm(d['txt'],'status')}")


CMDS = {'report': cmd_report, 'resolve': cmd_resolve, 'fix-rot': cmd_fix_rot,
        'backlink': cmd_backlink, 'suggest': cmd_suggest, 'mermaid': cmd_mermaid,
        'dup': cmd_dup, 'gate': cmd_gate,
        'semantic': cmd_semantic, 'semantic-dup': cmd_semantic_dup,
        'retrieve': cmd_retrieve, 'emit': cmd_emit, 'run-graph': cmd_run_graph,
        'set-status': cmd_set_status}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', nargs='?', default='report', choices=list(CMDS))
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--file')
    ap.add_argument('--threshold', type=float)
    # multi-agent
    ap.add_argument('--agent')
    ap.add_argument('--query')
    ap.add_argument('--kind')
    ap.add_argument('--title')
    ap.add_argument('--from', dest='from_nodes')
    ap.add_argument('--run')
    ap.add_argument('--topk', '-k', type=int)
    ap.add_argument('--shared-only', action='store_true')
    ap.add_argument('--body-file')
    ap.add_argument('--supersede')
    ap.add_argument('--node')
    ap.add_argument('--status')
    ap.add_argument('--include-dead', action='store_true')
    args = ap.parse_args()
    docs, index = load()
    CMDS[args.cmd](docs, index, args)


if __name__ == '__main__':
    main()
