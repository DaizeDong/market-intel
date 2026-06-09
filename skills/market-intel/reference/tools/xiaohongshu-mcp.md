# Tool: xpzouying/xiaohongshu-mcp (小红书 MCP)

- **Domain(s):** social-publishing (also: browser-automation)
- **Barrier route:** ④ browser/act-like-human · **Source tier:** L4 · **Ready MCP:** yes (Go binary, self-host — exposes MCP over HTTP)
- **Cost:** free (OSS, self-host) — you supply a logged-in 小红书 session; proxies are the only hidden cost at scale
- **Repo / Provider:** github.com/xpzouying/xiaohongshu-mcp — `xpzouying/xiaohongshu-mcp (14.1k★, gh-api 2026-06)`; active (pushed 2026-06-06, not archived, no LICENSE file declared)
- **Top pick for its domain:** yes (the default free route for 小红书/RED publishing + reading)

## What it does / when to pick it
Drives a real logged-in 小红书 (RED) browser session via a Go server that speaks MCP. Can **read** notes/feeds/search and **post notes** (图文) — rare among Chinese-platform tools, most only scrape. **Decision rule:** pick this when the task is 小红书-specific (post a note, pull note engagement, search RED). For multi-platform Chinese **read-only** crawling (抖音/B站/微博/快手/知乎/贴吧 too) prefer NanmiCoder/MediaCrawler instead; that one cannot post. For Western platforms use Bluesky/Mastodon official libs or Buffer.

## Install
Self-host the Go server, then point an MCP client at its HTTP endpoint. See the volatile L1 line `reference/volatile/pricing-install.md → browser-automation` (xiaohongshu-mcp is listed there, not under social-publishing) and the repo README for the current release-binary / `docker pull xpzouying/xiaohongshu-mcp` command and endpoint (verified 2026-06: prebuilt binaries per-platform on GitHub Releases, MCP exposed at `http://localhost:18060/mcp` by default — but verify the README, ports/paths can shift across releases, do not hardcode). Requires Go (or a prebuilt release binary) + a Chromium/browser the server can drive. On Windows prefer the HTTP transport this server already exposes over a stdio wrapper. L0 mechanics (HTTP vs stdio, restart-to-take-effect): `reference/install-guide.md`.

## Auth / keys
No API key. Auth is a **logged-in 小红书 session/cookies** — you log into RED once in the browser the server controls (typically a QR-code scan from the 小红书 app), and the session persists. No provider secret to leak, so the key-hygiene script does not apply here. Treat the session cookie like a credential: do not commit the cookie/profile dir.

## Usage — call examples
After the server is connected, MCP tools are exposed for: login/check-login, list feeds, search notes, read a note's detail/comments, and publish a note (title + body + images). Minimal flow: `check_login_status` → if needed `get_login_qrcode` (scan in app) → `publish_content` with title/content/image paths. Exact tool names track the README — list them with your client after connecting; do not assume signatures from memory.

## General experience & gotchas (踩坑)
- **Write is far more ban-prone than read** (shard rule, verified 2026-06-01). Use a throwaway / low-value RED account for posting; never your main.
- 小红书 aggressively rate-limits and risk-controls automated posting: space out notes, expect occasional 滑块/验证 challenges that pause the session. Posting bursts of links or identical content is the fastest way to get the account 限流 (shadow-throttled) — you often won't get an error, the note just gets near-zero reach.
- It drives a **real browser** — it needs a desktop/headed environment or a properly configured headless Chromium; a bare headless server box may silently fail login.
- Session **expires**; a stale cookie surfaces as "not logged in" mid-run, not a clean error. Re-scan the QR.
- **One account = one web session** (README, verified 2026-06): 小红书 does not allow the same account to be logged in on multiple web endpoints. If you log that account in anywhere else on the web while the MCP holds it, the MCP session gets kicked out ("踢出登录"). Use the mobile App to *check* the account without evicting the MCP session.
- **New/unverified accounts trigger 实名认证 (real-name) prompts** (README) — this is not a ban and happens with or without the MCP; do the real-name verification once up front so it doesn't stall a run.
- No declared LICENSE on the repo (2026-06) — fine for self-use, clear it before redistributing.
- Like all route-④ tools this **violates platform ToS**; it is for research/automation at your own risk.

## Failure signals & fallback
Failure looks like: login-status false mid-run, publish returns success but the note gets ~0 views (限流), or 验证码/滑块 stalls the browser. **Fallbacks:** for read-only 小红书 (and other 中文 platforms) drop to **NanmiCoder/MediaCrawler** (50k★, Playwright, 7 platforms); for generic act-like-human control use the already-connected **playwright MCP** with your own RED session.

## Last verified: 2026-06
