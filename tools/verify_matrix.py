#!/usr/bin/env python3
"""Deterministic anti-regression gate for the market-intel source matrix.

LLM proposes, this gate disposes. Run after an automated refresh edits the shards, BEFORE commit.
Exit 0 = matrix may land; exit non-zero = BLOCK (caller must not commit/push). Fail-closed: if a
check can't be performed (e.g. GitHub API unreachable), that's a BLOCK, not a pass.

Checks (the real failure modes of an unattended LLM refresh):
  ROUTE    (C2) a Default pick may not silently downgrade free/④③ → paid ①② without a CHANGELOG reason
  STRUCT   every domain in sources-index.md has a shard file, and vice versa
  TOOLS    tools/index.md <-> tools/*.md coverage (missing doc = BLOCK, orphan doc = WARN)
  REGISTRY tools/registry.json <-> index <-> docs 3-way (covers non-repo SaaS too; mismatch = BLOCK)
  REPO     every github.com/<owner>/<repo> in shards/pricing/tool-docs exists (gh api, fail-closed)
  GHACTIVE every github repo is alive (not archived) and pushed_at within 12mo (P4 deterministic gate
           against LLM-only "freshness" judgments; 404/archived = BLOCK, stale = WARN, RL = bypass)
  STAR     every star count in the corpus that can be attributed to a repo is within tolerance of
           the live API value; the run PRINTS what fraction of star-carrying rows it attributed, and
           WARNs with the rows it could not (see star_claims: the old shape-matcher saw 20%)
  FRESH    every `last_verified:`/`Last verified:` is real + non-future (shards, pricing, AND tool docs)
  STALE    (WARN) a tool doc not re-verified in >9 months is nominated for re-check (anti-rot)
  DOCCOVER (WARN) a github repo in a LIVE (non-tombstone) shard row with no per-tool doc (anti-lost-tracking)
  METH     SKILL.md still contains the 8 numbered guardrails, L1/L5 tiers, and ①②③④ route legend
  COVER    vs git main baseline: total source rows didn't drop >10%, no shard lost >30% of its rows
  PRICE    (WARN soft-launch) a CHANGED price line in pricing-install.md must carry an official URL +
           fetch date in the same diff hunk (C5); flip PRICE_BLOCK=True to enforce after one cycle
  AUDIT    (WARN) new source rows added with no independent cross-model audit line in the CHANGELOG
           (`AUDIT: <model> verdict=<pass|hold>`) — P4 editor!=verifier; WARN-tier launch, BLOCK later
  CONST    CONSTITUTION.md exists and was not modified by this run (scope guard)

Usage: python tools/verify_matrix.py [--no-net] [--base main]
Run from the repo root (~/market-intel).
"""
import json, re, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "market-intel")
REF = os.path.join(SKILL, "reference")
DOMAINS = os.path.join(REF, "domains")
INDEX = os.path.join(REF, "sources-index.md")
PRICING = os.path.join(REF, "volatile", "pricing-install.md")
SKILLMD = os.path.join(SKILL, "SKILL.md")
TOOLS_DIR = os.path.join(REF, "tools")
TOOLS_INDEX = os.path.join(TOOLS_DIR, "index.md")
INSTALL_GUIDE = os.path.join(REF, "install-guide.md")

STAR_TOL = 0.25          # display star annotations vs real, allow 25%
COVER_GLOBAL_DROP = 0.10 # total source rows may not drop >10%
COVER_SHARD_DROP = 0.30  # no single shard may lose >30% of its rows

NO_NET = "--no-net" in sys.argv
BASE = "main"
if "--base" in sys.argv:
    BASE = sys.argv[sys.argv.index("--base") + 1]

