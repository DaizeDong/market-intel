# Domain: reddit-community

**Triage signals:** Reddit, Hacker News, Discord, Quora, Stack Exchange, forums, pain-point mining,
社区/论坛调研, 用户需求挖掘.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **erithwik/mcp-hn** (HN) | ① free | top/new/ask/show, search, comments | mcp list / `uvx mcp-hn` | none — Algolia API, no key |
| **karanb192/reddit-mcp-buddy** (702★) | ① official | browse/search/post-details/user-analysis; zero-setup anon (10/min) → app-id (60) → login (100) tiers | `npx -y reddit-mcp-buddy` | free; anon tier needs no creds — **new top pick** |
| GridfireAI/reddit-mcp | ① official | submissions, search, subreddit (read-only) | connected + Reddit client id/secret | **D-SUPERSEDED** by reddit-mcp-buddy (stale 2025-03, 18★) — kept as minimal fallback |
| **king-of-the-grackles/reddit-research-mcp** (120★) | ① official | semantic subreddit discovery (ChromaDB, 20k+ subs) beyond Reddit's 250-result cap; citation-backed | hosted OAuth, no creds | complements buddy for discovery |
| dancolta/subscope (10★) | ④ | keyless public-RSS buyer-intent scoring, local SQLite (post-GummySearch) | self-host | thin adoption (10★), niche |
| Apify (Quora/forums/Reddit monitor) | ② resale | Quora, forums, brand monitor + sentiment | apify MCP | pay-per-use; SSE deprecated, use HTTP |
| midodimori stack-overflow-mcp | ① free | SE search/answers | connected + SE key (raises 300→10k/day) | — |
| elyxlz/discord-mcp | ④ browser | read/scrape via your user session | self-host | ⚠ violates Discord ToS, ban risk |

**Default pick:** mcp-hn (free) for HN; **reddit-mcp-buddy** (official, zero-setup, no creds) for
Reddit — replaces stale GridfireAI/reddit-mcp; reddit-research-mcp for discovery beyond the 250-cap.

**④ Browser/OSS route:** Reddit official API (PRAW, praw-dev/praw 4.1k★) is still free enough — no
real need to browser-scrape. For 中文社区 (微博/抖音/B站/知乎/贴吧) use **NanmiCoder/MediaCrawler**
(50k★, Playwright, login session). For YouTube/media use **yt-dlp** (167k★). See `browser-automation.md`.

**Watch:** Reddit API tightening — GummySearch shuts down 2026-11. Prefer official-API routes over
unauthorized scrapers. Discord/Quora scraping = ToS gray zone.

**Install guidance:** `reference/volatile/pricing-install.md` → reddit-community.
