# Domain: seo-keywords

**Triage signals:** keyword volume/difficulty, backlinks, competitor SEO, SERP rank tracking,
search traffic intel, 关键词/竞品SEO/排名.

> Most "pro SEO MCPs" don't charge for the MCP — they consume your underlying subscription/API
> quota. Real cost = the plan tier, not the MCP.

| source | route | capability | detect | cost note |
|---|---|---|---|---|
| **Google Search Console MCP** | ① free | your site's real clicks/impr/CTR/position | connected + Google OAuth | free, self-hosted;접 first |
| **DataForSEO MCP** | ② | keywords/SERP/backlinks/Trends, all engines | connected + login/pwd | $1 trial + free Sandbox; ~$0.0006/SERP |
| Ahrefs MCP (official) | ① | best backlink data (95 tools) | connected + paid sub | pricey; MCP interactive-only |
| Semrush One MCP | ① | full keyword/competitor/audit | connected + Pro+ sub | ~$299/mo; history = 5x units |
| SE Ranking MCP | ① | 160+ tools + 7 ready Claude Skills | connected + key | best pro-tier value, 14d trial 100k credits |
| SerpApi MCP | ② | multi-engine SERP, Trends | connected + key | free ~100/mo; pricey at scale |
| Google Ads Keyword Planner | ① free | real search volume + CPC | Google Ads dev token | free; easier via DataForSEO wrapper |

**Default pick:** Have a site → free GSC MCP first. External keyword/SERP/backlink cheap → DataForSEO
(Sandbox first). Pro coverage + Claude-friendly → SE Ranking. Deep backlinks → Ahrefs.

## ④ Browser/OSS route (free, self-host) — strong here
| repo | route | note |
|---|---|---|
| **searxng/searxng** (31k★) | ④ self-host | meta-search → JSON = private SerpApi, dozens of engines |
| **towfiqi/serpbear** (2k★) | ④ self-host | keyword rank tracker, replaces paid rank monitoring |
| deedy5/ddgs (2.7k★) | ④ | lightweight free web search lib, no key |
| flack0x/trendspyg / sdil87/trendspy | ④ | Google Trends after pytrends archived |
| playwright MCP | ④ | drive trends.google.com / SERP directly when no repo fits |

**Default (free route):** self-host **SearXNG** as a private SERP API + **serpbear** for rank
tracking — covers most paid-SERP needs at zero cost (needs proxies at high volume). Keep GSC ① for
your own site's real traffic (free, irreplaceable).

**Shaky (avoid for prod):** pytrends (archived, 429s), "free Ahrefs" scraper MCPs needing CAPTCHA
solvers. No official MCP: Moz, Majestic, Sitebulb.

**Install guidance:** `reference/volatile/pricing-install.md` → seo-keywords.
