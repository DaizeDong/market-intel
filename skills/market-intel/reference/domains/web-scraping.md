# Domain: web-scraping

**Triage signals:** general SERP, crawl a site, scrape JS-heavy page, break paywall/anti-bot,
extract structured data, 网页抓取/搜索基础设施.

**Layered stack, not one tool.** Built-in WebFetch runs no JS and uses your IP (easily blocked);
built-in WebSearch returns title+url only. Layer specialists on top.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **Tavily** / **Exa** | ② | search layer (semantic, date/domain filter) | mcp list / skill `exa-search` | Tavily AgentRank #1; Exa good for "recent" |
| **Firecrawl** | ② | JS-render scrape, crawl, JSON extract | skill `firecrawl` present | hosted stealth strong; self-host weak vs WAF |
| **Bright Data** | ② | Web Unlocker — beats Cloudflare/DataDome/CAPTCHA | bright-data MCP | strongest barrier-breaker; free 5k/mo |
| DataForSEO | ② | cheap large-scale SERP | connected | ~$0.0006/query, 1/10 of SerpApi |
| Apify | ② | 3000+ prebuilt actors (social/ecom/maps) | apify MCP | pin specific actors to avoid tool flood |
| Crawl4AI | ③ free | OSS self-host LLM crawler, auto anti-bot | docker MCP | zero cost if you self-host |

**Default architecture:** WebFetch (static/PDF fallback) + Tavily/Exa (search) + Firecrawl (JS
scrape) + Bright Data (hard targets) + DataForSEO (bulk SERP monitoring).

**Note:** firecrawl skill claims to take over all web ops — when both available, route web through
firecrawl but keep specialists for SERP/barrier work. Volatile pricing changes fast (Brave dropped
free tier, Exa raised prices) — verify before quoting.

**Install guidance:** `reference/volatile/pricing-install.md` → web-scraping.
