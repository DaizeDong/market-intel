# Domain: social-publishing

**Triage signals:** auto-post / schedule tweets, multi-platform content distribution, post to
X/LinkedIn/Threads/etc, 发帖/排期/内容分发.

**Platform write-API barriers (2026):** X is the ONLY paid one — pay-per-use, post $0.01 but
**link-posts $0.20 each**; new devs can't subscribe Basic/Pro. Bluesky/Mastodon/Threads = free.
LinkedIn free but approval wall (legal entity + vetting).

| source | route | capability | detect | cost |
|---|---|---|---|---|
| **Buffer API** (+ MCP) | ① | 11 platforms, free tier works with API + MCP | connected + key | best value, free tier usable |
| Ayrshare (+ MCP) | ② | 13+ platforms, multi-user SaaS | connected | $149/mo+; X creds自带 from 2026-03 |
| Blotato (+ MCP) | ② | 9 platforms, native Claude Code MCP | connected + key | $29/mo, cheap personal |
| Typefully API v2 | ① | text/thread first (X/LI/BS/Masto/Threads) | key | with subscription |
| **Postiz** (OSS, built-in MCP) | ③ self-host | 30+ platforms, agentic-first, no token storage | self-host URL | free OSS; v2.12+ needs Temporal |
| Mixpost (OSS) | ③ self-host | 11 platforms, REST+n8n, buy-once | self-host | Lite free / Pro $269 one-time |
| X single: EnesCinr/twitter-mcp, OpenTweet | ①/② | post+search / hosted no-dev-portal | connected | X API cost自负 / OpenTweet $11.99/mo |

**Default pick:** Multi-platform cheap + official → Buffer. Claude Code native cheap → Blotato.
OSS self-host → Postiz. Front-load free platforms (Bluesky/Mastodon/Threads).

**Cost trap:** X link-posts $0.20 each — budget before bulk posting links.

**Install guidance:** `reference/volatile/pricing-install.md` → social-publishing.
