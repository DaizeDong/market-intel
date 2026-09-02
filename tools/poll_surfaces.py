#!/usr/bin/env python3
"""poll_surfaces.py — weekly high-signal surface poller (E1-E6 of refresh-protocol.md).

Deterministic, LLM-free, zero-ops. Each surface is a single HTTP/RSS call (E2 uses `gh api`).
It pulls the six auto-pollable high-signal surfaces, applies each surface's inclusion threshold,
and appends surviving candidates to a LOCAL inbox that the monthly full sweep consumes.

Why this exists: the monthly headless-claude sweep is heavy and can time out mid-discovery. This
poller does the cheap, high-S/N discovery continuously so the monthly sweep starts from a
pre-populated inbox (less discovery burden -> less likely to time out) and nothing hot is missed
between monthly runs.

DATA BOUNDARY (Skill Repo Spec s9): this file is TOOL (public code). Its OUTPUT is a record of what
surfaced during a real run -> it is written to the PRIVATE data home, never into the public repo.
  inbox default: <tools/datadir.py resolution>/surface-inbox.jsonl
                 ($MARKET_INTEL_DATA_DIR -> $MARKET_INTEL_CONFIG/data -> ~/.market-intel-config/data)
  print it with: python tools/datadir.py --path market-intel surface-inbox.jsonl
Reads may degrade (a surface down -> warn + continue); the inbox WRITE hard-fails (never a repo
fallback). One candidate per JSONL line: {surface, key, title, url, signal, discovered_at, raw}.

Usage:
  python tools/poll_surfaces.py                 # poll all, append new candidates to the inbox
  python tools/poll_surfaces.py --dry-run       # poll all, print summary, write nothing
  python tools/poll_surfaces.py --since-days 7  # E2 GitHub velocity lookback window (default 7)
  python tools/poll_surfaces.py --only E2,E5    # run a subset of surfaces

Exit codes: 0 = run completed (individual surfaces may have degraded, reported in the summary);
            2 = catastrophic (could not write the inbox). Never silently drops a real observation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

UA = "market-intel-surface-poller/1.0 (+https://github.com/DaizeDong/market-intel)"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "surfaces.json")
SKILL = "market-intel"

sys.path.insert(0, HERE)
# datadir moved into the guards submodule: one copy for the fleet instead of one per repo,
# which had already begun to drift. The insert above stays, because sibling modules in this
# same tools/ directory are still imported by bare name.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "guards", "tools"))
from datadir import resolve_data_dir  # noqa: E402


# ----------------------------------------------------------------------------- helpers
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _http_get(url: str, timeout: int = 20, accept: str = "*/*") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _http_json(url: str, timeout: int = 20):
    return json.loads(_http_get(url, timeout=timeout, accept="application/json").decode("utf-8", "replace"))


def _gh_json(path: str):
    """`gh api <path>` -> parsed JSON. Raises on failure (caller wraps per-surface)."""
    exe = os.environ.get("GH_BIN", "gh")
    out = subprocess.run([exe, "api", path], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api failed: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def _load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _data_home() -> str:
    """The private data home, resolved by tools/datadir.py -- the ONE resolver, not a copy of it.

    This used to re-implement the discovery order in four lines, and the copy went stale: it knew
    only $MARKET_INTEL_DATA_DIR and the ~/.market-intel-config/data dotfile, so once the companion
    repo was pinned elsewhere with $MARKET_INTEL_CONFIG this writer kept appending to a directory
    nothing else read any more. A second ledger that nobody consumes is indistinguishable from
    losing the observation, which is exactly what the write-side hard-fail rule exists to prevent.
    """
    return str(resolve_data_dir(SKILL, create=True))


# ----------------------------------------------------------------------------- surfaces
def surface_E1_pulsemcp(cfg: dict) -> list[dict]:
    """PulseMCP directory API — notable MCP servers (keyless JSON). Replaces the Cloudflare-walled RSS.

    The old newsletter feed.xml is 403/404 to non-browser UAs (Cloudflare). PulseMCP does expose a
    keyless directory API (v0beta/servers) — but it is picky: plain tool UAs get rate-limited/410, a
    BROWSER UA works. The directory has no 'created' field, so 'what's new' comes from dedup against
    the inbox over weeks; a traction filter (github stars OR package downloads) keeps it to notable
    servers, not every directory row.
    """
    e1 = cfg.get("E1", {})
    api = e1.get("api_url", "https://api.pulsemcp.com/v0beta/servers")
    cpp = int(e1.get("count_per_page", 100))
    min_stars = int(e1.get("min_stars", 50))
    min_dl = int(e1.get("min_downloads", 1000))
    ua = e1.get("user_agent", "Mozilla/5.0 (market-intel surface poller)")
    req = urllib.request.Request(f"{api}?count_per_page={cpp}",
                                 headers={"User-Agent": ua, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    out = []
    for s in data.get("servers", []):
        stars = s.get("github_stars") or 0
        dl = s.get("package_download_count") or 0
        if stars < min_stars and dl < min_dl:  # traction filter: notable, not every row
            continue
        name = s.get("name") or s.get("url") or ""
        if not name:
            continue
        out.append({"surface": "E1", "key": f"E1:{name}", "title": name,
                    "url": s.get("external_url") or s.get("url") or "",
                    "signal": f"{stars}star/{dl}dl",
                    "raw": {"stars": stars, "downloads": dl, "pkg": s.get("package_name"),
                            "desc": (s.get("short_description") or "")[:200]}})
    return out


def surface_E2_github_velocity(cfg: dict, since_days: int) -> list[dict]:
    """GitHub Search velocity — repos <since_days old with >=min_stars in the target topics."""
    e2 = cfg.get("E2", {})
    topics = e2.get("topics", ["mcp-server", "claude-skill", "llm-agent"])
    min_stars = int(e2.get("min_stars", 50))
    since = (_now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
    seen, out = set(), []
    for topic in topics:
        q = f"created:>{since}+stars:>{min_stars}+topic:{topic}"
        data = _gh_json(f"search/repositories?q={q}&sort=stars&order=desc&per_page=30")
        for it in data.get("items", []):
            full = it.get("full_name")
            if not full or full in seen:
                continue
            seen.add(full)
            out.append({"surface": "E2", "key": f"E2:{full}", "title": full,
                        "url": it.get("html_url", ""), "signal": f"{it.get('stargazers_count')}star/{topic}",
                        "raw": {"stars": it.get("stargazers_count"), "created_at": it.get("created_at"),
                                "topic": topic, "desc": (it.get("description") or "")[:200]}})
    return out


def surface_E3_hf_spaces(cfg: dict) -> list[dict]:
    """HuggingFace Spaces trending — often catches new agent/tool demos before GitHub trending."""
    e3 = cfg.get("E3", {})
    limit = int(e3.get("limit", 50))
    min_score = float(e3.get("min_trending_score", 0))  # 0 = keep all top-N, calibrate after 2 rounds
    data = _http_json(f"https://huggingface.co/api/spaces?sort=trendingScore&limit={limit}")
    out = []
    for sp in data if isinstance(data, list) else []:
        score = sp.get("trendingScore", 0) or 0
        if score < min_score:
            continue
        sid = sp.get("id", "")
        out.append({"surface": "E3", "key": f"E3:{sid}", "title": sid,
                    "url": f"https://huggingface.co/spaces/{sid}", "signal": f"trend={score}",
                    "raw": {"trendingScore": score, "author": sp.get("author"),
                            "tags": (sp.get("tags") or [])[:8]}})
    return out


def surface_E4_npm_velocity(cfg: dict) -> list[dict]:
    """npm download velocity — WoW growth on a watchlist of candidate packages (verification surface).

    Downloads = real installs, far harder to fake than stars. This is a VERIFY surface, not a broad
    discovery one: it checks a configured watchlist. Empty watchlist -> nothing to poll (not an error).
    """
    e4 = cfg.get("E4", {})
    watch = e4.get("watchlist", [])
    min_weekly = int(e4.get("min_weekly", 500))
    min_wow = float(e4.get("min_wow", 2.0))
    out = []
    for pkg in watch:
        try:
            wk = _http_json(f"https://api.npmjs.org/downloads/point/last-week/{pkg}").get("downloads", 0)
            pm = _http_json(f"https://api.npmjs.org/downloads/point/last-month/{pkg}").get("downloads", 0)
        except Exception:
            continue
        prev3wk_avg = max((pm - wk) / 3.0, 1e-9)
        wow = wk / prev3wk_avg
        if wk >= min_weekly and wow >= min_wow:
            out.append({"surface": "E4", "key": f"E4:{pkg}", "title": pkg,
                        "url": f"https://www.npmjs.com/package/{pkg}", "signal": f"{wk}/wk WoW~{wow:.1f}x",
                        "raw": {"weekly": wk, "monthly": pm, "wow": round(wow, 2)}})
    return out


def surface_E5_show_hn(cfg: dict) -> list[dict]:
    """Show HN scan (Algolia) — tool-first launches, HN comments de-hype. points>=min or real thread."""
    e5 = cfg.get("E5", {})
    query = e5.get("query", "mcp OR agent OR scraper OR skill")
    min_points = int(e5.get("min_points", 30))
    min_comments = int(e5.get("min_comments", 10))
    url = ("https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=40"
           f"&query={urllib.request.quote(query)}")
    data = _http_json(url)
    out = []
    for h in data.get("hits", []):
        pts = h.get("points") or 0
        ncomment = h.get("num_comments") or 0
        if pts < min_points and ncomment < min_comments:
            continue
        oid = h.get("objectID")
        out.append({"surface": "E5", "key": f"E5:{oid}", "title": (h.get("title") or "").strip(),
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                    "signal": f"{pts}pts/{ncomment}c",
                    "raw": {"points": pts, "num_comments": ncomment, "hn": f"https://news.ycombinator.com/item?id={oid}"}})
    return out


def _resolve_ucid(handle: str) -> str | None:
    """Best-effort UCID resolution from a @handle page. Multiple markers; None if it can't be found."""
    for suffix in ("", "/about"):
        try:
            html = _http_get(f"https://www.youtube.com/@{handle}{suffix}&hl=en", timeout=15).decode("utf-8", "replace")
        except Exception:
            try:
                html = _http_get(f"https://www.youtube.com/@{handle}{suffix}?hl=en", timeout=15).decode("utf-8", "replace")
            except Exception:
                continue
        for marker in ('"channelId":"', '"externalId":', 'itemprop="identifier" content="', 'channel/'):
            i = html.find(marker)
            if i == -1:
                continue
            frag = html[i + len(marker): i + len(marker) + 40]
            j = frag.find("UC")
            if j != -1 and len(frag) >= j + 24:
                cand = frag[j:j + 24]
                if cand.startswith("UC") and all(c.isalnum() or c in "_-" for c in cand):
                    return cand
    return None


