# Refresh protocol — keep the source matrix current

This skill's value is a curated source matrix. Tools, prices, and barriers in the commercial-data
space move fast (every survey round found acquisitions, price changes, and dead tools within
months). Re-run this protocol periodically to keep `domains/`, `volatile/pricing-install.md`, and
`sources-index.md` accurate.

## Cadence

- **Default: quarterly** (every ~3 months) full sweep.
- **Faster (monthly)** for volatile domains: x-twitter, web-scraping, social-publishing, crypto-defi,
  browser-automation (fast-moving OSS repos + frequent API-policy and pricing changes).
- Also refresh opportunistically whenever you hit a dead/changed tool during a real research run —
  fix that one shard immediately.

## Procedure (full sweep)

1. **Fan out one subagent per domain** (13 total — see `sources-index.md`, incl. browser-automation).
   Each subagent's task: "Search for NEW or CHANGED tools/MCP servers/skills in <domain> since
   <last_verified date>. Check the MCP registries (smithery.ai, glama.ai, mcp.so, pulsemcp.com,
   registry.modelcontextprotocol.io, mcp.apify.com) AND GitHub for free open-source browser-
   automation / act-like-human repos (verify each repo really exists + its star count + last-push
   date via the GitHub API — do NOT fabricate repo names). Report: (a) NEW entries worth adding
   (especially free route-④ repos that could replace a paid API), (b) tools/repos that died /
   were archived / 404'd / changed pricing, (c) any barrier-route shift (e.g. an API that went
   paid-only, or a new OSS repo that makes a paid source unnecessary). Return a structured diff."
2. **Apply the same quality guardrails** as a normal run (verify each claimed tool exists and the
   price against its official site — do not trust a subagent's recalled pricing).
3. **Incremental edit, don't rewrite**: for each domain, update only changed rows in
   `domains/<domain>.md`; move/refresh price+install lines in `volatile/pricing-install.md`; bump
   that section's `last_verified: YYYY-MM`. Update `sources-index.md` only if a domain's top pick
   changed.
4. **Record the diff** in `CHANGELOG.md` at the repo root (date + per-domain added/removed/changed),
   and bump the plugin `version` in `.claude-plugin/plugin.json`.
5. **Commit + push** to the repo (DaizeDong/market-intel).

## Budget

Treat a full sweep like a `deep` run: cap at 12 subagents, single round each, plus verification.
Don't let a refresh balloon — it's a diff against an existing matrix, not a from-scratch survey.

## Trigger

- Manual: ask "refresh the market-intel source matrix" / "刷新工具库".
- Scheduled: an external cron/Task can launch a headless run of this protocol (see ROADMAP).
