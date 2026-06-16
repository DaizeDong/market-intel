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

## reddit-community `last_verified: 2026-06`
- HN: `uvx mcp-hn` (free, no key) or `npx -y @smithery/cli install mcp-hn --client claude`.
- Reddit (**top pick**): karanb192/reddit-mcp-buddy (702★): `npx -y reddit-mcp-buddy` (free; anon tier
  no creds, app-id 60/min, login 100/min). Replaces stale GridfireAI/reddit-mcp.
- king-of-the-grackles/reddit-research-mcp (120★): hosted OAuth MCP, no creds (semantic subreddit discovery).
- Reddit (D-SUPERSEDED fallback): GridfireAI/reddit-mcp — `uvx reddit-mcp`; create app at
  reddit.com/prefs/apps for REDDIT_CLIENT_ID/SECRET (free). Superseded by reddit-mcp-buddy; minimal fallback only.
- Stack Exchange: midodimori-stack-overflow-mcp (free; SE key raises 300→10k/day).
- dancolta/subscope (10★): self-host, keyless public-RSS buyer-intent.

## web-scraping `last_verified: 2026-06`
- Firecrawl: `npx -y firecrawl-mcp` (key from firecrawl.dev; free 1,000 credits/mo, cheapest paid
  Hobby $16/mo yearly). Repo github.com/firecrawl/firecrawl (130k★).
- Tavily: `claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=...`
  (free 1000 credits/mo).
- Exa: remote MCP, free 1000/mo with key or 150/day no-key. Skill `exa-search` already present.
- Bright Data (verified 2026-06, **hosted HTTP, Windows-friendly**): add to `~/.claude.json`
  `mcpServers.brightdata = {"type":"http","url":"https://mcp.brightdata.com/mcp?token=<API_TOKEN>"}`
  (token = Bright Data dashboard → Settings → "Users and API keys" → API keys; **free 5000 req/mo
  Rapid, no card**). ⚠ token is shown PLAINTEXT in that table — have the user copy it, do NOT
  browser_snapshot the page; write the URL via direct .claude.json edit (NOT `claude mcp add`, which
  echoes the URL+token). Verify: `claude mcp list | grep brightdata | sed -E 's/token=[^ &]*/token=***/'`.
  Stdio alt: `npx @brightdata/mcp` with env `API_TOKEN`.
- DataForSEO: official TS MCP github.com/dataforseo/mcp-server-typescript; $1 trial + free Sandbox, $50 min.
- patchright: `pip install patchright` or `npm i patchright` — Kaliiiiiiiiii-Vinyzu/patchright (3.4k★,
  undetected-Playwright, Apache-2.0, free).

## ecommerce-arbitrage `last_verified: 2026-06`
- Keepa: KEEPA_API_KEY from keepa.com (€49/mo @ 20 tokens/min start). MCP: cosjef/Keepa_MCP or
  BWB03/keepa-adapter (.mcpb one-click).
- eBay: developer.ebay.com AppID (free). Shopify Storefront MCP: `https://{shop}.myshopify.com/api/mcp` (free).
- PriceAPI: priceapi.com — Go €99/mo (5k credits) + free 1,000-credit no-card trial (€499 = Starter tier).
- Rainforest API: now hosted at trajectdata.com — Hobbyist $23/mo (Amazon product/offers/reviews).

## finance-markets `last_verified: 2026-06`
- SEC EDGAR: stefanoamorelli/sec-edgar-mcp (free, no key, set User-Agent).
- FRED: stefanoamorelli/fred-mcp-server (free key at fred.stlouisfed.org).
- Polygon.io → rebranded **Massive** (massive.com, 301 redirect; APIs/keys unchanged): free 5 req/min,
  paid $29/$79/$199. Finnhub free 60/min. Twelve Data free 800/day.
- Alpaca: alpacahq/alpaca-mcp-server (paper trading free — use FIRST).
- Alex2Yang97/yahoo-finance-mcp (306★): `uvx`/clone self-host, free no-key (⚠ yfinance scrapes
  Yahoo, not for prod).

