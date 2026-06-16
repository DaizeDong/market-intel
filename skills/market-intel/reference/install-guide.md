# Install guide — market-intel sources & MCP servers (Level 0 / overview)

This is the **top of a three-level install system**. Most market-intel sources need a one-time
setup (an MCP server, an API key, or a cloned OSS repo). This file holds the *mechanics that apply
to everything*; the exact per-tool command + price lives one level down.

> ⚠️ Commands and prices rot. This file holds stable **mechanics**; the volatile exact commands live
> in `reference/volatile/pricing-install.md` (time-stamped — verify against the official site before
> running). A newly added MCP only takes effect **after a session restart / `/mcp` reconnect**.

## The three levels — where to look

| level | file | holds |
|---|---|---|
| **L0 overview** (this file) | `reference/install-guide.md` | prerequisites, MCP transport types, the `add` mechanics, secret hygiene, Windows notes, how to verify |
| **L1 per-domain** | `reference/volatile/pricing-install.md` (+ each `domains/<domain>.md` "Install guidance" line) | the exact install command + price for every source, grouped by domain |
| **L2 per-tool** | `reference/tools/<slug>.md` → `## Install` | exact steps + auth + gotchas for one specific tool. Find the slug in `reference/tools/index.md` |
| **L3 ops state (recommended)** | `reference/companion-config-repo.md` | the recommended pattern for managing **your** install state — which tools *you* installed, *your* tier, *your* key rotation history — in a **per-user private companion repo** separate from this public matrix. Each user maintains their own; there is no canonical shared one. Templates committed, secrets gitignored, backed up out-of-band. |

Flow: triage the domain → open its shard → for the picked tool, read `tools/<slug>.md` `## Install`
(or the L1 line in `pricing-install.md`) → if it's an MCP, restart/reconnect before using it.

## Prerequisites (install once, reused by everything)

| prereq | why | check |
|---|---|---|
| **Node.js ≥ 18** (`npx`) | most stdio MCPs ship as npm packages | `node -v` |
| **Python ≥ 3.10 + uv** (`uvx`) | `uvx`-launched MCPs + pip-installed scraper libs | `uv --version` |
| **gh CLI** (authenticated) | GitHub-API verification + cloning OSS repos | `gh auth status` |
| **git** | clone self-host OSS repos (route ③④) | `git --version` |
| **playwright MCP** | route ④ default (act-like-human) — usually already connected | `claude mcp list` |
| **Docker** (optional) | self-host MCPs (crawl4ai, hummingbot, steel-browser…) | `docker --version` |
| **throwaway account + proxy pool** (route ③④ only) | platform scraping at scale; software is free, proxies are the hidden cost | — |

## MCP transport types — which to prefer

- **HTTP (hosted/remote)** — `claude mcp add --transport http <name> <url>`. **Prefer this on Windows**:
  no local Node/uv process, far fewer flakes. Many providers now ship a hosted MCP URL.
- **stdio (local `npx`/`uvx`)** — launches a local process per call. Works, but **flaky on Windows**
  (path/shell quirks). Use only when there is no HTTP option.

## Adding an MCP — two ways (and when to use each)

1. **`claude mcp add -s user <name> ...`** — convenient. ⚠️ But it **echoes the full command** (incl.
   any key in `--header`/URL) to stdout → the key lands in the transcript. **Never use this for a
   secret-bearing source.** Fine for no-key sources (HN, CoinGecko, GDELT…).
2. **Direct `~/.claude.json` edit** — for **secret-bearing** MCPs, write `mcpServers.<name>.headers`
   /url straight from the OS clipboard with a tiny no-echo script (see hygiene below). `-s user` scope
   makes a source reusable across projects.

## Secret-handling hygiene — HARD rules (keys leaked 3× in real runs; treat as non-negotiable)

A key must **never enter the transcript** (it can sync to the user's cloud backup). Configuring the
tool yourself is fine — leaking the value is not.

- **NEVER `browser_snapshot` a page that displays a key.** Provider dashboards render the API key in
  **plaintext in the DOM** (confirmed: twitterapi.io rotation page, Bright Data API-keys table).
  Instead: have the user click the page's **copy button**, read the OS clipboard
  (`powershell Get-Clipboard`), pipe it in, and **verify by length only — never print the value**.
- **For secret-bearing MCPs, do NOT use `claude mcp add`** (it echoes the `--header`/URL with the key).
  Edit `~/.claude.json` directly: a tiny python script reads the clipboard and writes
  `mcpServers.<name>.headers.Authorization` (or token-in-URL), with **no echo**.
- **Mask tokens when verifying**: token-in-URL servers print the token in `claude mcp list` → pipe
  through `sed -E 's/token=[^ &]*/token=***/'`.
- **Rotation cooldowns**: if a key leaks, rotate it — but check the provider's cooldown (e.g.
  twitterapi.io = once/24h). A truly transcript-clean key = the **user** rotates from their own browser.
