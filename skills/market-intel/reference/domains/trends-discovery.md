# Domain: trends-discovery

**Triage signals:** trends, Google Trends, Product Hunt, app store intel, startup/product
opportunity, news sentiment, alt-data signals, 趋势/选题/产品机会/舆情.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **GDELT MCP** | ① free | global news tone/events/entities, 100+ langs, 15-min | connected, no auth | zero cost sentiment首选 |
| **Product Hunt MCP** (jaipandya) | ① free | posts/topics/votes, new-launch tracking | connected + PH token | most mature impl |
| **Trends MCP** (trendsmcp.ai) | ② | 15+ platforms normalized + growth rate | connected + token | free 100/mo; best "acceleration signal" |
| SerpApi Google Trends | ② | reliable JSON, cross-region | connected + key | free 100/mo |
| Exploding Topics | ② | curated emerging topics + forecast | API (Business tier) | early-signal, no MCP |
| google-play-scraper / app-store-scraper (npm) | ③ free | app details/reviews/rankings | lib installed | free, no key |
| mobile-store-scraper-mcp | ③ free | both stores details/reviews/similar | self-host | free MCP |
| Sensor Tower MCP | ② | download/revenue estimates | connected + ST token | needs pricey ST sub |
| Finnhub MCP | ① | news + Reddit/Twitter sentiment + congress trades | connected + free key | scarce alt-data, free 60/min |
| idea-reality-MCP | ① free | scan GitHub/HN/npm/PyPI/PH → reality_signal 0-100 | self-host | "is this idea saturated" |

**Default pick:** Trends → Trends MCP (or SerpApi for clean JSON, pytrends if free-but-shaky).
Products → Product Hunt MCP + idea-reality-MCP. News/sentiment → GDELT MCP (free) + Finnhub.
Selling → Trends MCP (TikTok leads Amazon 2–4 weeks = opportunity window).

**Notes:** pytrends = relative values, no absolute volume, 429-prone. Composio Jungle Scout MCP being
deprecated. data.ai has no dedicated MCP.

**Install guidance:** `reference/volatile/pricing-install.md` → trends-discovery.
