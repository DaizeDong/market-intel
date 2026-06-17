# Domain: web-scraping

**Triage signals:** general SERP, crawl a site, scrape JS-heavy page, break paywall/anti-bot,
extract structured data, 网页抓取/搜索基础设施.

**Layered stack, not one tool.** Built-in WebFetch runs no JS and uses your IP (easily blocked);
built-in WebSearch returns title+url only. Layer specialists on top.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **Tavily** / **Exa** | ② | search layer (semantic, date/domain filter) | mcp list / skill `exa-search` | Tavily AgentRank #1; Exa good for "recent" |
| **Firecrawl** | ② | JS-render scrape, crawl, JSON extract | skill `firecrawl` present | hosted stealth strong; self-host weak vs WAF |
| **Bright Data** | ② | Web Unlocker — beats Cloudflare/DataDome/CAPTCHA; unlocks Amazon/Taobao/Reddit | hosted HTTP MCP (verified 2026-06) | strongest barrier-breaker; **free 5k/mo Rapid, no card** |
| DataForSEO | ② | cheap large-scale SERP | connected | ~$0.0006/query, 1/10 of SerpApi |
| Apify | ② | 3000+ prebuilt actors (social/ecom/maps) | apify MCP | pin specific actors to avoid tool flood |
| Crawl4AI | ③ free | OSS self-host LLM crawler, auto anti-bot | docker MCP | zero cost if you self-host |
| **Patchright** (3.4k★) | ④ free | undetected-Playwright patch: passes Cloudflare/DataDome/Akamai/Kasada/F5 | `pip install patchright` / npm | free Apache-2.0; patches the browser fingerprint but needs a proxy for IP-reputation blocks (complements Bright Data) |
| **Bright Data DaaS** | brokerage | curated datasets — Amazon, LinkedIn, Twitter/X, Crunchbase, Walmart, eBay; pay-per-record, no scrape | hosted MCP + REST | **v1.3 brokerage tier** — the "I don't want to scrape, I want the data" abstraction; collapses 4-5 source juggling into one bill |
| **datarade marketplace** | brokerage | aggregator over 1000+ data providers, single contract | REST API | **v1.3 brokerage tier** — for niche or geo-specific datasets the big providers don't cover; pricing on request per dataset |

**Default architecture:** WebFetch (static/PDF fallback) + Tavily/Exa (search) + Firecrawl (JS
scrape) + Bright Data (hard targets) + DataForSEO (bulk SERP monitoring).

**Note:** firecrawl skill claims to take over all web ops — when both available, route web through
firecrawl but keep specialists for SERP/barrier work. Volatile pricing changes fast (Brave dropped
free tier, Exa raised prices) — verify before quoting.

**Real-run lesson (2026-06): for live e-commerce prices, skip firecrawl/WebFetch, go straight to
browser(④)/Bright Data.** Amazon product pages return HTTP 500 to firecrawl/WebFetch (anti-bot);
Taobao/Tmall hide the real per-SKU price behind a login wall; Reddit returns empty to web search.
**playwright (connected) read the real Amazon price in one shot; Bright Data Web Unlocker is the
scalable version.** Don't waste fan-out rounds on firecrawl for these — route to ④ first.

**Brokerage tier (v1.3-active, 2026-06-17 sweep).** P2 trigger fired (≥3 D-PRICE domains in 90d):
data-acquisition barriers across leadgen-crm / x-twitter / finance-markets are simultaneously
hardening. The brokerage tier is the answer — pay-per-record / pay-per-dataset, no scraping at all.
When the calculus is "I will burn engineer-weeks fighting CAPTCHAs and proxy bans, OR pay $X for a
clean dataset," and ④ feels like more work than payoff, reach for brokerage. Bright Data DaaS is the
broad-stroke pick; datarade marketplace for niche/geo-specific data.

**Install guidance:** `reference/volatile/pricing-install.md` → web-scraping.
