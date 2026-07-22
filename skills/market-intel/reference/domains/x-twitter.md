# Domain: x-twitter

**Triage signals:** tweets, X/Twitter search, user/influencer analysis, viral tracking, 推特/X 舆情.

> **Real-run lesson (2026-06): X is a LOW-signal source for consumer / non-tech demand research.**
> For e.g. auto-modding/patio-heater, X "Top" search was nearly empty; the real demand discourse lives on
> 抖音/小红书/B站/懂车帝 (China) and Reddit/vertical forums (US). Route consumer-demand questions there
> (web/Bright Data), not X. X earns its keep for **tech/crypto/startup/founder** discourse, breaking
> news, and named-account/influencer tracking, use twitterapi for those, not for "do people buy X".

**Hard truth:** X killed anonymous scraping (login wall since 2024). Official free API is unusable;
snscrape and public Nitter instances are effectively dead. Choice = who absorbs the
account+proxy+login-wall cost.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **twitterapi.io** (+ its MCP) | ② resale | search, users, followers, replies, trends | `claude mcp list` → connected? else env key | gray-area, dep on provider |
| Apify tweet actors | ② resale | bulk historical, trends | apify MCP connected | pay-per-result |
| Bright Data X API/datasets | ② resale | enterprise, 22M+ historical | bright-data MCP | ~10x pricier, best SLA |
| **vladkens/twscrape** (2.5k★) | ③ scrape | search/users/followers, account rotation | python lib installed | needs X cookies+proxy, ban risk; very active (2026-06), pin the `vladkens/` repo |
| **d60/twikit** (4.5k★) + adhikasp/mcp-twikit (235★) | ③/④ self-host | read+write, search, DM, no API key | connected MCP or python lib | free; cookie/login, ban risk. ⚠ twikit itself hasn't been pushed since 2026-03 (4.5mo, 4.6k★ at last gh-api check) and mcp-twikit since 2025-03 (16+mo), functionally re-test against current X before next `## Last verified` bump, no fresher free③④ alternative surfaced this sweep |
| playwright MCP + browser-use | ④ browser | act-like-human: logged-in search, scrape rendered view | playwright connected | free, real session, best for fields API hides |
| Infatoshi/x-mcp, DataWhisker | ① official | full read+write incl. media | connected + X dev creds | needs Basic $200/mo+ |
| **FxEmbed** (4.8k★) fka FxTwitter | ② free / ③ self-host | resolve ONE post/thread as JSON (text+media+metrics), no key | plain GET, no `claude mcp` entry | read-one only (no search); public-instance uptime + ToS gray, self-host on CF Workers to own it |

**Default pick:** Free + good data → **twikit (+ adhikasp/mcp-twikit, ready MCP)** or
**playwright MCP** to act like a logged-in human (often richer than the stripped API). twitterapi.io
② only if you want the provider to absorb account/proxy upkeep. Official ① only when you must
post/write at scale. See `browser-automation.md` for the general browser route.

**Install guidance:** see `reference/volatile/pricing-install.md` → x-twitter. Remember a freshly
added MCP needs session reconnect before use.

**Avoid (dead):** (all verified 2026-06)
- **X official FREE API**, never offered usable read/search (write-only ~1,500 posts/mo); X moved to
  default pay-per-use **2026-02** and **closed the free tier to new signups**. The free read capability
  the matrix wants is effectively dead, use twikit ④ or twitterapi.io ② instead.
- **snscrape** (`JustAnotherArchivist/snscrape`), **dead for X specifically**: dev paused ~2023, the
  X HTML/JSON endpoints it used are gone (repo still exists, non-X modules may work). Successor =
  twscrape / twikit. Flag L5 if a plan relies on it for X.
- **Public Nitter instances**, public ecosystem **collapsed late-2024** after X's mandatory-auth +
  rate-limits; nitter.net decommissioned. Self-hosting still works but now needs real X session
  tokens. Treat public-instance scraping as unavailable; use Twiiit only to find a flaky live one.
- elizaOS/agent-twitter-client (原仓库下架，只剩 fork), flag as L5/unavailable if relied on.
