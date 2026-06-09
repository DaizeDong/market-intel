# Tool: Financial Modeling Prep (FMP)

- **Domain(s):** finance-markets (also: none)
- **Barrier route:** ① official API · **Source tier:** L1 · **Ready MCP:** no — REST API (key); wrap it yourself or call REST directly
- **Cost:** free tier 250 req/day (US stocks); paid plans above that [https://site.financialmodelingprep.com/pricing-plans, web-search-corroborated 2026-06; live page 403s to WebFetch]
- **Repo / Provider:** https://site.financialmodelingprep.com (official provider)
- **Top pick for its domain:** no (the pre-parsed-financials/valuation convenience layer)

## What it does / when to pick it
FMP serves company financials and valuation: income statement / balance sheet / cash flow (already parsed), ratios, DCF/valuation, key metrics, and market data. **Decision rule:** pick FMP when you want **pre-parsed financial statements and valuation ratios** without doing the XBRL extraction yourself — it's the convenience layer over what SEC EDGAR holds raw. Use EDGAR when you need the authoritative source-of-truth number or a non-standard line; use FMP when you want ratios/DCF/standardized statements fast. For live quotes prefer Finnhub/Twelve Data/Polygon.

## Install
**No ready MCP** — FMP is a plain REST API. Either call REST directly (`financialmodelingprep.com/api/v3/...` with `?apikey=`) or wrap it in a small custom MCP. Exact context: `reference/volatile/pricing-install.md → finance-markets` (shard line: "Financial Modeling Prep free 250/day"). L0 mechanics: `reference/install-guide.md`.

## Auth / keys
Free API key from site.financialmodelingprep.com (signup → dashboard; free 250 req/day, no card). **Secret hygiene (key-bearing):** USER supplies the key; never echo it into the transcript; never `browser_snapshot` the dashboard key page; keep the key out of any committed file. One line + full rules: `reference/install-guide.md`. (Key goes in the `apikey` query param for REST.)

## Usage — call examples
REST endpoints cover `income-statement/{ticker}`, `balance-sheet-statement`, `cash-flow-statement`, `ratios`, `key-metrics`, `discounted-cash-flow`, and `quote`. Minimal: `GET /api/v3/income-statement/AAPL?period=annual&apikey=KEY` → parsed annual income statements as JSON.

## General experience & gotchas (踩坑)
- **Free = 250/day (shard, confirmed 2026-06).** Lowest free budget of the quote-tier siblings (Finnhub 60/min, Twelve Data 800/day) — fine for a handful of company pulls, not for wide scans. Cache aggressively.
- **No MCP wrapper in the inventory — you call REST.** Don't wait on an MCP; hit the endpoint directly or wrap a thin one.
- **Free tier is US-stocks-only and history-limited:** 46+ global exchanges, 30+ yr history, and several endpoints (earnings calendar, stock peers, some premium datasets) are paid-only and return empty/`403`/`Legacy Endpoint` on the free key — an access gate, not "no data."
- **Live page 403s to automated fetch:** the pricing/docs pages block WebFetch (numbers here are web-search-corroborated 2026-06). Re-verify tier prices in a real browser before quoting/spending.
- **It's a parsed-financials convenience layer, not the source of record** — when a number must be authoritative or a line is non-standard, go to the SEC filing via **SEC EDGAR**.

## Failure signals & fallback
Failure looks like: empty/`403`/legacy-endpoint message on a premium or non-US endpoint (free gate), HTTP 429 (250/day exceeded), or a 401 on a bad key. **Fallbacks:** authoritative/raw fundamentals → **SEC EDGAR MCP**; live quotes → **Finnhub** (60/min) / **Twelve Data** (800/day); deep history/realtime → **Polygon.io**; macro context → **FRED**.

## Last verified: 2026-06