## crypto-defi `last_verified: 2026-06`
- CoinGecko: `npx mcp-remote https://mcp.api.coingecko.com/mcp` (public, no key).
- Etherscan: `https://mcp.etherscan.io/mcp` (free key as bearer). NOTE 2026-06: free-tier chain
  coverage cut ~10% (verified-contract/ABI endpoints stay free all chains); "Lite" plan = 25% of
  prior lowest tier (info.etherscan.com/whats-changing-in-the-free-api-tier-coverage-and-why).
  ⚠ July-2026 change drops max records returned 10k→1k (info.etherscan.com).
- Blockscout MCP (free, 3000+ chains, no key for dev; read-only on-chain): repo blockscout/mcp-server
  (40★, official) — install/endpoint per docs.blockscout.com/devs/mcp-server. Pro key (free) for prod throughput.
- Hummingbot: `claude mcp add --transport stdio hummingbot -- docker run --rm -i -e HUMMINGBOT_API_URL=http://host.docker.internal:8000 -v hummingbot_mcp:/root/.hummingbot_mcp hummingbot/hummingbot-mcp:latest`
- ccxt: `pip install ccxt` (lib, not MCP). funding-rates-mcp: Kukapay repo.
- CoinMarketCap: free Basic now 50 req/min + 15k credits/mo (key at pro.coinmarketcap.com).
- Nansen: ~$49/mo annual / $69 monthly (collapsed from up to ~$999/mo).
- DefiLlama: free no-key REST `https://api.llama.fi` + `https://yields.llama.fi`
  (TVL/yields/stablecoins/fees); 3rd-party MCPs only — frame as REST.
