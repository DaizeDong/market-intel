# Report template

> Data snapshot: <YYYY-MM-DD> · Depth: <quick|standard|deep> · Domains: <...>
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
- **Tool coverage:** invoked <N> / <M> available in scope (per domain + total) at scale `<scan|standard|deep|exhaustive>`. Makes "comprehensive" verifiable, not asserted.
- **Uncovered tools (explicit gaps, not silent skips):** <tool — reason: cold-mcp / missing-key / unreachable>
- **Not covered / insufficient data:** <dimensions that returned empty/failed>
- **Configure for deeper data:** "<domain> would be stronger with <source> — install via
  `claude mcp add ...` (then reconnect)."

## Sources
Full list with tier + date. Mark any unverified or dead links.
