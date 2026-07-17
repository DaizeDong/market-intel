# Tool: twscrape

- **Domain(s):** x-twitter (also: none)
- **Barrier route:** ③ self-host scrape · **Source tier:** L4 · **Ready MCP:** no (Python library, wrap it yourself or call from a script)
- **Cost:** free (OSS, self-host), you supply X account cookies + proxies; proxies are the hidden cost at scale
- **Repo / Provider:** github.com/vladkens/twscrape, `vladkens/twscrape (2.5k★, gh-api 2026-06)`; very active (pushed 2026-06-08, not archived, MIT)
- **Top pick for its domain:** no (the free default is twikit/playwright; twscrape is the pick when you specifically need **multi-account rotation**)

## What it does / when to pick it
Free Python lib for X search / user / followers / tweets via the GraphQL + Search API, with **built-in multi-account pool + automatic rotation** so you can spread load across many logged-in accounts. **Decision rule:** prefer the shard default (**twikit** for read+write, or **playwright** for richest fields). Reach for twscrape specifically when you need **volume read scraping with account rotation** (its standout feature, add N accounts, it round-robins and parks rate-limited ones). It is read-focused (search/users/followers/tweets), not a posting tool. Same shard caveat: **X is low-signal for consumer-demand research**, use for tech/crypto/founder discourse, breaking news, named-account tracking.

## Install
`pip install twscrape`. No MCP, call it from a Python script or wrap it. Volatile L1 line: `reference/volatile/pricing-install.md → x-twitter` ("twscrape (self-host, free): `pip install twscrape`, needs X account cookies + proxy"). Pure Python lib, so no transport/Windows MCP flakiness, but it needs your X account cookies + (at scale) a proxy pool. L0 prerequisites (Python ≥3.10, throwaway accounts + proxies): `reference/install-guide.md`.

## Auth / keys
No API key, auth is **one or more X account cookies/logins** added to its account pool (`twscrape add_accounts accounts.txt ...` then `twscrape login_accounts`). Use **throwaway accounts only** (ban risk). The pool's accounts DB (`accounts.db`) holds session cookies, treat it like a credential, do not commit it. No provider secret/header, so the `claude mcp add` key-echo issue does not apply. Proxy/account rotation hygiene: `reference/install-guide.md`.

## Usage, call examples
CLI: `twscrape add_accounts accounts.txt user:pass:email:email_pass` → `twscrape login_accounts` → `twscrape search "grok lang:en" --limit 100`. Python: `api = API(); await api.pool.add_account(...); await api.pool.login_all()` then `async for tweet in api.search("query", limit=100): ...`, or `await api.user_by_login("handle")`, `api.followers(user_id)`. It auto-rotates accounts and backs off rate-limited ones. List current API methods from the README; don't assume signatures from memory.

## General experience & gotchas (踩坑)
- **You must supply real X accounts + proxies**, the software is free, the accounts/proxies are the actual cost and the actual risk. Login-walled scraping at volume needs several accounts and residential proxies, or the whole pool gets flagged together.
- **Ban/lock risk per account.** twscrape parks rate-limited accounts, but X can lock or suspend them; budget for churn and keep adding fresh throwaways. Never use a real/main account.
- **Rides X's internal GraphQL/Search endpoints** → breaks when X changes them. The repo is **very active (pushed 2026-06-08)**, which is exactly why it's still viable, pin to a recent version and update when search silently returns empty.
- **Read-only-ish**, it's a scraper, not a poster; for write/DM use twikit.
- **Violates X ToS**, research/throwaway use at your own risk.
- **Shard truth:** X "Top"/search was nearly empty for consumer/non-tech demand (patio-heater real-run), rotating 10 accounts won't conjure demand signal that isn't on X; route consumer-demand questions to 抖音/小红书/B站 or Reddit/forums.
- Don't confuse with the **dead** snscrape (停更), twscrape is its living successor; flag snscrape L5 if a plan relies on it.

## Failure signals & fallback
Failure looks like: `login_accounts` fails or accounts go to a locked/parked state, search returns empty on queries that should hit (all accounts rate-limited/flagged, or X endpoint changed), or pool exhausted. **Fallbacks:** for read+write or simpler single-account use, **twikit (+ adhikasp/mcp-twikit)**; for richest fields / hardest cases, the already-connected **playwright MCP** with your own session; to pay past the barrier, **twitterapi.io ②** (provider absorbs account/proxy upkeep) → **Bright Data X datasets** for scale/SLA.

## Last verified: 2026-06
