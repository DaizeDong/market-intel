#!/usr/bin/env python3
"""L0 deterministic verify — pre-check layer of the reduced verify pipeline.

The 3-lens LLM verify is being collapsed to 1 lens + this deterministic L0 pre-check.
L0 catches what BigGo (13.5mo stale URL) slipped through. If L0 says BLOCK, no LLM
runs. If L0 says PASS, the LLM lens is the only remaining gate. If UNCERTAIN, the LLM
lens takes over.

Verdict rules per type:
  github       gh api repos/<o>/<r>: 404 / archived / pushed_at >12mo -> BLOCK
  web          HTTP HEAD/GET + DNS + cert: 404 -> BLOCK; anti-bot 403 with DNS+cert
               healthy + Last-Modified within 12mo -> PASS; else UNCERTAIN
  web-registry like web, but anti-bot 403 with healthy DNS+cert -> PASS
               (github.com/mcp, chatgpt.com/apps, lmarena.ai/leaderboard ARE the registry)
  npm          registry.npmjs.org/<pkg>: time.modified within 12mo, not deprecated
  pypi         pypi.org/pypi/<pkg>/json: has releases, latest release within 12mo

Cache: github checks share metrics/gh-api-cache.json (verify_matrix.py schema; L0
re-verdicts on read because verify_matrix WARNs >12mo stale, L0 BLOCKs it).
HTTP/npm/pypi use metrics/l0-cache.json (7-day TTL, keyed by URL/pkg).

CLI: python tools/l0_verify.py --url <url> [--type <type>]
     exit 0 if PASS, 1 if BLOCK, 2 if UNCERTAIN.
Run with --selftest (or no args) for the canonical fixtures.
"""
from __future__ import annotations
import argparse, datetime, io, json, os, re, socket, ssl, subprocess, sys
from urllib.parse import urlparse

import requests

# BOM-safe Windows stdout — matches verify_matrix.py / discover.py convention
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_CACHE_PATH = os.path.join(ROOT, "metrics", "gh-api-cache.json")
L0_CACHE_PATH = os.path.join(ROOT, "metrics", "l0-cache.json")
CACHE_TTL_DAYS = 7
STALE_MONTHS = 12
HTTP_TIMEOUT = 10
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36 market-intel-l0/1.0")

_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
_now_iso = _now.isoformat()


# ---------------- cache + probes ----------------

