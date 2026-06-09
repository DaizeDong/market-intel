# Tool: Apify (3000+ actors + MCP)

- **Domain(s):** web-scraping (also: x-twitter, reddit-community, ecommerce-arbitrage)
- **Barrier route:** ② resale API · **Source tier:** L2 · **Ready MCP:** yes — hosted HTTP `https://mcp.apify.com`
- **Cost:** free $5/mo platform credit (no card); paid plans bundle a monthly store/Actor credit — exact Starter/Scale plan prices unverified here, confirm at https://apify.com/pricing. Base billing is compute-unit (CU) based, but many individual actors layer a pay-per-result charge (~$0.1–0.25/1k for tweet actors, per pricing-install.md) [fetched 2026-06]
- **Repo / Provider:** https://apify.com (hosted marketplace — actors are individual; `apify/crawlee` is the OSS framework underneath)
- **Top pick for its domain:** no (marketplace, not a single tool — pin specific actors)

## What it does / when to pick it
A marketplace of 3,000+ prebuilt "actors" (hosted scrapers) for social, e-commerce, maps, and more, plus an MCP that can discover and run them. **Decision rule:** pick Apify when a *maintained prebuilt actor* already exists for your exact target (e.g. a specific Instagram/TikTok/Maps/Amazon scraper) and you'd rather rent it than build a route-④ scraper. For generic JS scraping use **Firecrawl**; for hard anti-bot use **Bright Data**; for search use **Tavily/Exa**. Apify wins on *coverage of niche platforms* with a ready actor. Cross-serves x-twitter (tweet actors ~$0.1–0.25/1k), reddit-community, and e-commerce.

## Install
Hosted HTTP MCP `https://mcp.apify.com` — Windows-friendly. **Critical:** pin the **specific actor(s)** you need rather than exposing the whole catalog, or the MCP floods the tool list (shard rule). Exact command + the actor-pinning note: `reference/volatile/pricing-install.md → web-scraping` (and `#x-twitter` for tweet actors). L0 mechanics: `reference/install-guide.md`. Restart / `/mcp` reconnect after adding.

## Auth / keys
Apify API token from the console (free plan = $5/mo platform credit, no card). **Secret hygiene (one line):** for the keyed HTTP MCP, edit `~/.claude.json` from clipboard rather than `claude mcp add` (which echoes the token), and never `browser_snapshot` the token page — see `reference/install-guide.md`.

## Usage — call examples
MCP lets you search the store, get an actor's input schema, and run it. Minimal flow: find the actor (e.g. an Amazon-product or tweet-scraper actor) → inspect its input schema → run it with the input JSON → fetch dataset results. Prefer pinning a known actor ID and calling it directly over open-ended store search (faster, fewer tools, predictable cost).

## General experience & gotchas (踩坑)
- **Pin specific actors to avoid tool flood** (shard) — the unpinned MCP can register dozens of tools and bury your real toolset; always scope to the actor(s) you need.
- **Cost is dual:** platform **compute units** (per-CU rate unverified — confirm at https://apify.com/pricing) PLUS many actors charge **pay-per-result** (~$0.1–0.25/1k for tweet actors). The $5/mo free credit is small — a single broad run can exhaust it; check the actor's pricing model (per-result vs per-CU) before a big run.
- **Actor quality varies** — actors are third-party; some are unmaintained or break when the target site changes. Check the actor's last-updated date and run-success rate before depending on it.
- An actor run is **async** (start run → poll status → read dataset) — not an instant return; budget for the poll.
- It's a route-② resale wrapper over what's often route-④ scraping; for X/Twitter the native **twitterapi.io** MCP or self-host **twikit** may be cheaper/cleaner than a tweet actor — compare before defaulting to Apify.

## Failure signals & fallback
Failure looks like: tool-list flood (forgot to pin), an actor returning empty/stale data (site changed, actor unmaintained), a run stuck in "running", or burning the $5 credit on one job. **Fallbacks:** generic JS scrape → **Firecrawl** (②); hard anti-bot/Amazon/Reddit → **Bright Data** (②); X/Twitter → **twitterapi.io** (native MCP) or **twikit** (③④); build-your-own self-host → `apify/crawlee` (the OSS framework Apify is built on) or **playwright MCP** (④).

## Last verified: 2026-06
