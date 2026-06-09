# Tool: playwright MCP

- **Domain(s):** browser-automation (also: x-twitter, web-scraping, ecommerce-arbitrage, seo-keywords, frontier-research)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** yes — already connected (verify `claude mcp list` → playwright ✓)
- **Cost:** free (open source; your own machine/session). No API fee.
- **Repo / Provider:** github.com/microsoft/playwright-mcp — `microsoft/playwright-mcp (33.7k★, gh-api 2026-06)`, Apache-2.0, pushed 2026-06
- **Top pick for its domain:** yes

## What it does / when to pick it
Drives a real Chromium with your logged-in session: navigate, click, fill forms, screenshot, read the rendered DOM (`browser_snapshot`), run JS. It is the **default first tool** for any bespoke "act like a human" task — reach for it before any paid API when (a) the API is expensive/quota-capped, (b) you need the real logged-in/rendered view, or (c) no ready repo covers the target. Escalate away from it only when it's too low-level (use browser-use / crawl4ai for AI-goal-driven extraction) or gets fingerprint-blocked (escalate to camoufox/nodriver).

## Install
Already connected in this environment — nothing to install. Verify with `claude mcp list` (look for `playwright ✓ Connected`). If absent, it's the official MS package; see `reference/install-guide.md` for MCP-add mechanics. No key, no proxy for basic use.

## Auth / keys
No API key. Auth is **per-site session state** in the browser profile (cookies). For logged-in targets, the user logs in once in the driven browser; the session persists in the profile. No secret-hygiene concern (no key), but treat the browser profile as sensitive — it carries live login cookies.

## Usage — call examples
MCP tools (prefix `mcp__plugin_playwright_playwright__`): `browser_navigate`, `browser_snapshot` (accessibility-tree text, cheaper than a screenshot), `browser_click`, `browser_type`, `browser_fill_form`, `browser_take_screenshot`, `browser_evaluate`, `browser_wait_for`, `browser_network_requests`.
Minimal: `browser_navigate {url}` → `browser_snapshot` to read the rendered page → `browser_click {ref}` using a ref from the snapshot.

## General experience & gotchas (踩坑)
- **Prefer `browser_snapshot` over screenshots** for reading — it returns the accessibility tree as text (refs to click), far more token-efficient than an image, and is what you act on.
- **Too low-level for multi-step goals.** For "log in and extract X across N pages," scripting every click burns context; switch to browser-use (NL goals) or crawl4ai (bulk crawl).
- **Fingerprint blocks.** Plain Chromium gets caught by Cloudflare/DataDome on hardened targets (some e-commerce, social). Signals: CAPTCHA wall, infinite challenge loop, 403/empty DOM. Then escalate to patchright/nodriver/camoufox, or hand the barrier to Bright Data ②.
- **Single browser, serial.** No built-in proxy pool or parallelism — at scale use crawlee/crawl4ai. Heavy SPA pages need explicit `browser_wait_for` or you snapshot a half-rendered DOM.
- **ToS / ban risk** on platform scraping — use throwaway accounts for write/scrape-heavy work; never drive the user's primary social login for bulk scraping.
- For consumer-demand research, X is low-signal — don't burn playwright steps scraping X timelines; prefer Reddit/forums.

## Failure signals & fallback
Failed = CAPTCHA/403/empty or half-rendered DOM, or step-count exploding on a multi-page goal. Fallbacks in order: **browser-use** (let an LLM drive the goal) → **crawl4ai** (bulk + auto anti-bot) → **patchright/nodriver/camoufox** (fingerprint) → **Bright Data ②** (provider absorbs the barrier).

## Last verified: 2026-06
