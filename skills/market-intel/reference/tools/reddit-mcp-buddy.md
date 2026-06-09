# Tool: karanb192/reddit-mcp-buddy

- **Domain(s):** reddit-community (also: none)
- **Barrier route:** ① official (free Reddit API) · **Source tier:** L2 · **Ready MCP:** yes — `npx -y reddit-mcp-buddy` (stdio); **connects with zero auth** on the anon tier (no creds, no Reddit account)
- **Cost:** free — rides Reddit's official API; tiered rate limits, no charge [https://www.npmjs.com/package/reddit-mcp-buddy, fetched 2026-06]
- **Repo / Provider:** github.com/karanb192/reddit-mcp-buddy — `karanb192/reddit-mcp-buddy (0.7k★, gh-api 2026-06)`; not archived, MIT, pushed 2026-05 (actively maintained)
- **Top pick for its domain:** yes — the **new Reddit default** (replaces the now-stale GridfireAI/reddit-mcp)

## What it does / when to pick it
LLM-optimized read access to Reddit: browse a subreddit's posts, search content, pull post details (with comments), and analyze a user's history. **Decision rule:** this is the shard's Reddit default as of the 2026-06 refresh — pick it for any subreddit pain-point mining, product-feedback hunting, or "what is r/<niche> saying about X". The killer feature is **zero-setup**: the anon tier needs no creds at all (10 req/min), so you can start mining immediately and only add a Reddit app later if you hit the cap. It **supersedes GridfireAI/reddit-mcp** (stale 2025-03, 18★) — prefer this. For *discovering which subreddits* to mine (semantic, beyond Reddit's 250-result cap), pair it with **reddit-research-mcp**; for keyless buyer-intent scoring use **subscope**.

## Install
`npx -y reddit-mcp-buddy` (stdio). No creds needed for the anon tier → `claude mcp add` is safe here (nothing secret to leak). To raise limits, set a free Reddit app id/secret (app-id tier 60/min) and optionally Reddit login (100/min). Exact L1 command: `reference/volatile/pricing-install.md → reddit-community`. On Windows, stdio `npx` is flaky (path/shell) — if it won't connect, test `npx -y reddit-mcp-buddy` in a plain shell first; prefer an HTTP-transport sibling if stdio keeps failing. See Windows + stdio mechanics in `reference/install-guide.md`. A newly added MCP needs a session restart / `/mcp` reconnect.

## Auth / keys
**None required for the anon tier (10 req/min).** To lift the cap: create a free "script" app at reddit.com/prefs/apps → `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (app-id tier, 60/min), or add Reddit username/password (login tier, 100/min). Those creds are **secrets** — supply via `-e REDDIT_CLIENT_ID=$VAR ...` that the **user** runs; never paste the values into the transcript, and for the secret-bearing case edit `~/.claude.json` from clipboard rather than `claude mcp add` (which echoes them). Full secret hygiene in `reference/install-guide.md`.

## Usage — call examples
Via MCP, tools cover: browse a subreddit's hot/new/top posts, search posts by keyword, fetch a post's details + comments, and analyze a user. Minimal: "browse top posts in r/<niche> this month" → open the highest-comment threads → read the post details for recurring complaints. List the exact tool names with your client after connecting — don't assume signatures from memory.

## General experience & gotchas (踩坑)
- **Tier cap is the trap.** The anon tier is only 10 req/min — a loop of browse+search+details calls exhausts it fast and returns rate-limit errors mid-run. For any real mining session, add the app-id creds (60/min) up front; pace requests and cache results regardless.
- **Subreddit search is keyword, not semantic**, and Reddit's own search is weak — run query variants and browse top/hot directly rather than trusting one search. To find the *right* subreddits at all, hand off to **reddit-research-mcp** (semantic discovery).
- **Reddit API is tightening** (shard "Watch": GummySearch shuts down 2026-11). Official-API access stays the safe route — prefer it over scrapers — but expect quota/policy drift; re-verify before relying at scale.
- **Post details include comments**, but for deep nested comment-tree walking / multi-sub aggregation with full pagination control, drop to **praw** (same free API, full control).
- Free official API, so per CONSTITUTION C2 use it before any paid Reddit-monitoring SaaS (Syften/Apify).

## Failure signals & fallback
Failure looks like: rate-limit errors under load (anon 10/min cap — add app-id creds), empty search on a live topic (Reddit search weakness — browse top/hot or broaden the query), or stdio connect failing on Windows (npx path). **Fallbacks:** for which-subreddit discovery beyond the 250-result cap → **reddit-research-mcp**; for keyless buyer-intent scoring → **subscope** (④ self-host); for comment trees / custom read logic → **praw**; for HN-flavored community signal → **mcp-hn**.

## Last verified: 2026-06
