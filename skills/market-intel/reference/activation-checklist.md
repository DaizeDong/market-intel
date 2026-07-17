# market-intel, 全工具激活清单 (activation checklist)

> 逐项配置到「可用」。**用法**：从上往下做（免费/快的在前）；每激活一个，跑 `python
> tools/console.py status` 看覆盖率上升即核验成功（可用性是探出来的，不是声称的）。详细 key 源/
> 免费档/步骤见 [`activation-recipes.md`](activation-recipes.md)；逐工具细节见 `tools/<slug>.md`。
> 不必全配,每个域配够好覆盖即可；`needs-deploy`/repo-dead 多为墓碑，核验后多半跳过。

## Last verified: 2026-06

**当前可用 37/168。** 待激活 131，按类别：
- **NEEDS KEY (free or paid -- see activation-recipes.md for cost/free-tier)**, 50
- **COLD MCP (configured but not connected)**, 34
- **NEEDS INSTALL (no key)**, 47

> 优先级提示：先做 `activation-recipes.md` 的「30 分钟清单」(FRED/Tavily/Firecrawl/Etherscan/Hunter，全免费)，再按需展开下表。★ = 域 top pick（最值得先激活）。

## NEEDS KEY (free or paid -- see activation-recipes.md for cost/free-tier)

### content-cms  (3)
- [ ] ★ **Sanity hosted MCP** (`sanity-mcp`), get a key (see activation-recipes.md / tools/sanity-mcp.md) -> `python tools/console.py connect sanity-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Notion hosted MCP** (`notion-mcp`), get a key (see activation-recipes.md / tools/notion-mcp.md) -> `python tools/console.py connect notion-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Strapi 5 native MCP** (`strapi-mcp`), get a key (see activation-recipes.md / tools/strapi-mcp.md) -> `python tools/console.py connect strapi-mcp` -> fill key -> `/mcp` reconnect

### crypto-defi  (5)
- [ ] ★ **Etherscan MCP** (`etherscan-mcp`), get a key (see activation-recipes.md / tools/etherscan-mcp.md) -> `python tools/console.py connect etherscan-mcp` -> fill key -> `/mcp` reconnect
- [ ] **CoinMarketCap MCP** (`coinmarketcap-mcp`), get a key (see activation-recipes.md / tools/coinmarketcap-mcp.md) -> `python tools/console.py connect coinmarketcap-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Covalent / GoldRush** (`covalent`), get a key (see activation-recipes.md / tools/covalent.md) -> `python tools/console.py connect covalent` -> fill key -> `/mcp` reconnect
- [ ] **Moralis** (`moralis`), get a key (see activation-recipes.md / tools/moralis.md) -> `python tools/console.py connect moralis` -> fill key -> `/mcp` reconnect
- [ ] **Nansen** (`nansen`), get a key (see activation-recipes.md / tools/nansen.md) -> `python tools/console.py connect nansen` -> fill key -> `/mcp` reconnect

### ecommerce-arbitrage  (6)
- [ ] **Amazon SP-API (private app)** (`amazon-sp-api`), get a key (see activation-recipes.md / tools/amazon-sp-api.md) -> `python tools/console.py connect amazon-sp-api` -> fill key -> `/mcp` reconnect
- [ ] **eBay Browse/Finding API** (`ebay-api`), get a key (see activation-recipes.md / tools/ebay-api.md) -> `python tools/console.py connect ebay-api` -> fill key -> `/mcp` reconnect
- [ ] **Oxylabs (ecom scrape + MCP)** (`oxylabs`), get a key (see activation-recipes.md / tools/oxylabs.md) -> `python tools/console.py connect oxylabs` -> fill key -> `/mcp` reconnect
- [ ] **PriceAPI** (`priceapi`), get a key (see activation-recipes.md / tools/priceapi.md) -> `python tools/console.py connect priceapi` -> fill key -> `/mcp` reconnect
- [ ] **Rainforest API** (`rainforest-api`), get a key (see activation-recipes.md / tools/rainforest-api.md) -> `python tools/console.py connect rainforest-api` -> fill key -> `/mcp` reconnect
- [ ] **Shopify Storefront MCP** (`shopify-storefront-mcp`), get a key (see activation-recipes.md / tools/shopify-storefront-mcp.md) -> `python tools/console.py connect shopify-storefront-mcp` -> fill key -> `/mcp` reconnect

### finance-markets  (5)
- [ ] **Financial Modeling Prep (FMP)** (`fmp`), get a key (see activation-recipes.md / tools/fmp.md) -> `python tools/console.py connect fmp` -> fill key -> `/mcp` reconnect
- [ ] **Polygon.io (now Massive)** (`polygon`), get a key (see activation-recipes.md / tools/polygon.md) -> `python tools/console.py connect polygon` -> fill key -> `/mcp` reconnect
- [ ] **Polygon (Massive), auto (install/auth/usage companion)** (`polygon.auto`), get a key (see activation-recipes.md / tools/polygon.auto.md) -> `python tools/console.py connect polygon.auto` -> fill key -> `/mcp` reconnect
- [ ] **Tradier MCP** (`tradier-mcp`), get a key (see activation-recipes.md / tools/tradier-mcp.md) -> `python tools/console.py connect tradier-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Unusual Whales MCP** (`unusual-whales`), get a key (see activation-recipes.md / tools/unusual-whales.md) -> `python tools/console.py connect unusual-whales` -> fill key -> `/mcp` reconnect

