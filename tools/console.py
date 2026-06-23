#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""market-intel CONSOLE — the ops-side command deck for the 168-tool source matrix.

WHY THIS EXISTS
  The registry (`reference/tools/registry.json`) is the *catalog*: 168 tools that the skill
  *could* route to. But "in the catalog" != "usable right now on this machine". A tool can be
  cataloged, its repo can be healthy, and it can still be unreachable because its MCP isn't
  connected, its key isn't set, or its CLI isn't installed. This console flattens that
  catalog-vs-reality gap into one four-state table and lets an operator drive it.

FOUR-STATE MODEL (computed per tool)
  1. cataloged       — always true (it's in registry.json).
  2. repo_healthy    — kind in {repo} (and mcp-backed-by-repo): gh-api-cache verdict says alive
                       (PASS/WARN = healthy-ish; BLOCK = 404/archived; missing = unknown).
                       Non-repo (saas/lib without repo) → n/a.
  3. available_now   — reachable on THIS machine right now:
                         · MCP-class  → `claude mcp list` shows it Connected
                         · CLI-class  → the binary is on PATH
                         · keyless web-API → assumed reachable (no probe; flagged web-assumed)
  4. blocked_by      — when available_now is false: cold-mcp / needs-key / needs-install /
                       needs-deploy / unknown.

HARD CONSTRAINT — P5 SEAM (PHILOSOPHY.md §P5)
  This file is REFRESH/OPS-side. It MUST NOT be imported by SKILL.md (the user-query path).
  `tools/check_p5_drift.py` greps SKILL.md for any import of refresh-side scripts. console.py is
  deliberately NOT referenced anywhere in the skill body; it is self-contained under tools/.

SAFETY
  Read-only + probe-only. Never logs in, pays, writes a secret, or mutates ~/.claude.json.
  `connect` only PRINTS a template for the user to paste themselves. Degrades gracefully: a
  missing data source marks that dimension `unknown` rather than crashing.

USAGE
  python tools/console.py status [--domain X] [--state available|cold|needs-key|needs-install|...]
  python tools/console.py tool <slug>
  python tools/console.py connect <slug>
  python tools/console.py <any-subcommand> --refresh      # re-probe env, rewrite snapshot cache
  python tools/console.py --refresh                        # refresh + default (status)

Pure stdlib (json/subprocess/argparse/os/...). UTF-8. Windows + Git Bash friendly.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

# Force UTF-8 on stdout/stderr: the Windows console defaults to GBK on this machine and chokes on
# the table glyphs (▸ ★ ✓ █). Python 3.7+ exposes .reconfigure; fall back silently if unavailable.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Paths (mirror verify_matrix.py layout so the two stay in lockstep)
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "market-intel")
REF = os.path.join(SKILL, "reference")
TOOLS_DIR = os.path.join(REF, "tools")
REGISTRY = os.path.join(TOOLS_DIR, "registry.json")
TOOLS_INDEX = os.path.join(TOOLS_DIR, "index.md")
GH_CACHE = os.path.join(ROOT, "metrics", "gh-api-cache.json")
# Snapshot cache. metrics/gh-api-cache.json is already gitignored; we co-locate ours and add it
# to .gitignore (see ensure_gitignore). It carries no secrets — only connected/installed booleans.
AVAIL_CACHE = os.path.join(ROOT, "metrics", "availability-cache.json")

# Marks for table cells
YES, NO, NA, UNK = "yes", "no", "n/a", "?"


def stderr(*a):
    print(*a, file=sys.stderr)


