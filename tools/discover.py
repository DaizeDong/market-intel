#!/usr/bin/env python3
"""Weekly discovery sweep — poll the 6 high-signal "E-class" surfaces from
`skills/market-intel/reference/refresh-protocol.md` §D1.E, dedupe, and append
candidates to the skill's `discovery-state.md` inbox.

The 6 surfaces (per refresh-protocol D1.E):
  E1  PulseMCP newsletter RSS               (https://www.pulsemcp.com/feed.xml)
  E2  GitHub Search velocity API            (new repos >=50 star, <90d old, mcp/skill/agent topics)
  E3  HF Spaces trending JSON               (https://huggingface.co/api/spaces?sort=trendingScore)
  E4  npm download velocity API             (last-week vs last-month for tracked pkgs)
  E5  Show HN scan via Algolia              (search_by_date?tags=show_hn&query=mcp/agent/scraper)
  E6  AI YouTube channel RSS                (4 channels: Matthew Berman, AI Explained, Cole Medin,
                                             AI Coffee Break)

Output: each candidate is a dict
  {discovered_at, surface, name, url, signal, one_line_pitch}
that gets appended to `## Inbox` under `### YYYY-MM-DD sweep`, deduped by URL.

When to run:
  - Weekly during hot-sweep cadence (refresh-protocol §Cadence). E-class polling is
    decoupled from the monthly Verify & Diff phase; monthly sweep consumes the inbox.
  - One-shot ad-hoc when investigating a domain that flipped to `hot`.

Exit codes:
  0   ran cleanly (some channels may have warned + skipped — that's fine)
  1   all six channels failed (network down / proxy block / etc.)
  2   bad args (e.g. unknown --channel)

Deps: stdlib + `requests` (already installed; pinned in market-intel env). No new deps.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Callable

import requests

# ─── stdout UTF-8 safety (Windows) ────────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ─── paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _companion_root():
    """Where this skill's private companion is, via tools/datadir.py. None when there is none."""
    p = os.path.join(ROOT, "tools", "datadir.py")
    if not os.path.isfile(p):
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("_dd_for_discover", p)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "resolve_companion_root", None)
    return str(fn("market-intel")) if fn and fn("market-intel") else None


def _default_out():
    """Where a discovery sweep writes its state. The companion, not this repo.

    This defaulted to skills/market-intel/reference/discovery-state.md: a TRACKED file, inside the
    public repo, with no gitignore entry and no class declared for it in .dataclass.json. Every
    sweep appended what the operator was researching, on the public side of the boundary, and the
    only reason it never tripped the guard is that check 4 recognises shapes and this one wears the
    shape of a document.

    Falls back to the repo path ONLY when no companion resolves, and that fallback is exactly what
    check 4 is there to catch, so an uninitialized machine produces a violation rather than a quiet
    write. Better to be caught than to be silent.
    """
    root = _companion_root()
    if root:
        return os.path.join(root, "data", "discovery-state.md")
    return os.path.join(ROOT, "skills", "market-intel", "reference", "discovery-state.md")


DEFAULT_OUT = _default_out()

# ─── config: what to track ────────────────────────────────────────────────────
# E2: GitHub topics scanned for "new + already stary" repos.
# Add a topic here if a new MCP/skill convention emerges (e.g. `agent-skill`).
GITHUB_TOPICS = ["mcp-server", "claude-skill", "llm-agent"]
GITHUB_STARS_MIN = 50

# E4: npm packages we want to track for download-velocity surges.
# Curated for MCP / agent infra. Add a row when a new candidate first surfaces.
NPM_PACKAGES = [
    "@modelcontextprotocol/sdk",
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-github",
    "@modelcontextprotocol/server-puppeteer",
    "fastmcp",
    "mcp-framework",
    "@anthropic-ai/sdk",
    "ai",
    "@vercel/mcp-adapter",
]
NPM_WOW_RATIO_MIN = 2.0   # weekly DL >= 2x last-month average
NPM_WEEKLY_MIN = 500       # absolute floor on weekly downloads

# E6: YouTube channel IDs (UCID, "UC..." 24-char). Filling these requires reading
# each channel's About page or yt-dlp probing, not done from memory. Leave as
# TODO placeholders until the user (or a follow-up agent) verifies them.
YOUTUBE_CHANNELS = [
    # (handle, UCID)
    ("Matthew Berman", "TODO_UCID_MATTHEW_BERMAN"),   # TODO: fill in
    ("AI Explained",   "TODO_UCID_AI_EXPLAINED"),     # TODO: fill in
    ("Cole Medin",     "TODO_UCID_COLE_MEDIN"),       # TODO: fill in
    ("AI Coffee Break", "TODO_UCID_AI_COFFEE_BREAK"), # TODO: fill in
]

