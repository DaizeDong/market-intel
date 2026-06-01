# Roadmap

## v0.1.0 (alpha) — current

- Thin orchestration layer: triage → detect (`claude mcp list`) → guide install → delegate.
- 12-domain source matrix (thin index + per-domain shards + isolated volatile pricing/install).
- 8 quality guardrails (citation verification, ≥2-source corroboration, tiers, no silent
  degradation, dated volatile data, disconfirmation mandate, conflict surfacing, explicit gaps).
- Refresh protocol for keeping the matrix current.

## Next

- [ ] **Scheduled auto-refresh.** Wire an external cron / Windows Task that launches a headless
      `claude -p "follow reference/refresh-protocol.md"` run on a cadence (quarterly full / monthly
      for volatile domains), commits the diff, and pushes. Needs a token budget cap per run.
- [ ] **CHANGELOG automation.** Have the refresh protocol write structured diffs to `CHANGELOG.md`
      and bump `plugin.json` version automatically.
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
