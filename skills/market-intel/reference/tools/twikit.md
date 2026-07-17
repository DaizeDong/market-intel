# Tool: d60/twikit (+ adhikasp/mcp-twikit)

- **Domain(s):** x-twitter (also: social-publishing, browser-automation)
- **Barrier route:** ③④ self-host scrape / act-like-human · **Source tier:** L4 · **Ready MCP:** yes, adhikasp/mcp-twikit wraps the lib (`235★`, MIT, pushed 2025-03, ~15mo stale but functional; the underlying twikit lib is the actively maintained part)
- **Cost:** free (OSS, self-host), you supply X account cookies; proxies are the only hidden cost at scale
- **Repo / Provider:** github.com/d60/twikit, `d60/twikit (4.5k★, gh-api 2026-06)`; active (pushed 2026-03-10, not archived, MIT). MCP wrapper: github.com/adhikasp/mcp-twikit (`235★, gh-api 2026-06`, MIT, pushed 2025-03)
- **Top pick for its domain:** yes (the **free default pick** for X read/write)

## What it does / when to pick it
Free Python lib that drives X via a logged-in account's cookies, **no API key, no X dev account.** Read (search, user, followers, tweets, replies) **and write** (post, reply, DM). **Decision rule:** this is the shard's free default for x-twitter alongside playwright. Pick twikit when you want library-level X access (search/users/write) for $0 and can supply a throwaway account + cookies. Choose **playwright MCP** instead when you need fields the stripped client misses (act like a real logged-in human on the rendered page). Choose **twitterapi.io ②** only when you'd rather a provider absorb the account/proxy/ban upkeep. Remember the shard rule: **X is low-signal for consumer-demand research**, use this for tech/crypto/founder discourse and named-account tracking.

## Install
Library: `pip install twikit`. Ready MCP (wraps the lib): adhikasp/mcp-twikit, clone + run per its README (stdio; supply X login creds via env/config). Volatile L1 line: `reference/volatile/pricing-install.md → x-twitter` (and the `browser-automation` section lists `pip install twikit, 4.5k★ + MCP adhikasp/mcp-twikit`). On Windows, stdio MCPs are flaky (path/shell), prefer running the lib directly in a Python script, or test the stdio MCP in a plain shell first; see `reference/install-guide.md` for Windows + stdio notes. A freshly added MCP needs a session restart / `/mcp` reconnect.

## Auth / keys
No API key, auth is an **X account's cookies / login** (username+password+email, or a saved cookies file). Use a **throwaway / low-value account**, never your main (ban risk, see below). The credential to protect is the account login + cookie file: do not commit the cookies file. No provider secret/header to leak, so the `claude mcp add` key-echo problem does not apply, but treat the cookie file like a credential. Login-hygiene and Windows mechanics: `reference/install-guide.md`.

## Usage, call examples
Library: `client = Client('en-US'); await client.login(auth_info_1=USER, auth_info_2=EMAIL, password=PW)` then `await client.search_tweet('grok', 'Latest')`, `await client.get_user_by_screen_name('handle')`, `await client.create_tweet('text')`, or `await client.send_dm(...)`. Save/reuse cookies with `client.save_cookies('cookies.json')` / `client.load_cookies(...)` to avoid re-login. Via the MCP, equivalent tools (search_twitter, get_user_*, post) are exposed, list them with your client after connecting; don't assume signatures from memory.

## General experience & gotchas (踩坑)
- **Ban risk is real and write >> read.** Posting/DM/follow at any volume from an automated session is the fastest path to suspension. Use a throwaway account; rotate cookies/proxies if you scale; keep write volume human-paced.
- **Cookie sessions expire / get challenged.** A stale session surfaces as a login error or an empty result mid-run, not a clean failure. Re-login and re-save cookies. Expect occasional X challenges (suspicious-login, verification) that pause the account.
- **twikit lib is active (pushed 2026-03), but the MCP wrapper is ~15mo stale (2025-03).** Since X changes its internal endpoints, the **lib** is the part that gets fixed, if the MCP breaks after an X change, update the underlying twikit version or drop to calling the lib directly.
- It rides X's **internal/undocumented** endpoints (act-like-human), so it breaks when X changes them and **violates X ToS**, research/throwaway use at your own risk.
- **Shard truth:** X "Top" search was nearly empty for consumer/non-tech demand (patio-heater real-run), don't burn a throwaway account chasing consumer-demand signal here; route that to 抖音/小红书/B站 or Reddit/forums.
- Don't confuse with the **dead** elizaOS/agent-twitter-client (原仓库下架，只剩 fork), flag that one L5 if a plan relies on it.

## Failure signals & fallback
Failure looks like: login raises (bad creds / challenge), search returns empty on a query that should hit (session invalid or X endpoint changed), account suspended, or the stale MCP wrapper errors after an X-side change. **Fallbacks:** drop to the already-connected **playwright MCP** with your own logged-in X session (most robust act-like-human route, richer fields); or pay your way past the barrier with **twitterapi.io ②** (provider absorbs account/proxy upkeep) → **Bright Data X datasets** for scale/SLA.

## Last verified: 2026-06