fails, warns = [], []
def block(code, msg): fails.append(f"[{code}] {msg}")
def warn(code, msg): warns.append(f"[{code}] {msg}")

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def git_show(ref, relpath):
    try:
        return subprocess.run(["git", "show", f"{ref}:{relpath}"], cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8").stdout
    except Exception:
        return ""

REPO_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
# canonical bare owner/name slug (registry `repo` field for kind=repo tools)
SLUG_FMT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
# STAR_LINE_RE is the STRICT shape: a slug immediately followed by a bare `(NNk★)`. It is used for
# ONE job only, seeding repo_set for the 404-hard-BLOCK existence gate, where a false positive costs
# a bogus BLOCK. The STAR TOLERANCE check does NOT use it, see star_claims() below for why.
STAR_LINE_RE = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\*{0,2}\s*\((\d+(?:\.\d+)?)k★\)")

# ---- STAR claim extraction (the shape survey, not a guess) --------------------------------------
# STAR_LINE_RE above requires the annotation to be exactly `(NNk★)` and to close IMMEDIATELY after
# the glyph. Enumerating every line in the corpus that carries a star count showed that shape is a
# MINORITY of the corpus: 57 of 282 rows, 20.2%. The gate was verifying a fifth of its own subject
# and reporting on all of it, and among the four fifths it could not see were rows more than 25%
# off. Refreshing the three rows it could see and calling it armed is the exact false confidence
# this gate exists to prevent.
#
# The shapes the corpus actually uses (all of these were invisible):
#   `(1236★)`                        no `k` suffix at all, the single largest class
#   `(WordPress/mcp-adapter, 1236★ official)`   comma and/or trailing words inside the parens
#   `(contentful/contentful-mcp-server 58★)`    slug and count share one paren group, no comma
#   `**directus/mcp** (79★ official)`           bold, plus words after the count
#   `` `omkarcloud/amazon-scraper (0.2k★, gh-api 2026-06)` ``  backticked, count followed by a date
#   `github.com/steel-dev/steel-browser, 7.1k★, self-host`     anchored by a URL, no parens at all
#   `jaipandya/**producthunt-mcp-server** 46★`  emphasis INSIDE the slug
#   `(0.2k★, ...)`; active (220★, ...)`         a second count for the same repo later in the line
#
# So the matcher stops pattern-matching a fixed annotation and instead does what a reader does:
# find every numeric star claim, then attribute it to the nearest repo named before it, refusing to
# attribute across a boundary that means the subject changed.
STAR_CLAIM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*([kK])?\s*★")
STAR_ANCHOR_RE = re.compile(r"(?:github\.com/)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
STAR_WINDOW = 60         # chars between the repo and its count; beyond this the subject has moved on


def star_claims(line):
    """[(repo|None, claimed_stars, unpaired_reason|None)] for every star claim on `line`.

    Attribution rules, each one paying for a specific misattribution seen in the corpus:
      * markdown emphasis is blanked (not deleted) so `jaipandya/**producthunt-mcp-server**` is one
        token while every offset below stays comparable to the raw line;
      * the anchor is the nearest repo-shaped token BEFORE the count, `github.com/` prefix optional;
      * a `|`, `·` or `;` between them un-pairs it: those separate table cells, list items and
        clauses, i.e. a different subject. `(697★) | ... (717★ at last gh-api check)` must not pair
        the historical second reading to the row's repo, and `replaces ComposioHQ/awesome-claude-
        skills** (less-maintained); 40k★` must not pair the ROW's own 40k to the repo it replaced
        (that one was caught by this gate misfiring on it before `;` was added);
      * more than STAR_WINDOW chars between them un-pairs it: `(79★ official) | ① | official MCP for
        Directus (SQL-backed headless CMS, 36k★)` claims 36k for DIRECTUS CORE, a repo the line never
        names, and pairing it to directus/mcp would BLOCK on a true statement;
      * a count may chain off the PREVIOUS COUNT for the same repo, which is how
        `(0.2k★, gh-api 2026-06)`; active (220★, pushed ...)` gets both numbers checked.

    What it deliberately does NOT do is invent an anchor. A claim with no repo named near it
    ("Free MIT, 2.6k★, actively pushed") is returned UNPAIRED with a reason, and the caller reports
    the count of those. Attributing them to the enclosing document's subject would be a guess, and
    the corpus contains counterexamples that prove the guess wrong: tools/directus-mcp.md says "the
    weight is the Directus core platform (36k★)" and claude-marketing-research-skill.md compares
    itself to "the 8k to 32k★ bundles". A gate that BLOCKS on a guess is worse than one that says
    out loud what it could not see.
    """
    n = re.sub(r"[*`]", " ", line)
    anchors = [(m.end(1), m.group(1).rstrip("./,);:")) for m in STAR_ANCHOR_RE.finditer(n)]
    out, last_claim = [], None
    for c in STAR_CLAIM_RE.finditer(n):
        claimed = float(c.group(1)) * (1000 if c.group(2) else 1)
        prev = [a for a in anchors if a[0] <= c.start()]
        cand = prev[-1] if prev else None
        if last_claim and (cand is None or last_claim[0] > cand[0]):
            cand = last_claim                       # chain: same repo, second count on the line
        if cand is None:
            out.append((None, claimed, "no repo named earlier on the line"))
            continue
        pos, repo = cand
        win = n[pos:c.start()]
        if any(ch in win for ch in "|·;"):
            out.append((None, claimed, "separated from %s by a cell/clause boundary" % repo))
        elif len(win) > STAR_WINDOW:
            out.append((None, claimed, "nearest repo %s is %d chars away (>%d)"
                        % (repo, len(win), STAR_WINDOW)))
        else:
            out.append((repo, claimed, None))
            last_claim = (c.end(), repo)
    return out

def count_table_rows(text):
    """Count markdown source-table rows (lines starting with '|' that aren't header/sep)."""
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", s) and "---" not in s:
            # skip header rows that contain the literal column names
            if not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I):
                n += 1
    return n

# ---- STRUCT ----
idx = read(INDEX)
idx_domains = set(re.findall(r"domains/([a-z0-9-]+)\.md", idx))
fs_domains = {f[:-3] for f in os.listdir(DOMAINS) if f.endswith(".md")}
missing = idx_domains - fs_domains
orphan = fs_domains - idx_domains
if missing: block("STRUCT", f"index references missing shards: {sorted(missing)}")
if orphan: warn("STRUCT", f"shards not in index: {sorted(orphan)}")

# ---- TOOLS (per-tool doc coverage: tools/index.md <-> tools/*.md) ----
# Every tool listed in tools/index.md must have a doc file, and vice versa. Deterministic, like
# STRUCT. Missing doc = BLOCK (the index promised a how-to that isn't there); orphan doc = WARN.
tool_docs_text = {}
# Bound unconditionally: the STAR scan below reads it, and it used to be assigned only inside the
# isdir branch, so a repo with no reference/tools/ would have raised NameError there instead of
# running the gate.
tools_idx = ""
if os.path.isdir(TOOLS_DIR):
    if not os.path.exists(TOOLS_INDEX):
        block("TOOLS", "reference/tools/ exists but index.md is missing")
        tools_idx = ""
    else:
        tools_idx = read(TOOLS_INDEX)
    # allow a dot inside the slug so companion "auto" docs (e.g. apify.auto.md) are extractable
    idx_slugs = set(re.findall(r"\(([a-z0-9][a-z0-9.-]*?)\.md\)", tools_idx))
    fs_slugs = {f[:-3] for f in os.listdir(TOOLS_DIR) if f.endswith(".md") and f != "index.md"}
    miss_docs = idx_slugs - fs_slugs
    orphan_docs = fs_slugs - idx_slugs
    if miss_docs: block("TOOLS", f"tools/index.md references missing docs: {sorted(miss_docs)}")
    if orphan_docs: warn("TOOLS", f"tool docs not listed in index.md: {sorted(orphan_docs)}")
    tool_docs_text = {s: read(os.path.join(TOOLS_DIR, s + ".md")) for s in fs_slugs}
else:
    warn("TOOLS", "reference/tools/ directory not present (no per-tool docs)")

# ---- gather repos + per-shard text ----
shard_text = {d: read(os.path.join(DOMAINS, d + ".md")) for d in fs_domains}
# tool docs + install-guide are scanned alongside shards/pricing so the REPO existence + STAR
# tolerance gates also cover per-tool docs (a hallucinated repo in a tool doc 404s -> BLOCK).
all_text = ("\n".join(shard_text.values()) + "\n" + (read(PRICING) if os.path.exists(PRICING) else "")
            + "\n" + "\n".join(tool_docs_text.values())
            + "\n" + (read(INSTALL_GUIDE) if os.path.exists(INSTALL_GUIDE) else ""))
# HIGH-CONFIDENCE repos (404 → hard BLOCK): explicit github.com URLs + star-annotated slugs.
# Strip a trailing ".git", a `git clone https://github.com/o/r.git` URL is the same repo as o/r;
# without this the literal "o/r.git" token 404s on the API (false positive).
# Also strip trailing sentence punctuation the slug regex greedily swallows ("OpenBB-finance/OpenBB."
# at end of a sentence captures the period), that lone dot 404s on the API (false positive).
def _strip_git(r):
    r = r.rstrip("./,);:")          # drop trailing sentence punctuation (incl. a stray ".")
    return r[:-4] if r.endswith(".git") else r
repo_set = {_strip_git(r) for r in REPO_RE.findall(all_text)}
repo_set |= {_strip_git(m.group(1)) for m in STAR_LINE_RE.finditer(all_text)}
repos = sorted(r for r in repo_set if not r.endswith(".md") and r.count("/") == 1 and "github.com" not in r)

# HEURISTIC bare slugs (404 → WARN only): unstarred slug-like tokens in table rows. Catches likely
# hallucinations (e.g. a mistyped erithwik/mcp-hn) for human attention, but does NOT hard-block ,
# regex can't tell a real bare repo from prose like "10-K/Q" or an npm scope "@ryukimin/ghost-mcp".
# The BLOCK-level existence guarantee for ALL repos is the job of the machine-readable mirror block
# (ROADMAP Stage A root fix); this WARN is the interim visibility net, not a substitute.
SLUG_RE = re.compile(r"(?<![A-Za-z0-9_./@-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?![A-Za-z0-9_./-])")
warn_slugs = set()
for txt in shard_text.values():
    for ln in txt.splitlines():
        if not ln.lstrip().startswith("|"):
            continue
        for tok in SLUG_RE.findall(ln):
            o, _, r2 = tok.partition("/")
            if ("-" in tok or "_" in tok) and o.isascii() and r2.isascii() \
               and not tok.endswith(".md") and "github.com" not in tok and tok not in repo_set \
               and not o[:1].isdigit():          # skip "10-K/Q"-style prose
                warn_slugs.add(tok)

# ---- extract every star claim in the corpus (text only, no network yet) ----
# Done HERE, before the fetch, because a starred repo that is named nowhere as a github.com URL
# (dozens of shard rows are bare slugs) still has to be fetched for its count to be checkable.
#
# WHAT IS IN SCOPE, and why tools/index.md had to be added by name. `tool_docs_text` is built by
# excluding index.md (it is the catalog, not a tool doc), so for its whole life the STAR gate could
# not see it. It carries a live star claim about a current top pick, which is exactly the kind of
# claim this gate exists to hold to the API. A file being excluded from one check's input set is not
# a reason for it to be excluded from every check's.
#
# WHAT IS DELIBERATELY OUT OF SCOPE: volatile/discovery-state.md, 93 rows of star counts, the single
# largest concentration in the repo. It is an append-only DATED ledger whose rows are written as
# `1569★ (was 1514★ 2026-06, +55, slow)` -- a measurement taken on a stated date, plus the previous
# measurement kept on purpose to show the trend. Holding a dated historical reading to today's API
# value would BLOCK on rows that are true, and "fixing" them would destroy the growth signal the
# file exists to record. Its own header already binds it to C1 (real gh-api values at the noted
# date). Scope is decided by whether a claim asserts a CURRENT value, not by where the glyph is.
STAR_SCAN = ([("domains/%s.md" % d, t) for d, t in sorted(shard_text.items())]
             + ([("volatile/pricing-install.md", read(PRICING))] if os.path.exists(PRICING) else [])
             + ([("tools/index.md", tools_idx)] if tools_idx else [])
             + [("tools/%s.md" % s, t) for s, t in sorted(tool_docs_text.items())])
star_pairs, star_unpaired, star_rows = [], [], 0
for _fname, _txt in STAR_SCAN:
    for _lno, _ln in enumerate(_txt.splitlines(), 1):
        if "★" not in _ln:
            continue
        _claims = star_claims(_ln)
        if not _claims:
            continue
        star_rows += 1
        for _repo, _claimed, _why in _claims:
            if _why is None:
                star_pairs.append((_fname, _lno, _repo, _claimed))
            else:
                star_unpaired.append((_fname, _lno, _claimed, _why))

# ---- combined parallel GitHub fetch (feeds REPO + STAR + GHACTIVE) ----
# WHY: REPO and GHACTIVE each hit `gh api repos/<r>` SEPARATELY (2 calls/repo), and the
# per-repo network round-trip dominated wall-clock (109 repos ~= 70s serial). Fetch once
# per repo, in PARALLEL, into repo_api; every block/warn/cache DECISION below stays SERIAL
# over the sorted repo list, so message order and each gate's error semantics are byte-for-byte
# unchanged (REPO/STAR = fail-closed on transient; GHACTIVE = fail-open, WARN on rate-limit).
# The fetch returns a normalized dict, ok=True -> stars/archived/pushed_at; ok=False -> err in
# {404, transient, unparseable} with stderr carried for the message text. Retry mirrors the
# original REPO loop (3 attempts, back off on transient, 404 decided at once).
def _fetch_repo_api(r):
    import time
    res = None
    for attempt in range(3):
        res = subprocess.run(
            ["gh", "api", f"repos/{r}", "--jq", "{s:.stargazers_count,a:.archived,p:.pushed_at}"],
            capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            break
        if "Not Found" in (res.stderr or "") or "404" in (res.stderr or ""):
            break                                # real 404, don't retry, it's a hard fact
        time.sleep(2 * (attempt + 1))            # transient (rate-limit/network): back off and retry
    stderr = res.stderr or ""
    if res.returncode != 0:
        if "Not Found" in stderr or "404" in stderr:
            return {"ok": False, "err": "404", "stderr": stderr}
        return {"ok": False, "err": "transient", "stderr": stderr}
    try:
        d = json.loads(res.stdout)
        return {"ok": True, "stars": d.get("s"), "archived": bool(d.get("a")), "pushed_at": d.get("p")}
    except Exception:
        return {"ok": False, "err": "unparseable", "stderr": stderr}

repo_api = {}
if not NO_NET:
    import concurrent.futures as _cf
    # Star anchors join the fetch set. They are NOT added to repo_set: repo_set drives the 404
    # hard-BLOCK, and the widened matcher can legitimately anchor on a prose token that merely looks
    # like a slug ("umbrella/TS repo"). Such a token 404s, and the STAR check below treats a 404
    # anchor as unverifiable rather than as a lie, so a loose anchor costs one wasted API call and
    # never a false BLOCK. Existence remains REPO's job, on REPO's stricter input.
    _to_fetch = sorted(set(repos) | set(warn_slugs) | {p[2] for p in star_pairs})
    _workers = max(1, min(8, len(_to_fetch)))
    if _workers <= 1:
        for _r in _to_fetch:
            repo_api[_r] = _fetch_repo_api(_r)
    else:
        with _cf.ThreadPoolExecutor(max_workers=_workers) as _ex:
            for _r, _out in zip(_to_fetch, _ex.map(_fetch_repo_api, _to_fetch)):
                repo_api[_r] = _out

# ---- REPO + STAR (fail-closed) ----
repo_stars = {}
if NO_NET:
    warn("REPO", "skipped GitHub verification (--no-net)")
else:
    for r in repos:
        a = repo_api.get(r) or {"ok": False, "err": "transient", "stderr": "not fetched"}
        if not a["ok"]:
            if a["err"] == "404":
                block("REPO", f"{r} does not exist (404) — hallucinated or dead repo")
            elif a["err"] == "unparseable":
                block("REPO", f"{r} returned unparseable API response")
            else:
                block("REPO", f"{r} could not be verified after retries (fail-closed): {a['stderr'].strip()[:80]}")
            continue
        repo_stars[r] = a["stars"]
    # heuristic bare slugs: verify but only WARN (avoid false-blocking prose / npm scopes)
    for r in sorted(warn_slugs):
        a = repo_api.get(r)
        if a and not a["ok"] and a["err"] == "404":
            warn("REPO?", f"{r} not found on GitHub — if it's a repo it may be hallucinated/mistyped; "
                          f"if prose/npm-scope, ignore (mirror block will disambiguate)")
    # ---- STAR tolerance, over every claim star_claims() could attribute to a repo ----
    # Fail-closed on a transient error, mirroring REPO: an anchor we could not resolve is an
    # unanswered question, not a pass. A 404 anchor is the one exception and is COUNTED, not
    # silently dropped: it is either prose the matcher over-read (harmless) or a hallucinated repo,
    # and the second is REPO/REPO?'s job on its own stricter input.
    star_unresolved, star_checked_rows, _star_said = [], set(), set()
    for fname, lno, repo, claimed in star_pairs:
        a = repo_api.get(repo)
        if a is None:
            block("STAR", f"{fname}:{lno} {repo}: star anchor was never fetched (internal error)")
            continue
        if not a["ok"]:
            if a["err"] == "404":
                star_unresolved.append(f"{fname}:{lno} {repo} (404)")
            else:
                block("STAR", f"{fname}:{lno} {repo}: could not verify {claimed:g}★ "
                              f"(fail-closed): {a['stderr'].strip()[:60]}")
            continue
        real = a["stars"]
        if real is None:
            block("STAR", f"{fname}:{lno} {repo}: API returned no star count")
            continue
        star_checked_rows.add((fname, lno))
        # `real == 0` is a DIVISION GUARD, not a verdict. Written as part of the tolerance test it
        # meant "a repo with no stars always BLOCKs", so five rows that honestly said 0★ about a
        # repo the API also reports at 0★ were reported as a mismatch, printing the self-refuting
        # "claims 0★ but API says 0". Zero is a fact like any other: it matches iff the claim is 0.
        off = (claimed != 0) if real == 0 else (abs(claimed - real) / real > STAR_TOL)
        msg = (f"{fname}:{lno} {repo}: claims {claimed:g}★ but API says {real} "
               f"(>{int(STAR_TOL*100)}% off)")
        if off and msg not in _star_said:     # one line can carry the same claim twice
            _star_said.add(msg)
            block("STAR", msg)
    if star_unresolved:
        warn("STAR?", f"{len(star_unresolved)} star claim(s) anchored on a token GitHub does not "
                      f"know; unverifiable (prose the matcher over-read, or a dead repo — REPO/REPO? "
                      f"owns existence): {', '.join(star_unresolved[:6])}"
                      f"{' …' if len(star_unresolved) > 6 else ''}")
    # DECLARE THE BLIND SPOT. A star claim with no repo named near it cannot be attributed without
    # guessing, so it is not checked -- but silence about that is what let 80% of the corpus go
    # unverified behind a green gate. The coverage line prints on every run, pass or fail.
    # Report the VERIFIED fraction, not the attributed one. An anchor the API does not know was
    # attributed but never compared to anything, and counting it as covered would re-tell the exact
    # lie this whole change exists to end: a percentage that flatters the gate.
    print(f"STAR coverage: {len(star_checked_rows)}/{star_rows} rows carrying a star claim were "
          f"attributed to a repo and CHECKED against the live API "
          f"({100.0 * len(star_checked_rows) / max(1, star_rows):.1f}%); "
          f"{len(star_pairs)} claim(s) attributed, {len(star_unpaired)} unattributable, "
          f"{len(star_unresolved)} attributed-but-unresolvable")
    if star_unpaired:
        _u = ", ".join(f"{f}:{l}({c:g}★)" for f, l, c, _w in star_unpaired[:8])
        warn("STAR-BLIND", f"{len(star_unpaired)} star claim(s) name no repo close enough to "
                           f"attribute, so they are NOT verified. Name the repo on the line to "
                           f"bring one into the gate: {_u}{' …' if len(star_unpaired) > 8 else ''}")

# ---- GHACTIVE (P4 deterministic activity gate) ----
# WHY: LLM-judgment lenses (existence, freshness, top_pick_impact) confidently passed a candidate
# (BigGo, 2026-06-17 sweep) whose repo was 13 months stale. PHILOSOPHY §4 demands an independent
# deterministic source, gh api `pushed_at` + `archived`. Inviolable, not optional.
# 404                  -> BLOCK (URL fabricated or dead)
# archived=true        -> BLOCK (formally retired upstream)
# pushed_at >12mo old  -> WARN  (silent rot; same severity class as STALE)
# rate-limited         -> RATE_LIMITED (do NOT block on transient external state; surfaces as WARN)
# Cache results to metrics/gh-api-cache.json keyed by owner/repo with timestamp; entries older
# than 7d are refetched. This avoids hammering the API on every refresh.
import datetime
GH_CACHE = os.path.join(ROOT, "metrics", "gh-api-cache.json")
GH_CACHE_MAX_AGE_DAYS = 7
GHACTIVE_STALE_MONTHS = 12
_now_ts = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
_now_iso = _now_ts.isoformat()
gh_cache = {}
if os.path.exists(GH_CACHE):
    try:
        gh_cache = json.loads(read(GH_CACHE))
    except Exception:
        gh_cache = {}
ghactive_results = []
if NO_NET:
    warn("GHACTIVE", "skipped GitHub activity verification (--no-net)")
else:
    for r in repos:
        # cache hit if entry exists and is fresh enough
        c = gh_cache.get(r)
        if c and "checked_at" in c:
            try:
                age = (_now_ts - datetime.datetime.fromisoformat(c["checked_at"])).days
            except Exception:
                age = 999
            if age <= GH_CACHE_MAX_AGE_DAYS and c.get("verdict") != "RATE_LIMITED":
                ghactive_results.append(c)
                continue
        # Read the combined fetch (repo_api) instead of a second gh call. Verdict/cache/message
        # logic is unchanged: only the network round-trip moved to the parallel phase above.
        a = repo_api.get(r) or {"ok": False, "err": "transient", "stderr": ""}
        if not a["ok"]:
            stderr = a.get("stderr") or ""
            if a["err"] == "404":
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "BLOCK", "reason": "404 not found", "checked_at": _now_iso}
                block("GHACTIVE", f"{r}: 404 not found (URL fabricated, deleted, or moved)")
            elif a["err"] == "unparseable":
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "RATE_LIMITED", "reason": "unparseable response",
                         "checked_at": _now_iso}
                warn("GHACTIVE", f"{r}: unparseable activity response")
            elif "rate limit" in stderr.lower() or "API rate" in stderr or "403" in stderr:
                # Rate-limit is transient external state; per the philosophy we must not gate the
                # gate on it. Surface as WARN and skip, re-run will pick it up.
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "RATE_LIMITED", "reason": "gh api rate-limited",
                         "checked_at": _now_iso}
                warn("GHACTIVE", f"{r}: rate-limited — re-run when quota resets (not blocking)")
            else:
                # Other transient errors: surface as WARN, do not block (REPO gate already
                # fail-closed on existence; GHACTIVE is the activity layer, not the existence layer).
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "RATE_LIMITED",
                         "reason": f"gh error: {stderr.strip()[:60]}", "checked_at": _now_iso}
                warn("GHACTIVE", f"{r}: could not check activity ({stderr.strip()[:60]})")
            ghactive_results.append(entry)
            gh_cache[r] = entry
            continue
        pushed_at = a["pushed_at"]
        archived = bool(a["archived"])
        if archived:
            entry = {"repo": r, "pushed_at": pushed_at, "archived": True,
                     "verdict": "BLOCK", "reason": "archived upstream", "checked_at": _now_iso}
            block("GHACTIVE", f"{r}: archived=true (formally retired upstream — tombstone the row)")
        else:
            # parse pushed_at (RFC3339 like "2026-06-17T04:33:39Z")
            try:
                pushed_dt = datetime.datetime.strptime(pushed_at[:10], "%Y-%m-%d")
                months_old = (_now_ts - pushed_dt).days / 30.44
            except Exception:
                months_old = 0
            if months_old > GHACTIVE_STALE_MONTHS:
                entry = {"repo": r, "pushed_at": pushed_at, "archived": False,
                         "verdict": "WARN",
                         "reason": f"pushed_at {pushed_at[:10]} is ~{int(months_old)}mo old (>{GHACTIVE_STALE_MONTHS}mo)",
                         "checked_at": _now_iso}
                warn("GHACTIVE", f"{r}: last push {pushed_at[:10]} (~{int(months_old)}mo ago, "
                                 f">{GHACTIVE_STALE_MONTHS}mo) — re-verify still maintained")
            else:
                entry = {"repo": r, "pushed_at": pushed_at, "archived": False,
                         "verdict": "PASS",
                         "reason": f"pushed_at {pushed_at[:10]} within {GHACTIVE_STALE_MONTHS}mo",
                         "checked_at": _now_iso}
        ghactive_results.append(entry)
        gh_cache[r] = entry
    # persist cache (best-effort; cache miss is harmless)
    try:
        os.makedirs(os.path.dirname(GH_CACHE), exist_ok=True)
        with open(GH_CACHE, "w", encoding="utf-8") as f:
            json.dump(gh_cache, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        pass
    # aggregate summary into the gate's output
    _verdicts = {v: 0 for v in ("PASS", "WARN", "BLOCK", "RATE_LIMITED")}
    for e in ghactive_results:
        _verdicts[e["verdict"]] = _verdicts.get(e["verdict"], 0) + 1
    print(f"GHACTIVE summary: {_verdicts['PASS']} PASS, {_verdicts['WARN']} WARN, "
          f"{_verdicts['BLOCK']} BLOCK, {_verdicts['RATE_LIMITED']} RATE_LIMITED "
          f"(of {len(ghactive_results)} repos checked)")

# ---- FRESH (shards/pricing: `last_verified:` · tool docs: `Last verified:`) ----
today = datetime.date.today()
this_month = today.strftime("%Y-%m")
def _ym_to_months(ym): return int(ym[:4]) * 12 + int(ym[5:7])
this_m = _ym_to_months(this_month)
STALE_MONTHS = 9          # a per-tool doc unchecked this long is nominated for re-verification (WARN)
for m in re.finditer(r"last_verified:\s*(\d{4})-(\d{2})", all_text):
    ym = f"{m.group(1)}-{m.group(2)}"
    if ym > this_month:
        block("FRESH", f"last_verified {ym} is in the future")
# Per-tool doc freshness: every doc must carry a `Last verified: YYYY-MM`; future = BLOCK (a lie),
# >STALE_MONTHS old = WARN (surfaced so a sweep re-verifies it, closes the silent-rot gap).
stale_docs = []
for slug, txt in tool_docs_text.items():
    fm = re.search(r"Last verified:\s*(\d{4})-(\d{2})", txt)
    if not fm:
        warn("FRESH", f"tools/{slug}.md has no 'Last verified: YYYY-MM' line")
        continue
    ym = f"{fm.group(1)}-{fm.group(2)}"
    if ym > this_month:
        block("FRESH", f"tools/{slug}.md 'Last verified {ym}' is in the future")
    elif this_m - _ym_to_months(ym) > STALE_MONTHS:
        stale_docs.append((slug, ym))
if stale_docs:
    worst = sorted(stale_docs, key=lambda x: x[1])
    shown = ", ".join(f"{s}({y})" for s, y in worst[:10])
    warn("STALE", f"{len(stale_docs)} tool doc(s) not re-verified in >{STALE_MONTHS}mo — re-check "
                  f"repo/price + bump 'Last verified' when next sweeping their domain: {shown}"
                  f"{' …' if len(stale_docs) > 10 else ''}")

# ---- DOCCOVER (coverage net: every repo in a LIVE shard row should have a per-tool doc) ----
# Surfaces "added a shard tool but forgot its tools/<slug>.md", the tracking gap that TOOLS
# (index<->doc) cannot see. WARN, not BLOCK: prose / cross-domain / tombstone repos would false-block.
if tool_docs_text:
    documented = {_strip_git(r).lower() for txt in tool_docs_text.values() for r in REPO_RE.findall(txt)}
    TOMB = ("avoid", "dead", "d-404", "d-stale", "d-supersed", "~~", "deprecated", "(404)")
    undoc = {}
    for d, txt in shard_text.items():
        for ln in txt.splitlines():
            s = ln.strip()
            if not s.startswith("|") or "---" in s or any(t in s.lower() for t in TOMB):
                continue
            for r in REPO_RE.findall(ln):
                r = _strip_git(r).lower()
                if r not in documented:
                    undoc.setdefault(r, d)
    if undoc:
        items = ", ".join(f"{r}({d})" for r, d in list(undoc.items())[:10])
        if len(undoc) > 10:
            items += f" (showing 10 of {len(undoc)})"
        warn("DOCCOVER", f"{len(undoc)} live shard repo(s) have no per-tool doc — add tools/<slug>.md "
                         f"+ an index row (or tombstone the shard row): {items}")

# ---- REGISTRY (machine-readable authoritative tool list, 3-way registry<->index<->doc) ----
# Brings NON-GitHub SaaS/lib tools into a deterministic tracking net (DOCCOVER only sees repos).
# registry.json is THE list of tools; the gate enforces it equals the doc files and the index slugs,
# so a SaaS tool can't lose its doc or fall out of the index without a hard BLOCK.
REGISTRY = os.path.join(TOOLS_DIR, "registry.json")
if os.path.isdir(TOOLS_DIR) and 'fs_slugs' in dir():
    if not os.path.exists(REGISTRY):
        warn("REGISTRY", "tools/registry.json absent — SaaS/non-repo tools have no deterministic net")
    else:
        try:
            reg = json.loads(read(REGISTRY))
        except Exception as e:
            block("REGISTRY", f"tools/registry.json is not valid JSON: {e}")
            reg = {"tools": []}
        reg_slugs = {t.get("slug") for t in reg.get("tools", []) if t.get("slug")}
        no_doc = reg_slugs - fs_slugs
        no_idx = reg_slugs - idx_slugs
        no_reg = fs_slugs - reg_slugs
        if no_doc: block("REGISTRY", f"registry lists tools with no doc file: {sorted(no_doc)}")
        if no_idx: block("REGISTRY", f"registry lists tools missing from index.md: {sorted(no_idx)}")
        if no_reg: block("REGISTRY", f"tool docs missing from registry (it is authoritative — add them): {sorted(no_reg)}")
        valid_domains = fs_domains  # the authoritative shard set (STRUCT block, computed above)
        for t in reg.get("tools", []):
            slug = t.get("slug")
            domain = t.get("domain")
            if not domain:
                warn("REGISTRY", f"{slug} has no domain in registry")
            elif domain not in valid_domains:
                block("REGISTRY", f"{slug}: domain '{domain}' is not a real shard (valid: {sorted(valid_domains)})")

        # repo field validation (kind=repo only): the authoritative repo slug must be a
        # well-formed owner/name AND actually appear as a github.com URL in that tool's own doc.
        # The REPO/GHACTIVE existence gates scan the markdown (REPO_RE over all_text), NEVER the
        # registry field, so a refresh could mutate registry.json's canonical repo to a typo/
        # hallucination while the doc URL stays correct, registry lies, gate stays green. This
        # closes that drift. saas/lib (repo=None) are untouched.
        for t in reg.get("tools", []):
            if t.get("kind") != "repo":
                continue
            slug, repo = t.get("slug"), t.get("repo")
            if not repo:
                block("REGISTRY", f"{slug} is kind=repo but has no repo slug")
                continue
            if not SLUG_FMT.match(repo):
                block("REGISTRY", f"{slug}: registry repo '{repo}' is not a well-formed owner/name slug")
                continue
            doc_slugs = {_strip_git(r).lower() for r in REPO_RE.findall(tool_docs_text.get(slug, ""))}
            if repo.lower() not in doc_slugs:
                block("REGISTRY", f"{slug}: registry repo '{repo}' does not match any github.com URL "
                                  f"in tools/{slug}.md (registry-doc drift)")

# ---- METH ----
skill = read(SKILLMD)
for marker in ["L1", "L5"]:                       # source-tier definitions live in SKILL.md
    if marker not in skill:
        block("METH", f"SKILL.md lost source-tier marker '{marker}'")
for marker in ["①", "②", "③", "④"]:  # ①②③④ route legend lives in the index
    if marker not in idx:
        block("METH", f"sources-index.md lost barrier-route marker '{marker}'")
guardrail_nums = len(re.findall(r"^\s*\d+\.\s+\*\*", skill, re.M))
if guardrail_nums < 8:
    warn("METH", f"SKILL.md numbered guardrails look reduced ({guardrail_nums} found, expect >=8)")

# ---- COVER (vs baseline) ----
base_total = 0
cur_total = 0
for d in fs_domains:
    cur = count_table_rows(shard_text[d])
    cur_total += cur
    base_txt = git_show(BASE, f"skills/market-intel/reference/domains/{d}.md")
    base = count_table_rows(base_txt) if base_txt else cur
    base_total += base
    if base and (base - cur) / base > COVER_SHARD_DROP:
        block("COVER", f"{d}: source rows dropped {base}->{cur} (>{int(COVER_SHARD_DROP*100)}%) — possible mass deletion")
if base_total and (base_total - cur_total) / base_total > COVER_GLOBAL_DROP:
    block("COVER", f"total source rows dropped {base_total}->{cur_total} (>{int(COVER_GLOBAL_DROP*100)}%)")

# ---- CHURN (C7: incremental edits, not rewrite) + DELETE (C4: deletion needs a death-code) ----
def git_diff(relpath):
    return subprocess.run(["git", "diff", BASE, "--", relpath], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8").stdout

DEATH_CODES = ("D-404", "D-STALE", "D-PRICE", "D-TOS", "D-SUPERSEDED")
changelog_added = "\n".join(l[1:] for l in git_diff("CHANGELOG.md").splitlines()
                            if l.startswith("+") and not l.startswith("+++"))
genuinely_added_any = []   # AUDIT (P4): names of source rows that are NEW this sweep (not edits)
for d in fs_domains:
    rel = f"skills/market-intel/reference/domains/{d}.md"
    diff = git_diff(rel)
    if not diff.strip():
        continue                                  # untouched shard
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    base_lines = len(git_show(BASE, rel).splitlines()) or 1
    churn = (len(added) + len(removed)) / base_lines
    if churn > 0.40:
        block("CHURN", f"{d}: {int(churn*100)}% of lines changed (>40%) — looks like a rewrite, not an "
                       f"incremental edit (C7); route to human review")
    def _row_name(line):
        # first cell of a markdown table row = the source identity; strip markdown emphasis AND the
        # volatile (NNk★) star annotation. A star-count refresh is an EDIT of an existing source, not
        # a delete+add of a different one, so it must NOT change the row's identity -- otherwise fixing
        # a stale star (required by the STAR check) trips the DELETE check (C4), the two contradicting
        # each other on any star fix living in the identity cell. The STAR check still verifies the
        # number independently; identity is the repo/tool name, never its (volatile) star count.
        cells = [c.strip() for c in line.lstrip("+-").strip().strip("|").split("|")]
        if not cells:
            return ""
        name = re.sub(r"[*`]", "", cells[0])
        # Strip the star count in EVERY shape, via the same regex the STAR gate matches with. It
        # used to strip only the literal `(NNk★)`, the same narrow assumption STAR itself made, so
        # the moment STAR started catching a stale `(133★)` and the fix landed, DELETE saw the row's
        # identity change and blocked the very edit STAR demanded. Two gates disagreeing about what
        # a star annotation looks like is how a repo ends up unable to satisfy both.
        name = STAR_CLAIM_RE.sub("", name)
        name = re.sub(r"\(\s*[,;]?\s*\)", "", name)
        return re.sub(r"\s{2,}", " ", name).strip().lower()
    def _is_src_row(line):
        s = line.lstrip("+-").strip()
        return s.startswith("|") and "---" not in s and not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I)
    added_names = {_row_name(l) for l in added if _is_src_row(l)}
    removed_names = {_row_name(l) for l in removed if _is_src_row(l)}
    # an added table row whose source-name was NOT already present (removed line) = a genuinely NEW
    # source row (mirror of genuinely_removed). Edits show as remove+add of the same name -> excluded.
    genuinely_added_any += [n for n in added_names if n and n not in removed_names]
    # a removed table row whose source-name still appears in an added row = MODIFICATION, not a
    # deletion (git diff shows an edited line as remove+add). Only a name that's GONE is a real delete.
    genuinely_removed = [l for l in removed if _is_src_row(l) and _row_name(l) and _row_name(l) not in added_names]
    if genuinely_removed:
        added_text = "\n".join(added)
        if not any(c in changelog_added or c in added_text for c in DEATH_CODES):
            block("DELETE", f"{d}: source row(s) removed without a death-code (C4: "
                            f"D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED) in CHANGELOG or an Avoid(dead) line")

    # ---- ROUTE (C2: a Default pick may not silently downgrade free/④③ -> paid ①②) ----
    # A route downgrade is a MODIFICATION (the source name is present on BOTH the removed and added
    # sides of the diff), NOT a deletion, so it lives at LOOP level as a sibling of DELETE, never
    # nested under `if genuinely_removed:` (genuinely_removed is empty for a modification, so the
    # check would silently never fire). Escape hatch: an intent-bearing CHANGELOG/row reason. We key
    # on the MAX route glyph per side (a row can list several barrier routes; the best one is what a
    # user gets), mirroring how DELETE keys on specific DEATH_CODES, not common prose words.
    GLYPH_RANK = {"④": 4, "③": 3, "②": 2, "①": 1}
    ROUTE_REASON = ("why paid", "paid because", "免费替代", "free route unavailable",
                    "no free route", "free route blocked", "free route gone")
    def _route_glyphs(line):
        return [GLYPH_RANK[g] for g in line if g in GLYPH_RANK]
    added_by_name = {}
    for l in added:
        if _is_src_row(l):
            added_by_name.setdefault(_row_name(l), l)
    for rl in removed:
        if not _is_src_row(rl):
            continue
        name = _row_name(rl)
        al = added_by_name.get(name)
        if not name or not al:                        # only MODIFICATIONS (name in both sides)
            continue
        rem_routes, add_routes = _route_glyphs(rl), _route_glyphs(al)
        if not rem_routes or not add_routes:
            continue
        if max(rem_routes) >= 3 and max(add_routes) <= 2:   # ④/③ -> ①/② downgrade
            if not any(c in changelog_added or c in al for c in ROUTE_REASON):
                block("ROUTE", f"{d}: '{name}' route downgraded free/④③ -> paid ①② without a "
                               f"CHANGELOG reason (C2) — add why (route/why paid) or revert")

# ---- AUDIT (P4: editor != verifier, new source rows need an independent cross-model attestation) ----
# EVOLUTION.md openly admits a P4 violation: the same headless LLM both edits AND verifies a refresh.
# This makes the mechanical/existence half gate-checked the same way DELETE gate-checks a death-code:
# a genuinely-NEW source row (mirror of genuinely_removed) requires a CHANGELOG attestation line
# `AUDIT: <model> verdict=<pass|hold>` written by a fresh zero-context reviewer of a DIFFERENT model.
# WARN-tier this cycle (advisory), flips to BLOCK once the cross-model review step is routine.
AUDIT_RE = re.compile(r"^\s*AUDIT:\s*\S+\s+verdict=(pass|hold)\b", re.IGNORECASE)
if genuinely_added_any:
    if not any(AUDIT_RE.match(l) for l in changelog_added.splitlines()):
        _names = ", ".join(sorted(set(genuinely_added_any))[:8])
        warn("AUDIT", f"{len(genuinely_added_any)} new source row(s) added ({_names}) without an "
                      f"independent cross-model audit attestation in CHANGELOG (expected a line "
                      f"`AUDIT: <model> verdict=<pass|hold>`) — P4 editor!=verifier "
                      f"(WARN-tier this cycle; will BLOCK once routine)")

# ---- PRICE (C5: a CHANGED price line must carry an official URL + fetch date in the same hunk) ----
# WARN-tier soft launch, flip PRICE_BLOCK=True to enforce after one populated sweep cycle. The
# sidecar sweep JSON carries no {price,url,fetched} evidence tuple, so the robust path is a diff-hunk
# evidence check: when a price token is ADDED to pricing-install.md, the same hunk must show an
# official https:// URL + a fetch/verify date (C5 + the EVOLUTION.md auto-merge precondition).
PRICE_BLOCK = False  # WARN-tier soft launch; flip to True after one populated sweep cycle
PRICE_TOKEN_RE = re.compile(r"[$€£]\s?\d|\d+\s?(?:USD|EUR|GBP)\b|/1k\b|/mo\b|/min\b|/day\b|\bfree\s+\d", re.I)
URL_RE = re.compile(r"https?://")
DATE_RE = re.compile(r"\b(?:fetched|verified|last_verified)\b|\b\d{4}-\d{2}(?:-\d{2})?\b", re.I)
pricing_rel = os.path.relpath(PRICING, ROOT).replace(os.sep, "/")
pricing_diff = git_diff(pricing_rel) if os.path.exists(PRICING) else ""
if pricing_diff.strip():
    _emit_price = block if PRICE_BLOCK else warn
    # split the diff into hunks (each starts at an @@ header); a price line's evidence may live
    # anywhere in its own hunk, not just on the same physical line.
    hunks, cur = [], []
    for ln in pricing_diff.splitlines():
        if ln.startswith("@@"):
            if cur:
                hunks.append(cur)
            cur = []
        cur.append(ln)
    if cur:
        hunks.append(cur)
    for hunk in hunks:
        hunk_added = [l[1:] for l in hunk if l.startswith("+") and not l.startswith("+++")]
        hunk_blob = "\n".join(hunk_added)
        hunk_has_url = bool(URL_RE.search(hunk_blob))
        hunk_has_date = bool(DATE_RE.search(hunk_blob))
        for al in hunk_added:
            if not PRICE_TOKEN_RE.search(al):
                continue
            line_has_url = bool(URL_RE.search(al))
            line_has_date = bool(DATE_RE.search(al))
            has_url = line_has_url or hunk_has_url
            has_date = line_has_date or hunk_has_date
            if has_url and has_date:
                continue
            missing = []
            if not has_url: missing.append("official URL")
            if not has_date: missing.append("fetch date")
            _emit_price("PRICE-EVIDENCE", f"changed price line missing {' + '.join(missing)} "
                                          f"in the same diff hunk (C5): {al.strip()[:80]}")

# ---- CONST (scope guard: automated run must not modify CONSTITUTION.md) ----
const_path = os.path.join(ROOT, "CONSTITUTION.md")
if not os.path.exists(const_path):
    block("CONST", "CONSTITUTION.md missing")
else:
    diff = subprocess.run(["git", "diff", "--name-only", BASE, "--", "CONSTITUTION.md"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    if diff:
        block("CONST", "CONSTITUTION.md was modified — automation may not change the constitution")

# ---- verdict ----
print(f"market-intel verify_matrix: {len(repos)} repos checked, "
      f"{cur_total} source rows, base={BASE}")
for w in warns: print("WARN", w)
if fails:
    for f in fails: print("BLOCK", f)
    print(f"\nRESULT: BLOCK ({len(fails)} blocking issue(s)) — do NOT commit/push")
    sys.exit(1)
print("\nRESULT: PASS — matrix may land")
sys.exit(0)
