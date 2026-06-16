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
| **L3a ops state — overview** | `reference/companion-config-repo.md` | the recommended pattern + tutorial for managing **your** install state in a per-user private companion repo separate from this public matrix |
| **L3b ops state — formal spec** | `reference/companion-config-spec.md` (version 1) | machine-readable contract: discovery convention, `registry.json` schema, template formats, conformance checklist. What skills + tooling actually consume. |
| **L3c ops state — GitHub hardening** | `reference/companion-config-hardening.md` | 12-step lockdown runbook for a freshly-created private repo (visibility, Features off, Actions disabled, GitHub Apps audit, Copilot training opt-out). **Run before the first push.** |

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
  Instead: have the user click the page's **copy button**, read the OS clipboard using whichever
  command fits the user's shell (Windows PowerShell: `Get-Clipboard`; macOS: `pbpaste`; Linux:
  `xclip -o` or `wl-paste`), pipe it in, and **verify by length only — never print the value**.
- **For secret-bearing MCPs, do NOT use `claude mcp add`** (it echoes the `--header`/URL with the key).
  Edit `~/.claude.json` directly: a tiny python script reads the clipboard and writes
  `mcpServers.<name>.headers.Authorization` (or token-in-URL), with **no echo**.
- **Mask tokens when verifying**: token-in-URL servers print the token in `claude mcp list` → pipe
  through `sed -E 's/token=[^ &]*/token=***/'`.
- **Rotation cooldowns**: if a key leaks, rotate it — but check the provider's cooldown (e.g.
  twitterapi.io = once/24h). A truly transcript-clean key = the **user** rotates from their own browser.
- Keys land plaintext in `~/.claude.json` — **never commit/screenshot it.** The skill holds the
  *procedure*, not the key. Prefer `-e KEY=$VAR` forms the **user** runs themselves.
- **Clipboard-capture sanity gates** — when piping a key from clipboard, reject anything outside
  `length ∈ [8, 512]`, anything containing whitespace, or anything matching `^https?://` (someone
  copied a URL by mistake). These cheap checks catch ~all paste-by-mistake errors before the value
  reaches `~/.claude.json`. Reference impl: companion-config-repo's `scripts/capture-key.ps1`.

## Anti-automation patterns to expect during install

Real-world batch registrations across 2026-06 hit these bot defenses. **None can be bypassed
headlessly**; the agent's job is to recognize the pattern fast, stop wasting cycles, and hand
off cleanly to the user with the right URL + clipboard handoff. Recording them here so a
first-time-setup user knows what to expect *before* clicking signup.

| Defense | Where we hit it | What it looks like | Workaround |
|---|---|---|---|
| **PerimeterX / Akamai fingerprint deny** | Webflow `/signup` | "Access to this page has been denied" served on first navigation | User-only signup in a normal browser |
| **Cloudflare Turnstile** | Buffer `/signup` | Submit button hangs in "Signing Up..." waiting for Turnstile token the headless browser never produces | User-only signup |
| **reCAPTCHA + hCaptcha double gate** | Contentful post-Google-OAuth lead-gen form | OAuth completes, but the follow-up form has `g-recaptcha-response` + `h-captcha-response` textareas; submit silently no-ops without both solved | User clears both captchas |
| **hCaptcha on forgot-password** | eBay `/fyp` | DOM has `target-icaptcha-slot` + 2 hcaptcha iframes; "Send Now" stays `disabled` | User solves captcha first |
| **B2B work-email gate** | Attio, Lusha | Rejects `gmail.com`; Attio's Google OAuth callback redirects to `email_is_public=1` error; Lusha's signup placeholder says "Enter your work email" | Skip unless you have a work-domain email |
| **readonly+disabled with active watcher** | Apollo onboarding wizard | Inputs render `readonly disabled`; if JS removes attrs, a watcher reapplies within milliseconds — defeats `playwright.fill`, JS event dispatch, attr removal | User-driven onboarding only |
| **OAuth provider mismatch** | HubSpot CRM signup | Only Microsoft / Apple / email; some matrices say Google but the page doesn't offer it | User chooses Microsoft or email + captcha |
| **Provider-side approval delay** | eBay developer | New developer account shows "Access to your new account is pending approval, which takes at least one business day" — not a bot defense, fraud-prevention policy | Wait 1 business day, re-check `/my/keys` |
| **Email-verification email out of reach** | SerpApi, Buffer, Contentful, ZeroBounce, Mastodon | Verification email goes to the signup mailbox (e.g. `user1@example.com`); if the agent's Gmail MCP is bound to a *different* Google account (e.g. user's claude.ai login), agent can't read it | User opens the mailbox, clicks link, then continues |
| **Multi-step React onboarding wizards** | Sanity (8 steps), Apollo, FMP (5 questions) | Radio buttons rendered with `sr-only` (visually hidden) `<input>` under cosmetic labels; sticky header intercepts `playwright.click`; "Next" only enables after React state validates inputs | Click the `label[for=...]`, not the hidden input; use JS `.click()` to bypass sticky-header pointer interception; tolerate that some wizards need real keystrokes |