# E1: PulseMCP RSS, URL not curl-verified per refresh-protocol footnote.
# If feed.xml 404s, we fall back to scraping the homepage for an <link rel="alternate">.
PULSEMCP_FEED = "https://www.pulsemcp.com/feed.xml"
PULSEMCP_HOME = "https://www.pulsemcp.com/"

# E3: HF Spaces trending JSON.
HF_SPACES_URL = "https://huggingface.co/api/spaces?sort=trendingScore&limit=50"

# E5: Show HN via Algolia HN API.
HN_API = "https://hn.algolia.com/api/v1/search_by_date"
HN_QUERY = "mcp OR agent OR scraper"

UA = "market-intel-discover/0.1 (+https://github.com/DaizeDong/market-intel)"
HTTP_TIMEOUT = 20


# ═══════════════ channel functions ════════════════════════════════════════════
# Uniform return shape per refresh-protocol D1.E:
#   {discovered_at, surface, name, url, signal, one_line_pitch}
# discovered_at is YYYY-MM-DD UTC.

def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def channel_e1_pulsemcp(since: dt.date) -> list[dict]:
    """E1 — PulseMCP newsletter RSS.

    API shape (RSS 2.0): <rss><channel><item><title/><link/><pubDate/><description/></item>...
    or Atom: <feed><entry><title/><link href=.../><published/><summary/></entry>...
    Extraction: title -> name, link -> url, description (first sentence) -> one_line_pitch.
    Signal: 'newsletter:<pubDate>' (any item past `since` is high-signal — already curated).
    """
    headers = {"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"}
    r = requests.get(PULSEMCP_FEED, headers=headers, timeout=HTTP_TIMEOUT)
    if r.status_code != 200 or not r.text.strip().startswith("<"):
        # fallback: scrape homepage for <link rel="alternate" type="application/rss+xml">
        h = requests.get(PULSEMCP_HOME, headers=headers, timeout=HTTP_TIMEOUT)
        m = re.search(
            r'<link[^>]+rel=["\']alternate["\'][^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']',
            h.text, re.I)
        if not m:
            raise RuntimeError(f"E1: feed {PULSEMCP_FEED} returned {r.status_code} and homepage exposed no alternate feed link")
        feed_url = urllib.parse.urljoin(PULSEMCP_HOME, m.group(1))
        r = requests.get(feed_url, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()

    root = ET.fromstring(r.text)
    # Strip namespaces for simpler XPath
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]

    items = root.findall(".//item") or root.findall(".//entry")
    out: list[dict] = []
    for it in items:
        title = (it.findtext("title") or "").strip()
        link_el = it.find("link")
        if link_el is not None and link_el.text and link_el.text.strip():
            link = link_el.text.strip()
        elif link_el is not None and link_el.get("href"):
            link = link_el.get("href").strip()
        else:
            link = ""
        pub = (it.findtext("pubDate") or it.findtext("published") or it.findtext("updated") or "").strip()
        desc = (it.findtext("description") or it.findtext("summary") or "").strip()
        desc_clean = re.sub(r"<[^>]+>", " ", desc)
        pitch = re.split(r"(?<=[\.\!\?])\s", desc_clean, maxsplit=1)[0][:200].strip()

        # filter by `since`
        pub_date = _parse_any_date(pub)
        if pub_date and pub_date < since:
            continue

        if not title or not link:
            continue
        out.append({
            "discovered_at": _today(),
            "surface": "E1",
            "name": title,
            "url": link,
            "signal": f"newsletter:{pub}" if pub else "newsletter",
            "one_line_pitch": pitch or "(no description)",
        })
    return out


def channel_e2_github(since: dt.date) -> list[dict]:
    """E2 — GitHub Search velocity API.

    Endpoint: https://api.github.com/search/repositories?q=created:>YYYY-MM-DD+stars:>N+topic:T
    Response: {items: [{full_name, html_url, stargazers_count, created_at, description, ...}]}
    Extraction per item: full_name -> name, html_url -> url,
      signal = f"stars:{n} age:{days}d topic:{topic}", description -> pitch.
    Unauth rate limit is 10 req/min — we use 3 topics × 1 req each, well under.
    """
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    out: list[dict] = []
    since_str = since.strftime("%Y-%m-%d")
    for topic in GITHUB_TOPICS:
        q = f"created:>{since_str} stars:>{GITHUB_STARS_MIN} topic:{topic}"
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=30"
        r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            raise RuntimeError(f"E2 topic={topic}: {r.status_code} {r.text[:200]}")
        for it in r.json().get("items", []):
            created = it.get("created_at", "")[:10]
            try:
                age_days = (dt.date.today() - dt.date.fromisoformat(created)).days if created else None
            except ValueError:
                age_days = None
            stars = it.get("stargazers_count", 0)
            signal = f"stars:{stars} age:{age_days}d topic:{topic}" if age_days is not None else f"stars:{stars} topic:{topic}"
            out.append({
                "discovered_at": _today(),
                "surface": "E2",
                "name": it.get("full_name", "?"),
                "url": it.get("html_url", ""),
                "signal": signal,
                "one_line_pitch": (it.get("description") or "(no description)")[:200],
            })
    return out


