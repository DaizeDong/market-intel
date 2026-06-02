#!/usr/bin/env python3
"""Stage B sensor — emit a deterministic quality snapshot per refresh into metrics/history.jsonl.

Pure stdlib, no network, no LLM (P4: measured, not self-reported). Run after each refresh. The
time series feeds check_drift.py to catch SLOW degradation that any single run looks fine for.

Usage: python tools/emit_metrics.py [--period YYYY-MM]   (run from repo root)
"""
import json, os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "skills", "market-intel", "reference")
DOMAINS = os.path.join(REF, "domains")
PRICING = os.path.join(REF, "volatile", "pricing-install.md")
HIST = os.path.join(ROOT, "metrics", "history.jsonl")

period = "unknown"
if "--period" in sys.argv:
    period = sys.argv[sys.argv.index("--period") + 1]

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def count_rows(text):
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|") and "---" not in s and not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I):
            n += 1
    return n

def git_sha():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "?"

pricing = read(PRICING) if os.path.exists(PRICING) else ""
per_domain, total = {}, 0
free_tokens_g = paid_tokens_g = 0
for f in sorted(os.listdir(DOMAINS)):
    if not f.endswith(".md"):
        continue
    d = f[:-3]
    txt = read(os.path.join(DOMAINS, f))
    rows = count_rows(txt)
    total += rows
    # route mix: count ③④ (free/browser) vs ①② (official/resale) occurrences in the shard body
    free = txt.count("③") + txt.count("④")
    paid = txt.count("①") + txt.count("②")
    free_tokens_g += free
    paid_tokens_g += paid
    # last_verified for this domain's pricing section (if present)
    m = re.search(rf"##\s*{re.escape(d)}.*?last_verified:\s*(\d{{4}}-\d{{2}})", pricing, re.S)
    per_domain[d] = {
        "sources": rows,
        "free_route_tokens": free,
        "paid_route_tokens": paid,
        "last_verified": m.group(1) if m else None,
    }

snapshot = {
    "period": period,
    "git_sha": git_sha(),
    "global": {
        "domains": len(per_domain),
        "total_sources": total,
        "free_route_share": round(free_tokens_g / max(free_tokens_g + paid_tokens_g, 1), 3),
    },
    "per_domain": per_domain,
}

os.makedirs(os.path.dirname(HIST), exist_ok=True)
with open(HIST, "a", encoding="utf-8") as f:
    f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
print(f"emitted metrics for {period}: {len(per_domain)} domains, {total} sources, "
      f"free_route_share={snapshot['global']['free_route_share']}")
