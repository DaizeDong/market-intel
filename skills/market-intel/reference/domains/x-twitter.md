# Domain: x-twitter

**Triage signals:** tweets, X/Twitter search, user/influencer analysis, viral tracking, 推特/X 舆情.

**Hard truth:** X killed anonymous scraping (login wall since 2024). Official free API is unusable;
snscrape and public Nitter instances are effectively dead. Choice = who absorbs the
account+proxy+login-wall cost.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **twitterapi.io** (+ its MCP) | ② resale | search, users, followers, replies, trends | `claude mcp list` → connected? else env key | gray-area, dep on provider |
| Apify tweet actors | ② resale | bulk historical, trends | apify MCP connected | pay-per-result |
| Bright Data X API/datasets | ② resale | enterprise, 22M+ historical | bright-data MCP | ~10x pricier, best SLA |
| twscrape (self-host) | ③ scrape | search/users/followers, account rotation | python lib installed | needs X cookies+proxy, ban risk |
| **d60/twikit** (4.4k★) + adhikasp/mcp-twikit | ③/④ self-host | read+write, search, DM, no API key | connected MCP or python lib | free; cookie/login, ban risk — **has ready MCP** |
| playwright MCP + browser-use | ④ browser | act-like-human: logged-in search, scrape rendered view | playwright connected | free, real session, best for fields API hides |
| Infatoshi/x-mcp, DataWhisker | ① official | full read+write incl. media | connected + X dev creds | needs Basic $200/mo+ |

**Default pick:** Free + good data → **twikit (+ adhikasp/mcp-twikit, ready MCP)** or
**playwright MCP** to act like a logged-in human (often richer than the stripped API). twitterapi.io
② only if you want the provider to absorb account/proxy upkeep. Official ① only when you must
post/write at scale. See `browser-automation.md` for the general browser route.

**Install guidance:** see `reference/volatile/pricing-install.md` → x-twitter. Remember a freshly
added MCP needs session reconnect before use.

**Avoid (dead):** official free API, snscrape (停更), public Nitter, elizaOS/agent-twitter-client
(原仓库下架，只剩 fork) — flag as L5/unavailable if relied on.