def channel_e3_hf_spaces(since: dt.date) -> list[dict]:
    """E3 — Hugging Face Spaces trending JSON.

    Endpoint: https://huggingface.co/api/spaces?sort=trendingScore&limit=50
    Response: list of {id, author, sdk, likes, trendingScore, lastModified, cardData{...}, ...}
    Extraction per space: id -> name, https://huggingface.co/spaces/<id> -> url,
      signal = f"trendingScore:{x} likes:{y}",
      pitch = cardData.short_description or cardData.title or id.
    No auth required. `since` filters by lastModified; trending Spaces are recent by definition.
    """
    headers = {"User-Agent": UA, "Accept": "application/json"}
    r = requests.get(HF_SPACES_URL, headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    out: list[dict] = []
    for sp in r.json():
        space_id = sp.get("id", "")
        if not space_id:
            continue
        last_mod = sp.get("lastModified", "")[:10]
        try:
            if last_mod and dt.date.fromisoformat(last_mod) < since:
                continue
        except ValueError:
            pass
        score = sp.get("trendingScore")
        likes = sp.get("likes", 0)
        signal = f"trendingScore:{score} likes:{likes}"
        card = sp.get("cardData") or {}
        pitch = card.get("short_description") or card.get("title") or space_id
        out.append({
            "discovered_at": _today(),
            "surface": "E3",
            "name": space_id,
            "url": f"https://huggingface.co/spaces/{space_id}",
            "signal": signal,
            "one_line_pitch": str(pitch)[:200],
        })
    return out


def channel_e4_npm(since: dt.date) -> list[dict]:
    """E4 — npm download velocity.

    Endpoints:
      https://api.npmjs.org/downloads/range/last-week/<pkg>
      https://api.npmjs.org/downloads/range/last-month/<pkg>
    Response: {start, end, package, downloads:[{day, downloads}, ...]}
    Calc: weekly = sum(last-week.downloads); monthly_avg_weekly = sum(last-month) * 7/30.
    Emit only when weekly >= NPM_WEEKLY_MIN AND weekly / monthly_avg_weekly >= NPM_WOW_RATIO_MIN.
    Signal: f"weekly:{w} WoW:{r:.1f}x".
    `since` is unused (npm endpoint is a fixed last-week window) but kept for signature uniformity.
    """
    del since  # signature uniformity
    headers = {"User-Agent": UA, "Accept": "application/json"}

    def _one(pkg):
        # Two independent npm HTTP calls per package -> pure IO. Returns (record_or_None, log_or_None);
        # the caller emits both SERIALLY in NPM_PACKAGES order so output stays deterministic.
        enc = urllib.parse.quote(pkg, safe="@/")
        wk = requests.get(f"https://api.npmjs.org/downloads/range/last-week/{enc}",
                          headers=headers, timeout=HTTP_TIMEOUT)
        mo = requests.get(f"https://api.npmjs.org/downloads/range/last-month/{enc}",
                          headers=headers, timeout=HTTP_TIMEOUT)
        if wk.status_code != 200 or mo.status_code != 200:
            # Single-pkg miss is not fatal, log and continue.
            return None, f"  [E4] {pkg}: skipped (week={wk.status_code} month={mo.status_code})"
        wk_total = sum(d.get("downloads", 0) for d in wk.json().get("downloads", []))
        mo_total = sum(d.get("downloads", 0) for d in mo.json().get("downloads", []))
        mo_weekly_avg = (mo_total * 7 / 30) if mo_total else 0
        ratio = (wk_total / mo_weekly_avg) if mo_weekly_avg else float("inf") if wk_total else 0
        if wk_total < NPM_WEEKLY_MIN or ratio < NPM_WOW_RATIO_MIN:
            return None, None
        return {
            "discovered_at": _today(),
            "surface": "E4",
            "name": pkg,
            "url": f"https://www.npmjs.com/package/{pkg}",
            "signal": f"weekly:{wk_total} WoW:{ratio:.1f}x",
            "one_line_pitch": f"npm download velocity surge ({wk_total}/wk, {ratio:.1f}x last-month avg)",
        }, None

    # Each package is independent IO; fetch them in parallel. pool.map preserves input order, so the
    # serial emit below yields byte-for-byte the same output (and stderr log lines) as the old loop.
    pkgs = list(NPM_PACKAGES)
    workers = max(1, min(8, len(pkgs)))
    if workers <= 1:
        results = [_one(p) for p in pkgs]
    else:
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_one, pkgs))

    out: list[dict] = []
    for rec, log in results:
        if log:
            print(log, file=sys.stderr)
        if rec is not None:
            out.append(rec)
    return out