def surface_E6_youtube(cfg: dict, since_days: int) -> list[dict]:
    """AI early-demo YouTube channels — fastest 'someone actually tried it' signal (per-channel RSS).

    Channels come from config as {name, handle, ucid}. Missing ucid -> resolve once and warn if it
    can't (graceful degrade: the run continues, that channel is skipped, config can be filled later).
    """
    chans = cfg.get("E6", {}).get("channels", [])
    since = _now() - timedelta(days=max(since_days, 7))
    out, warnings = [], []
    for ch in chans:
        ucid = ch.get("ucid") or (_resolve_ucid(ch["handle"]) if ch.get("handle") else None)
        if not ucid:
            warnings.append(ch.get("name") or ch.get("handle") or "?")
            continue
        try:
            raw = _http_get(f"https://www.youtube.com/feeds/videos.xml?channel_id={ucid}",
                            accept="application/atom+xml")
        except Exception:
            warnings.append((ch.get("name") or ucid) + "(feed)")
            continue
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(raw)
        for entry in root.findall("a:entry", ns):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            pub = entry.findtext("a:published", default="", namespaces=ns)
            try:
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except Exception:
                pub_dt = None
            if pub_dt and pub_dt < since:
                continue
            out.append({"surface": "E6", "key": f"E6:{link}", "title": title, "url": link,
                        "signal": f"video/{ch.get('name','?')}",
                        "raw": {"channel": ch.get("name"), "published_at": pub}})
    if warnings:
        out.append({"surface": "E6", "key": "E6:_warn", "title": f"UCID unresolved: {', '.join(warnings)}",
                    "url": "", "signal": "degraded", "raw": {"unresolved": warnings}})
    return out


