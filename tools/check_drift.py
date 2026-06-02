#!/usr/bin/env python3
"""Stage B feedback — read metrics/history.jsonl and flag SLOW degradation via cross-period operators.

The point: a single snapshot always looks fine; rot shows up only as a trend. So we compare the
latest period against history (monotonic-worsening detection + long-horizon delta + stagnation).
Prints alerts (for the Discord digest); exit 0 always (advisory, never blocks — blocking is the
gate's job, P3 single-period; this is the slow-rot sensor).

Usage: python tools/check_drift.py   (run from repo root)
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "metrics", "history.jsonl")

if not os.path.exists(HIST):
    print("no history yet — drift check skipped"); sys.exit(0)
rows = [json.loads(l) for l in open(HIST, encoding="utf-8") if l.strip()]
if len(rows) < 2:
    print(f"only {len(rows)} snapshot(s) — need >=2 for drift; skipped"); sys.exit(0)

cur, prev = rows[-1], rows[-2]
alerts = []

# global free-route share: long-horizon erosion (C2 spirit — free/④ being replaced by paid)
base = rows[max(0, len(rows) - 7)]
d_share = cur["global"]["free_route_share"] - base["global"]["free_route_share"]
if d_share < -0.10:
    alerts.append(f"⚠ free/④ route share dropped {base['global']['free_route_share']}→"
                  f"{cur['global']['free_route_share']} over {len(rows)-1} periods (paid creeping in)")

# per-domain: source-count crash + stagnation
for d, m in cur.get("per_domain", {}).items():
    pm = prev.get("per_domain", {}).get(d)
    if pm and pm["sources"] and (pm["sources"] - m["sources"]) / pm["sources"] > 0.30:
        alerts.append(f"⚠ {d}: sources {pm['sources']}→{m['sources']} (>30% drop)")
    # stagnation: same source count for >=3 consecutive snapshots
    last3 = [r.get("per_domain", {}).get(d, {}).get("sources") for r in rows[-3:]]
    if len(last3) == 3 and len(set(last3)) == 1 and last3[0] is not None:
        alerts.append(f"• {d}: sources unchanged for 3 periods — verify it's stable, not stagnant")

# monotonic worsening of any domain's source count over last >=4 periods
if len(rows) >= 4:
    for d in cur.get("per_domain", {}):
        seq = [r.get("per_domain", {}).get(d, {}).get("sources") for r in rows[-4:]]
        if all(s is not None for s in seq) and all(seq[i] > seq[i+1] for i in range(3)):
            alerts.append(f"⚠ {d}: source count monotonically declining {seq} — slow rot")

if alerts:
    print("DRIFT ALERTS:")
    for a in alerts: print(" ", a)
else:
    print("drift: healthy — no slow-degradation signals")
sys.exit(0)
