# Tool: Polygon.io (now Massive)

- **Domain(s):** finance-markets (also: none)
- **Barrier route:** ① official API · **Source tier:** L1 · **Ready MCP:** yes (official Polygon MCP; key required)
- **Cost:** free 5 req/min (Basic, 15-min delayed); paid ~$29 / $79 / $199 per month (unlimited calls; realtime at the top tier) [confirm at https://polygon.io/pricing → 301 https://massive.com/pricing, web-search-corroborated 2026-06; live page is JS-rendered/unfetchable]
- **Repo / Provider:** https://polygon.io (official provider; rebranded to **Massive** — polygon.io 301-redirects to massive.com; APIs and existing keys unchanged)
- **Top pick for its domain:** no (the **Pro upgrade** pick once the free trio isn't enough)

## What it does / when to pick it
Full market-data API: realtime + ~20 years of history across stocks/options/indices/forex/crypto/futures, via REST, WebSocket streaming, and flat files. **Decision rule:** pick Polygon when the free trio (SEC EDGAR + FRED + Finnhub) can't deliver — specifically when you need *deep tick/aggregate history*, *WebSocket realtime*, or *reliable high-volume pulls*. It's the shard's designated **Pro** step-up. For a few quotes a day, Finnhub (60/min) or Twelve Data (800/day) free tiers are cheaper; pay for Polygon when scale, history depth, or true realtime is the requirement.

## Install
Official Polygon/Massive MCP (key-bearing). Exact, time-stamped command + the latest tier prices: `reference/volatile/pricing-install.md → finance-markets`. L0 mechanics (prefer HTTP transport on Windows): `reference/install-guide.md`. Restart / `/mcp` reconnect after adding.

## Auth / keys
Key from the Polygon.io (Massive) dashboard — same key works post-rebrand. Free Basic tier needs no card. **Secret hygiene (key-bearing):** have the USER supply the key via the env/`-e` form themselves; never echo it into the transcript; for a header/URL-bearing MCP edit `~/.claude.json` directly rather than `claude mcp add` (which echoes args), and never `browser_snapshot` the dashboard key page. One line + full rules: `reference/install-guide.md`.

## Usage — call examples
REST/MCP endpoints cover aggregates (OHLC bars), trades/quotes, reference data (tickers/splits/dividends), and a WebSocket feed for streaming. Minimal: fetch daily aggregate bars for a ticker over a date range, or open a WebSocket subscription for live trades on a symbol (realtime only on the paid realtime tier).

## General experience & gotchas (踩坑)
- **REBRAND, not a death (shard):** polygon.io now 301-redirects to **massive.com**. This is a pure rename — the API base, endpoints, and your existing key did not change, and it remains the live Pro top pick (NOT demoted/superseded). Don't be alarmed by the redirect — verify pricing on the live site, which is JS-rendered (WebFetch returns an empty shell, so confirm tiers in-browser).
- **"Free realtime" is a trap (shard):** the free Basic tier is **15-minute delayed** at 5 req/min — fine for research, not for anything time-sensitive. True realtime is the top (~$199) tier.
- **Tier pricing rots — confirm before quoting (this file's numbers are corroborated by web search 2026-06, not the live page).** The shard lists $29 / $79 / $199; re-verify on massive.com before committing spend.
- **Rate-limit shape matters:** free is 5 req/min (easy to trip in a loop); paid tiers remove the per-minute cap. Batch and back off on the free tier.
- It's a quote/market-data source, not fundamentals — for filings use SEC EDGAR, for macro use FRED.
- **PyPI MCP wrappers for Polygon are unstable** (confirmed 2026-06) — community packages publishing as `polygon-mcp` / `polygon-mcp-server` have flaky installs and break across uvx versions. Recommendation: **keep the API key in `secrets/polygon.env` and call REST directly from a subagent Bash** rather than chasing a stable MCP install. The companion-config-repo pattern records this as `pending_registrations.polygon` with `mcp_installed: false, key_saved: true`.

## Failure signals & fallback
Failure looks like: HTTP 429 (free 5/min exceeded), delayed data when you expected realtime (wrong tier), or auth errors after the rebrand (key should still work — re-check the dashboard). **Fallbacks:** low-volume free quotes → **Finnhub** (60/min) or **Twelve Data** (800/day); fundamentals/filings → **SEC EDGAR**; the only free *no-key* price route in this domain is `Alex2Yang97/yahoo-finance-mcp` (④, yfinance — not for prod, IP-ban prone).

## Last verified: 2026-06