### frontier-research  (1)
- [ ] ★ **Hugging Face, Daily Papers + Hub API + official MCP** (`huggingface`), get a key (see activation-recipes.md / tools/huggingface.md) -> `python tools/console.py connect huggingface` -> fill key -> `/mcp` reconnect

### leadgen-crm  (11)
- [ ] ★ **Apollo.io (native connector)** (`apollo`), get a key (see activation-recipes.md / tools/apollo.md) -> `python tools/console.py connect apollo` -> fill key -> `/mcp` reconnect
- [ ] ★ **Hunter.io (official MCP)** (`hunter`), get a key (see activation-recipes.md / tools/hunter.md) -> `python tools/console.py connect hunter` -> fill key -> `/mcp` reconnect
- [ ] **Attio official MCP** (`attio-mcp`), get a key (see activation-recipes.md / tools/attio-mcp.md) -> `python tools/console.py connect attio-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Clay (+ MCP)** (`clay`), get a key (see activation-recipes.md / tools/clay.md) -> `python tools/console.py connect clay` -> fill key -> `/mcp` reconnect
- [ ] **HubSpot official MCP** (`hubspot-mcp`), get a key (see activation-recipes.md / tools/hubspot-mcp.md) -> `python tools/console.py connect hubspot-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Instantly.ai MCP (official hosted)** (`instantly-mcp`), get a key (see activation-recipes.md / tools/instantly-mcp.md) -> `python tools/console.py connect instantly-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Outscraper Google Maps** (`outscraper-google-maps`), get a key (see activation-recipes.md / tools/outscraper-google-maps.md) -> `python tools/console.py connect outscraper-google-maps` -> fill key -> `/mcp` reconnect
- [ ] **Salesforce official MCP** (`salesforce-mcp`), get a key (see activation-recipes.md / tools/salesforce-mcp.md) -> `python tools/console.py connect salesforce-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Smartlead MCP (LeadMagic)** (`smartlead-mcp`), get a key (see activation-recipes.md / tools/smartlead-mcp.md) -> `python tools/console.py connect smartlead-mcp` -> fill key -> `/mcp` reconnect
- [ ] **ZeroBounce (official MCP)** (`zerobounce`), get a key (see activation-recipes.md / tools/zerobounce.md) -> `python tools/console.py connect zerobounce` -> fill key -> `/mcp` reconnect
- [ ] **ZoomInfo / Lusha** (`zoominfo-lusha`), get a key (see activation-recipes.md / tools/zoominfo-lusha.md) -> `python tools/console.py connect zoominfo-lusha` -> fill key -> `/mcp` reconnect

### ready-skills  (1)
- [ ] **Anthropic official Marketing plugin** (`anthropic-marketing-plugin`), get a key (see activation-recipes.md / tools/anthropic-marketing-plugin.md) -> `python tools/console.py connect anthropic-marketing-plugin` -> fill key -> `/mcp` reconnect

