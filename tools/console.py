#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catalog and selected-operation console, used only for maintenance.

status/tool/connect read the public catalog and explicitly supplied session evidence.
They never discover machine inventory. Only --refresh collects inventory, after a
PRIVATE versioned destination has been verified, and persists it atomically.
Catalog health, inventory presence, active session exposure and operation readiness
remain separate signals. No model is needed for these deterministic decisions.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys

if __package__:
    from . import host_capabilities, private_inventory
else:
    import host_capabilities
    import private_inventory

# Force UTF-8 on stdout/stderr: the Windows console defaults to GBK on this machine and chokes on
# the table glyphs (▸ ★ ✓ █). Python 3.7+ exposes .reconfigure; fall back silently if unavailable.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
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
    except (OSError, UnicodeError, ValueError):
        stderr("console: warning — optional JSON input is unreadable or malformed")
        return default


# ---------------------------------------------------------------------------
# Slug ↔ live-signal bridge tables
#
# The registry has no MCP-server-name or CLI-command field, so we bridge here. These are
# OPS-side hints, not part of the skill contract, when a guess is wrong the worst case is a
# tool shows `unknown`/`cold`, never a crash and never a false "available".
# ---------------------------------------------------------------------------

# Registry slugs with known MCP setup routes. This table is install guidance only.
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
    # free-first browser/scrape libs (no key, no cookie), all live import-verified 2026-06-24.
    "nodriver": "nodriver",
    "camoufox": "camoufox",
    # browser-use / scrapegraph-ai: the LIBRARY is keyless-importable; their AI driving needs an
    # LLM key. Listed here for inventory only; the selected operation still needs its own evidence.
    "browser-use": "browser_use",
    "scrapegraph-ai": "scrapegraphai",
    # activation (self-evolve R1): free-first lib routes, each live-verified installed +
    # its keyless capability confirmed (SEC raw endpoint UA-only, yfinance keyless) ,
    # console was under-reporting these as cold though P1 free-first makes them usable.
    "sec-edgar-mcp": "edgar",       # edgartools installed; SEC EDGAR public API keyless (UA only)
    "openbb-mcp": "openbb",         # openbb installed (aggregates ~100 providers incl keyless)
    "yahoo-finance-mcp": "yfinance",  # yfinance installed, fully keyless
}

# Keyless web-APIs: reachable without install OR key OR MCP. We do NOT block on these, mark
# guidance only. No entry is treated as available without current operation evidence.
KEYLESS_WEB = {
    "google-suggest", "stackexchange", "defillama", "geckoterminal",
    "arxiv-sanity-lite", "papers-with-code", "connected-papers-researchrabbit",
    "ai-lab-blogs", "ai-news-roundups", "lmarena", "github-mcp-registry",
    "chatgpt-apps-directory",
    # activation (self-evolve R1): keyless endpoints live-verified HTTP 200 (no key, UA only)
    "coingecko-mcp", "blockscout-mcp", "barker", "mcp-hn",
    # activation R2: GDELT DOC 2.0 is a keyless public API (live-checked: responds without a
    # key, only a 1-req/5s rate-limit notice, no auth).
    "gdelt-mcp",
}

def normalize(s: str) -> str:
    """Lowercase, strip everything but [a-z0-9] — for fuzzy name/slug matching."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ---------------------------------------------------------------------------
# Live environment probes (the `--refresh` data)
# ---------------------------------------------------------------------------
def probe_mcp():
    """Inventory cannot observe the caller's active MCP session from a child CLI."""
    return {"servers": [], "ran": False,
            "note": "active host capabilities are supplied separately by the caller"}


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
        except (ImportError, ValueError, AttributeError):
            mods[slug] = False
    return mods


def find_companion_repo():
    """Use the writer's selected, verified companion without a registry fallback."""
    return str(private_inventory.resolve_destination().repository)


