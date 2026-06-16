# Tool: halcy/Mastodon.py

- **Domain(s):** social-publishing (also: none)
- **Barrier route:** ① official API · **Source tier:** L1 · **Ready MCP:** no (Python library, not an MCP — call it from a script)
- **Cost:** free — Mastodon is open; posting via the official API has no per-post fee and no approval wall
- **Repo / Provider:** github.com/halcy/Mastodon.py — `halcy/Mastodon.py (1.0k★, gh-api 2026-06)`; active (pushed 2026-05-28, not archived, MIT)
- **Top pick for its domain:** no (not flagged top_pick) — but the shard says **"official, free, no ban; front-load it"**

## What it does / when to pick it
The official, mature Python client for the Mastodon REST API. Register an app on any instance, get a token, then post (toots) with media/polls/CW, read timelines, follow, search, and stream. **Decision rule:** whenever a Mastodon instance is a target, use this **first** — route ①, free, **zero ban risk** (it is the sanctioned API). Like atproto for Bluesky, it is a free open network you should front-load. Reach for a multi-platform aggregator (Buffer/Blotato/Postiz/Typefully) only when you need Mastodon *plus* other networks in one call.

## Install
`pip install Mastodon.py` (note the capital M and the `.py`). It is a **library, not an MCP** — no `claude mcp add`; the agent drives it from a Python script. Exact line: `reference/volatile/pricing-install.md → browser-automation` ("Mastodon: `pip install Mastodon.py`"). No transport/restart concerns. L0 mechanics: `reference/install-guide.md`.

## Auth / keys
Two-step, all free: (1) register an app on your instance to get client id/secret (`Mastodon.create_app(...)` once, or do it in the instance's Settings → Development), (2) get a **user access token** (log in once, or paste the token from the instance's app page). Tokens are **per-instance** — a token for `mastodon.social` does not work on another server. Treat the token as a secret: user supplies via env var, never echo/commit it. One-line hygiene reminder; full procedure in `reference/install-guide.md`.

## Usage — call examples
```python
from mastodon import Mastodon
m = Mastodon(access_token="<token>", api_base_url="https://mastodon.social")
m.status_post("hello from Mastodon.py")          # post a toot
m.timeline_home()                                  # read
# media: media = m.media_post("img.png"); m.status_post("...", media_ids=[media])
```

## General experience & gotchas (踩坑)
- **No ban risk** — sanctioned API, not scraping. This is why Mastodon is front-loaded alongside Bluesky in multi-platform jobs (shard: "official, free, no ban").
- **Decentralized = per-instance everything.** `api_base_url` and the token must match the same instance; a token from instance A silently 401s on instance B. Pick the instance the account lives on.
- Each instance sets its **own** rate limits, max toot length (often 500 chars, but some raise it), and media rules — do **not** assume mastodon.social defaults hold elsewhere; read the instance's `/api/v1/instance`.
- Some instances throttle or block automated/bot posting per their rules — respect the instance ToS even though the protocol allows it.
- Use a **user access token**, not app-only creds, for posting; app-only can read public timelines but cannot post as the user.
- **mastodon.social signup is fully scriptable, no captcha** (confirmed 2026-06-16) — `mastodon.social/auth/sign_up` accepts agent form fill (username + email + password + DOB + agreement). Email verification is still required (link goes to signup mailbox). Username must be unique on the chosen instance — `the skill's Mastodon account` worked on mastodon.social.
- **Application creation at `/settings/applications/new`** — requires explicit scope checkboxes (default is none); pick `read` at minimum for research use. After creation, the application page renders **all 3 of `client_key`, `client_secret`, `access_token` as readonly plaintext inputs simultaneously** (no copy-only button). For most research workflows you only need `access_token`; the client pair is for OAuth-app flows. **DOM-leak risk:** reading via `browser_evaluate` pipes all three values into the agent transcript.

## Failure signals & fallback
Failure looks like: 401/`MastodonUnauthorizedError` (token/instance mismatch or revoked), 422 on over-length/over-media toots, or 429 rate-limit from the instance. **Fallbacks:** route Mastodon through a **multi-platform aggregator** (Buffer ① free-tier / Blotato / Postiz / Typefully) when bundling with other networks; for one-offs, the instance web UI. No scraping fallback needed — the API is open.

## Last verified: 2026-06
