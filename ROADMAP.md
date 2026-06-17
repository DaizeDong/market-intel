# Roadmap

## v0.1.0 (alpha) — foundation

- Thin orchestration layer: triage → detect (`claude mcp list`) → guide install → delegate.
- 14-domain source matrix (thin index + per-domain shards + isolated volatile pricing/install).
- 8 quality guardrails (citation verification, ≥2-source corroboration, tiers, no silent
  degradation, dated volatile data, disconfirmation mandate, conflict surfacing, explicit gaps).
- Refresh protocol for keeping the matrix current.

## Done (v0.3.0) — self-evolution / anti-regression core

- [x] **Scheduled auto-refresh** — Windows Task `RefreshMarketIntel`, monthly, branch + gate + PR.
- [x] **Constitution** (`CONSTITUTION.md`, C1–C10) injected as hard constraints each run.
- [x] **Deterministic gate** (`tools/verify_matrix.py`) — API-verified repo existence + star
      tolerance + structure + freshness + methodology + anti-mass-deletion + constitution lock.
- [x] **Branch + PR isolation** — bad updates never reach main; Discord notify on pass/fail.
- [x] **Horizon scan (v0.5.0)** — refresh discovers NEW territories / tool-categories / research
      angles beyond the existing domains (not just better tools within them), with a fold/new-domain/
      new-skill decision gate, an anti-bloat watchlist (must recur across ≥2 scans), and human review
      for any structural addition. Scope evolves with the field, decay-guarded.
- [x] **Per-tool doc layer + multi-level install guide (v0.10.0)** — every matrix tool now has a
      `reference/tools/<slug>.md` how-to (what/install/auth/usage + General experience & gotchas/
      failure-fallback), reached on-demand via a thin `tools/index.md`; an L0 `install-guide.md`
      overview sits atop the L1 per-domain `pricing-install.md` and L2 per-tool docs. The gate gained a
      **TOOLS** coverage check (index↔doc) and now also gh-api-verifies repos/stars cited inside tool
      docs. The refresh protocol keeps the docs in sync each sweep (step 3b).

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
- [ ] **Gate: distinguish transient fail-closed from real 404.** `verify_matrix.py` correctly fails
      closed (can't verify → BLOCK), but a transient GitHub API rate-limit/network blip then discards
      an otherwise-good refresh. Retry the gate once on non-404 network errors before blocking; only a
      true 404 (hallucinated/dead repo) is an immediate hard block. (Observed during the v0.4.0 run.)
- [ ] **Per-domain `last_verified` surfacing.** Show staleness in the report ("seo-keywords matrix
      last verified 2026-05, may be outdated").
- [ ] **Install-state cache.** Optional snapshot of `claude mcp list` so triage can warn about
      `Failed`/`Needs auth` sources without re-running detection every time.
- [ ] **More domains as the space grows** (e.g. video/creator analytics, app-store ASO, alt-data
      marketplaces) — only when a real research run hits a gap the current 12 don't cover.
- [ ] **Delegation polish.** Tighten the hand-off contract to `deep-research` / `research-lit`
      (structured evidence-unit schema, combiner layer for large fan-outs).

## Triggered work (v0.18.1) — gated by external conditions

The items below are designed but deferred. Each has a **trigger condition**: when the
condition fires, the item moves to "Next" and gets a sweep. Don't pre-build.

- [ ] **MCP-registry federation — sync-check bucket H.** Trigger: `registry.modelcontextprotocol.io`
      exposes a stable `/v0/servers?since=` API (verified working in 2026-06, but auth +
      stability unconfirmed). Action: extend `companion-config/scripts/sync-check.py` with
      bucket H ("upstream registry has it, our local matrix is stale"). Companion-config
      consumers gain auto-prompted catch-up. Future audit predicted as Q4 2026 critical
      cliff — without this, ~50% of `tools/*.md` becomes mirror negative-value.

- [ ] **`transport: brokerage` abstraction.** Trigger: 3rd D-PRICE event hits the matrix in
      a single sweep (`live-runs.jsonl` outcome=barrier_found, code=D-PRICE, distinct
      domains ≥3). Action: add `transport: brokerage` to companion-config-spec; matrix gets
      pay-per-query wrappers (datarade, Bright Data Marketplace, SerpApi) as canonical
      "the API I rent so I don't have to pay 5 separate subscriptions" tier. The
      brokerage tier blunts the X / Reddit / finance-data paywall wave.

- [ ] **Compliance fields — `data_lineage`, `tos_ack_required`, `jurisdiction`.** Trigger:
      EU AI Act implementation detail rules land, OR any US state-level anti-scraping
      legislation passes. Action: add the three OPTIONAL fields to spec §3.1. matrix gates
      gain a COMPLIANCE check for high ban_risk + missing tos_ack_required combinations.

- [ ] **Route ⑤ agent-native default.** Trigger: Computer Use / Operator / Skyvern single-
      call cost drops below playwright + residential-proxy aggregate cost for a representative
      benchmark task. Track via spot-checks during browser-automation weekly sweeps. Action:
      change SKILL.md language — route ⑤ becomes the recommended barrier-breaker for at
      least 3 domains; matrix entries flip `route_agent_native: true` where appropriate;
      patchright drops to "still useful for fingerprint-only blocks".

- [ ] **`model_tier: local-ok` migration.** Trigger: a local model (Llama 4 / Qwen3-VL /
      DeepSeek class) becomes viable on the user's machine for triage / dedup /
      citation-recheck tasks (benchmark: matches Claude Sonnet output on a 20-task eval
      with <50% latency hit). Action: tag matrix entries' `model_tier`; subagent
      dispatcher routes the tagged tasks to local; frontier-only tasks stay on Claude.
      Expected to cut refresh-token cost 50%+ at no quality loss.

## Future domain placeholders (v0.18.1)

The audit identified six new domains that will likely materialize in 2026-2027. Each gets
an empty placeholder in `sources-index.md` — owning the namespace before someone duplicates
it. Per future-proofing doctrine: occupied placeholders force refresh-protocol to point at
them, so they don't get forgotten until the right moment to populate.

- [ ] `agent-marketplace` — Anthropic Skills Hub / OpenAI GPT Store / Smithery as research
      surfaces themselves (not just MCP distribution channels — research on what's selling
      / which builders are launching what).
- [ ] `ai-data-licensing` — datarade / Bright Data DaaS / Scale Data Engine / similar.
      Where to legally rent data when scraping isn't permitted.
- [ ] `voice-and-podcast-intel` — Podscan / Listen Notes / video-subtitle corpora;
      ElevenLabs class generation-side reverse-lookup.
- [ ] `synthetic-and-evals` — synthetic-data catalogs / Vals.ai / lmarena; research's
      "self-verification basis" — eval-driven matrix.
- [ ] `regulatory-watch` — SEC 8-K / EU AI Act trackers / state-level anti-scraping
      legislation; legal-tech MCPs as they mature.
- [ ] `on-chain-intel-private` — TEE / zk privacy on-chain data (Chainlink Functions /
      Nillion / EigenLayer class).

## Maintenance cadence

See `skills/market-intel/reference/refresh-protocol.md` — cadence overhauled in v0.17.0.
Default monthly · weekly for the fast-moving set (crypto-defi / browser-automation /
frontier-research / mcp-ecosystem) · quarterly reserved for Horizon scan.
