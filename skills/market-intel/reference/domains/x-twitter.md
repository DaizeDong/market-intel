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
| Infatoshi/x-mcp, DataWhisker | ① official | full read+write incl. media | connected + X dev creds | needs Basic $200/mo+ |

**Default pick:** twitterapi.io for read research (cheapest, provider absorbs barrier, has .edu
discount). twscrape if zero budget + can supply accounts. Official only when you must post/write.

**Install guidance:** see `reference/volatile/pricing-install.md` → x-twitter. Remember a freshly
added MCP needs session reconnect before use.

**Avoid:** official free API, snscrape, public Nitter — flag as L5/unavailable if relied on.