def probe_companion():
    """Read the companion repo registry if present. Returns {"present":bool, "tools":{slug:entry}}.

    Per companion-config-spec §3.1: tools[] entries carry slug/installed/tier/transport. We index
    by slug (and matrix_slug) so the four-state model can answer 'did the user install this + is a
    key present'. Absent companion → present:False, dimension simply skipped (not an error).
    """
    path = find_companion_repo()
    if not path:
        return {"present": False, "path": None, "tools": {}}
    registry_path = os.path.join(path, "registry.json")
    if not os.path.isfile(registry_path):
        return {"present": False, "path": path, "tools": {}, "note": "registry.json missing"}
    reg = read_json(registry_path, default={})
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
    # does a secret file exist for this slug? (presence only, never read contents)
    # Secrets are named by the CONFIG slug; the matrix carries a different (often -mcp-suffixed)
    # slug. Map config slug -> matrix_slug so a key credits the matrix-side tool too, otherwise
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
        "schema_version": 1,
        "generated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "?",
        "mcp": probe_mcp(),
        "clis": probe_clis(),
        "py_modules": probe_python_modules(),
        "companion": probe_companion(),
    }
    return snap


def load_snapshot(refresh: bool):
    """Catalog reads need no DATA. Refresh validates storage before collecting inventory."""
    if not refresh:
        return {}, "catalog-only (inventory not probed)"
    destination = private_inventory.resolve_destination()
    snap = build_snapshot()
    saved = write_snapshot(snap, destination)
    return snap, f"fresh inventory; PRIVATE companion {saved.identity}"


def write_snapshot(snap, destination=None):
    return private_inventory.write_snapshot(snap, destination)


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
        return UNK, "not inspected by the catalog console; run verify_matrix.py for a separate health report"
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
def is_mcp_class(tool):
    """A tool is MCP-class if its name/slug/registry says it has a ready MCP. Heuristic but safe:
    used only to choose the *probe path* and the blocked_by label, never to assert availability."""
    blob = normalize(tool["slug"] + " " + tool.get("name", ""))
    return "mcp" in blob or tool["slug"] in MCP_NAME_HINTS


def compute_states(tool, snap, gh_cache):
    """Catalog health and discovery hints never grant selected-operation readiness."""
    slug = tool["slug"]
    rh_state, rh_detail = repo_health(gh_cache, tool.get("repo"))
    readiness = host_capabilities.classify(
        snap.get("_host_evidence"), tool.get("source_id"),
        snap.get("_selected_capability") or tool.get("capability_id"),
        authentication_required=tool.get("authentication_required"))
    available = readiness["status"] == "available-now"
    return {
        "slug": slug, "name": tool.get("name", slug), "kind": tool.get("kind", "?"),
        "domain": tool.get("domain", "?"), "repo": tool.get("repo"),
        "top_pick": tool.get("top_pick", False), "cataloged": YES,
        "repo_healthy": rh_state, "repo_detail": rh_detail,
        "available_now": YES if available else NO,
        "blocked_by": None if available else readiness["status"],
        "how": [readiness["reason"]], "mcp_class": is_mcp_class(tool),
        "readiness": readiness,
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
    return [compute_states(t, snap, {}) for t in reg["tools"]], reg


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
    "available-now": ("available_now", YES),
    "setup": ("blocked_by", "setup"),
    "hard-gap": ("blocked_by", "hard-gap"),
    "cold": ("blocked_by", "setup"),
    "cold-mcp": ("blocked_by", "setup"),
    "needs-key": ("blocked_by", "setup"),
    "needs-install": ("blocked_by", "setup"),
    "needs-deploy": ("blocked_by", "setup"),
    "unknown": ("blocked_by", "setup"),
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

    print(f"market-intel CONSOLE (source: {source})")
    print(f"  selected capability: {snap.get('_selected_capability', 'read')}")
    print("  Catalog health and machine inventory are not operation readiness.")
    print()

    # column widths
    SLUG_W, KIND_W = 30, 5
    header = f"  {'tool':<{SLUG_W}} {'kind':<{KIND_W}} {'repo_ok':<8} {'avail':<6} blocked_by"
    sep = "  " + "-" * (SLUG_W + KIND_W + 8 + 6 + 12)

    total_cat = total_avail = total_setup = 0
    dom_summary = []  # (domain, avail, cat)

    for dom in sorted(by_domain):
        rows = sorted(by_domain[dom], key=lambda r: (r["available_now"] != YES, r["slug"]))
        d_cat = len(rows)
        d_avail = sum(1 for r in rows if r["available_now"] == YES)
        d_setup = sum(1 for r in rows if r["blocked_by"] == "setup")
        total_cat += d_cat
        total_avail += d_avail
        total_setup += d_setup
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
                  f"{avail_mark:<6} {blocked} | {r['readiness']['reason']}")
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
    print(f"  setup (selected operation not ready): {total_setup}")
    reg_count = reg.get("count", total_cat)
    if not args.domain and not args.state and total_cat != reg_count:
        print(f"  (registry declares count={reg_count}; computed over {total_cat} tools)")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: tool <slug>
