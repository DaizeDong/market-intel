# Volatile: pricing & install commands

> ⚠️ ALL prices and exact commands below are time-stamped and rot fast. **Verify against the
> official site before quoting or installing.** `last_verified: 2026-05` unless noted.
> A newly added MCP only takes effect after session restart / `/mcp` reconnect.
>
> Security: never fill in or echo the user's API key. Have the USER run the `-e KEY=$VAR` form
> themselves. Keys land in plaintext in `~/.claude.json` — warn them not to commit/screenshot it.
> Prefer `-s user` scope for reusable sources. Prefer HTTP-transport sources on Windows.

## x-twitter `last_verified: 2026-05`
- twitterapi.io: pay-per-use $0.15/1k tweets, $0.18/1k profiles, $0.1 free credit, .edu discount.
  Get key at twitterapi.io → then add its MCP (see glama.ai/mcp kaitoInfra/twitterapi-io-mcp-server).
- Apify tweet actors: pay-per-result ~$0.1–0.25/1k. Apify MCP: `https://mcp.apify.com` (HTTP).
- twscrape (self-host, free): `pip install twscrape` — needs X account cookies + proxy.

## reddit-community
- HN: `uvx mcp-hn` (free, no key) or `npx -y @smithery/cli install mcp-hn --client claude`.
- Reddit: GridfireAI/reddit-mcp — `uvx reddit-mcp`; create app at reddit.com/prefs/apps for
  REDDIT_CLIENT_ID/SECRET (free).
- Stack Exchange: midodimori-stack-overflow-mcp (free; SE key raises 300→10k/day).

## web-scraping
- Firecrawl: `npx -y firecrawl-mcp` (key from firecrawl.dev; free 500 one-time credits).
- Tavily: `claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=...`
  (free 1000 credits/mo).
- Exa: remote MCP, free 1000/mo with key or 150/day no-key. Skill `exa-search` already present.
- Bright Data: `@brightdata/mcp` — free 5000 req/mo, no card (Rapid mode).
- DataForSEO: official TS MCP github.com/dataforseo/mcp-server-typescript; $1 trial + free Sandbox, $50 min.

## ecommerce-arbitrage
- Keepa: KEEPA_API_KEY from keepa.com (€49/mo @ 20 tokens/min start). MCP: cosjef/Keepa_MCP or
  BWB03/keepa-adapter (.mcpb one-click).
- eBay: developer.ebay.com AppID (free). Shopify Storefront MCP: `https://{shop}.myshopify.com/api/mcp` (free).

## finance-markets
- SEC EDGAR: stefanoamorelli/sec-edgar-mcp (free, no key, set User-Agent).
- FRED: stefanoamorelli/fred-mcp-server (free key at fred.stlouisfed.org).
- Polygon.io $29/mo unlimited (15min) / $199 realtime. Finnhub free 60/min. Twelve Data free 800/day.
- Alpaca: alpacahq/alpaca-mcp-server (paper trading free — use FIRST).

## crypto-defi
- CoinGecko: `npx mcp-remote https://mcp.api.coingecko.com/mcp` (public, no key).
- Etherscan: `https://mcp.etherscan.io/mcp` (free key as bearer).
- Hummingbot: `claude mcp add --transport stdio hummingbot -- docker run --rm -i -e HUMMINGBOT_API_URL=http://host.docker.internal:8000 -v hummingbot_mcp:/root/.hummingbot_mcp hummingbot/hummingbot-mcp:latest`
- ccxt: `pip install ccxt` (lib, not MCP). funding-rates-mcp: Kukapay repo.

## seo-keywords
- GSC: ahonn/mcp-server-gsc — `npx -y mcp-server-gsc` (free; Google OAuth/service-account JSON).
- DataForSEO: see web-scraping. SE Ranking: `claude mcp add --transport http se-ranking https://api.seranking.com/mcp --header "X-Api-Key: ..."` (14d trial 100k credits).
- Ahrefs official remote MCP `https://api.ahrefs.com/mcp/mcp` (needs Lite+ sub).

## social-publishing
- Buffer: API key from dashboard (free tier works) + official MCP.
- Blotato: $29/mo, `backend.blotato.com/v2` + MCP (Claude Code via API key header).
- Postiz (OSS, free): self-host → Settings → Public API → copy MCP URL. v2.12+ needs Temporal.
- X single: `npx -y @enescinar/twitter-mcp` (needs X dev creds, API cost自负). OpenTweet $11.99/mo (hosted).

## content-cms
- WordPress: gaupoit/wordpress-mcp (`uv sync`) or wolffcatskyy (Docker); Application Password.
- Ghost: `@ryukimin/ghost-mcp` — GHOST_URL + GHOST_ADMIN_API_KEY.
- Sanity: `sanity` CLI auto-configures, or remote `https://mcp.sanity.io` (OAuth).
- Notion: `https://mcp.notion.com/mcp` (OAuth). Pipepost: multi-platform OSS MCP.

## leadgen-crm
- Apollo.io: Claude → Customize → Connectors → "Apollo.io" (OAuth). ⚠ disable model training first.
- Hunter: `https://mcp.hunter.io/mcp` (X-API-KEY). ZeroBounce: official MCP (key).
- HubSpot/Salesforce/Attio: official connectors/MCP (OAuth). Smartlead: smartlead-mcp-by-leadmagic (npx, key).
- Bright Data Crunchbase MCP: free 5k/mo.

## trends-discovery
- GDELT MCP: mcpbundles.com/skills/gdelt (free, no auth). Product Hunt: `pip install product-hunt-mcp` (PH token).
- Trends MCP: trendsmcp.ai (free 100/mo, bearer token). SerpApi: key, free ~100/mo.
- App stores: `npm i google-play-scraper app-store-scraper` (free) or mobile-store-scraper-mcp (self-host).
- Finnhub MCP: cfdude/mcp-finnhub (free 60/min key).

## Discovery registries (find more)
smithery.ai (one-click) · glama.ai (largest) · mcp.so · pulsemcp.com (curated + traffic) ·
registry.modelcontextprotocol.io (official) · mcp.apify.com (3000+ actors).
