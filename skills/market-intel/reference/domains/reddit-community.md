# Domain: reddit-community

**Triage signals:** Reddit, Hacker News, Discord, Quora, Stack Exchange, forums, pain-point mining,
社区/论坛调研, 用户需求挖掘.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **erithwik/mcp-hn** (HN) | ① free | top/new/ask/show, search, comments | mcp list / `uvx mcp-hn` | none, Algolia API, no key |
| **karanb192/reddit-mcp-buddy** (702★) | ① official | browse/search/post-details/user-analysis; zero-setup anon (10/min) → app-id (60) → login (100) tiers | `npx -y reddit-mcp-buddy` | free; repo active (756★ at last gh-api check, 2026-07-22), but **⚠ anon tier currently non-functional** (Reddit is 403-blocking the unauthenticated JSON API since ~2026-06-03, upstream issue #58, fix PR #60 open/unmerged 6+wks; live-tested 2026-07-22, still forbidden). Use the app-id/login tier (OAuth, not the blocked anon path) or route to reddit-research-mcp below until #60 merges |
| GridfireAI/reddit-mcp | ① official | submissions, search, subreddit (read-only) | connected + Reddit client id/secret | **D-SUPERSEDED** by reddit-mcp-buddy (stale 2025-03, 18★), kept as minimal fallback |
| **king-of-the-grackles/reddit-research-mcp** (120★) | ① official | semantic subreddit discovery (ChromaDB, 20k+ subs) beyond Reddit's 250-result cap; citation-backed, hosted OAuth needs no creds | hosted OAuth, no creds | confirmed working 2026-07-22 (219★ at last gh-api check); **currently the only no-cred Reddit route that works**, given buddy's anon-tier outage above, elevated to co-top-pick until #58/#60 resolve |
| dancolta/subscope (10★) | ④ | keyless public-RSS buyer-intent scoring, local SQLite (post-GummySearch) | self-host | thin adoption (10★), niche |
| Apify (Quora/forums/Reddit monitor) | ② resale | Quora, forums, brand monitor + sentiment | apify MCP | pay-per-use; SSE deprecated, use HTTP |
| midodimori stack-overflow-mcp | ① free | SE search/answers | connected + SE key (raises 300→10k/day) | none |
| **ArthurHeitmann/arctic_shift** (1.1k★) | ③ archive | Pushshift successor: bulk historical Reddit dumps + JSON API + hosted web UI (arctic-shift.photon-reddit.com); monthly dump refresh | self-host or use hosted UI | active 2026-06, MIT-style, **solo maintainer** (bus-factor risk worth flagging) |
| **SaseQ/discord-mcp** (356★) | ① bot-token | Bot-token Discord MCP (JDA-based, Docker) for own/admin servers, ToS-compliant | bot token + `docker run :8085/mcp` | MIT, active 2026-04 |
| elyxlz/discord-mcp | ④ browser | read/scrape via your user session | self-host | ⚠ violates Discord ToS, ban risk, prefer SaseQ/discord-mcp for own servers |

**Default pick:** mcp-hn (free) for HN; Reddit → **reddit-research-mcp** (currently the only working
no-cred route, see anon-tier outage note above) or reddit-mcp-buddy on its app-id/login tier; both
replace stale GridfireAI/reddit-mcp. Revert to reddit-mcp-buddy anon as default once upstream #60 lands.

**④ Browser/OSS route:** Reddit official API (PRAW, praw-dev/praw 4.1k★) is still free enough, no
real need to browser-scrape. For 中文社区 (微博/抖音/B站/知乎/贴吧) use **NanmiCoder/MediaCrawler**
(57.1k★, Playwright, login session). For YouTube/media use **yt-dlp** (167k★). See `browser-automation.md`.

**Historical / archival route:** for >30-day-old Reddit data or bulk dump access, the new top pick is
**arctic_shift** (route ③, free, monthly refresh), live API picks (reddit-mcp-buddy, GridfireAI)
cover current data only.

**Watch:** Reddit API tightening, prefer official-API routes over unauthorized scrapers.
Discord/Quora scraping = ToS gray zone.

**Avoid (dead/dying):** **GummySearch**, phased shutdown after it could not reach a compliant Reddit
Data API license (verified gh/official 2026-06): commercial close **2025-11-30** (stopped new
signups/renewals), legacy subscribers wind down through 2026, **full shutdown + data deletion
2026-12-01**. As of 2026-06 it serves only legacy paid subscribers, do not start anything on it. Its
free, keyless successor is **`dancolta/subscope`** (route ④, in this shard; active 2026-06, MIT,
self-bills as an open-source GummySearch/Syften/F5Bot alternative), RSS-only, so a monitoring tool,
not a historical backfill.

**Install guidance:** `reference/volatile/pricing-install.md` → reddit-community.
