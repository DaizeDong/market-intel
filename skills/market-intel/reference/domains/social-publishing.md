# Domain: social-publishing

**Triage signals:** auto-post / schedule tweets, multi-platform content distribution, post to
X/LinkedIn/Threads/etc, 发帖/排期/内容分发.

**Platform write-API barriers (2026):** X is the ONLY paid one — pay-per-use, post $0.01 but
**link-posts $0.20 each**; new devs can't subscribe Basic/Pro. Bluesky/Mastodon/Threads = free.
LinkedIn free but approval wall (legal entity + vetting).

| source | route | capability | detect | cost |
|---|---|---|---|---|
| **Buffer API** (+ MCP) | ① | 11 platforms, free tier works with API + MCP | connected + key | best value; public API + hosted MCP officially launched 2026-05-27, on every plan incl. Free |
| Ayrshare (+ MCP) | ② | 13+ platforms, multi-user SaaS | connected | $149/mo+; X creds自带 from 2026-03 |
| **Publora** (MCP-native) | ① core | MCP-native social publishing API across X/LinkedIn/TikTok/YouTube/Instagram + others | connected + key | **replaces Blotato** — confirmed via G2/ProductHunt/mcp.so/official GitHub org. 50-80% cost cut at the MCP-native tier (per Discovery; re-verify before quoting) |
| Typefully API v2 | ① | text/thread first (X/LI/BS/Masto/Threads) | key | Free $0 (1 post) / Starter $8 / Creator $19 / Team $39; API needs a paid plan |
| **Postiz** (OSS, built-in MCP) | ③ self-host | 30+ platforms, agentic-first, no token storage | self-host URL | free OSS; v2.12+ needs Temporal |
| **gitroomhq/postiz-agent** (278★) | ③ | official Postiz agent front-end (`npx skills add`) for 28+ platforms | self-host | lowers agent-vs-API friction over Postiz |
| **langchain-ai/social-media-agent** (2.6k★) | ③ | source/curate/schedule agent w/ human-in-loop | self-host + key | content-pipeline tier above the post APIs; pairs w/ Buffer/Postiz |
| Mixpost (OSS) | ③ self-host | 11 platforms, REST+n8n, buy-once | self-host | Lite free / Pro $269 one-time |
| X single: EnesCinr/twitter-mcp, OpenTweet | ①/② | post+search / hosted no-dev-portal | connected | X API cost自负 / OpenTweet $11.99/mo |

**Default pick:** Multi-platform cheap + official → Buffer. Claude Code MCP-native → **Publora**
(replaces Blotato 2026-06-17). OSS self-host → Postiz. Front-load free platforms (Bluesky/Mastodon/Threads).

**Cost trap:** X link-posts $0.20 each — budget before bulk posting links.

## ④ Browser/OSS "act like a human" alternatives (free, per platform)
Often better than paid post APIs — real logged-in session, no per-post fee. All violate platform
ToS → use throwaway accounts; write/post is far more ban-prone than read. Verified 2026-06-01.

| platform | repo | route | note |
|---|---|---|---|
| X | d60/twikit (4.5k★) + adhikasp/mcp-twikit | ③/④ | read+write+DM, ready MCP, free |
| Instagram | subzeroid/instagrapi (6.3k★) | ③ | post图文/Reels/comment/DM, most active |
| LinkedIn | stickerdaniel/linkedin-mcp-server (2.2k★) | ④ | ready MCP; ⚠ highest ban risk, small acct |
| TikTok | davidteather/TikTok-Api (6.4k★) | ④ | Playwright-signed, scrape+search |
| 小红书 | **xpzouying/xiaohongshu-mcp (14k★)** | ④ | browser + ready MCP, **can post notes** |
| 中文多平台 | NanmiCoder/MediaCrawler (50k★) | ④ | Playwright, 小红书/抖音/B站/微博/快手/知乎/贴吧 |
| Bluesky | MarshalX/atproto (653★) | ① | official, free, no ban — just use it |
| Mastodon | halcy/Mastodon.py (961★) | ① | official, free, no ban |

**Default (free route):** post via OSS repo for the platform (X→twikit MCP, 小红书→xiaohongshu-mcp,
IG→instagrapi). Bluesky/Mastodon are open — use official libs, zero ban risk, front-load them.

**Install guidance:** `reference/volatile/pricing-install.md` → social-publishing.
