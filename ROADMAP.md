# Roadmap

## v0.1.0 (alpha) — current

- Thin orchestration layer: triage → detect (`claude mcp list`) → guide install → delegate.
- 12-domain source matrix (thin index + per-domain shards + isolated volatile pricing/install).
- 8 quality guardrails (citation verification, ≥2-source corroboration, tiers, no silent
  degradation, dated volatile data, disconfirmation mandate, conflict surfacing, explicit gaps).
- Refresh protocol for keeping the matrix current.

## Done (v0.3.0) — self-evolution / anti-regression core

- [x] **Scheduled auto-refresh** — Windows Task `RefreshMarketIntel`, monthly, branch + gate + PR.
- [x] **Constitution** (`CONSTITUTION.md`, C1–C10) injected as hard constraints each run.
- [x] **Deterministic gate** (`tools/verify_matrix.py`) — API-verified repo existence + star
      tolerance + structure + freshness + methodology + anti-mass-deletion + constitution lock.
- [x] **Branch + PR isolation** — bad updates never reach main; Discord notify on pass/fail.

## Next — deferred pieces of the 5-subagent design

- [ ] **Machine-readable mirror block** per shard (YAML of {repo, stars, route, evidence_id}) so the
      gate parses structured data instead of regex — closes the v1 gap where a bare repo slug with
      no github URL / no star annotation evades existence-check.
- [ ] **Quality-drift time series** (`metrics/history.jsonl`) — per-domain source counts,
      last_verified freshness, dead-link rate, free/④ route share, added:removed ratio; cross-period
      alerts to catch *slow* degradation (e.g. a domain stagnant ≥6 months, freshness monotonically
      worsening) — the failure mode a single run looks fine but half a year rots.
- [ ] **Evidence ledger** (`evidence/run-<date>.json`) — archive the gh-api responses each run cited,
      so "where did this star count come from" is auditable; + `rationale-log.jsonl` append-only
      deletion justifications (C4 evidence codes).
- [ ] **Independent cross-model audit gate** — reuse the `citation-audit` / `experiment-audit`
      pattern (fresh zero-context reviewer verifies new entries against official sources), so the
      editor isn't the only verifier. Optionally invoke `auto-review-loop` for the diff.
- [ ] **Tiered automation** — auto-land trivial changes (dead-link cleanup, star refresh) but route
      new tools / top-pick replacements / major price changes to PR/HOLD (currently everything goes
      to one PR).
- [ ] **Quarterly meta-loop** — reuse `meta-optimize`: review run history + CHANGELOG to improve
      `refresh-protocol.md` *itself*, PR-only, never auto-merge (immutable-core guarded).
- [ ] **CHANGELOG/version automation** from the structured diff.
- [ ] **Per-domain `last_verified` surfacing.** Show staleness in the report ("seo-keywords matrix
      last verified 2026-05, may be outdated").
- [ ] **Install-state cache.** Optional snapshot of `claude mcp list` so triage can warn about
      `Failed`/`Needs auth` sources without re-running detection every time.
- [ ] **More domains as the space grows** (e.g. video/creator analytics, app-store ASO, alt-data
      marketplaces) — only when a real research run hits a gap the current 12 don't cover.
- [ ] **Delegation polish.** Tighten the hand-off contract to `deep-research` / `research-lit`
      (structured evidence-unit schema, combiner layer for large fan-outs).

## Maintenance cadence

| scope | cadence |
|---|---|
| full 12-domain sweep | quarterly |
| volatile domains (x-twitter, web-scraping, social-publishing, crypto-defi) | monthly |
| opportunistic single-shard fix | whenever a live run hits a dead/changed tool |

See [`skills/market-intel/reference/refresh-protocol.md`](skills/market-intel/reference/refresh-protocol.md) for the procedure.
