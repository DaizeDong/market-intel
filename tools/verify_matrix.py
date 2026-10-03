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
  FRESH    verification dates are valid, non-future, and never regress from the verified baseline
  STALE    (WARN) a tool doc not re-verified in >9 months is nominated for re-check (anti-rot)
  DOCCOVER (WARN) a github repo in a LIVE (non-tombstone) shard row with no per-tool doc (anti-lost-tracking)
  METH     SKILL.md still contains the 8 numbered guardrails, L1/L5 tiers, and ①②③④ route legend
  COVER    vs git main baseline: total source rows didn't drop >10%, no shard lost >30% of its rows
  PRICE    (WARN soft-launch) a CHANGED price line in pricing-install.md must carry an official URL +
           fetch date in the same diff hunk (C5); flip PRICE_BLOCK=True to enforce after one cycle
  AUDIT    (WARN) new source rows added with no independent cross-model audit line in the CHANGELOG
           (`AUDIT: <model> verdict=<pass|hold>`) — P4 editor!=verifier; WARN-tier launch, BLOCK later
  CONST    CONSTITUTION.md exists and was not modified by this run (scope guard)

Usage: python tools/verify_matrix.py [--no-net] [--no-cache] [--base main]
Default cache persistence requires a verified PRIVATE companion. Use --no-cache to skip
cache reads and writes intentionally while retaining current network checks.
Run from the repo root (~/market-intel).
"""
import json, re, subprocess, sys, os
from git_baseline import Baseline, BaselineError
from domain_changes import historical_domains, check_coverage, check_domain_diff, count_table_rows
from github_activity import activity_results
from private_cache import GH_CACHE_PATH, load_cache, prepare_write, save_entries
from private_inventory import InventoryError
from human_review import REVIEW_ENV, ReviewError, load_review

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
CACHE_ENABLED = "--no-cache" not in sys.argv
BASE = "main"
if "--base" in sys.argv:
    try:
        BASE = sys.argv[sys.argv.index("--base") + 1]
    except IndexError:
        print("RESULT: NOT_EXAMINED --base requires a commit reference", file=sys.stderr)
        sys.exit(2)
try:
    human_review = load_review(os.environ.get(REVIEW_ENV))
    comparison = Baseline(ROOT, BASE)
except (BaselineError, ReviewError) as exc:
    print(f"RESULT: {exc}", file=sys.stderr)
    sys.exit(2)

fails, warns = [], []
def block(code, msg): fails.append(f"[{code}] {msg}")
def warn(code, msg): warns.append(f"[{code}] {msg}")

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def git_show(ref, relpath):
    try:
        return comparison.show(relpath)
    except BaselineError as exc:
        print(f"RESULT: {exc}", file=sys.stderr)
        sys.exit(2)

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
    fs_slugs = {f[:-3] for f in os.listdir(TOOLS_DIR)
                if f.endswith(".md") and f != "index.md" and not f.endswith(".auto.md")}
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
            ["gh", "api", "--hostname", "github.com", f"repos/{r}", "--jq", "{s:.stargazers_count,a:.archived,p:.pushed_at}"],
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
        return {"ok": True, "stars": d.get("s"), "archived": d.get("a"), "pushed_at": d.get("p")}
    except Exception:
        return {"ok": False, "err": "unparseable", "stderr": stderr}

repo_api = {}
gh_destination, gh_cache = None, {}
if not NO_NET:
    try:
        gh_destination, gh_cache = load_cache(GH_CACHE_PATH, enabled=CACHE_ENABLED)
        prepare_write(GH_CACHE_PATH, gh_destination, enabled=CACHE_ENABLED)
    except InventoryError as exc:
        print(f"RESULT: NOT_EXAMINED private verification cache: {exc}", file=sys.stderr)
        sys.exit(2)
    if not CACHE_ENABLED:
        print("CACHE: disabled (--no-cache); current network checks remain enabled")
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
# Decide from the combined current fetch, then share evidence in the PRIVATE cache.
# 404/archived remain BLOCK, stale remains WARN, and unavailable evidence remains a warning.
import datetime
_now_ts = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
ghactive_results = []
if NO_NET:
    warn("GHACTIVE", "skipped GitHub activity verification (--no-net)")
else:
    ghactive_results = activity_results(repos, repo_api, gh_cache, _now_ts, block, warn)
    for entry in ghactive_results:
        entry["hostname"] = "github.com"
    try:
        save_entries(GH_CACHE_PATH, {entry["repo"]: entry for entry in ghactive_results},
                     gh_destination, enabled=CACHE_ENABLED)
    except InventoryError as exc:
        block("GHACTIVE", f"private activity cache persistence failed: {exc}")
    _verdicts = {v: 0 for v in ("PASS", "WARN", "BLOCK", "RATE_LIMITED")}
    for entry in ghactive_results:
        _verdicts[entry["verdict"]] += 1
    print(f"GHACTIVE summary: {_verdicts['PASS']} PASS, {_verdicts['WARN']} WARN, "
          f"{_verdicts['BLOCK']} BLOCK, {_verdicts['RATE_LIMITED']} RATE_LIMITED "
          f"(of {len(ghactive_results)} repos checked)")

# ---- FRESH (shards/pricing: `last_verified:` · tool docs: `Last verified:`) ----
today = datetime.date.today()
this_month = today.strftime("%Y-%m")
def _ym_to_months(ym): return int(ym[:4]) * 12 + int(ym[5:7])
this_m = _ym_to_months(this_month)
STALE_MONTHS = 9          # a per-tool doc unchecked this long is nominated for re-verification (WARN)
VERIFIED_RE = re.compile(r"\blast[_ ]verified:\s*([^\s`*]+)", re.I)


def _section_dates(text, *, card=False):
    """Key shard markers by heading path; cards use one document-level marker."""
    headings, sections = {}, {}
    for line in text.splitlines():
        heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading and not card:
            level = len(heading.group(1))
            title = heading.group(2)
            marker = VERIFIED_RE.search(title)
            if marker:
                title = title[:marker.start()]
            title = re.sub(r"[*`~]", "", title).strip(" ()[]").casefold()
            if title:
                headings = {depth: value for depth, value in headings.items() if depth < level}
                headings[level] = title
        key = "document" if card else " / ".join(headings.values()) or "document"
        for match in VERIFIED_RE.finditer(line):
            sections.setdefault(key, []).append(match.group(1).rstrip(".,;)]"))
    return sections


def _validated_dates(sections, label, *, historical=False):
    valid = {}
    for section, values in sections.items():
        for value in values:
            try:
                if not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value):
                    raise ValueError("invalid date shape")
                day = datetime.date.fromisoformat(value + "-01" if len(value) == 7 else value)
            except ValueError:
                report = warn if historical else block
                report("FRESH", f"{label} [{section}] has an invalid last_verified date")
                continue
            valid.setdefault(section, []).append(day)
    return valid


fresh_documents = {f"domains/{domain}.md": text for domain, text in shard_text.items()}
fresh_documents.update({f"tools/{slug}.md": text for slug, text in tool_docs_text.items()})
for relative, path in (("volatile/pricing-install.md", PRICING), ("install-guide.md", INSTALL_GUIDE)):
    if os.path.isfile(path):
        fresh_documents[relative] = read(path)

stale_docs = []
for relative, text in sorted(fresh_documents.items()):
    card = relative.startswith("tools/")
    current_sections = _section_dates(text, card=card)
    if card and sum(map(len, current_sections.values())) > 1:
        block("FRESH", f"{relative} has ambiguous verification markers; use one card-level Last verified marker")
    current_dates = _validated_dates(current_sections, relative)
    previous = git_show(BASE, "skills/market-intel/reference/" + relative) or ""
    baseline_sections = _section_dates(previous, card=card)
    if card and sum(map(len, baseline_sections.values())) > 1:
        warn("FRESH", f"baseline {relative} has ambiguous verification markers")
    baseline_dates = _validated_dates(baseline_sections, "baseline " + relative, historical=True)
    for section, dates in current_dates.items():
        if max(dates) > today:
            block("FRESH", f"{relative} [{section}] last_verified is in the future")
    for section, dates in baseline_dates.items():
        current = current_dates.get(section)
        if not current:
            block("FRESH", f"{relative} [{section}] lost its baseline last_verified evidence")
        elif max(current) < max(dates):
            block("FRESH", f"{relative} [{section}] last_verified moved backward from "
                           f"{max(dates).isoformat()} to {max(current).isoformat()}")
    if card:
        dates = [day for values in current_dates.values() for day in values]
        if not dates:
            warn("FRESH", f"{relative} has no valid 'Last verified: YYYY-MM' line")
        elif this_m - _ym_to_months(max(dates).strftime("%Y-%m")) > STALE_MONTHS:
            stale_docs.append((relative[6:-3], max(dates).strftime("%Y-%m")))
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
if not os.path.isfile(REGISTRY):
    block("REGISTRY", "tools/registry.json is missing; authoritative catalog was not examined")
if os.path.isdir(TOOLS_DIR) and 'fs_slugs' in dir():
    if not os.path.exists(REGISTRY):
        pass  # The required local input was blocked above, independently of network mode.
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
try:
    baseline_domains = historical_domains(comparison, fs_domains)
except BaselineError as exc:
    print(f"RESULT: {exc}", file=sys.stderr)
    sys.exit(2)
cur_total, base_total = check_coverage(
    shard_text, baseline_domains, count_table_rows, block, COVER_GLOBAL_DROP, COVER_SHARD_DROP)

# ---- CHURN (C7: incremental edits, not rewrite) + DELETE (C4: deletion needs a death-code) ----
def git_diff(relpath):
    try:
        return comparison.diff(relpath)
    except BaselineError as exc:
        print(f"RESULT: {exc}", file=sys.stderr)
        sys.exit(2)

changelog_added = "\n".join(l[1:] for l in git_diff("CHANGELOG.md").splitlines()
                            if l.startswith("+") and not l.startswith("+++"))
genuinely_added_any = []
for d, base_text in baseline_domains.items():
    rel = f"skills/market-intel/reference/domains/{d}.md"
    genuinely_added_any.extend(check_domain_diff(
        d, git_diff(rel), base_text, changelog_added, STAR_CLAIM_RE, block,
        current_text=shard_text.get(d, ""), human_review=human_review,
        baseline_commit=comparison.commit))

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
    diff = git_diff("CONSTITUTION.md").strip()
    if diff:
        block("CONST", "CONSTITUTION.md was modified — automation may not change the constitution")

# ---- verdict ----
comparison.close()
print(f"market-intel verify_matrix: {len(repos)} repos checked, "
      f"{cur_total} source rows, base={BASE}")
for w in warns: print("WARN", w)
if fails:
    for f in fails: print("BLOCK", f)
    print(f"\nRESULT: BLOCK ({len(fails)} blocking issue(s)) — do NOT commit/push")
    sys.exit(1)
print("\nRESULT: PASS — matrix may land")
sys.exit(0)