- Barker: free no-key REST + agent-friendly index at `https://docs.barker.money/llms.txt`
  (read this first for endpoint catalog). Stablecoin yields across 515 DeFi + 20 CEX, no MCP yet.
  Vault deposits via per-partner `BarkerEngine` ERC-4626 contract on Base/Arbitrum/ETH/BNB
  (out of scope for research; relevant only if recommending it as user's execution venue).

## seo-keywords `last_verified: 2026-06`
- GSC: ahonn/mcp-server-gsc — `npx -y mcp-server-gsc` (free; Google OAuth/service-account JSON).
- DataForSEO: see web-scraping. SE Ranking: `claude mcp add --transport http se-ranking https://api.seranking.com/mcp --header "X-Api-Key: ..."` (14d trial 100k credits).
- Ahrefs official remote MCP `https://api.ahrefs.com/mcp/mcp` (needs Lite+ sub).
- Semrush: Pro ~$140/mo (annual ~$117); $299 = Business tier.
- SerpApi: key, free 250/mo; Starter $25/1k.
- Google Suggest: `https://suggestqueries.google.com/complete/search?client=firefox&q=...`
  (free no-key, undocumented).
- respectlytics/respectaso (377★): self-host, free (iTunes Search API, iOS only).

## social-publishing `last_verified: 2026-06`
- Buffer: API key from dashboard (free tier works) + official MCP.
- Blotato: Starter $29/mo = 20 social accounts, `backend.blotato.com/v2` + MCP (API key header;
  API needs a paid plan).
- Typefully: Free $0 (1 scheduled post) / Starter $8 / Creator $19 / Team $39 (API needs a paid plan).
- Postiz (OSS, free): self-host → Settings → Public API → copy MCP URL. v2.12+ needs Temporal.
- X single: `npx -y @enescinar/twitter-mcp` (needs X dev creds, API cost自负). OpenTweet $11.99/mo (hosted).
- gitroomhq/postiz-agent (278★): `npx skills add` (official Postiz agent, self-host).
- langchain-ai/social-media-agent (2.6k★): clone + keys (content pipeline).

## content-cms `last_verified: 2026-06`
- WordPress: WordPress/mcp-adapter (1236★, official WP MCP via Abilities API; Application Password).
  Replaces stale gaupoit/wordpress-mcp + archived Automattic/wordpress-mcp.
- Ghost: MFYDev/ghost-mcp (199★) — GHOST_URL + GHOST_ADMIN_API_KEY. Replaces dead @ryukimin/ghost-mcp (404).
- Sanity: `sanity` CLI auto-configures, or remote `https://mcp.sanity.io` (OAuth).
- Notion: `https://mcp.notion.com/mcp` (OAuth). Pipepost: multi-platform OSS MCP.
- Directus: directus/mcp (79★, official Directus MCP).
- Webflow: webflow/mcp-server (132★, official Webflow MCP, OAuth).

## leadgen-crm `last_verified: 2026-06`
- Apollo.io: Claude → Customize → Connectors → "Apollo.io" (OAuth). ⚠ disable model training first.
- Hunter: `https://mcp.hunter.io/mcp` (X-API-KEY). ZeroBounce: official MCP (key).
- HubSpot/Salesforce/Attio: official connectors/MCP (OAuth). Smartlead: npm `smartlead-mcp-server`
  (latest 1.2.1, 2025-04) ⚠ repo archived 2025-07 — verify before use (prior "smartlead-mcp-by-leadmagic"
  hint was unreliable).
- Bright Data Crunchbase: free 5k/mo via Rapid route (source of record); brightdata.com web-MCP
  product page is 404 — use the dashboard API-keys route, not the dead product URL.

## trends-discovery `last_verified: 2026-06`
- GDELT MCP: mcpbundles.com/skills/gdelt (free, no auth). Product Hunt: jaipandya/producthunt-mcp-server
  (46★, PH token) — old `product-hunt-mcp` path is dead (404, repo stale 2025-04).
- Trends MCP: trendsmcp.ai (25+ sources, bearer token); paid $19/1k, $49/5k, $199/25k.
  SerpApi: key, free 250/mo; Starter $25/1k.
- Exploding Topics: Entrepreneur $39 / Investor $99 / Business $249 (⚠ trial-only, NO permanent free
  tier; forecasting gated Investor+).
- App stores: `npm i google-play-scraper app-store-scraper` (free) or mobile-store-scraper-mcp (self-host).
- Finnhub MCP: cfdude/mcp-finnhub (free 60/min key).
- claude-world/trend-pulse (41★): self-host, free no-key (20-source aggregator + lifecycle).
- jmanek/google-news-trends-mcp (81★): self-host, free no-key (Google News RSS + Trends).

## frontier-research `last_verified: 2026-06`
Most sources are free / no-key (arXiv, HF read, OpenReview).
- arXiv: REST `http://export.arxiv.org/api/query` (free, no key). MCP: `uvx arxiv-mcp-server`
  (blazickjp/arxiv-mcp-server). Be polite (~1 req / 3s).
- Hugging Face: Daily Papers `https://huggingface.co/api/daily_papers` + Hub API (free, no key for
  read). Official HF MCP `https://huggingface.co/mcp` (HF token only for write/private/gated).
- Semantic Scholar: Graph API `https://api.semanticscholar.org/graph/v1` (free; request a free key
  at semanticscholar.org/product/api to lift rate limits). MCP: search "semantic-scholar mcp".
- Papers with Code: ⚠ DEAD — REST `https://paperswithcode.com/api/v1/` sunset by Meta (302-redirects
  to huggingface.co/papers/trending). SOTA-leaderboard is now a gap.
- OpenReview: API2 `https://api2.openreview.net` (free; openreview-py client `pip install openreview-py`).
- GitHub: official github MCP (PAT) or REST for trending/releases/star velocity.
- AI lab blogs / roundups: RSS where available + playwright MCP (no API) — OpenAI, Anthropic,
  DeepMind, Meta AI, Mistral, Qwen, DeepSeek; AINews (smol.ai), The Batch, Import AI.
- alphaXiv (browser) · arxiv-sanity-lite (`karpathy/arxiv-sanity-lite`, self-host free) ·
  Connected Papers / ResearchRabbit (browser, no official API → playwright MCP).
- openags/paper-search-mcp (1.8k★): `uvx`/clone (arXiv+PubMed+bioRxiv multi-venue).
- Future-House/paper-qa (8.7k★): `pip install paper-qa` (grounded full-text PDF research).
- Deep synthesis → delegate to the `research-lit` skill (don't re-implement lit-review here).

## browser-automation `last_verified: 2026-06` (stars verified via GitHub API 2026-06-01)
General frameworks (all free, self-host):
- browser-use: `pip install browser-use` — github.com/browser-use/browser-use (96k★)
- stagehand: `npm i @browserbasehq/stagehand` — github.com/browserbase/stagehand (23k★)
- skyvern: github.com/Skyvern-AI/skyvern (22k★, self-host + API)
- crawl4ai: `pip install crawl4ai` or docker — github.com/unclecode/crawl4ai (67k★)
- crawlee: `npm i crawlee` — github.com/apify/crawlee (24k★)
- scrapegraph-ai: `pip install scrapegraphai` — github.com/ScrapeGraphAI/Scrapegraph-ai (27k★)
- agent-browser: native CLI, ships `.claude-plugin` — github.com/vercel-labs/agent-browser (35.6k★,
  token-efficient browser agent)
Anti-detection: nodriver (`pip install nodriver`, 4.3k★) · camoufox (`pip install camoufox`, 9.1k★) ·
steel-browser (github.com/steel-dev/steel-browser, 7.1k★, self-host) ·
camofox-browser (github.com/jo-inc/camofox-browser, 6.5k★, free MIT, fingerprint spoofing on Camoufox).
playwright MCP already connected — verify with `claude mcp list`.

Platform-specific OSS repos (free; most violate platform ToS — throwaway accounts for write/scrape):
- X: d60/twikit (`pip install twikit`, 4.5k★) + MCP adhikasp/mcp-twikit
- Instagram: subzeroid/instagrapi (`pip install instagrapi`, 6.3k★) · instaloader (`pip install instaloader`, 12.5k★, read-only)
- LinkedIn: stickerdaniel/linkedin-mcp-server (2.1k★, ready MCP, ⚠ high ban risk) · joeyism/linkedin_scraper (4.2k★)
- TikTok: davidteather/TikTok-Api (`pip install TikTokApi`, 6.4k★)
- 小红书: xpzouying/xiaohongshu-mcp (14k★, Go, ready MCP, can post) · NanmiCoder/MediaCrawler (50k★, 7 中文平台)
- YouTube/media: yt-dlp (`pip install yt-dlp`, 167k★)
- 微博: dataabc/weibo-crawler (4.5k★)
- Bluesky: `pip install atproto` (MarshalX/atproto, official) · Mastodon: `pip install Mastodon.py` (official)
- Ecom: Cybrarist/Discount-Bandit (697★, self-host tracker) · omkarcloud/amazon-scraper (220★)
- SERP/SEO: searxng/searxng (31k★, self-host meta-search) · towfiqi/serpbear (2k★, rank tracker) · deedy5/ddgs (2.7k★)
- B2B leads: gosom/google-maps-scraper (4.3k★, low-risk) · omkarcloud/google-maps-scraper (2.7k★)
- Trends: flack0x/trendspyg · sdil87/trendspy. App stores: facundoolano/google-play-scraper (2.9k★) + app-store-scraper
- Dead/avoid: tomquirk/linkedin-api (404), pytrends (archived), snscrape (停更), elizaOS/agent-twitter-client (下架)

## ready-skills `last_verified: 2026-06`
- ericosiu/ai-marketing-skills (2.6k★): `git clone` + pip + cp (NOT npx) — marketing skill pack.
- indranilbanerjee/digital-marketing-pro (133★): GitHub clone (AEO/GEO skills).

## Discovery registries (find more)
smithery.ai (one-click) · glama.ai (largest) · mcp.so · pulsemcp.com (curated + traffic) ·
registry.modelcontextprotocol.io (official) · mcp.apify.com (3000+ actors).