def channel_e5_show_hn(since: dt.date) -> list[dict]:
    """E5 — Show HN scan via Algolia HN API.

    Endpoint: https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&query=...&numericFilters=...
    Response: {hits: [{objectID, title, url, points, num_comments, created_at, ...}]}
    Extraction per hit: title -> name, url (or hn item) -> url,
      signal = f"points:{p} comments:{c}",
      pitch = title (Show HN titles are already a pitch).
    Filter: created_at >= since AND (points >= 30 OR num_comments >= 10).
    """
    headers = {"User-Agent": UA, "Accept": "application/json"}
    since_ts = int(dt.datetime(since.year, since.month, since.day,
                               tzinfo=dt.timezone.utc).timestamp())
    params = {
        "tags": "show_hn",
        "query": HN_QUERY,
        "numericFilters": f"created_at_i>{since_ts}",
        "hitsPerPage": 100,
    }
    r = requests.get(HN_API, params=params, headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    out: list[dict] = []
    for h in r.json().get("hits", []):
        points = h.get("points") or 0
        comments = h.get("num_comments") or 0
        if points < 30 and comments < 10:
            continue
        title = (h.get("title") or "").strip()
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        if not title:
            continue
        out.append({
            "discovered_at": _today(),
            "surface": "E5",
            "name": title,
            "url": url,
            "signal": f"points:{points} comments:{comments}",
            "one_line_pitch": title[:200],
        })
    return out


def channel_e6_youtube(since: dt.date) -> list[dict]:
    """E6 — AI YouTube channel RSS feeds.

    Endpoint per channel: https://www.youtube.com/feeds/videos.xml?channel_id=<UCID>
    Response: Atom feed; <entry><title/><link href=.../><published/><media:description/></entry>
    Extraction per entry: title -> name, link -> url, published (filter by since),
      signal = f"channel:{handle} published:{date}",
      pitch = first sentence of media:description.
    Skips channels whose UCID is still a TODO placeholder.
    """
    headers = {"User-Agent": UA, "Accept": "application/atom+xml, application/xml, */*"}
    out: list[dict] = []
    skipped_todo = []
    for handle, ucid in YOUTUBE_CHANNELS:
        if ucid.startswith("TODO"):
            skipped_todo.append(handle)
            continue
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ucid}"
        r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            print(f"  [E6] {handle} ({ucid}): {r.status_code}", file=sys.stderr)
            continue
        root = ET.fromstring(r.text)
        for el in root.iter():
            if "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]
        for entry in root.findall(".//entry"):
            title = (entry.findtext("title") or "").strip()
            link_el = entry.find("link")
            link = link_el.get("href") if link_el is not None else ""
            published = (entry.findtext("published") or "").strip()
            pub_date = _parse_any_date(published)
            if pub_date and pub_date < since:
                continue
            desc = (entry.findtext("description") or "").strip()
            pitch = re.split(r"(?<=[\.\!\?])\s", desc, maxsplit=1)[0][:200].strip() or title[:200]
            if not title or not link:
                continue
            out.append({
                "discovered_at": _today(),
                "surface": "E6",
                "name": f"{handle}: {title}",
                "url": link,
                "signal": f"channel:{handle} published:{published[:10]}",
                "one_line_pitch": pitch,
            })
    if skipped_todo:
        print(f"  [E6] skipped (UCID TODO): {', '.join(skipped_todo)}", file=sys.stderr)
    return out


# ═══════════════ helpers ══════════════════════════════════════════════════════

CHANNELS: dict[str, Callable[[dt.date], list[dict]]] = {
    "e1": channel_e1_pulsemcp,
    "e2": channel_e2_github,
    "e3": channel_e3_hf_spaces,
    "e4": channel_e4_npm,
    "e5": channel_e5_show_hn,
    "e6": channel_e6_youtube,
}


