# Tool: praw-dev/praw (Reddit API wrapper)

- **Domain(s):** reddit-community (also: none)
- **Barrier route:** ① official (free Reddit API) · **Source tier:** L1 · **Ready MCP:** no — it's a Python library, not an MCP; call it from a script (or via a PRAW-based MCP wrapper such as the superseded reddit-mcp)
- **Cost:** free — official Reddit OAuth API, no charge (rate-limited) [https://praw.readthedocs.io, fetched 2026-06]
- **Repo / Provider:** github.com/praw-dev/praw — `praw-dev/praw (4.1k★, gh-api 2026-06)`; not archived, BSD-2-Clause, **actively maintained** (pushed 2026-06-09)
- **Top pick for its domain:** no — the **escalation** when the read-only reddit-mcp isn't enough

## What it does / when to pick it
The mature, canonical Python client for the official Reddit API: full read access to submissions, search, subreddits, **and nested comment trees**, plus pagination and multi-sub aggregation. **Decision rule:** the shard's `④`-route note says PRAW (official API) is "still free enough — no real need to browser-scrape" Reddit. Pick **reddit-mcp-buddy** first for quick read-only subreddit/search queries (the zero-setup Reddit default; GridfireAI/reddit-mcp is the superseded fallback); escalate to **praw** when you need what the MCP can't give: the **comment tree** (objections, "I switched because…"), custom pagination, or aggregating many subreddits in one flow. It's a library (L1), so it lives in your script, not the MCP list.

## Install
`pip install praw`. No MCP to add — write a short Python script. The L1 line: `reference/volatile/pricing-install.md → reddit-community` (notes PRAW as the still-free official-API route under `④ Browser/OSS`). Windows: pure-Python, so no stdio/path flakiness — runs fine in any Python ≥3.10 env. (If you'd rather have it in the MCP list, use `reddit-mcp-buddy` first; the superseded `reddit-mcp` also wraps PRAW — see `reddit-mcp-buddy.md` / `reddit-mcp.md`.)

## Auth / keys
Create a free "script" app at reddit.com/prefs/apps → get `client_id`, `client_secret`, set a descriptive `user_agent`. These are **secrets** — load them from env vars the **user** sets (e.g. a local `.env`), never hard-code or echo the values into the transcript. No MCP header to leak here, but treat the client secret like a credential and keep it out of committed code. One-line reminder; full hygiene in `reference/install-guide.md`.

## Usage — call examples
```python
import praw
reddit = praw.Reddit(client_id=..., client_secret=..., user_agent="market-intel/0.x")
for s in reddit.subreddit("homeimprovement").search("patio heater", sort="top", time_filter="year", limit=25):
    s.comments.replace_more(limit=0)          # flatten the comment tree
    pains = [c.body for c in s.comments.list()]
```
`reddit.subreddit(...).top()/hot()/new()`, `.search(...)`, and `submission.comments.list()` are the core calls. Always set `user_agent`; respect `time_filter`/`limit`.

## General experience & gotchas (踩坑)
- **This is the tool that closes the comment-tree gap** the shard flagged on the patio-heaters run — `submission.comments.replace_more(limit=0)` then `.list()` flattens nested replies the read-only MCP can't return. That's the main reason to reach for praw over reddit-mcp.
- **Reddit API rate limits (~60 req/min)** still apply — PRAW handles backoff internally but a wide multi-sub + comment-tree crawl is slow; cache and pace. `replace_more` calls are the expensive part (each costs a request).
- **Reddit API is tightening** (shard "Watch": API restrictions ongoing, GummySearch shuts 2026-11). Official OAuth access remains compliant and free for read — stay on it rather than scraping — but watch for quota/policy drift.
- **Read-only is enough for research; avoid write/vote actions** (post/comment/vote) which carry account-action risk and add nothing to intel work.
- Actively maintained (pushed 2026-06) and 4.1k★ — the dependable, non-dead choice, unlike many one-off Reddit scrapers.

## Failure signals & fallback
Failure looks like: 401/403 (bad client creds or missing user_agent), 429 (rate-limited — slow down), or a `replace_more` crawl timing out on a huge thread (cap `limit`). **Fallbacks:** for quick read-only queries without writing a script, use **reddit-mcp-buddy** (or the superseded GridfireAI/reddit-mcp); for cross-platform keyword monitoring use **Apify** Reddit actors (② paid) or free F5Bot; for HN discourse use **mcp-hn**.

## Last verified: 2026-06