### seo-keywords  (5)
- [ ] **Ahrefs official MCP** (`ahrefs-mcp`), get a key (see activation-recipes.md / tools/ahrefs-mcp.md) -> `python tools/console.py connect ahrefs-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Google Ads Keyword Planner** (`google-ads-keyword-planner`), get a key (see activation-recipes.md / tools/google-ads-keyword-planner.md) -> `python tools/console.py connect google-ads-keyword-planner` -> fill key -> `/mcp` reconnect
- [ ] **SE Ranking MCP** (`se-ranking-mcp`), get a key (see activation-recipes.md / tools/se-ranking-mcp.md) -> `python tools/console.py connect se-ranking-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Semrush One MCP** (`semrush-mcp`), get a key (see activation-recipes.md / tools/semrush-mcp.md) -> `python tools/console.py connect semrush-mcp` -> fill key -> `/mcp` reconnect
- [ ] **SerpApi (MCP)** (`serpapi`), get a key (see activation-recipes.md / tools/serpapi.md) -> `python tools/console.py connect serpapi` -> fill key -> `/mcp` reconnect

### social-publishing  (5)
- [ ] ★ **Blotato (+ MCP)** (`blotato`), get a key (see activation-recipes.md / tools/blotato.md) -> `python tools/console.py connect blotato` -> fill key -> `/mcp` reconnect
- [ ] ★ **Buffer API (+ MCP)** (`buffer`), get a key (see activation-recipes.md / tools/buffer.md) -> `python tools/console.py connect buffer` -> fill key -> `/mcp` reconnect
- [ ] **Ayrshare (+ MCP)** (`ayrshare`), get a key (see activation-recipes.md / tools/ayrshare.md) -> `python tools/console.py connect ayrshare` -> fill key -> `/mcp` reconnect
- [ ] **OpenTweet (hosted)** (`opentweet`), get a key (see activation-recipes.md / tools/opentweet.md) -> `python tools/console.py connect opentweet` -> fill key -> `/mcp` reconnect
- [ ] **Typefully API v2** (`typefully`), get a key (see activation-recipes.md / tools/typefully.md) -> `python tools/console.py connect typefully` -> fill key -> `/mcp` reconnect

### trends-discovery  (3)
- [ ] ★ **GDELT MCP** (`gdelt-mcp`), get a key (see activation-recipes.md / tools/gdelt-mcp.md) -> `python tools/console.py connect gdelt-mcp` -> fill key -> `/mcp` reconnect
- [ ] **Exploding Topics** (`exploding-topics`), get a key (see activation-recipes.md / tools/exploding-topics.md) -> `python tools/console.py connect exploding-topics` -> fill key -> `/mcp` reconnect
- [ ] **Sensor Tower MCP** (`sensor-tower-mcp`), get a key (see activation-recipes.md / tools/sensor-tower-mcp.md) -> `python tools/console.py connect sensor-tower-mcp` -> fill key -> `/mcp` reconnect

### web-scraping  (4)
- [ ] ★ **Exa (search; skill `exa-search`)** (`exa`), get a key (see activation-recipes.md / tools/exa.md) -> `python tools/console.py connect exa` -> fill key -> `/mcp` reconnect
- [ ] ★ **Tavily (search MCP)** (`tavily`), get a key (see activation-recipes.md / tools/tavily.md) -> `python tools/console.py connect tavily` -> fill key -> `/mcp` reconnect
- [ ] **Apify (3000+ actors + MCP)** (`apify`), get a key (see activation-recipes.md / tools/apify.md) -> `python tools/console.py connect apify` -> fill key -> `/mcp` reconnect
- [ ] **Apify, auto (install/auth/usage companion)** (`apify.auto`), get a key (see activation-recipes.md / tools/apify.auto.md) -> `python tools/console.py connect apify.auto` -> fill key -> `/mcp` reconnect

### x-twitter  (1)
- [ ] ★ **twitterapi.io (+ native MCP)** (`twitterapi-io`), get a key (see activation-recipes.md / tools/twitterapi-io.md) -> `python tools/console.py connect twitterapi-io` -> fill key -> `/mcp` reconnect