# ---------------------------------------------------------------------------
def print_readiness(readiness):
    """Report requested identity and only the observation fields classification proves."""
    for key in ("status", "reason", "access", "operation", "host", "session_id", "source_id",
                "capability_id", "observed_at", "observation_method"):
        if key in readiness:
            print(f"  {key}: {readiness[key]}")


def cmd_tool(args, snap, source):
    states, registry = all_states(snap)
    selected_slug = registry.get("aliases", {}).get(args.slug, args.slug)
    match = [s for s in states if s["slug"] == selected_slug]
    if not match:
        # fuzzy suggest
        nz = normalize(args.slug)
        near_all = [s["slug"] for s in states if nz in normalize(s["slug"])]
        near = near_all[:8]
        stderr(f"console: no tool with slug '{args.slug}'.")
        if near:
            more = f"  (showing {len(near)} of {len(near_all)} matches)" if len(near_all) > len(near) else ""
            stderr("  did you mean: " + ", ".join(near) + more)
        sys.exit(2)
    s = match[0]
    print(f"TOOL · {s['slug']}   ({s['name']})")
    print(f"  source: {source}")
    print(f"  domain        : {s['domain']}")
    print(f"  kind          : {s['kind']}" + (f"   repo: {s['repo']}" if s['repo'] else ""))
    print(f"  top_pick      : {'yes (★ domain leader)' if s['top_pick'] else 'no'}")
    print()
    print(f"  cataloged: yes")
    print(f"  repo_healthy: {s['repo_healthy']} ({s['repo_detail']})")
    readiness = s["readiness"]
    print_readiness(readiness)
    print()
    if s["how"]:
        print("  SIGNALS")
        for h in s["how"]:
            print(f"    · {h}")
        print()
    # how to call, prefer the concrete local path (CLI/lib) over a generic MCP note, since many
    # lib tools also ship an optional MCP wrapper (twikit, ccxt) and the install path is the actual
    # workhorse. A pure MCP-class tool with no local path falls through to the MCP instructions.
    print("  HOW TO CALL")
    if s["slug"] in CLI_COMMANDS and CLI_COMMANDS[s["slug"]]:
        print(f"    CLI: shell out to `{CLI_COMMANDS[s['slug']]}` (see doc for flags).")
        if s["mcp_class"]:
            print("    (also has an MCP wrapper; inspect exposure in the active host session.)")
    elif s["slug"] in PY_IMPORTS:
        print(f"    Python lib: `import {PY_IMPORTS[s['slug']]}` (pip install first if missing).")
        if s["mcp_class"]:
            print("    (also has an MCP wrapper; inspect exposure in the active host session.)")
    elif s["mcp_class"]:
        print("    MCP-class: inspect tools exposed by this active host session.")
        print("    Verify the selected operation, authentication and returned content before using it.")
    elif s["slug"] in KEYLESS_WEB:
        print("    Keyless web-API: HTTP GET, no key (see doc for endpoints).")
    else:
        print("    See the per-tool doc for the exact install + auth + call recipe.")
    doc = doc_path_for(s["slug"])
    print(f"    doc: {os.path.relpath(doc, ROOT) if doc else '(no per-tool doc found)'}")
    print()
    if s["available_now"] != YES:
        print("  NEXT STEP")
        print(f"    {readiness['reason']}")
        print("    Use the active host to verify the selected source operation, then supply")
        print("    fresh session evidence. See reference/host-capabilities.md for the schema.")
        print(f"    Install guidance: python tools/console.py connect {s['slug']}")
        print()
    return 0