def read_json(path, default=None):
    """Load JSON, tolerating absence/corruption (returns default → graceful degrade)."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        stderr(f"console: warning — could not parse {os.path.relpath(path, ROOT)}: {e}")
        return default


# ---------------------------------------------------------------------------
# Slug ↔ live-signal bridge tables
#
# The registry has no MCP-server-name or CLI-command field, so we bridge here. These are
# OPS-side hints, not part of the skill contract — when a guess is wrong the worst case is a
# tool shows `unknown`/`cold`, never a crash and never a false "available".
# ---------------------------------------------------------------------------

# registry slug -> substrings that, if present in a `claude mcp list` server NAME, mean "this
# tool's MCP". Matching is case-insensitive on a normalized (alnum-only) form. A slug absent
# here is still MCP-matched by its own normalized slug as a fallback (see mcp_match).
MCP_NAME_HINTS = {
    "trends-mcp": ["trendsmcp", "trends"],
    "coingecko-mcp": ["coingecko"],
    "coinmarketcap-mcp": ["coinmarketcap"],
    "etherscan-mcp": ["etherscan"],
    "blockscout-mcp": ["blockscout"],
    "sec-edgar-mcp": ["secedgar", "edgar"],
    "fred-mcp": ["fred"],
    "alpaca-mcp": ["alpaca"],
    "finnhub": ["finnhub"],
    "yahoo-finance-mcp": ["yahoofinance", "yahoo"],
    "tradier-mcp": ["tradier"],
    "openbb-mcp": ["openbb"],
    "unusual-whales": ["unusualwhales"],
    "github-mcp": ["github"],
    "huggingface": ["huggingface", "hf"],
    "notion-mcp": ["notion"],
    "sanity-mcp": ["sanity"],
    "webflow-mcp": ["webflow"],
    "wordpress-mcp": ["wordpress"],
    "strapi-mcp": ["strapi"],
    "directus-mcp": ["directus"],
    "contentful-mcp": ["contentful"],
    "ghost-mcp": ["ghost"],
    "apollo": ["apollo"],
    "attio-mcp": ["attio"],
    "hubspot-mcp": ["hubspot"],
    "salesforce-mcp": ["salesforce"],
    "hunter": ["hunter"],
    "clay": ["clay"],
    "zerobounce": ["zerobounce"],
    "smartlead-mcp": ["smartlead"],
    "instantly-mcp": ["instantly"],
    "ahrefs-mcp": ["ahrefs"],
    "semrush-mcp": ["semrush"],
    "se-ranking-mcp": ["seranking"],
    "serpapi": ["serpapi"],
    "gsc-mcp": ["gsc", "searchconsole"],
    "dataforseo": ["dataforseo"],
    "brightdata": ["brightdata", "brightdatamcp"],
    "firecrawl": ["firecrawl"],
    "exa": ["exa"],
    "tavily": ["tavily"],
    "apify": ["apify"],
    "gdelt-mcp": ["gdelt"],
    "product-hunt-mcp": ["producthunt"],
    "sensor-tower-mcp": ["sensortower"],
    "twitterapi-io": ["twitterapi", "twitterapiio"],
    "x-official-api": ["xmcp", "twitter"],
    "enescinar-twitter-mcp": ["twittermcp"],
    "discord-mcp": ["discord"],
    "saseq-discord-mcp": ["discord"],
    "mcp-hn": ["hackernews", "mcphn", "hn"],
    "reddit-mcp-buddy": ["redditbuddy", "reddit"],
    "reddit-mcp": ["reddit"],
    "reddit-research-mcp": ["redditresearch"],
    "stack-overflow-mcp": ["stackoverflow"],
    "playwright-mcp": ["playwright"],
    "shopify-storefront-mcp": ["shopify"],
    "keepa": ["keepa"],
    "ayrshare": ["ayrshare"],
    "blotato": ["blotato"],
    "buffer": ["buffer"],
    "postiz": ["postiz"],
    "xiaohongshu-mcp": ["xiaohongshu"],
    "linkedin-mcp-server": ["linkedin"],
    "mobile-store-scraper-mcp": ["mobilestorescraper"],
    "google-news-trends-mcp": ["googlenewstrends"],
    "funding-rates-mcp": ["fundingrates"],
    "idea-reality-mcp": ["idearealty", "ideareality"],
    "trend-pulse": ["trendpulse"],
    "paper-search-mcp": ["papersearch"],
    "arxiv": ["arxiv"],
}

# registry slug -> the local CLI binary that means "this tool is installed here".
# Probed with shutil.which (+ optional `--version` confirm in deep-probe).
CLI_COMMANDS = {
    "yt-dlp": "yt-dlp",
    "github-mcp": "gh",           # github tooling is reachable via the gh CLI even sans MCP
    "searxng": "searxng",
    "ccxt": None,                 # python lib, handled by python_import probe below
}

# slug -> importable python module name (lib-class availability probe).
PY_IMPORTS = {
    "ccxt": "ccxt",
    "praw": "praw",
    "twikit": "twikit",
    "twscrape": "twscrape",
    "instaloader": "instaloader",
    "instagrapi": "instagrapi",
    "atproto": "atproto",
    "mastodon-py": "mastodon",
    "botasaurus": "botasaurus",
    "crawl4ai": "crawl4ai",
    "crawlee": "crawlee",
    "tiktok-api": "TikTokApi",
    "linkedin-scraper": "linkedin_scraper",
    "staffspy": "staffspy",
    "people-data-labs": "peopledatalabs",
    "twelve-data": "twelvedata",
    "openreview": "openreview",
    "paper-qa": "paperqa",
    "trendspy": "trendspy",
    "app-store-scraper": "app_store_scraper",
    "google-play-scraper": "google_play_scraper",
    "ddgs": "ddgs",
    "patchright": "patchright",
    # activation (self-evolve R1): free-first lib routes, each live-verified installed +
    # its keyless capability confirmed (SEC raw endpoint UA-only, yfinance keyless) —
    # console was under-reporting these as cold though P1 free-first makes them usable.
    "sec-edgar-mcp": "edgar",       # edgartools installed; SEC EDGAR public API keyless (UA only)
    "openbb-mcp": "openbb",         # openbb installed (aggregates ~100 providers incl keyless)
    "yahoo-finance-mcp": "yfinance",  # yfinance installed, fully keyless
}

# Keyless web-APIs: reachable without install OR key OR MCP. We do NOT block on these — mark
# available_now=yes with a "web-assumed" note (a real reachability ping is optional and skipped
# by default to keep the console offline-safe). Conservative list — only genuinely keyless ones.
KEYLESS_WEB = {
    "google-suggest", "stackexchange", "defillama", "geckoterminal",
    "arxiv-sanity-lite", "papers-with-code", "connected-papers-researchrabbit",
    "ai-lab-blogs", "ai-news-roundups", "lmarena", "github-mcp-registry",
    "chatgpt-apps-directory",
    # activation (self-evolve R1): keyless endpoints live-verified HTTP 200 (no key, UA only)
    "coingecko-mcp", "blockscout-mcp", "barker", "mcp-hn",
}

# Tools that are really "a skill you invoke", not an installable/connectable source. Treated as
# available (the skill ships with the harness) with a note.
SKILL_BACKED = {
    "research-lit-skill", "alphaxiv", "semantic-scholar", "static-blog",
}


def normalize(s: str) -> str:
    """Lowercase, strip everything but [a-z0-9] — for fuzzy name/slug matching."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ---------------------------------------------------------------------------
