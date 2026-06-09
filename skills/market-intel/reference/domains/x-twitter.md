# Domain: x-twitter

**Triage signals:** tweets, X/Twitter search, user/influencer analysis, viral tracking, 推特/X 舆情.

> **Real-run lesson (2026-06): X is a LOW-signal source for consumer / non-tech demand research.**
> For e.g. auto-modding/patio-heater, X "Top" search was nearly empty; the real demand discourse lives on
> 抖音/小红书/B站/懂车帝 (China) and Reddit/vertical forums (US). Route consumer-demand questions there
> (web/Bright Data), not X. X earns its keep for **tech/crypto/startup/founder** discourse, breaking
> news, and named-account/influencer tracking — use twitterapi for those, not for "do people buy X".

**Hard truth:** X killed anonymous scraping (login wall since 2024). Official free API is unusable;
snscrape and public Nitter instances are effectively dead. Choice = who absorbs the
account+proxy+login-wall cost.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **twitterapi.io** (+ its MCP) | ② resale | search, users, followers, replies, trends | `claude mcp list` → connected? else env key | gray-area, dep on provider |
| Apify tweet actors | ② resale | bulk historical, trends | apify MCP connected | pay-per-result |
| Bright Data X API/datasets | ② resale | enterprise, 22M+ historical | bright-data MCP | ~10x pricier, best SLA |
| **vladkens/twscrape** (2.5k★) | ③ scrape | search/users/followers, account rotation | python lib installed | needs X cookies+proxy, ban risk; very active (2026-06) — pin the `vladkens/` repo |
| **d60/twikit** (4.5k★) + adhikasp/mcp-twikit (235★) | ③/④ self-host | read+write, search, DM, no API key | connected MCP or python lib | free; cookie/login, ban risk — ready MCP but ⚠ mcp-twikit stale (2025-03); the lib is the maintained part |
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
