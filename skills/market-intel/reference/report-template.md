# Report template

> Data snapshot: <YYYY-MM-DD> · Scale: <scan|standard|deep|exhaustive> · Domains: <...>
> Sources available this run: <connected MCPs> · Fallbacks used: <...>

## Executive summary
3–6 bullets. Each decision-grade bullet carries a confidence tag (high/medium/low).

## Findings by domain
For each triaged domain:
- **<claim>** — value/finding `[L? tier]` `[fetched DATE | published DATE]` `confidence: high/med/low`
  - source: <verified URL> — verbatim quote: "…" — `✓verified / ⚠unverifiable`
  - corroboration: <2nd independent source, or "single source ⚠">

## Cross-verification verdicts
Per key claim: `confirmed / disputed / unresolved` + why.

## Disagreement matrix
| claim | source A says | source B says | likely cause | lean / undecided |
|---|---|---|---|---|

## Risks & counter-evidence (mandatory)
From the disconfirmation subagent. For arbitrage/investing also list **execution friction**
(fees, slippage, capacity, time window, compliance/ban risk). If none found, state that reverse
search was run and found nothing — not proof of no risk.

## Coverage gaps
- **Tool coverage:** invoked <N> / <M> available-now in scope (per domain + total) at scale `<scan|standard|deep|exhaustive>`. Makes "comprehensive" verifiable, not asserted.
- **Availability gate (Step 2b classification, this run):** available-now <list> · configurable-with-setup <list> · hard-gap <list>. Fan-out hit only the available-now bucket.
- **Uncovered tools (explicit gaps, not silent skips):** <tool — reason: cold-mcp / missing-key / unreachable / paid-tier-only>
- **Not covered / insufficient data:** <dimensions that returned empty/failed>
- **Configure for deeper data (JIT, theme-tied):** "To deepen <this theme aspect>, configure
  <source> (<free-key | free-tier | install-no-key | paid $X>) — `python tools/console.py connect <slug>`
  (canonical, resolves by slug), or see `reference/activation-recipes.md` for the key source;
  then `/mcp` reconnect (won't help this turn)."

## Sources
Full list with tier + date. Mark any unverified or dead links.
