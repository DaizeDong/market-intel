# Tool: Trends MCP (trendsmcp.ai)

- **Domain(s):** trends-discovery (also: none)
- **Barrier route:** ② resale (provider absorbs the multi-platform scraping/upkeep) · **Source tier:** L2 · **Ready MCP:** yes, hosted, bearer-token (same key works for REST + MCP)
- **Cost:** free 100 req/mo (no card); paid Starter $19/mo (1k req), Pro $49/mo (5k req), Business $199/mo (25k req); annual −20% [https://trendsmcp.ai, fetched 2026-06]
- **Repo / Provider:** https://trendsmcp.ai (commercial hosted service, no public repo)
- **Top pick for its domain:** yes, the best "acceleration / growth-rate" signal across platforms

## What it does / when to pick it
Normalizes trend data across 25+ sources (Google Search/Images/News/Shopping, Amazon, Wikipedia, TikTok, Reddit, YouTube, npm/Steam/GitHub, mobile-app installs, site visits) and, crucially, returns a **growth rate**, not just a level. **Decision rule:** pick Trends MCP when the question is "is this *accelerating*?" or you need one normalized cross-platform view (esp. selling research: TikTok leads Amazon 2 to 4 weeks = the opportunity window). For clean single-source Google Trends JSON, **SerpApi** is the cross-region workhorse; for a fully free route use **trendspy/trendspyg** OSS (route ④, pytrends is archived). Use GDELT for news tone, Product Hunt for launches.

## Install
Hosted HTTP MCP, register with your bearer token (see the volatile L1 line `reference/volatile/pricing-install.md → trends-discovery`: free 100/mo, bearer token). **Secret-bearing**, do **not** `claude mcp add` with the token in a header (it echoes into the transcript); edit `~/.claude.json` `mcpServers` headers directly from clipboard. HTTP transport = Windows-friendly (preferred). Restart / `/mcp` reconnect before use. L0 mechanics + secret hygiene: `reference/install-guide.md`.

## Auth / keys
Sign up at trendsmcp.ai → dashboard → copy the API key (free tier needs no card). The **same key works for REST and MCP** with identical limits. One-line secret reminder: never `browser_snapshot` the key page; copy via the page button → clipboard → write to `~/.claude.json` with a no-echo script, verify by length only. Full procedure: `reference/install-guide.md`.

## Usage, call examples
After connecting, tools let you query a keyword/topic across the source set and return level + growth rate + (where available) sentiment/volume. REST equivalent uses the same bearer key. Minimal flow: query a candidate term → read the growth-rate field across TikTok vs Amazon to spot a lead/lag opportunity window. List exact tool names with your client after connecting, do not assume signatures from memory.

## General experience & gotchas (踩坑)
- **The growth-rate field is the whole point**, don't just read the absolute level. A high level with flat/negative growth is a *mature/declining* topic, not an opportunity.
- **Free tier is only 100 req/mo**, each cross-platform query can burn a request; budget it. Both free and paid plans **hard-pause at the cap and return HTTP 429** (no surprise overage, but also no silent degradation, a 429 means you're capped, not that the topic is dead).
- **Resale (②) means you're trusting the provider's normalization**, the cross-platform "normalized" number hides each source's own quirks (e.g. Google Trends is relative 0 to 100, not absolute volume). Treat it as a comparative signal, not an absolute install/sales count.
- **Selling-research play (shard):** TikTok virality typically leads Amazon demand by 2 to 4 weeks, a term accelerating on TikTok but flat on Amazon is the classic arbitrage window. Confirm with app-store/Amazon data before acting.
- For absolute search *volume* (not relative trend) you still need Google Ads Keyword Planner / DataForSEO, Trends MCP gives direction, not magnitude.
- **Signup is email-magic-link, no captcha** (confirmed 2026-06-16), `trendsmcp.ai/account?tab=signup` accepts the agent's form fill; API key is **emailed instantly** to the signup mailbox (not displayed in dashboard). The email body also contains a ready-to-paste MCP config snippet.
- **MCP path is the claude.ai connector UI**, NOT `claude mcp add`, the server publishes at `https://www.trendsmcp.ai/mcp` and surfaces in `claude mcp list` as `claude.ai TrendsMCP` (i.e. claude.ai-managed, not user-managed). Means it's session-wide but does NOT appear in a user-managed companion config repo's `registry.json`.

## Failure signals & fallback
Failure looks like: HTTP 429 (monthly cap hit), or a normalized number with no growth field on an unsupported source. **Fallbacks:** for clean Google Trends JSON cross-region use **SerpApi** (free 250/mo); for a fully free route use OSS **flack0x/trendspyg** or **sdil87/trendspy** (route ④, see browser-automation shard); pytrends is archived/429-prone, avoid.

## Last verified: 2026-06
