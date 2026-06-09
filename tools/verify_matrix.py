#!/usr/bin/env python3
"""Deterministic anti-regression gate for the market-intel source matrix.

LLM proposes, this gate disposes. Run after an automated refresh edits the shards, BEFORE commit.
Exit 0 = matrix may land; exit non-zero = BLOCK (caller must not commit/push). Fail-closed: if a
check can't be performed (e.g. GitHub API unreachable), that's a BLOCK, not a pass.

Checks (the real failure modes of an unattended LLM refresh):
  STRUCT  every domain in sources-index.md has a shard file, and vice versa
  REPO    every github.com/<owner>/<repo> referenced actually exists (gh api, fail-closed)
  STAR    where a repo and an (NNk★) annotation co-occur on a line, the count is within tolerance
  FRESH   every `last_verified: YYYY-MM` is a real, non-future month
  METH    SKILL.md still contains the 8 numbered guardrails, L1/L5 tiers, and ①②③④ route legend
  COVER   vs git main baseline: total source rows didn't drop >10%, no shard lost >30% of its rows
  CONST   CONSTITUTION.md exists and was not modified by this run (scope guard)

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
    idx_slugs = set(re.findall(r"\(([a-z0-9][a-z0-9-]*)\.md\)", tools_idx))
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
def _strip_git(r): return r[:-4] if r.endswith(".git") else r
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

# ---- FRESH ----
import datetime
this_month = datetime.date.today().strftime("%Y-%m")
for m in re.finditer(r"last_verified:\s*(\d{4})-(\d{2})", all_text):
    ym = f"{m.group(1)}-{m.group(2)}"
    if ym > this_month:
        block("FRESH", f"last_verified {ym} is in the future")

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
