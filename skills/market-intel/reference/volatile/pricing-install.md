# Volatile: pricing & install commands

> ⚠️ ALL prices and exact commands below are time-stamped and rot fast. **Verify against the
> official site before quoting or installing.** `last_verified: 2026-05` unless noted.
> A newly added MCP only takes effect after session restart / `/mcp` reconnect.
>
> Security: never fill in or echo the user's API key. Have the USER run the `-e KEY=$VAR` form
> themselves. Keys land in plaintext in `~/.claude.json` — warn them not to commit/screenshot it.
> Prefer `-s user` scope for reusable sources. Prefer HTTP-transport sources on Windows.

## x-twitter `last_verified: 2026-06`
- twitterapi.io: pay-per-use $0.15/1k tweets, $0.18/1k profiles, $0.1 free credit (no card),
  .edu 50% rebate (email hello@twitterapi.io). Key from dashboard (Google login, no X dev account).
  Official native MCP (HTTP, verified 2026-06): `claude mcp add --transport http --scope user
  twitterapi-mcp https://mcp.twitterapi.io/mcp --header "Authorization: Bearer YOUR_API_KEY"`.
  ⚠ Secret-config hygiene (lesson learned): `claude mcp add` ECHOES the header (key leaks into the
  transcript) — for secret-bearing MCPs, edit `~/.claude.json` headers directly from clipboard
  instead, and never `browser_snapshot` a dashboard page that reveals the key (use the copy button
  → clipboard pipe; verify by length only). twitterapi.io rotates only once / 24h.
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
- Etherscan: `https://mcp.etherscan.io/mcp` (free key as bearer). NOTE 2026-06: free-tier chain
  coverage cut ~10% (verified-contract/ABI endpoints stay free all chains); "Lite" plan = 25% of
  prior lowest tier (info.etherscan.com/whats-changing-in-the-free-api-tier-coverage-and-why).
- Blockscout MCP (free, 3000+ chains, no key for dev; read-only on-chain): repo blockscout/mcp-server
  (39★, official) — install/endpoint per docs.blockscout.com/devs/mcp-server. Pro key (free) for prod throughput.
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

## browser-automation `last_verified: 2026-06` (stars verified via GitHub API 2026-06-01)
General frameworks (all free, self-host):
- browser-use: `pip install browser-use` — github.com/browser-use/browser-use (96k★)
- stagehand: `npm i @browserbasehq/stagehand` — github.com/browserbase/stagehand (23k★)
- skyvern: github.com/Skyvern-AI/skyvern (22k★, self-host + API)
- crawl4ai: `pip install crawl4ai` or docker — github.com/unclecode/crawl4ai (67k★)
- crawlee: `npm i crawlee` — github.com/apify/crawlee (24k★)
- scrapegraph-ai: `pip install scrapegraphai` — github.com/ScrapeGraphAI/Scrapegraph-ai (27k★)
Anti-detection: nodriver (`pip install nodriver`, 4.3k★) · camoufox (`pip install camoufox`, 8.9k★) ·
steel-browser (github.com/steel-dev/steel-browser, 7.1k★, self-host).
playwright MCP already connected — verify with `claude mcp list`.

Platform-specific OSS repos (free; most violate platform ToS — throwaway accounts for write/scrape):
- X: d60/twikit (`pip install twikit`, 4.4k★) + MCP adhikasp/mcp-twikit
- Instagram: subzeroid/instagrapi (`pip install instagrapi`, 6.3k★) · instaloader (`pip install instaloader`, 12.5k★, read-only)
- LinkedIn: stickerdaniel/linkedin-mcp-server (2.1k★, ready MCP, ⚠ high ban risk) · joeyism/linkedin_scraper (4.2k★)
- TikTok: davidteather/TikTok-Api (`pip install TikTokApi`, 6.4k★)
- 小红书: xpzouying/xiaohongshu-mcp (14k★, Go, ready MCP, can post) · NanmiCoder/MediaCrawler (50k★, 7 中文平台)
- YouTube/media: yt-dlp (`pip install yt-dlp`, 167k★)
- 微博: dataabc/weibo-crawler (4.5k★)
- Bluesky: `pip install atproto` (MarshalX/atproto, official) · Mastodon: `pip install Mastodon.py` (official)
- Ecom: Cybrarist/Discount-Bandit (690★, self-host tracker) · omkarcloud/amazon-scraper (220★)
- SERP/SEO: searxng/searxng (31k★, self-host meta-search) · towfiqi/serpbear (2k★, rank tracker) · deedy5/ddgs (2.7k★)
- B2B leads: gosom/google-maps-scraper (4.2k★, low-risk) · omkarcloud/google-maps-scraper (2.7k★)
- Trends: flack0x/trendspyg · sdil87/trendspy. App stores: facundoolano/google-play-scraper (2.9k★) + app-store-scraper
- Dead/avoid: tomquirk/linkedin-api (404), pytrends (archived), snscrape (停更), elizaOS/agent-twitter-client (下架)

## Discovery registries (find more)
smithery.ai (one-click) · glama.ai (largest) · mcp.so · pulsemcp.com (curated + traffic) ·
registry.modelcontextprotocol.io (official) · mcp.apify.com (3000+ actors).
