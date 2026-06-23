#!/usr/bin/env python3
"""Deterministic anti-regression gate for the market-intel source matrix.

LLM proposes, this gate disposes. Run after an automated refresh edits the shards, BEFORE commit.
Exit 0 = matrix may land; exit non-zero = BLOCK (caller must not commit/push). Fail-closed: if a
check can't be performed (e.g. GitHub API unreachable), that's a BLOCK, not a pass.

Checks (the real failure modes of an unattended LLM refresh):
  STRUCT   every domain in sources-index.md has a shard file, and vice versa
  TOOLS    tools/index.md <-> tools/*.md coverage (missing doc = BLOCK, orphan doc = WARN)
  REGISTRY tools/registry.json <-> index <-> docs 3-way (covers non-repo SaaS too; mismatch = BLOCK)
  REPO     every github.com/<owner>/<repo> in shards/pricing/tool-docs exists (gh api, fail-closed)
  GHACTIVE every github repo is alive (not archived) and pushed_at within 12mo (P4 deterministic gate
           against LLM-only "freshness" judgments; 404/archived = BLOCK, stale = WARN, RL = bypass)
  STAR     where a repo and an (NNk★) annotation co-occur on a line, the count is within tolerance
  FRESH    every `last_verified:`/`Last verified:` is real + non-future (shards, pricing, AND tool docs)
  STALE    (WARN) a tool doc not re-verified in >9 months is nominated for re-check (anti-rot)
  DOCCOVER (WARN) a github repo in a LIVE (non-tombstone) shard row with no per-tool doc (anti-lost-tracking)
  METH     SKILL.md still contains the 8 numbered guardrails, L1/L5 tiers, and ①②③④ route legend
  COVER    vs git main baseline: total source rows didn't drop >10%, no shard lost >30% of its rows
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
# repo token must be IMMEDIATELY before the (NNk★) annotation (only **/spaces between) —
# prevents pairing a star with a prose token or an adjacent repo on the same line.
STAR_LINE_RE = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\*{0,2}\s*\((\d+(?:\.\d+)?)k★\)")

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
# Strip a trailing ".git" — a `git clone https://github.com/o/r.git` URL is the same repo as o/r;
# without this the literal "o/r.git" token 404s on the API (false positive).
# Also strip trailing sentence punctuation the slug regex greedily swallows ("OpenBB-finance/OpenBB."
# at end of a sentence captures the period) — that lone dot 404s on the API (false positive).
def _strip_git(r):
    r = r.rstrip("./,);:")          # drop trailing sentence punctuation (incl. a stray ".")
    return r[:-4] if r.endswith(".git") else r
repo_set = {_strip_git(r) for r in REPO_RE.findall(all_text)}
repo_set |= {_strip_git(m.group(1)) for m in STAR_LINE_RE.finditer(all_text)}
repos = sorted(r for r in repo_set if not r.endswith(".md") and r.count("/") == 1 and "github.com" not in r)

# HEURISTIC bare slugs (404 → WARN only): unstarred slug-like tokens in table rows. Catches likely
# hallucinations (e.g. a mistyped erithwik/mcp-hn) for human attention, but does NOT hard-block —
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

# ---- REPO + STAR (fail-closed) ----
repo_stars = {}
if NO_NET:
    warn("REPO", "skipped GitHub verification (--no-net)")
else:
    import time
    for r in repos:
        res = None
        for attempt in range(3):                 # retry transient errors; 404 is decided immediately
            res = subprocess.run(["gh", "api", f"repos/{r}", "--jq", "{s:.stargazers_count,a:.archived}"],
                                 capture_output=True, text=True, encoding="utf-8")
            if res.returncode == 0:
                break
            if "Not Found" in (res.stderr or "") or "404" in (res.stderr or ""):
                break                            # real 404 — don't retry, it's a hard fact
            time.sleep(2 * (attempt + 1))        # transient (rate-limit/network): back off and retry
        if res.returncode != 0:
            if "Not Found" in (res.stderr or "") or "404" in (res.stderr or ""):
                block("REPO", f"{r} does not exist (404) — hallucinated or dead repo")
            else:
                block("REPO", f"{r} could not be verified after retries (fail-closed): {res.stderr.strip()[:80]}")
            continue
        try:
            d = json.loads(res.stdout)
            repo_stars[r] = d["s"]
        except Exception:
            block("REPO", f"{r} returned unparseable API response")
    # heuristic bare slugs: verify but only WARN (avoid false-blocking prose / npm scopes)
    for r in sorted(warn_slugs):
        res = subprocess.run(["gh", "api", f"repos/{r}", "--jq", ".full_name"],
                             capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0 and ("Not Found" in (res.stderr or "") or "404" in (res.stderr or "")):
            warn("REPO?", f"{r} not found on GitHub — if it's a repo it may be hallucinated/mistyped; "
                          f"if prose/npm-scope, ignore (mirror block will disambiguate)")
    # STAR tolerance on lines pairing a repo with an (NNk★)
    for txt in list(shard_text.values()) + list(tool_docs_text.values()) + ([read(PRICING)] if os.path.exists(PRICING) else []):
        for ln in txt.splitlines():
            m = STAR_LINE_RE.search(ln)
            if not m:
                continue
            repo, claimed_k = m.group(1), float(m.group(2))
            real = repo_stars.get(repo)
            if real is None:
                continue
            claimed = claimed_k * 1000
            if real == 0 or abs(claimed - real) / real > STAR_TOL:
                block("STAR", f"{repo}: claims {claimed_k}k★ but API says {real} (>{int(STAR_TOL*100)}% off)")

# ---- GHACTIVE (P4 deterministic activity gate) ----
# WHY: LLM-judgment lenses (existence, freshness, top_pick_impact) confidently passed a candidate
# (BigGo, 2026-06-17 sweep) whose repo was 13 months stale. PHILOSOPHY §4 demands an independent
# deterministic source — gh api `pushed_at` + `archived`. Inviolable, not optional.
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
        res = subprocess.run(
            ["gh", "api", f"repos/{r}", "--jq", "{pushed_at:.pushed_at,archived:.archived}"],
            capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            stderr = (res.stderr or "")
            if "Not Found" in stderr or "404" in stderr:
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "BLOCK", "reason": "404 not found", "checked_at": _now_iso}
                block("GHACTIVE", f"{r}: 404 not found (URL fabricated, deleted, or moved)")
            elif "rate limit" in stderr.lower() or "API rate" in stderr or "403" in stderr:
                # Rate-limit is transient external state; per the philosophy we must not gate the
                # gate on it. Surface as WARN and skip — re-run will pick it up.
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
        try:
            d = json.loads(res.stdout)
            pushed_at = d.get("pushed_at")
            archived = bool(d.get("archived"))
        except Exception:
            entry = {"repo": r, "pushed_at": None, "archived": None,
                     "verdict": "RATE_LIMITED", "reason": "unparseable response",
                     "checked_at": _now_iso}
            warn("GHACTIVE", f"{r}: unparseable activity response")
            ghactive_results.append(entry)
            gh_cache[r] = entry
            continue
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
# >STALE_MONTHS old = WARN (surfaced so a sweep re-verifies it — closes the silent-rot gap).
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
# Surfaces "added a shard tool but forgot its tools/<slug>.md" — the tracking gap that TOOLS
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
        warn("DOCCOVER", f"{len(undoc)} live shard repo(s) have no per-tool doc — add tools/<slug>.md "
                         f"+ an index row (or tombstone the shard row): {items}")

# ---- REGISTRY (machine-readable authoritative tool list — 3-way registry<->index<->doc) ----
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
        for t in reg.get("tools", []):
            if not t.get("domain"):
                warn("REGISTRY", f"{t.get('slug')} has no domain in registry")

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
        # first cell of a markdown table row = the source identity; strip markdown emphasis
        cells = [c.strip() for c in line.lstrip("+-").strip().strip("|").split("|")]
        return re.sub(r"[*`]", "", cells[0]).strip().lower() if cells else ""
    def _is_src_row(line):
        s = line.lstrip("+-").strip()
        return s.startswith("|") and "---" not in s and not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I)
    added_names = {_row_name(l) for l in added if _is_src_row(l)}
    # a removed table row whose source-name still appears in an added row = MODIFICATION, not a
    # deletion (git diff shows an edited line as remove+add). Only a name that's GONE is a real delete.
    genuinely_removed = [l for l in removed if _is_src_row(l) and _row_name(l) and _row_name(l) not in added_names]
    if genuinely_removed:
        added_text = "\n".join(added)
        if not any(c in changelog_added or c in added_text for c in DEATH_CODES):
            block("DELETE", f"{d}: source row(s) removed without a death-code (C4: "
                            f"D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED) in CHANGELOG or an Avoid(dead) line")

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