SURFACES = {
    "E1": lambda cfg, sd: surface_E1_pulsemcp(cfg),
    "E2": lambda cfg, sd: surface_E2_github_velocity(cfg, sd),
    "E3": lambda cfg, sd: surface_E3_hf_spaces(cfg),
    "E4": lambda cfg, sd: surface_E4_npm_velocity(cfg),
    "E5": lambda cfg, sd: surface_E5_show_hn(cfg),
    "E6": lambda cfg, sd: surface_E6_youtube(cfg, sd),
}


# ----------------------------------------------------------------------------- run
def main() -> int:
    ap = argparse.ArgumentParser(description="Weekly E1-E6 high-signal surface poller.")
    ap.add_argument("--inbox", default=None, help="inbox JSONL path (default: private data home)")
    ap.add_argument("--config", default=CONFIG_PATH)
    ap.add_argument("--since-days", type=int, default=7)
    ap.add_argument("--only", default=None, help="comma list e.g. E2,E5")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = {}
    if os.path.exists(args.config):
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)

    inbox = args.inbox or os.path.join(_data_home(), "surface-inbox.jsonl")
    seen_keys = set()
    if not args.dry_run and os.path.exists(inbox):
        with open(inbox, encoding="utf-8") as f:
            for line in f:
                try:
                    seen_keys.add(json.loads(line).get("key"))
                except Exception:
                    pass

    which = [s.strip() for s in (args.only.split(",") if args.only else SURFACES.keys())]
    stamp = _now().isoformat()
    all_new, summary = [], []

    # Each surface is a single independent HTTP/gh call -> pure IO, and per-surface isolation already
    # means one failing surface never sinks the poll. Fetch all surfaces in PARALLEL, then do the
    # order-sensitive post-processing (cross-surface seen_keys dedup, all_new order, summary order)
    # SERIALLY in `which` order below -> byte-for-byte the same result as the old serial loop, just
    # with the round-trips overlapped. raw[name] holds either the candidate list or the exception.
    raw: dict = {}
    _pollable = [n for n in which if SURFACES.get(n)]
    _workers = max(1, min(6, len(_pollable)))
    if _workers <= 1:
        for name in _pollable:
            try:
                raw[name] = SURFACES[name](cfg, args.since_days)
            except Exception as e:  # captured, re-surfaced in `which` order below
                raw[name] = e
    else:
        import concurrent.futures as _cf
        with _cf.ThreadPoolExecutor(max_workers=_workers) as _ex:
            _fut = {_ex.submit(SURFACES[n], cfg, args.since_days): n for n in _pollable}
            for _f in _cf.as_completed(_fut):
                n = _fut[_f]
                try:
                    raw[n] = _f.result()
                except Exception as e:
                    raw[n] = e

    for name in which:
        fn = SURFACES.get(name)
        if not fn:
            summary.append((name, "ERR", "unknown surface"))
            continue
        r = raw.get(name)
        if isinstance(r, Exception):  # per-surface isolation: one down != whole poll down
            summary.append((name, "DEGRADED", str(r)[:120]))
            continue
        cands = r
        fresh = [c for c in cands if c["key"] not in seen_keys]
        for c in fresh:
            c["discovered_at"] = stamp
            seen_keys.add(c["key"])
        all_new.extend(fresh)
        summary.append((name, "OK", f"{len(fresh)} new / {len(cands)} seen"))

    # write (hard-fail on write error; never a repo fallback)
    if not args.dry_run and all_new:
        try:
            os.makedirs(os.path.dirname(inbox), exist_ok=True)
            with open(inbox, "a", encoding="utf-8") as f:
                for c in all_new:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"FATAL: cannot write inbox {inbox}: {e}", file=sys.stderr)
            return 2

    # summary (stdout, machine-greppable last line for the wrapper)
    print(f"# market-intel surface poll @ {stamp}  (inbox: {inbox})")
    for name, status, detail in summary:
        print(f"  {name:3} {status:9} {detail}")
    degraded = [n for n, s, _ in summary if s != "OK"]
    print(f"SUMMARY new={len(all_new)} surfaces_ok={sum(1 for _,s,_ in summary if s=='OK')}/{len(summary)}"
          f" degraded={','.join(degraded) if degraded else 'none'} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