# Live environment probes (the `--refresh` data)
# ---------------------------------------------------------------------------
def run(cmd, timeout=30):
    """Run a command, return (rc, stdout, stderr). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:  # pragma: no cover — defensive
        return 1, "", str(e)


_CONNECTED_RE = re.compile(r"connected", re.IGNORECASE)
_NOTCONN_RE = re.compile(r"needs?\s+auth|failed|disconnect|error", re.IGNORECASE)


def probe_mcp():
    """Parse `claude mcp list`. Returns {"servers":[{name,connected}], "ran":bool}.

    Connected iff the line says 'Connected' and NOT 'Needs authentication'/'Failed'. This mirrors
    SKILL.md Step-2 detect (only ✓/✔ Connected counts; ! Needs auth and ✗ Failed are NOT usable).
    The checkmark glyph varies (✓ U+2713 vs ✔ U+2714) across CLI versions, so we key on the word.
    """
    claude_bin = shutil.which("claude")
    cmd = [claude_bin or "claude", "mcp", "list"]
    rc, out, err = run(cmd, timeout=60)
    if rc == 127 or (rc != 0 and not out):
        return {"servers": [], "ran": False, "note": (err or "claude CLI not found").strip()[:120]}
    servers = []
    for line in out.splitlines():
        # lines look like: "claude.ai Gmail: https://... - ✔ Connected"
        if ":" not in line or " - " not in line:
            continue
        name = line.split(":", 1)[0].strip()
        status = line.rsplit(" - ", 1)[-1]
        connected = bool(_CONNECTED_RE.search(status)) and not bool(_NOTCONN_RE.search(status))
        servers.append({"name": name, "connected": connected})
    return {"servers": servers, "ran": True}


def probe_clis():
    """which-probe every CLI we care about. Returns {cmd: path|None}."""
    found = {}
    wanted = {c for c in CLI_COMMANDS.values() if c}
    wanted |= {"codex", "gh", "yt-dlp", "node", "npx", "uvx"}
    for c in sorted(wanted):
        found[c] = shutil.which(c)
    return found


def probe_python_modules():
    """Check importability of lib-class modules in THIS interpreter. Best-effort, fast.

    Uses importlib.util.find_spec — does not execute the module. Only flags 'installed in the
    interpreter running the console', which is a reasonable ops signal (not authoritative for
    every venv, hence a note in `tool` output).
    """
    import importlib.util
    mods = {}
    for slug, mod in PY_IMPORTS.items():
        try:
            mods[slug] = importlib.util.find_spec(mod) is not None
        except Exception:
            mods[slug] = False
    return mods


def find_companion_repo():
    """Discover the companion config repo per SKILL.md convention. Returns path or None."""
    env = os.environ.get("MARKET_INTEL_CONFIG")
    candidates = []
    if env:
        candidates.append(env)
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, ".market-intel-config"))
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    candidates.append(os.path.join(xdg, "market-intel-config"))
    for c in candidates:
        if c and os.path.isdir(c) and os.path.exists(os.path.join(c, "registry.json")):
            return c
    return None


def probe_companion():
    """Read the companion repo registry if present. Returns {"present":bool, "tools":{slug:entry}}.

    Per companion-config-spec §3.1: tools[] entries carry slug/installed/tier/transport. We index
    by slug (and matrix_slug) so the four-state model can answer 'did the user install this + is a
    key present'. Absent companion → present:False, dimension simply skipped (not an error).
    """
    path = find_companion_repo()
    if not path:
        return {"present": False, "path": None, "tools": {}}
    reg = read_json(os.path.join(path, "registry.json"), default={})
    if not isinstance(reg, dict):
        return {"present": True, "path": path, "tools": {}, "note": "registry.json not an object"}
    by_slug = {}
    for t in reg.get("tools", []) or []:
        if not isinstance(t, dict):
            continue
        key = t.get("matrix_slug") or t.get("slug")
        if key:
            by_slug[key] = t
        # also index by raw slug so either matches
        if t.get("slug"):
            by_slug.setdefault(t["slug"], t)
    # does a secret file exist for this slug? (presence only — never read contents)
    # Secrets are named by the CONFIG slug; the matrix carries a different (often -mcp-suffixed)
    # slug. Map config slug -> matrix_slug so a key credits the matrix-side tool too — otherwise
    # an already-keyed tool reads as needs-key purely from a suffix mismatch. Skip _-prefixed
    # account/credential files (not per-tool secrets).
    secrets_dir = os.path.join(path, "secrets")
    have_secret = set()
    slug_to_matrix = {t["slug"]: t.get("matrix_slug") for t in reg.get("tools", []) or []
                      if isinstance(t, dict) and t.get("slug")}
    if os.path.isdir(secrets_dir):
        for fn in os.listdir(secrets_dir):
            if fn.endswith(".env") and not fn.startswith("_"):
                cfg_slug = fn[:-4]
                have_secret.add(cfg_slug)
                ms = slug_to_matrix.get(cfg_slug)
                if ms:
                    have_secret.add(ms)
    return {"present": True, "path": path, "tools": by_slug, "have_secret": sorted(have_secret),
            "schema_version": reg.get("schema_version")}


def build_snapshot():
    """Run all live probes and assemble the snapshot dict written to availability-cache.json."""
    snap = {
        "generated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "?",
        "mcp": probe_mcp(),
        "clis": probe_clis(),
        "py_modules": probe_python_modules(),
        "companion": probe_companion(),
    }
    return snap


def load_snapshot(refresh: bool):
    """Return (snapshot, source) where source is 'fresh-probe' or 'cache' or 'fresh-no-cache'."""
    if refresh:
        snap = build_snapshot()
        write_snapshot(snap)
        return snap, "fresh-probe"
    cached = read_json(AVAIL_CACHE, default=None)
    if cached:
        return cached, "cache"
    # no cache and not asked to refresh → probe live but do not necessarily persist (we do persist,
    # it's harmless and gitignored), so the next call is fast.
    snap = build_snapshot()
    write_snapshot(snap)
    return snap, "fresh-no-cache"


def write_snapshot(snap):
    try:
        os.makedirs(os.path.dirname(AVAIL_CACHE), exist_ok=True)
        with open(AVAIL_CACHE, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2, sort_keys=True)
        ensure_gitignore()
    except Exception as e:
        stderr(f"console: warning — could not write snapshot cache: {e}")


def ensure_gitignore():
    """Make sure metrics/availability-cache.json is gitignored (it's a TTL snapshot, no history)."""
    gi = os.path.join(ROOT, ".gitignore")
    needle = "metrics/availability-cache.json"
    try:
        existing = ""
        if os.path.exists(gi):
            with open(gi, encoding="utf-8") as f:
                existing = f.read()
        if needle in existing:
            return
        with open(gi, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n# Console availability snapshot — TTL probe state, no git history\n")
            f.write(needle + "\n")
    except Exception:
        pass  # best-effort; gate doesn't scan this file regardless


# ---------------------------------------------------------------------------
# Repo health from gh-api-cache.json (verify_matrix's GHACTIVE output)
# ---------------------------------------------------------------------------
def repo_health(gh_cache, repo):
    """Map a gh-api-cache verdict to (state, detail). state ∈ {yes,no,unknown}.

    verify_matrix writes verdicts: PASS (alive, fresh) / WARN (stale but alive) / BLOCK
    (404 or archived) / RATE_LIMITED (transient). PASS|WARN → healthy(yes); BLOCK → no;
    RATE_LIMITED|missing → unknown.
    """
    if not repo:
        return NA, "non-repo source"
    entry = gh_cache.get(repo)
    if not entry:
        return UNK, "no gh-api-cache entry (run verify_matrix to populate)"
    v = entry.get("verdict")
    reason = entry.get("reason", "")
    if v in ("PASS", "WARN"):
        return YES, reason or v
    if v == "BLOCK":
        return NO, reason or "404/archived"
    return UNK, reason or (v or "unknown")


# ---------------------------------------------------------------------------
# THE four-state computation per tool
# ---------------------------------------------------------------------------
def mcp_match(slug, name, mcp_servers):
    """Is there a Connected MCP server matching this tool? Returns (connected, cold, matched_name).

    connected = a matched server is Connected. cold = a server matched by name but NOT connected
    (the 'cold-mcp' signal — it's configured but down/needs-auth). matched_name for display.
    """
    hints = MCP_NAME_HINTS.get(slug, [])
    # always allow the tool's own normalized slug + registry name as implicit hints
    implicit = {normalize(slug), normalize(name)}
    # drop noise tokens from implicit slug match to avoid over-matching ('mcp','api')
    norm_hints = {h for h in (normalize(h) for h in hints) if h} | {h for h in implicit if len(h) >= 4}
    connected = cold = False
    matched = None
    for srv in mcp_servers:
        sn = normalize(srv["name"])
        if not sn:
            continue
        hit = any(h and h in sn for h in norm_hints)
        if hit:
            matched = srv["name"]
            if srv["connected"]:
                connected = True
            else:
                cold = True
    # a connected match wins over a cold one
    return connected, (cold and not connected), matched


def is_mcp_class(tool):
    """A tool is MCP-class if its name/slug/registry says it has a ready MCP. Heuristic but safe:
    used only to choose the *probe path* and the blocked_by label, never to assert availability."""
    blob = normalize(tool["slug"] + " " + tool.get("name", ""))
    return "mcp" in blob or tool["slug"] in MCP_NAME_HINTS


def compute_states(tool, snap, gh_cache):
    """Return a dict with the four states + supporting detail for one registry tool."""
    slug = tool["slug"]
    name = tool.get("name", slug)
    kind = tool.get("kind", "?")
    repo = tool.get("repo")
    domain = tool.get("domain", "?")

    rh_state, rh_detail = repo_health(gh_cache, repo)

    mcp = snap.get("mcp", {})
    mcp_ran = mcp.get("ran")
    servers = mcp.get("servers", [])
    clis = snap.get("clis", {})
    pymods = snap.get("py_modules", {})
    companion = snap.get("companion", {})
    comp_tools = companion.get("tools", {})
    comp_secret = set(companion.get("have_secret", []))

    avail = NO
    blocked = None
    how = []          # human-readable "how it's reachable / why not"

    # ---- MCP path ----
    connected, cold, matched = mcp_match(slug, name, servers)
    if connected:
        avail = YES
        how.append(f"MCP connected: {matched}")
    cli_cmd = CLI_COMMANDS.get(slug)
    cli_found = bool(cli_cmd and clis.get(cli_cmd))
    py_mod_found = bool(pymods.get(slug))

    # ---- CLI / lib path ----
    if avail != YES and cli_found:
        avail = YES
        how.append(f"CLI installed: {cli_cmd} on PATH")
    if avail != YES and py_mod_found:
        avail = YES
        how.append(f"python module importable: {PY_IMPORTS.get(slug)}")

    # ---- skill-backed / keyless web ----
    if avail != YES and slug in SKILL_BACKED:
        avail = YES
        how.append("skill-backed (ships with harness)")
    if avail != YES and slug in KEYLESS_WEB:
        avail = YES
        how.append("keyless web-API (assumed reachable; not pinged)")

    # ---- companion repo says installed (with key present) ----
    comp = comp_tools.get(slug)
    comp_installed = bool(comp and comp.get("installed"))
    comp_has_key = slug in comp_secret
    if avail != YES and comp_installed:
        # companion claims installed. If it's MCP-class we still trust mcp list over companion for
        # 'connected', but companion 'installed' upgrades a CLI/lib/saas to available_now=yes.
        if not is_mcp_class(tool) or comp_has_key:
            avail = YES
            how.append("companion repo: installed" + (" + key present" if comp_has_key else ""))

    # A tool with a concrete local-install path (python lib or CLI) is fundamentally an
    # install-class source even if its registry name happens to mention an MCP wrapper
    # (e.g. twikit = "d60/twikit (+ adhikasp/mcp-twikit)"). Only call it cold-mcp when an
    # actually-configured-but-down MCP server matched it.
    has_install_path = (slug in PY_IMPORTS) or bool(cli_cmd)

    # ---- blocked_by reason (only when not available) ----
    if avail != YES:
        if cold:
            blocked = "cold-mcp"
            how.append(f"MCP configured but not connected: {matched}")
        elif has_install_path:
            blocked = "needs-deploy" if rh_state == NO else "needs-install"
        elif is_mcp_class(tool):
            # MCP-class, not in mcp list at all
            if not mcp_ran:
                blocked = "unknown"
                how.append("could not run `claude mcp list`")
            elif kind == "saas":
                blocked = "needs-key"
            else:
                blocked = "cold-mcp"
        elif kind == "saas":
            blocked = "needs-key"
        elif kind in ("repo", "lib"):
            # self-hostable / installable
            if rh_state == NO:
                blocked = "needs-deploy"   # repo dead → can't even deploy without a fork
            else:
                blocked = "needs-install"
        else:
            blocked = "unknown"
        # companion present but tool not installed there is itself a 'not installed' hint
        if companion.get("present") and comp is None and blocked == "needs-install":
            how.append("not present in companion repo")

    return {
        "slug": slug,
        "name": name,
        "kind": kind,
        "domain": domain,
        "repo": repo,
        "top_pick": tool.get("top_pick", False),
        "cataloged": YES,
        "repo_healthy": rh_state,
        "repo_detail": rh_detail,
        "available_now": avail,
        "blocked_by": blocked,
        "how": how,
        "mcp_class": is_mcp_class(tool),
    }


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_registry():
    reg = read_json(REGISTRY, default=None)
    if not reg or "tools" not in reg:
        stderr(f"console: FATAL — cannot read registry at {REGISTRY}")
        sys.exit(2)
    return reg


def all_states(snap):
    reg = load_registry()
    gh_cache = read_json(GH_CACHE, default={}) or {}
    return [compute_states(t, snap, gh_cache) for t in reg["tools"]], reg


# ---------------------------------------------------------------------------
# Doc path + invocation hint (for `tool`)
# ---------------------------------------------------------------------------
def doc_path_for(slug):
    p = os.path.join(TOOLS_DIR, slug + ".md")
    return p if os.path.exists(p) else None


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------
STATE_FILTER_ALIASES = {
    "available": ("available_now", YES),
    "cold": ("blocked_by", "cold-mcp"),
    "cold-mcp": ("blocked_by", "cold-mcp"),
    "needs-key": ("blocked_by", "needs-key"),
    "needs-install": ("blocked_by", "needs-install"),
    "needs-deploy": ("blocked_by", "needs-deploy"),
    "unknown": ("blocked_by", "unknown"),
}


def cmd_status(args, snap, source):
    states, reg = all_states(snap)

    # filter
    if args.domain:
        states = [s for s in states if s["domain"] == args.domain]
    if args.state:
        key = args.state.lower()
        if key not in STATE_FILTER_ALIASES:
            stderr(f"console: unknown --state '{args.state}'. Options: {', '.join(STATE_FILTER_ALIASES)}")
            sys.exit(2)
        field, val = STATE_FILTER_ALIASES[key]
        states = [s for s in states if s.get(field) == val]

    # group by domain
    by_domain = {}
    for s in states:
        by_domain.setdefault(s["domain"], []).append(s)

    print(f"market-intel CONSOLE · four-state availability  (snapshot: {source}, "
          f"generated {snap.get('generated','?')})")
    mcp = snap.get("mcp", {})
    if not mcp.get("ran"):
        print(f"  ! MCP probe did not run ({mcp.get('note','?')}) — MCP-class tools may show 'unknown'.")
    comp = snap.get("companion", {})
    print(f"  companion-config: {'present @ ' + comp.get('path','') if comp.get('present') else 'absent (dimension skipped)'}")
    print()

    # column widths
    SLUG_W, KIND_W = 30, 5
    header = f"  {'tool':<{SLUG_W}} {'kind':<{KIND_W}} {'repo_ok':<8} {'avail':<6} blocked_by"
    sep = "  " + "-" * (SLUG_W + KIND_W + 8 + 6 + 12)

    total_cat = total_avail = total_cold = 0
    dom_summary = []  # (domain, avail, cat)

    for dom in sorted(by_domain):
        rows = sorted(by_domain[dom], key=lambda r: (r["available_now"] != YES, r["slug"]))
        d_cat = len(rows)
        d_avail = sum(1 for r in rows if r["available_now"] == YES)
        d_cold = sum(1 for r in rows if r["blocked_by"] == "cold-mcp")
        total_cat += d_cat
        total_avail += d_avail
        total_cold += d_cold
        dom_summary.append((dom, d_avail, d_cat))

        print(f"▸ {dom}  ({d_avail}/{d_cat} available)")
        print(header)
        print(sep)
        for r in rows:
            star = "★" if r["top_pick"] else " "
            slug = (star + r["slug"])[:SLUG_W]
            blocked = r["blocked_by"] or ""
            avail_mark = {"yes": "✓", "no": "✗", "?": "?"}.get(r["available_now"], r["available_now"])
            print(f"  {slug:<{SLUG_W}} {r['kind']:<{KIND_W}} {r['repo_healthy']:<8} "
                  f"{avail_mark:<6} {blocked}")
        print()

    # ---- coverage summary ----
    print("=" * 60)
    print("COVERAGE SUMMARY  (available_now / cataloged)")
    print("-" * 60)
    for dom, av, cat in sorted(dom_summary, key=lambda x: (-(x[1] / x[2] if x[2] else 0), x[0])):
        pct = (av / cat * 100) if cat else 0
        bar = "█" * int(pct / 5)
        print(f"  {dom:<24} {av:>3}/{cat:<3} {pct:5.1f}%  {bar}")
    print("-" * 60)
    tot_pct = (total_avail / total_cat * 100) if total_cat else 0
    print(f"  {'TOTAL':<24} {total_avail:>3}/{total_cat:<3} {tot_pct:5.1f}%")
    print(f"  cold-mcp (configured but not connected): {total_cold}")
    reg_count = reg.get("count", total_cat)
    if not args.domain and not args.state and total_cat != reg_count:
        print(f"  (registry declares count={reg_count}; computed over {total_cat} tools)")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: tool <slug>
# ---------------------------------------------------------------------------
def cmd_tool(args, snap, source):
    states, _ = all_states(snap)
    match = [s for s in states if s["slug"] == args.slug]
    if not match:
        # fuzzy suggest
        nz = normalize(args.slug)
        near = [s["slug"] for s in states if nz in normalize(s["slug"])][:8]
        stderr(f"console: no tool with slug '{args.slug}'.")
        if near:
            stderr("  did you mean: " + ", ".join(near))
        sys.exit(2)
    s = match[0]
    print(f"TOOL · {s['slug']}   ({s['name']})")
    print(f"  domain        : {s['domain']}")
    print(f"  kind          : {s['kind']}" + (f"   repo: {s['repo']}" if s['repo'] else ""))
    print(f"  top_pick      : {'yes (★ domain leader)' if s['top_pick'] else 'no'}")
    print()
    print("  FOUR-STATE")
    print(f"    1 cataloged     : yes  (in registry.json)")
    print(f"    2 repo_healthy  : {s['repo_healthy']:<4} ({s['repo_detail']})")
    print(f"    3 available_now : {s['available_now']}")
    print(f"    4 blocked_by    : {s['blocked_by'] or '— (available)'}")
    print()
    if s["how"]:
        print("  SIGNALS")
        for h in s["how"]:
            print(f"    · {h}")
        print()
    # how to call — prefer the concrete local path (CLI/lib) over a generic MCP note, since many
    # lib tools also ship an optional MCP wrapper (twikit, ccxt) and the install path is the actual
    # workhorse. A pure MCP-class tool with no local path falls through to the MCP instructions.
    print("  HOW TO CALL")
    if s["slug"] in CLI_COMMANDS and CLI_COMMANDS[s["slug"]]:
        print(f"    CLI: shell out to `{CLI_COMMANDS[s['slug']]}` (see doc for flags).")
        if s["mcp_class"]:
            print("    (also has an optional MCP wrapper — `claude mcp list` to check if connected.)")
    elif s["slug"] in PY_IMPORTS:
        print(f"    Python lib: `import {PY_IMPORTS[s['slug']]}` (pip install first if missing).")
        if s["mcp_class"]:
            print("    (also has an optional MCP wrapper — `claude mcp list` to check if connected.)")
    elif s["mcp_class"]:
        print("    MCP-class: invoke its mcp__<server>__<tool> functions once Connected.")
        print("    Detect/connect: `claude mcp list` (must show ✓ Connected), then call its tools.")
    elif s["slug"] in KEYLESS_WEB:
        print("    Keyless web-API: HTTP GET, no key (see doc for endpoints).")
    else:
        print("    See the per-tool doc for the exact install + auth + call recipe.")
    doc = doc_path_for(s["slug"])
    print(f"    doc: {os.path.relpath(doc, ROOT) if doc else '(no per-tool doc found)'}")
    print()
    # lighting guidance when cold/unavailable
    if s["available_now"] != YES:
        print("  TO LIGHT IT UP")
        b = s["blocked_by"]
        if b == "cold-mcp":
            print(f"    MCP is configured but not Connected → run `python tools/console.py connect {s['slug']}`")
            print("    for the claude.json template, fill the key, then `/mcp` reconnect / restart.")
        elif b == "needs-key":
            print(f"    Needs an API key → `python tools/console.py connect {s['slug']}` for the template,")
            print("    add your key (never echo it), then reconnect. Pricing: reference/volatile/pricing-install.md.")
        elif b == "needs-install":
            print("    Not installed locally → `pip install` the lib / clone the repo (see doc 'Install').")
        elif b == "needs-deploy":
            print("    Upstream repo is dead/archived (repo_healthy=no) → self-host from a fork or pick the")
            print("    domain's ★ top_pick instead (see the domain shard).")
        else:
            print("    Availability unknown — re-run with `--refresh` (and ensure `claude mcp list` works).")
        print()
    return 0


# ---------------------------------------------------------------------------
# Subcommand: connect <slug>  (PRINT-ONLY template; never writes/echoes secrets)
# ---------------------------------------------------------------------------
def cmd_connect(args, snap, source):
    states, _ = all_states(snap)
    match = [s for s in states if s["slug"] == args.slug]
    if not match:
        stderr(f"console: no tool with slug '{args.slug}'.")
        sys.exit(2)
    s = match[0]
    print(f"CONNECT GUIDE · {s['slug']}  ({s['name']})")
    print("  (this only PRINTS a template — it never writes ~/.claude.json and never handles a key)")
    print()
    if not s["mcp_class"]:
        print("  This tool is not MCP-class — there's nothing to add to mcpServers.")
        if s["slug"] in PY_IMPORTS:
            print(f"  Install path: pip install the python lib (module `{PY_IMPORTS[s['slug']]}`).")
        elif s["slug"] in CLI_COMMANDS and CLI_COMMANDS[s["slug"]]:
            print(f"  Install path: install the CLI `{CLI_COMMANDS[s['slug']]}`.")
        else:
            print("  See its per-tool doc 'Install' section.")
        doc = doc_path_for(s["slug"])
        if doc:
            print(f"  doc: {os.path.relpath(doc, ROOT)}")
        return 0

    server_name = s["slug"]
    print("  1) Add to the `mcpServers` block of ~/.claude.json (HTTP transport preferred on Windows).")
    print("     Replace <ENDPOINT_URL> and the placeholder header with the real values from the")
    print("     provider dashboard. DO NOT paste your key into this terminal or any transcript.")
    print()
    template = {
        "mcpServers": {
            server_name: {
                "type": "http",
                "url": "<ENDPOINT_URL>",
                "headers": {
                    "Authorization": "Bearer <YOUR_API_KEY>"
                }
            }
        }
    }
    print(json.dumps(template, indent=2, ensure_ascii=False))
    print()
    print("  2) Secret hygiene (HARD rules — keys have leaked 3× in real runs):")
    print("     · NEVER browser_snapshot a page showing the key (it's plaintext in the DOM).")
    print("     · Do NOT `claude mcp add` for secret-bearing servers (it echoes the header).")
    print("     · Copy the key via the dashboard's copy button → write it into ~/.claude.json")
    print("       with a no-echo script; verify by length only, never print the value.")
    print("  3) Restart the session or run `/mcp` to reconnect — a freshly added MCP does NOT")
    print("     take effect in the current turn.")
    print("  4) Verify: `claude mcp list` should then show this server as ✓ Connected.")
    print()
    doc = doc_path_for(s["slug"])
    print(f"  Exact endpoint/cost/auth for this tool: "
          f"{os.path.relpath(doc, ROOT) if doc else 'reference/volatile/pricing-install.md'}")
    print("  Where install-state + keys are tracked durably: the companion config repo")
    print("  (reference/companion-config-spec.md). This console never writes there.")
    return 0


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------
def build_parser():
    # --refresh is accepted both before AND after the subcommand (a parent parser carries it onto
    # every subparser), so `console.py --refresh status` and `console.py status --refresh` both work.
    refresh_parent = argparse.ArgumentParser(add_help=False)
    refresh_parent.add_argument(
        "--refresh", action="store_true",
        help="re-probe the environment (claude mcp list + local CLIs + python libs + companion "
             "repo) and rewrite metrics/availability-cache.json before running.")

    p = argparse.ArgumentParser(
        prog="console.py",
        parents=[refresh_parent],
        description="market-intel ops console — four-state (cataloged/repo_healthy/available_now/"
                    "blocked_by) view of the 168-tool source matrix. Read-only + probe-only.")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("status", parents=[refresh_parent],
                        help="four-state table grouped by domain + coverage summary")
    ps.add_argument("--domain", help="restrict to one domain (e.g. finance-markets)")
    ps.add_argument("--state", help="filter: available|cold|needs-key|needs-install|needs-deploy|unknown")

    pt = sub.add_parser("tool", parents=[refresh_parent],
                        help="single-tool detail + how-to-call + light-up guidance")
    pt.add_argument("slug")

    pc = sub.add_parser("connect", parents=[refresh_parent],
                        help="print a claude.json mcpServers template for a cold MCP "
                             "(NEVER writes secrets / never mutates claude.json)")
    pc.add_argument("slug")

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    snap, source = load_snapshot(refresh=args.refresh)

    cmd = args.cmd or "status"
    if cmd == "status":
        # bare `console.py` (no subcommand) defaults to status but lacks its filter attrs
        if not hasattr(args, "domain"):
            args.domain = None
        if not hasattr(args, "state"):
            args.state = None
        return cmd_status(args, snap, source)
    if cmd == "tool":
        return cmd_tool(args, snap, source)
    if cmd == "connect":
        return cmd_connect(args, snap, source)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
