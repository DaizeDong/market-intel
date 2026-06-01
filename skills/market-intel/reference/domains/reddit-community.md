# Domain: reddit-community

**Triage signals:** Reddit, Hacker News, Discord, Quora, Stack Exchange, forums, pain-point mining,
社区/论坛调研, 用户需求挖掘.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **erithwik/mcp-hn** (HN) | ① free | top/new/ask/show, search, comments | mcp list / `uvx mcp-hn` | none — Algolia API, no key |
| **GridfireAI/reddit-mcp** | ① official | submissions, search, subreddit (read-only) | connected + Reddit client id/secret | Reddit API rate limits |
| Apify (Quora/forums/Reddit monitor) | ② resale | Quora, forums, brand monitor + sentiment | apify MCP | pay-per-use; SSE deprecated, use HTTP |
| midodimori stack-overflow-mcp | ① free | SE search/answers | connected + SE key (raises 300→10k/day) | — |
| elyxlz/discord-mcp | ④ browser | read/scrape via your user session | self-host | ⚠ violates Discord ToS, ban risk |

**Default pick:** mcp-hn (free, zero auth) for HN; GridfireAI/reddit-mcp (official, read-only) for
Reddit. Cross-platform keyword monitoring → Syften (paid, MCP) or free F5Bot.

**Watch:** Reddit API tightening — GummySearch shuts down 2026-11. Prefer official-API routes over
unauthorized scrapers. Discord/Quora scraping = ToS gray zone.

**Install guidance:** `reference/volatile/pricing-install.md` → reddit-community.