### DOM-visible plaintext credentials — a transcript-hygiene hazard

Several providers render the secret in **readable plaintext** on the dashboard page (no
masking, no copy-only button):

- **Twelve Data** `/account/api-keys` — key in the page DOM unmasked.
- **FMP** dashboard — key in the page DOM unmasked.
- **Mastodon** `/settings/applications/<id>` — all 3 of `client_key`, `client_secret`,
  `access_token` rendered simultaneously as readonly plaintext inputs.
- **Bluesky** App Password dialog — shows the password ONCE with no copy button; agent must
  read the DOM string before the user closes the dialog.
- **Stack Apps** new-API-key dialog — masks all but last 4 chars in the visible cell, but
  the actual full value is reachable via `navigator.clipboard.writeText` from a hidden
  readonly input — the agent must copy from DOM, not from the masked display.

When the agent reads any of these via `browser_evaluate`, the **full value enters the
conversation transcript**. Under Mode A (committed-secrets) the residual exposure is
tolerable; under Mode B prefer one of:

1. Have the user click the page's own copy button, then `Get-Clipboard | length-verify`.
2. Use `navigator.clipboard.writeText(...)` from inside the page (browser-side), then read
   clipboard — never returns the value to the JS evaluation result.

See [`companion-config-hardening.md`](companion-config-hardening.md) for the wider Mode
A vs Mode B trade-off.

## Troubleshoot a non-Connected MCP

When `claude mcp list` shows `✗ Failed` or `! Needs authentication`, the cause is almost always
one of five categories. Walk these in order:

| symptom | likely cause | first move |
|---|---|---|
| `! Needs authentication` | OAuth token expired or never completed | run `/mcp` and re-OAuth the server |
| `✗ Failed` for stdio MCP, immediate exit | `uvx`/`npx` not on PATH, or absolute path wrong | shell-test the exact `command + args` line outside Claude; check `uv --version` / `node -v`; on Windows see `uv-path.md`-style PATH gotchas |
| `✗ Failed` for HTTP MCP | Bearer token wrong / rotated / quota exceeded | `curl -H "Authorization: Bearer $TOKEN" <url>/health` to isolate transport vs auth |
| `✗ Failed` with env var error in logs | required env var missing from `mcpServers.<name>.env` | re-check `tools/<slug>/env.template` against `secrets/<slug>.env`; common miss: `_STORAGE_DIR` paths that need pre-creating |
| `✓ Connected` but actual tool calls fail | provider subscription gate (free tier read-only, etc.) | check provider dashboard for plan + quota; `functional-test.py`-style JSON-RPC ping catches this where `claude mcp list` doesn't |

If still stuck, the active session's `~/.claude/logs/` directory has per-MCP stderr capture —
search for the server name in the most recent log file.

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
