# Tool: MarshalX/atproto (Bluesky SDK)

- **Domain(s):** social-publishing (also: none)
- **Barrier route:** ① official API · **Source tier:** L1 · **Ready MCP:** no (Python SDK / library, not an MCP — call it from a script)
- **Cost:** free — Bluesky write API is open and free, no per-post fee, no dev-account approval wall
- **Repo / Provider:** github.com/MarshalX/atproto — `MarshalX/atproto (0.7k★, gh-api 2026-06)`; active (pushed 2026-06-05, not archived, MIT)
- **Top pick for its domain:** no (not flagged top_pick) — but the shard says **"just use it / front-load it"** for Bluesky

## What it does / when to pick it
Official-grade Python SDK for the AT Protocol (Bluesky). Authenticate with a handle + app password and post, read timelines/feeds, follow, and read threads — the full firehose/XRPC surface. **Decision rule:** whenever Bluesky is one of the target platforms, reach for this **first** — it is route ①, free, open, and carries **zero ban risk** (unlike X/Instagram/LinkedIn write routes). Use a multi-platform aggregator (Buffer/Blotato/Postiz) only when you need Bluesky *plus* several other networks from one call; for Bluesky alone this lib is simpler and free.

## Install
`pip install atproto` (Python ≥ 3.8). It is a library, **not** an MCP — there is no `claude mcp add`; you drive it from a small Python script the agent writes. Exact line: `reference/volatile/pricing-install.md → browser-automation` ("Bluesky: `pip install atproto`"). No transport/restart concerns since it is not an MCP server. L0 mechanics: `reference/install-guide.md`.

## Auth / keys
Create a free **App Password** at Bluesky → Settings → App Passwords (do **not** use the main account password). Auth = handle (`you.bsky.social`) + that app password. This is a credential: have the **user** supply it via env var; never echo it into the transcript or commit it. Standard secret-hygiene reminder applies — one line, full procedure in `reference/install-guide.md`.

## Usage — call examples
```python
from atproto import Client
client = Client()
client.login("you.bsky.social", "<app-password>")  # from env
client.send_post(text="hello from atproto")          # post
client.get_timeline()                                 # read
```
For rich posts use `client_utils.TextBuilder` (mentions/links/tags); images via `send_images`.

## General experience & gotchas (踩坑)
- **No ban risk** — this is the sanctioned API, not scraping. This is the whole reason to front-load Bluesky/Mastodon in any multi-platform job (shard: "official, free, no ban — just use it").
- Use an **app password**, never the real password; a leaked app password is revocable in one click, the main password is not.
- Rate limits exist but are generous for normal posting; bulk backfills can hit them — batch politely.
- `send_post` text is **300 graphemes** max; over-length silently/errors depending on path — truncate first.
- Links/mentions are **not auto-detected** from plain text — you must attach facets (use `TextBuilder`) or the URL posts as inert text.
- Small star count (0.7k) is **not** a quality signal here — it is the de-facto reference SDK and tracks the protocol closely (pushed 2026-06).

## Failure signals & fallback
Failure looks like: `login` raising on a bad/again-rate-limited app password, or posts appearing as plain text because facets were omitted. **Fallbacks:** drive Bluesky through a **multi-platform aggregator** (Buffer ① free-tier / Blotato / Postiz) if you need it bundled with other networks; for ad-hoc one-offs the Bluesky web UI. There is no scraping fallback needed — the API is open.

## Last verified: 2026-06