# ---------------------------------------------------------------------------
# Subcommand: connect <slug>  (PRINT-ONLY template; never writes/echoes secrets)
# ---------------------------------------------------------------------------
def cmd_connect(args, snap, source):
    states, registry = all_states(snap)
    selected_slug = registry.get("aliases", {}).get(args.slug, args.slug)
    match = [s for s in states if s["slug"] == selected_slug]
    if not match:
        stderr(f"console: no tool with slug '{args.slug}'.")
        sys.exit(2)
    s = match[0]
    print(f"CONNECT GUIDE · {s['slug']}  ({s['name']})")
    print(f"  source: {source}")
    print_readiness(s["readiness"])
    print("  (connect only prints guidance; it never writes host settings or handles a key)")
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
    host = snap.get("_host_evidence", {}).get("host", "")
    if host == "codex":
        print("  Codex: configure this source in Codex MCP settings or activate its installed app.")
        print("  Reconnect Codex, inspect its callable tools, then verify the selected operation.")
        print("  The JSON below is a Claude example; use the equivalent Codex settings fields.")
    else:
        print("  Claude: add the source to the mcpServers block of your Claude settings.")
    print("  1) Use the selected host's supported MCP configuration (HTTP preferred on Windows).")
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
    print("  2) Configure secrets without printing their values:")
    print("     · NEVER browser_snapshot a page showing the key (it's plaintext in the DOM).")
    print("     · Do NOT `claude mcp add` for secret-bearing servers (it echoes the header).")
    print("     · Use the provider's copy button and your selected host's secret configuration")
    print("       with a no-echo script; verify by length only, never print the value.")
    print("  3) Reconnect the selected host when required for the new configuration.")
    print("  4) Verify active-session exposure, execution, authentication and usable content.")
    print()
    doc = doc_path_for(s["slug"])
    print(f"  Exact endpoint/cost/auth for this tool: "
          f"{os.path.relpath(doc, ROOT) if doc else 'reference/volatile/pricing-install.md'}")
    print("  Where install-state + keys are tracked durably: the companion config repo")
    print("  (reference/companion-config-spec.md). Only explicit --refresh writes private inventory.")
    return 0


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------
def build_parser():
    # --refresh is accepted both before AND after the subcommand (a parent parser carries it onto
    # every subparser), so `console.py --refresh status` and `console.py status --refresh` both work.
    refresh_parent = argparse.ArgumentParser(add_help=False)
    refresh_parent.add_argument(
        "--refresh", action="store_true", default=argparse.SUPPRESS,
        help="collect inventory after verifying a PRIVATE versioned companion; persist atomically.")
    refresh_parent.add_argument("--capability", default=argparse.SUPPRESS,
                                help="selected operation for the catalog source_id (default: catalog capability_id)")

    p = argparse.ArgumentParser(
        prog="console.py",
        parents=[refresh_parent],
        description="market-intel catalog console with current-session operation evidence. "
                     "Only explicit --refresh writes PRIVATE inventory.")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("status", parents=[refresh_parent],
                        help="four-state table grouped by domain + coverage summary")
    ps.add_argument("--domain", help="restrict to one domain (e.g. finance-markets)")
    ps.add_argument("--state", help="filter: available-now|setup|hard-gap (legacy aliases accepted)")

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

    try:
        snap, source = load_snapshot(refresh=getattr(args, "refresh", False))
    except private_inventory.InventoryError as exc:
        stderr(f"console: inventory refresh failed: {exc}")
        return 2
    except OSError:
        stderr("console: inventory refresh failed: input or destination is inaccessible")
        return 2
    snap["_host_evidence"] = host_capabilities.load_environment()
    snap["_selected_capability"] = getattr(args, "capability", None)

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