- Keys land plaintext in `~/.claude.json` — **never commit/screenshot it.** The skill holds the
  *procedure*, not the key. Prefer `-e KEY=$VAR` forms the **user** runs themselves.

## Verify an install (always do this after adding)

- `claude mcp list` → parse the three-state health: only **`✓ Connected`** is usable. Treat
  **`✗ Failed`** and **`! Needs authentication`** as not available (they fail at call time).
- Mask any token first: `claude mcp list | sed -E 's/token=[^ &]*/token=***/'`.
- `claude mcp get <name>` for per-server detail.
- **Tool-name prefix matching (`mcp__*twitter*`) is unreliable** — deferred tools, plugin prefixes,
  and dead connections distort it. Use it only as a cross-check, never the primary signal.

## Install by barrier route (①②③④)

| route | what install looks like | cost shape |
|---|---|---|
| **① official API** | get key from provider dashboard → HTTP MCP or REST. Compliant, no ban risk | often paid/quota-limited; many free tiers |
| **② resale API** | provider key → HTTP MCP. Provider absorbs the account/proxy/login-wall barrier | cheap pay-per-use, gray-area |
| **③ self-host scrape** | `git clone` + `pip`/`npm install` → supply your own accounts + proxies | free software; you carry ToS/ban risk |
| **④ browser / act-like-human** | playwright MCP (already connected) or a per-platform OSS repo → supply a logged-in session/cookies | free; proxies at scale; most platform scraping violates ToS |

**Prefer ④/③ (free) over paid ①/② when equivalent** (CONSTITUTION C2). Reach for paid only for data
the free route can't get (e.g. Keepa price history), scale reliability, or compliance.

## Per-domain install entry points

For the exact command, open the L1 section in `pricing-install.md`, or the L2 `tools/<slug>.md`.

| domain | free-first pick (route) | L1 section |
|---|---|---|
| x-twitter | twikit ④③ / playwright ④ (twitterapi.io ② if you want the provider to absorb upkeep) | `pricing-install.md#x-twitter` |
| reddit-community | mcp-hn ① (no key) · reddit-mcp-buddy ① (zero-setup anon tier) | `#reddit-community` |
| web-scraping | Tavily/Exa ② + Firecrawl ② + Bright Data ② (free 5k/mo) | `#web-scraping` |
| ecommerce-arbitrage | Discount-Bandit ④ / playwright ④ (Keepa ① for history) | `#ecommerce-arbitrage` |
| finance-markets | SEC EDGAR + FRED ① (free, no/low key) | `#finance-markets` |
| crypto-defi | CoinGecko ① + ccxt + Etherscan/Blockscout ① (free) | `#crypto-defi` |
| seo-keywords | GSC ① (own site) + SearXNG ④ self-host | `#seo-keywords` |
| social-publishing | Buffer ① free-tier / twikit·xiaohongshu ④ · Bluesky/Mastodon official | `#social-publishing` |
| content-cms | static blog ④ (Hugo/Astro) / WordPress·Sanity MCP ① | `#content-cms` |
| leadgen-crm | gosom/google-maps-scraper ④ (low risk) / Apollo ① | `#leadgen-crm` |
| trends-discovery | GDELT ① (no auth) + Product Hunt ① | `#trends-discovery` |
| frontier-research | arXiv + HF Daily Papers ① (free, no key) | `#frontier-research` |
| ready-skills | `npx skills add coreyhaines31/marketingskills` (skill, not MCP) | shard `ready-skills.md` |
| browser-automation | playwright MCP ④ (connected) + browser-use/crawl4ai | `#browser-automation` |

## Windows-specific notes

- **Read `~/.claude.json` as UTF-8** — it contains non-ASCII paths; the default GBK decode crashes.
- **Prefer HTTP-transport MCPs**; stdio `npx`/`uvx` are flaky (path/shell). If you must use stdio,
  use absolute paths and test in a plain shell first.
- **PowerShell** for clipboard secret piping: `Get-Clipboard`.
- Prefer `claude mcp get`/`list` over raw JSON parsing when possible.

## When an install is missing mid-research (non-blocking protocol)

Never block on install. If a topic clearly depends on a missing source, tell the user the one-line
`claude mcp add` (or the `tools/<slug>.md` install) + cost, note that **it won't work until session
restart**, then **proceed with a fallback source and flag the gap** in the report (SKILL.md guardrail
#4 — no silent degradation).
