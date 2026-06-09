# Commercial source index (thin)

One line per domain. At triage, match the topic to 1–N domains, then read ONLY the matched
shard(s) in `domains/`. Do not read shards you didn't match.

| domain | triage signals | top pick (barrier route) | shard |
|---|---|---|---|
| x-twitter | tweets, X sentiment, influencer, viral, 推特舆情 | twitterapi.io ② resale | `domains/x-twitter.md` |
| reddit-community | Reddit/HN/Discord/forum pain points, 社区调研 | HN MCP ① free · Reddit API ① | `domains/reddit-community.md` |
| web-scraping | general SERP, crawl, JS site, break paywall, 抓取 | Tavily/Exa + Firecrawl + Bright Data | `domains/web-scraping.md` |
| ecommerce-arbitrage | Amazon/eBay price, BSR, retail arbitrage, 选品比价 | Keepa ① official | `domains/ecommerce-arbitrage.md` |
| finance-markets | stocks, options, fundamentals, SEC, macro, 股票 | SEC EDGAR + FRED ① free | `domains/finance-markets.md` |
| crypto-defi | crypto price, on-chain, DEX, funding rate, MEV, 套利 | CoinGecko ① + ccxt | `domains/crypto-defi.md` |
| seo-keywords | keyword volume, backlinks, competitor SEO, SERP rank | GSC ① free + DataForSEO ② | `domains/seo-keywords.md` |
| social-publishing | auto-post/schedule X/LinkedIn/multi-platform, 发帖 | Buffer ① free-tier · Postiz OSS | `domains/social-publishing.md` |
| content-cms | blog publish to WordPress/Ghost/Notion/Sanity, 发博客 | Sanity/WordPress MCP ① | `domains/content-cms.md` |
| leadgen-crm | B2B leads, email find, company intel, CRM, 获客 | Apollo.io ① + Hunter ① | `domains/leadgen-crm.md` |
| trends-discovery | Google Trends, Product Hunt, app store, 趋势/选题 | GDELT + Product Hunt MCP ① free | `domains/trends-discovery.md` |
| frontier-research | AI/ML papers, arXiv, SOTA, new models, conference, citations, 论文/前沿研究 | arXiv API + HF Daily Papers ① free | `domains/frontier-research.md` |
| ready-skills | "is there a ready skill for marketing/SEO/research" | coreyhaines31/marketingskills | `domains/ready-skills.md` |
| **browser-automation** | API too costly/walled, want real-browser "act like human", free | playwright MCP + browser-use/crawl4ai | `domains/browser-automation.md` |

Barrier-route legend (see each shard for detail):
① official API — compliant, often paid/limited, no ban risk
② resale API — provider absorbs the barrier, cheap pay-per-use, gray-area
③ self-host scrape (reverse-engineered API) — free, you supply accounts+proxies, ban risk
④ **browser automation / act-like-human** — real logged-in browser (playwright MCP + OSS repos);
   FIRST-CLASS, not last resort. Often **richer data** (rendered/logged-in view, fields APIs hide)
   at zero API cost. Cost = proxies at scale; most platform scraping violates ToS (ban risk).
   When a topic's official/resale source is paid or quota-capped, check route ④ before paying.