def _parse_any_date(s: str) -> dt.date | None:
    """Best-effort parse of RSS pubDate / ISO8601 / Atom published into a date.
    Returns None if unparseable.
    """
    if not s:
        return None
    s = s.strip()
    # ISO 8601
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass
    # RFC 822-ish, e.g. "Tue, 03 Jun 2026 12:34:56 +0000"
    for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z",
                "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def _dedupe_by_url(candidates: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for c in candidates:
        u = c.get("url", "")
        if u and u in seen:
            continue
        seen.add(u)
        out.append(c)
    return out


def _render_inbox_block(date_str: str, by_channel: dict[str, list[dict]]) -> str:
    lines = [f"### {date_str} sweep", ""]
    for ch in ("E1", "E2", "E3", "E4", "E5", "E6"):
        rows = by_channel.get(ch, [])
        if not rows:
            continue
        lines.append(f"**{ch}** ({len(rows)})")
        for c in rows:
            # one-line format matching the existing inbox style:
            # [YYYY-MM-DD] @source: <pitch> <url>  + signal in parens
            lines.append(
                f"- [{c['discovered_at']}] @{c['surface']} **{c['name']}** — "
                f"{c['one_line_pitch']} ({c['signal']}) {c['url']}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _append_to_inbox(out_path: str, block: str) -> None:
    """Insert the block immediately under `## Inbox` in the target file.
    Preserves the rest of the file. UTF-8 with no BOM rewrite.
    """
    with open(out_path, encoding="utf-8") as f:
        body = f.read()
    marker = "## Inbox"
    idx = body.find(marker)
    if idx < 0:
        # No inbox section yet, append one at end.
        new = body.rstrip() + f"\n\n## Inbox\n\n{block}\n"
    else:
        # Find end of the inbox heading line + intro paragraph: insert after the
        # first blank line that follows the marker.
        head_end = body.find("\n", idx)
        # find the first occurrence of the next H3 or H2 after marker
        # to keep prior sweeps intact, we just insert right after the heading.
        insert_at = head_end + 1
        new = body[:insert_at] + "\n" + block + "\n" + body[insert_at:]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new)


# ═══════════════ main ═════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", default=None,
                    help="YYYY-MM-DD; only emit candidates dated >= this (default: 30 days ago)")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help=f"path to discovery-state.md (default: {DEFAULT_OUT})")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the block that would be appended, don't write")
    ap.add_argument("--channel", default=None,
                    help="run only one channel: e1|e2|e3|e4|e5|e6")
    args = ap.parse_args(argv)

    if args.since:
        since = dt.date.fromisoformat(args.since)
    else:
        since = dt.date.today() - dt.timedelta(days=30)

    selected = list(CHANNELS.items())
    if args.channel:
        key = args.channel.lower()
        if key not in CHANNELS:
            print(f"unknown --channel {args.channel}; valid: {list(CHANNELS)}", file=sys.stderr)
            return 2
        selected = [(key, CHANNELS[key])]

    results: dict[str, list[dict]] = {}
    failures: dict[str, str] = {}

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn, since): name for name, fn in selected}
        for fut in cf.as_completed(futures):
            name = futures[fut]
            try:
                results[name.upper()] = fut.result()
            except Exception as e:
                failures[name.upper()] = f"{type(e).__name__}: {e}"
                print(f"  WARN [{name.upper()}] {type(e).__name__}: {e}", file=sys.stderr)

    # dedupe across channels by URL
    all_cands = [c for rows in results.values() for c in rows]
    deduped = _dedupe_by_url(all_cands)
    # regroup
    by_channel: dict[str, list[dict]] = {ch: [] for ch in results}
    for c in deduped:
        by_channel.setdefault(c["surface"], []).append(c)

    # summary
    print("=" * 60)
    print(f"Discovery sweep — since {since.isoformat()}, out={args.out}")
    print("=" * 60)
    for ch in ("E1", "E2", "E3", "E4", "E5", "E6"):
        if ch in failures:
            print(f"  {ch}: FAIL — {failures[ch]}")
        elif ch in by_channel:
            print(f"  {ch}: {len(by_channel[ch])} candidates")
    total = sum(len(v) for v in by_channel.values())
    print(f"  total (deduped): {total}")
    print(f"  failures: {len(failures)}/{len(selected)}")

    if not by_channel or total == 0:
        if failures and len(failures) == len(selected):
            return 1
        # nothing to write but no hard fail
        return 0

    block = _render_inbox_block(_today(), by_channel)

    if args.dry_run:
        print("\n----- DRY RUN — would append: -----\n")
        print(block)
        return 0

    _append_to_inbox(args.out, block)
    print(f"\nAppended {total} candidates to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
