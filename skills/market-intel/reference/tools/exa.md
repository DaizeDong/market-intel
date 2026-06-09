# Tool: Exa (search; skill `exa-search`)

- **Domain(s):** web-scraping (also: frontier-research)
- **Barrier route:** ② resale API · **Source tier:** L2 · **Ready MCP:** yes — remote MCP + ready skill `exa-search` already present
- **Cost:** free 1,000 requests/mo with key (150/day no-key); paid per-request pricing scales with result count — exact $/1k rates unverified here, confirm at https://exa.ai/pricing [fetched 2026-06]
- **Repo / Provider:** https://exa.ai (hosted SaaS — no public source repo)
- **Top pick for its domain:** yes (the "recent / semantic" SEARCH-layer pick)

## What it does / when to pick it
Neural/embedding-based web search plus content extraction (`get_contents`) and similar-page discovery (`find_similar`). **Decision rule:** pick Exa over Tavily when the query is "recent / latest" (its index skews fresher — shard: "Exa good for 'recent'") or when you want to find pages *similar to* a seed URL. Pick **Tavily** when you want broad agent-ranked relevance for general discovery. Exa also cross-serves **frontier-research** (semantic paper/blog discovery). Like Tavily it is a search/extract layer — it does NOT defeat anti-bot; hand hard targets to Firecrawl/Bright Data.

## Install
A ready skill `exa-search` is already present — prefer invoking that skill for search+content jobs. For the raw MCP, use the remote/hosted endpoint with your Exa key; exact command in `reference/volatile/pricing-install.md → web-scraping`. HTTP transport, Windows-friendly. L0 mechanics (transport, secret, Windows): `reference/install-guide.md`. New MCP needs a session restart / `/mcp` reconnect.

## Auth / keys
Free key from exa.ai (1,000 req/mo); a no-key mode allows ~150/day. **Secret hygiene (one line):** for the keyed MCP, edit `~/.claude.json` from clipboard rather than `claude mcp add` (which echoes the key), and never `browser_snapshot` the key page — see `reference/install-guide.md`. The `exa-search` skill manages the key per its own setup.

## Usage — call examples
Via the `exa-search` skill: ask for a web search with content extraction, "find similar pages", or recent results. Via MCP: a `search` tool (`query`, `num_results`, `type: neural|keyword|auto`, `start_published_date` / `end_published_date` for recency), plus `get_contents(ids/urls)` and `find_similar(url)`. Each request returns ≤10 results on the base price; asking for more results costs extra per the pricing table.

## General experience & gotchas (踩坑)
- **Pricing is volatile** — shard explicitly flags "Exa raised prices"; re-confirm the free 1,000/mo and the paid per-request rate before quoting (exact $/1k unverified — see https://exa.ai/pricing). The base price covers a small fixed number of results/request; large `num_results` adds a per-extra-result charge.
- Neural search shines on conceptual/recency queries but can underperform plain keyword search for exact-string / proper-noun lookups — fall back to `type: keyword` or Tavily when results drift.
- Search/extract layer only: it will not read a login-walled Amazon/Taobao price or beat Cloudflare. The shard's e-commerce-price lesson applies — route those to playwright(④)/Bright Data.
- The no-key 150/day tier is fine for spot checks but will throttle a real fan-out; use the keyed 1,000/mo tier for actual research runs.

## Failure signals & fallback
Failure looks like: irrelevant neural matches on an exact-string query, stale results despite a date filter, or 401/quota at call time. **Fallbacks:** for broad agent-ranked discovery → **Tavily** (sibling); free no-key → `ddgs` / self-host **SearXNG** (④); to fetch/render a found URL → **Firecrawl** (②) then **Bright Data** (②) for anti-bot targets; for deep multi-paper synthesis delegate to the `research-lit` skill.

## Last verified: 2026-06