def _load_cache(path: str) -> dict:
    if not os.path.exists(path): return {}
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _save_cache(path: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception: pass

def _cache_fresh(entry: dict) -> bool:
    try:
        ts = datetime.datetime.fromisoformat(entry["checked_at"])
        return (_now - ts).days <= CACHE_TTL_DAYS
    except Exception: return False

def _dns_resolves(host: str) -> bool:
    try: socket.gethostbyname(host); return True
    except OSError: return False

def _cert_check(host: str, port: int = 443) -> dict:
    """Return {ok, expires:'YYYY-MM-DD'|None, reason}."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=HTTP_TIMEOUT) as s, \
             ctx.wrap_socket(s, server_hostname=host) as ss:
            cert = ss.getpeercert()
        not_after = (cert or {}).get("notAfter")
        if not not_after:
            return {"ok": False, "expires": None, "reason": "no notAfter in cert"}
        exp = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        ok = exp > _now
        return {"ok": ok, "expires": exp.strftime("%Y-%m-%d"),
                "reason": "valid" if ok else f"expired {exp.date()}"}
    except (ssl.SSLError, ssl.CertificateError) as e:
        return {"ok": False, "expires": None, "reason": f"ssl: {e}"}
    except (socket.timeout, OSError) as e:
        return {"ok": False, "expires": None, "reason": f"connect: {e}"}

def _parse_last_modified(v: str | None) -> datetime.datetime | None:
    if not v: return None
    for fmt in ("%a, %d %b %Y %H:%M:%S GMT", "%a, %d %b %Y %H:%M:%S %Z"):
        try: return datetime.datetime.strptime(v, fmt)
        except ValueError: continue
    return None

def _months_old(iso10: str) -> float:
    try:
        return (_now - datetime.datetime.strptime(iso10[:10], "%Y-%m-%d")).days / 30.44
    except Exception:
        return 0.0

def _result(entry: dict) -> dict:
    v = entry["verdict"]
    if v in ("RATE_LIMITED", "WARN"): v = "UNCERTAIN"  # legacy verify_matrix verdicts
    return {"verdict": v, "evidence": entry.get("reason", ""), "details": entry}

TRANSIENT_REASONS = ("timeout", "transient HTTP", "unreachable", "indeterminate",
                     "no response", "no freshness signal")

def _is_transient(entry: dict) -> bool:
    reason = (entry.get("reason") or "").lower()
    return (entry.get("verdict") == "UNCERTAIN"
            and any(t in reason for t in TRANSIENT_REASONS))

def _cached_or(path: str, key: str, fn) -> dict:
    """Return cached fresh entry as a result, else run fn() -> entry, persist, return.
    Transient UNCERTAINs (timeout / 5xx / unreachable) are NOT cached — a flake on
    one run shouldn't poison the cache for the next 7 days. Run fn up to twice on
    transient outcomes; the second attempt closes the typical TLS-handshake flake."""
    cache = _load_cache(path)
    entry = cache.get(key)
    if entry and _cache_fresh(entry) and entry.get("verdict") not in ("RATE_LIMITED",):
        if not _is_transient(entry):
            return _result(entry)
    entry = fn()
    if _is_transient(entry):
        retry = fn()
        if not _is_transient(retry):
            entry = retry
    if not _is_transient(entry):
        cache[key] = entry
        _save_cache(path, cache)
    return _result(entry)


# ---------------- github (gh api) ----------------

def _reverdict_github(entry: dict) -> dict:
    """Recompute verdict from pushed_at/archived per L0's stricter rules.
    verify_matrix.py records >12mo stale as WARN; L0 must surface BLOCK."""
    if entry.get("verdict") == "BLOCK": return entry
    if entry.get("archived"):
        return {**entry, "verdict": "BLOCK", "reason": "archived upstream"}
    pa = entry.get("pushed_at")
    if not pa: return entry
    mo = _months_old(pa)
    if mo > STALE_MONTHS:
        return {**entry, "verdict": "BLOCK",
                "reason": f"stale: pushed_at={pa[:10]} (~{int(mo)}mo)"}
    return {**entry, "verdict": "PASS",
            "reason": f"pushed_at {pa[:10]} within {STALE_MONTHS}mo"}

def _check_github(url: str) -> dict:
    m = re.match(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", url)
    if not m:
        return {"verdict": "UNCERTAIN",
                "evidence": "URL is not github.com/<owner>/<repo>",
                "details": {"url": url}}
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"): repo = repo[:-4]
    slug = f"{owner}/{repo}"

    cache = _load_cache(GH_CACHE_PATH)
    cached = cache.get(slug)
    if cached and _cache_fresh(cached) and cached.get("verdict") != "RATE_LIMITED":
        return _result(_reverdict_github(cached))

    res = subprocess.run(
        ["gh", "api", f"repos/{slug}", "--jq", "{pushed_at:.pushed_at,archived:.archived}"],
        capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        err = res.stderr or ""
        if "Not Found" in err or "404" in err:
            entry = {"repo": slug, "pushed_at": None, "archived": None,
                     "verdict": "BLOCK", "reason": "404 not found"}
        elif "rate limit" in err.lower() or "API rate" in err:
            entry = {"repo": slug, "pushed_at": None, "archived": None,
                     "verdict": "RATE_LIMITED", "reason": "gh api rate-limited"}
        else:
            entry = {"repo": slug, "pushed_at": None, "archived": None,
                     "verdict": "RATE_LIMITED",
                     "reason": f"gh error: {err.strip()[:60]}"}
    else:
        try:
            d = json.loads(res.stdout)
            entry = _reverdict_github({"repo": slug,
                                       "pushed_at": d.get("pushed_at"),
                                       "archived": bool(d.get("archived")),
                                       "verdict": "PASS", "reason": ""})
        except Exception:
            entry = {"repo": slug, "pushed_at": None, "archived": None,
                     "verdict": "RATE_LIMITED", "reason": "unparseable gh response"}
    entry["checked_at"] = _now_iso
    cache[slug] = entry
    _save_cache(GH_CACHE_PATH, cache)
    return _result(entry)


# ---------------- web (HTTP + DNS + cert) ----------------

def _check_web(url: str, registry: bool = False) -> dict:
    key = f"{'reg' if registry else 'web'}:{url}"

    def probe() -> dict:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if not host:
            return {"url": url, "verdict": "BLOCK", "reason": "unparseable URL",
                    "checked_at": _now_iso}
        headers = {"User-Agent": UA,
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        status = last_modified = error = None
        final_url = url
        try:
            r = requests.head(url, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
            status = r.status_code
            last_modified = r.headers.get("Last-Modified")
            final_url = r.url
            if status in (403, 405, 501):  # retry with GET — some servers misreport HEAD
                try:
                    r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT,
                                     allow_redirects=True, stream=True)
                    status = r.status_code
                    last_modified = r.headers.get("Last-Modified") or last_modified
                    final_url = r.url
                    r.close()
                except requests.exceptions.RequestException:
                    pass
        except requests.exceptions.Timeout:
            error = "timeout"
        except requests.exceptions.SSLError as e:
            error = f"ssl error: {e}"
        except requests.exceptions.ConnectionError as e:
            error = f"connection error: {str(e)[:80]}"
        except requests.exceptions.RequestException as e:
            error = f"request error: {str(e)[:80]}"

        dns_ok = _dns_resolves(host)
        cert = (_cert_check(host) if parsed.scheme == "https" and dns_ok
                else {"ok": False, "expires": None, "reason": "skipped"})

        if status is not None and 200 <= status < 300:
            verdict, reason = "PASS", f"HTTP {status}"
        elif status in (301, 302, 307, 308):
            verdict, reason = "UNCERTAIN", f"redirect chain unresolved ({status})"
        elif status == 404:
            verdict, reason = "BLOCK", "HTTP 404"
        elif status in (401, 403):
            lm_dt = _parse_last_modified(last_modified)
            lm_ok = lm_dt and (_now - lm_dt).days <= STALE_MONTHS * 30
            if registry and dns_ok and cert["ok"]:
                verdict, reason = "PASS", f"registry anti-bot {status} but DNS+cert healthy"
            elif dns_ok and cert["ok"] and lm_ok:
                verdict, reason = "PASS", (f"anti-bot {status} but DNS+cert healthy and "
                                           f"Last-Modified {lm_dt.date()} within {STALE_MONTHS}mo")
            elif dns_ok and cert["ok"]:
                # Plain web anti-bot with no freshness signal -> UNCERTAIN, not BLOCK
                # (avoids false-rejecting live SaaS like Publora / ChatGPT Apps that
                # serve modern SPAs without Last-Modified). registry mode upgrades to PASS.
                verdict, reason = "UNCERTAIN", f"anti-bot {status}, DNS+cert healthy but no freshness signal"
            elif not dns_ok:
                verdict, reason = "BLOCK", f"anti-bot {status} and DNS unresolvable"
            elif not cert["ok"]:
                verdict, reason = "BLOCK", f"anti-bot {status} and cert: {cert['reason']}"
            else:
                verdict, reason = "UNCERTAIN", f"anti-bot {status}, indeterminate"
        elif status in (500, 502, 503, 504):
            verdict, reason = "UNCERTAIN", f"transient HTTP {status}"
        elif status is not None:
            verdict, reason = "UNCERTAIN", f"HTTP {status}"
        elif error == "timeout":
            verdict, reason = "UNCERTAIN", "timeout"
        elif not dns_ok:
            verdict, reason = "BLOCK", "DNS unresolvable"
        elif parsed.scheme == "https" and not cert["ok"]:
            verdict, reason = "BLOCK", f"cert problem: {cert['reason']}"
        else:
            verdict, reason = "UNCERTAIN", error or "no response"

        return {"url": url, "verdict": verdict, "reason": reason, "status": status,
                "final_url": final_url, "dns_ok": dns_ok, "cert_ok": cert["ok"],
                "cert_expires": cert.get("expires"), "last_modified": last_modified,
                "registry_mode": registry, "checked_at": _now_iso}

    return _cached_or(L0_CACHE_PATH, key, probe)


# ---------------- npm / pypi ----------------

def _check_npm(pkg: str) -> dict:
    def probe() -> dict:
        try:
            r = requests.get(f"https://registry.npmjs.org/{pkg}",
                             headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return {"pkg": pkg, "verdict": "UNCERTAIN",
                    "reason": f"npm registry unreachable: {str(e)[:60]}",
                    "checked_at": _now_iso}
        if r.status_code == 404:
            return {"pkg": pkg, "verdict": "BLOCK", "reason": "npm 404", "checked_at": _now_iso}
        if r.status_code != 200:
            return {"pkg": pkg, "verdict": "UNCERTAIN",
                    "reason": f"npm HTTP {r.status_code}", "checked_at": _now_iso}
        try: d = r.json()
        except Exception:
            return {"pkg": pkg, "verdict": "UNCERTAIN", "reason": "npm unparseable",
                    "checked_at": _now_iso}
        modified = (d.get("time") or {}).get("modified")
        if d.get("deprecated"):
            return {"pkg": pkg, "verdict": "BLOCK",
                    "reason": f"deprecated: {str(d['deprecated'])[:60]}",
                    "modified": modified, "checked_at": _now_iso}
        if not modified:
            return {"pkg": pkg, "verdict": "UNCERTAIN", "reason": "no time.modified",
                    "checked_at": _now_iso}
        mo = _months_old(modified)
        if mo > STALE_MONTHS:
            return {"pkg": pkg, "verdict": "BLOCK",
                    "reason": f"stale: time.modified={modified[:10]} (~{int(mo)}mo)",
                    "modified": modified, "checked_at": _now_iso}
        return {"pkg": pkg, "verdict": "PASS",
                "reason": f"time.modified {modified[:10]} within {STALE_MONTHS}mo",
                "modified": modified, "checked_at": _now_iso}
    return _cached_or(L0_CACHE_PATH, f"npm:{pkg}", probe)

def _check_pypi(pkg: str) -> dict:
    def probe() -> dict:
        try:
            r = requests.get(f"https://pypi.org/pypi/{pkg}/json",
                             headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return {"pkg": pkg, "verdict": "UNCERTAIN",
                    "reason": f"pypi unreachable: {str(e)[:60]}", "checked_at": _now_iso}
        if r.status_code == 404:
            return {"pkg": pkg, "verdict": "BLOCK", "reason": "pypi 404", "checked_at": _now_iso}
        if r.status_code != 200:
            return {"pkg": pkg, "verdict": "UNCERTAIN",
                    "reason": f"pypi HTTP {r.status_code}", "checked_at": _now_iso}
        try: d = r.json()
        except Exception:
            return {"pkg": pkg, "verdict": "UNCERTAIN", "reason": "pypi unparseable",
                    "checked_at": _now_iso}
        info = d.get("info") or {}
        releases = d.get("releases") or {}
        if not releases:
            return {"pkg": pkg, "verdict": "BLOCK", "reason": "no releases",
                    "checked_at": _now_iso}
        latest = None
        for files in releases.values():
            for f in files or []:
                ut = f.get("upload_time")
                if not ut: continue
                try:
                    dt = datetime.datetime.strptime(ut[:10], "%Y-%m-%d")
                    if latest is None or dt > latest: latest = dt
                except Exception: pass
        if latest is None:
            return {"pkg": pkg, "verdict": "UNCERTAIN",
                    "reason": "releases present but no upload_time", "checked_at": _now_iso}
        mo = (_now - latest).days / 30.44
        if mo > STALE_MONTHS:
            return {"pkg": pkg, "verdict": "BLOCK",
                    "reason": f"stale: latest release {latest.date()} (~{int(mo)}mo)",
                    "checked_at": _now_iso}
        note = "" if info.get("requires_python") else " (no requires_python)"
        return {"pkg": pkg, "verdict": "PASS",
                "reason": f"latest release {latest.date()} within {STALE_MONTHS}mo{note}",
                "checked_at": _now_iso}
    return _cached_or(L0_CACHE_PATH, f"pypi:{pkg}", probe)


# ---------------- dispatcher ----------------

def _npm_pkg_from_url(url: str) -> str | None:
    m = re.match(r"https?://(?:www\.)?npmjs\.com/package/([^?#]+)", url)
    if m: return m.group(1).rstrip("/")
    m = re.match(r"https?://registry\.npmjs\.org/([^?#]+)", url)
    return m.group(1).rstrip("/") if m else None

def _pypi_pkg_from_url(url: str) -> str | None:
    m = re.match(r"https?://pypi\.org/(?:project|pypi)/([^/?#]+)", url)
    return m.group(1) if m else None

def _infer_type(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host in ("github.com", "www.github.com"): return "github"
    if host in ("www.npmjs.com", "npmjs.com", "registry.npmjs.org"): return "npm-page"
    if host in ("pypi.org", "www.pypi.org"): return "pypi-page"
    return "web"

def verify(url: str, candidate_type: str = "auto") -> dict:
    """Return {verdict:'PASS'|'BLOCK'|'UNCERTAIN', evidence:str, details:dict}."""
    if candidate_type == "auto":
        t = _infer_type(url)
        if t == "npm-page":
            pkg = _npm_pkg_from_url(url)
            return _check_npm(pkg) if pkg else _check_web(url)
        if t == "pypi-page":
            pkg = _pypi_pkg_from_url(url)
            return _check_pypi(pkg) if pkg else _check_web(url)
        candidate_type = t

    if candidate_type == "github":       return _check_github(url)
    if candidate_type == "web":          return _check_web(url, registry=False)
    if candidate_type == "web-registry": return _check_web(url, registry=True)
    if candidate_type == "npm":
        return _check_npm(_npm_pkg_from_url(url) or url)
    if candidate_type == "pypi":
        return _check_pypi(_pypi_pkg_from_url(url) or url)
    return {"verdict": "UNCERTAIN",
            "evidence": f"unknown candidate_type {candidate_type!r}",
            "details": {"url": url, "type": candidate_type}}


# ---------------- self-test ----------------

SELF_TESTS = [
    ("https://github.com/ArthurHeitmann/arctic_shift",  "github",       "PASS"),
    ("https://github.com/karpathy/arxiv-sanity-lite",   "github",       "BLOCK"),
    ("https://publora.com",                             "web",          "PASS"),
    ("https://chatgpt.com/apps",                        "web-registry", "PASS"),
    ("https://outscraper.com",                          "web",          "PASS"),
    ("https://this-domain-does-not-exist-fake12345.com","web",          "BLOCK"),
    ("https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem", "npm", "PASS"),
]

def _selftest() -> int:
    rows, passed = [], 0
    for url, ctype, expected in SELF_TESTS:
        try:
            r = verify(url, ctype); got = r["verdict"]
        except Exception as e:
            got, r = "ERROR", {"evidence": str(e)[:80], "details": {}}
        ok = (got == expected)
        passed += int(ok)
        rows.append((ok, url, ctype, expected, got, r.get("evidence", "")[:60]))
    print(f"\n{'OK':<5} {'TYPE':<13} {'EXP':<9} {'GOT':<9} URL")
    print("-" * 110)
    for ok, url, ctype, exp, got, _ in rows:
        print(f"{('ok' if ok else 'FAIL'):<5} {ctype:<13} {exp:<9} {got:<9} {url}")
    total = len(SELF_TESTS)
    print(f"\nmodule ready: {passed}/{total} self-tests passed")
    if passed < total:
        print("FAILED:")
        for ok, url, _, exp, got, ev in rows:
            if not ok: print(f"  - {url} (expected {exp}, got {got}; {ev})")
    return 0 if passed == total else 1


# ---------------- CLI ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description="L0 deterministic verify for market-intel")
    ap.add_argument("--url", help="URL or package name to verify")
    ap.add_argument("--type", default="auto",
                    choices=["auto", "github", "web", "web-registry", "npm", "pypi"])
    ap.add_argument("--selftest", action="store_true",
                    help="run canonical self-tests instead of a single URL")
    args = ap.parse_args()

    if args.selftest or not args.url:
        return _selftest()
    result = verify(args.url, args.type)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    v = result["verdict"]
    return 0 if v == "PASS" else (1 if v == "BLOCK" else 2)

if __name__ == "__main__":
    sys.exit(main())