## COLD MCP (configured but not connected)

### browser-automation  (1)
- [ ] ★ **playwright MCP** (`playwright-mcp`), `python tools/console.py connect playwright-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### content-cms  (5)
- [ ] ★ **WordPress MCP (WordPress/mcp-adapter, official)** (`wordpress-mcp`), `python tools/console.py connect wordpress-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **Contentful MCP (official)** (`contentful-mcp`), `python tools/console.py connect contentful-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **directus/mcp** (`directus-mcp`), `python tools/console.py connect directus-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **Ghost MCP (MFYDev/ghost-mcp)** (`ghost-mcp`), `python tools/console.py connect ghost-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **webflow/mcp-server** (`webflow-mcp`), `python tools/console.py connect webflow-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### crypto-defi  (2)
- [ ] **Kukapay/funding-rates-mcp** (`funding-rates-mcp`), `python tools/console.py connect funding-rates-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **Hummingbot (+ MCP)** (`hummingbot`), `python tools/console.py connect hummingbot` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### ecommerce-arbitrage  (1)
- [ ] ★ **Keepa (+ Keepa MCP)** (`keepa`), `python tools/console.py connect keepa` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### finance-markets  (3)
- [ ] ★ **stefanoamorelli/fred-mcp-server** (`fred-mcp`), `python tools/console.py connect fred-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **Alpaca MCP (alpacahq/alpaca-mcp-server)** (`alpaca-mcp`), `python tools/console.py connect alpaca-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **Finnhub (cfdude/mcp-finnhub)** (`finnhub`), `python tools/console.py connect finnhub` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### frontier-research  (2)
- [ ] ★ **arXiv API (+ blazickjp/arxiv-mcp-server)** (`arxiv`), `python tools/console.py connect arxiv` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **openags/paper-search-mcp** (`paper-search-mcp`), `python tools/console.py connect paper-search-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### reddit-community  (6)
- [ ] ★ **karanb192/reddit-mcp-buddy** (`reddit-mcp-buddy`), `python tools/console.py connect reddit-mcp-buddy` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **elyxlz/discord-mcp** (`discord-mcp`), `python tools/console.py connect discord-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **GridfireAI/reddit-mcp  `D-SUPERSEDED`** (`reddit-mcp`), `python tools/console.py connect reddit-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **king-of-the-grackles/reddit-research-mcp** (`reddit-research-mcp`), `python tools/console.py connect reddit-research-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **SaseQ/discord-mcp** (`saseq-discord-mcp`), `python tools/console.py connect saseq-discord-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **midodimori/stack-overflow-mcp** (`stack-overflow-mcp`), `python tools/console.py connect stack-overflow-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### seo-keywords  (1)
- [ ] ★ **ahonn/mcp-server-gsc (Google Search Console)** (`gsc-mcp`), `python tools/console.py connect gsc-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### social-publishing  (4)
- [ ] ★ **Postiz (OSS, built-in MCP)** (`postiz`), `python tools/console.py connect postiz` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] ★ **xpzouying/xiaohongshu-mcp (小红书 MCP)** (`xiaohongshu-mcp`), `python tools/console.py connect xiaohongshu-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **EnesCinr/twitter-mcp (X single)** (`enescinar-twitter-mcp`), `python tools/console.py connect enescinar-twitter-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **stickerdaniel/linkedin-mcp-server** (`linkedin-mcp-server`), `python tools/console.py connect linkedin-mcp-server` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### trends-discovery  (5)
- [ ] ★ **jaipandya/producthunt-mcp-server (Product Hunt MCP)** (`product-hunt-mcp`), `python tools/console.py connect product-hunt-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **jmanek/google-news-trends-mcp** (`google-news-trends-mcp`), `python tools/console.py connect google-news-trends-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **idea-reality-MCP** (`idea-reality-mcp`), `python tools/console.py connect idea-reality-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **mobile-store-scraper-mcp** (`mobile-store-scraper-mcp`), `python tools/console.py connect mobile-store-scraper-mcp` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] **claude-world/trend-pulse** (`trend-pulse`), `python tools/console.py connect trend-pulse` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### web-scraping  (3)
- [ ] ★ **Bright Data (Web Unlocker + datasets + MCP)** (`brightdata`), `python tools/console.py connect brightdata` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] ★ **DataForSEO (MCP)** (`dataforseo`), `python tools/console.py connect dataforseo` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect
- [ ] ★ **Firecrawl (skill `firecrawl`)** (`firecrawl`), `python tools/console.py connect firecrawl` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

### x-twitter  (1)
- [ ] **X official API (Infatoshi/x-mcp etc.)** (`x-official-api`), `python tools/console.py connect x-official-api` -> paste claude.json snippet (+ key if any) -> `/mcp` reconnect

## NEEDS INSTALL (no key)

### browser-automation  (12)
- [ ] ★ **browser-use/browser-use** (`browser-use`), install per tools/browser-use.md (pip/uvx/git/docker) -- no key needed
- [ ] **vercel-labs/agent-browser** (`agent-browser`), install per tools/agent-browser.md (pip/uvx/git/docker) -- no key needed
- [ ] **jo-inc/camofox-browser** (`camofox-browser`), install per tools/camofox-browser.md (pip/uvx/git/docker) -- no key needed
- [ ] **daijro/camoufox** (`camoufox`), install per tools/camoufox.md (pip/uvx/git/docker) -- no key needed
- [ ] **apify/crawlee** (`crawlee`), install per tools/crawlee.md (pip/uvx/git/docker) -- no key needed
- [ ] **NanmiCoder/MediaCrawler** (`mediacrawler`), install per tools/mediacrawler.md (pip/uvx/git/docker) -- no key needed
- [ ] **ultrafunkamsterdam/nodriver** (`nodriver`), install per tools/nodriver.md (pip/uvx/git/docker) -- no key needed
- [ ] **ScrapeGraphAI/Scrapegraph-ai** (`scrapegraph-ai`), install per tools/scrapegraph-ai.md (pip/uvx/git/docker) -- no key needed
- [ ] **Skyvern-AI/skyvern** (`skyvern`), install per tools/skyvern.md (pip/uvx/git/docker) -- no key needed
- [ ] **browserbase/stagehand** (`stagehand`), install per tools/stagehand.md (pip/uvx/git/docker) -- no key needed
- [ ] **steel-dev/steel-browser** (`steel-browser`), install per tools/steel-browser.md (pip/uvx/git/docker) -- no key needed
- [ ] **dataabc/weibo-crawler** (`weibo-crawler`), install per tools/weibo-crawler.md (pip/uvx/git/docker) -- no key needed

### content-cms  (1)
- [ ] **Pipepost (multi-platform)** (`pipepost`), install per tools/pipepost.md (pip/uvx/git/docker) -- no key needed

### ecommerce-arbitrage  (2)
- [ ] **omkarcloud/amazon-scraper** (`amazon-scraper`), install per tools/amazon-scraper.md (pip/uvx/git/docker) -- no key needed
- [ ] **Cybrarist/Discount-Bandit** (`discount-bandit`), install per tools/discount-bandit.md (pip/uvx/git/docker) -- no key needed

### finance-markets  (1)
- [ ] **Twelve Data** (`twelve-data`), install per tools/twelve-data.md (pip/uvx/git/docker) -- no key needed

### frontier-research  (1)
- [ ] **OpenReview API** (`openreview`), install per tools/openreview.md (pip/uvx/git/docker) -- no key needed

### leadgen-crm  (5)
- [ ] ★ **gosom/google-maps-scraper** (`gosom-google-maps-scraper`), install per tools/gosom-google-maps-scraper.md (pip/uvx/git/docker) -- no key needed
- [ ] **joeyism/linkedin_scraper** (`linkedin-scraper`), install per tools/linkedin-scraper.md (pip/uvx/git/docker) -- no key needed
- [ ] **omkarcloud/google-maps-scraper** (`omkarcloud-google-maps-scraper`), install per tools/omkarcloud-google-maps-scraper.md (pip/uvx/git/docker) -- no key needed
- [ ] **People Data Labs** (`people-data-labs`), install per tools/people-data-labs.md (pip/uvx/git/docker) -- no key needed
- [ ] **cullenwatson/StaffSpy** (`staffspy`), install per tools/staffspy.md (pip/uvx/git/docker) -- no key needed

### ready-skills  (11)
- [ ] ★ **ishwarjha/claude-marketing-research-skill** (`claude-marketing-research-skill`), install per tools/claude-marketing-research-skill.md (pip/uvx/git/docker) -- no key needed
- [ ] ★ **AgricIDaniel/claude-seo** (`claude-seo`), install per tools/claude-seo.md (pip/uvx/git/docker) -- no key needed
- [ ] ★ **coreyhaines31/marketingskills** (`marketingskills`), install per tools/marketingskills.md (pip/uvx/git/docker) -- no key needed
- [ ] **Imbad0202/academic-research-skills** (`academic-research-skills`), install per tools/academic-research-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **ericosiu/ai-marketing-skills** (`ai-marketing-skills`), install per tools/ai-marketing-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **alirezarezvani/claude-skills** (`alirezarezvani-claude-skills`), install per tools/alirezarezvani-claude-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **sickn33/antigravity-awesome-skills** (`antigravity-awesome-skills`), install per tools/antigravity-awesome-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **Eronred/aso-skills** (`aso-skills`), install per tools/aso-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **ComposioHQ/awesome-claude-skills** (`awesome-claude-skills`), install per tools/awesome-claude-skills.md (pip/uvx/git/docker) -- no key needed
- [ ] **indranilbanerjee/digital-marketing-pro** (`digital-marketing-pro`), install per tools/digital-marketing-pro.md (pip/uvx/git/docker) -- no key needed
- [ ] **gtmagents/gtm-agents** (`gtm-agents`), install per tools/gtm-agents.md (pip/uvx/git/docker) -- no key needed

### reddit-community  (2)
- [ ] **ArthurHeitmann/arctic_shift** (`arctic-shift`), install per tools/arctic-shift.md (pip/uvx/git/docker) -- no key needed
- [ ] **dancolta/subscope** (`subscope`), install per tools/subscope.md (pip/uvx/git/docker) -- no key needed

### seo-keywords  (3)
- [ ] ★ **searxng/searxng** (`searxng`), install per tools/searxng.md (pip/uvx/git/docker) -- no key needed
- [ ] ★ **towfiqi/serpbear** (`serpbear`), install per tools/serpbear.md (pip/uvx/git/docker) -- no key needed
- [ ] **respectlytics/respectaso** (`respectaso`), install per tools/respectaso.md (pip/uvx/git/docker) -- no key needed

### social-publishing  (6)
- [ ] **subzeroid/instagrapi** (`instagrapi`), install per tools/instagrapi.md (pip/uvx/git/docker) -- no key needed
- [ ] **instaloader/instaloader** (`instaloader`), install per tools/instaloader.md (pip/uvx/git/docker) -- no key needed
- [ ] **Mixpost (OSS)** (`mixpost`), install per tools/mixpost.md (pip/uvx/git/docker) -- no key needed
- [ ] **gitroomhq/postiz-agent** (`postiz-agent`), install per tools/postiz-agent.md (pip/uvx/git/docker) -- no key needed
- [ ] **langchain-ai/social-media-agent** (`social-media-agent`), install per tools/social-media-agent.md (pip/uvx/git/docker) -- no key needed
- [ ] **davidteather/TikTok-Api** (`tiktok-api`), install per tools/tiktok-api.md (pip/uvx/git/docker) -- no key needed

### web-scraping  (1)
- [ ] ★ **unclecode/crawl4ai** (`crawl4ai`), install per tools/crawl4ai.md (pip/uvx/git/docker) -- no key needed

### x-twitter  (2)
- [ ] ★ **d60/twikit (+ adhikasp/mcp-twikit)** (`twikit`), install per tools/twikit.md (pip/uvx/git/docker) -- no key needed
- [ ] **twscrape** (`twscrape`), install per tools/twscrape.md (pip/uvx/git/docker) -- no key needed

