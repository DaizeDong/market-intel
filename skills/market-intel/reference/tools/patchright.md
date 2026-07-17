# Tool: patchright (Undetected-Playwright patch)

- **Domain(s):** web-scraping (also: browser-automation)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** no, it's a Playwright-API drop-in library (Python `patchright` / Node `patchright`), drive it from your own script or wire it under a playwright-style runner. No prebuilt MCP server.
- **Cost:** free, Apache-2.0 (no key, no quota) [github.com/Kaliiiiiiiiii-Vinyzu/patchright, fetched 2026-06]
- **Repo / Provider:** `Kaliiiiiiiiii-Vinyzu/patchright (3.4k★, gh-api 2026-06)` (umbrella/TS repo; the language packages are `patchright-python` 1.4k★ and `patchright-nodejs` 710★, both gh-api 2026-06). Apache-2.0, not archived, pushed 2026-06-03.
- **Top pick for its domain:** no (Bright Data ② is the top barrier-breaker; patchright is the free ④ fallback)

## What it does / when to pick it
A patched, undetected build of Playwright that fixes the runtime leaks (CDP `Runtime.enable`, console hooks, fingerprint tells) bot-detection vendors use to flag automation. As a near drop-in, it passes Cloudflare, DataDome, Akamai, Kasada, and F5/Shape on targets that vanilla Playwright trips. **Decision rule:** when you already use Playwright/browser-automation and a target throws CAPTCHAs or 403/challenge pages, swap to patchright before paying for a barrier-breaker, it's the free ④ route. Reach for **Bright Data** (②, free 5k/mo Rapid) instead when the block is IP-reputation based (datacenter-IP bans, geo-walls) rather than browser-fingerprint based, patchright cleans the fingerprint but still uses *your* IP, so it does not solve IP blocks on its own.

## Install
Python: `pip install patchright` then `patchright install chromium` (downloads its patched Chromium). Node: `npm i patchright` then `npx patchright install chromium`. Prereqs: Python ≥3.10 (or Node ≥18) per `install-guide.md` "Prerequisites". This is a **library, not an MCP**, there is no `claude mcp add` step and no HTTP/stdio transport to choose; you call it from a script (or behind crawl4ai/an agent runner). Windows note: the bundled Chromium download is large; if `patchright install` stalls behind a proxy, set the standard Playwright env (`PLAYWRIGHT_DOWNLOAD_HOST`), patchright reuses Playwright's download machinery. For IP-reputation targets, pair it with a residential proxy pool (the hidden cost of route ④; see `install-guide.md` Prerequisites). Volatile install line: `pricing-install.md` → web-scraping.

## Auth / keys
None. No account, no API key, no quota, it's a local OSS browser patch. The only "credential" is whatever logged-in session/cookies you feed the browser context for the target site (same as Playwright). No secret-hygiene step needed for the tool itself; if you load a target's session cookies, keep that cookie file out of the transcript and out of git.

## Usage, call examples
Identical surface to Playwright, change only the import. **Use the persistent-context launch for max stealth** (the README's recommended config); do not pass extra `--disable-blink-features` flags, which re-introduce tells.

```python
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir="./udir", channel="chrome",
        headless=False, no_viewport=True)   # README-recommended undetected config
    page = ctx.new_page()
    page.goto("https://target-behind-cloudflare.example")
    print(page.title())
```

Node: `const { chromium } = require('patchright');` then the usual `launchPersistentContext(...)`.

## General experience & gotchas (踩坑)
- **Fingerprint-only, not IP:** patches the browser so the *automation* is invisible, but the request still leaves *your* IP. Datacenter-IP / rate / geo blocks survive, that's the documented split vs Bright Data in the shard ("patches the browser fingerprint but needs a proxy for IP-reputation blocks; complements Bright Data").
- **Headless still leaks more than headful:** for the hardest targets (Kasada/DataDome) run headful + persistent context + real `channel="chrome"`. Pure `headless=True` raises detection odds.
- **Don't over-configure:** adding stealth args, extra flags, or other anti-detect wrappers on top can *re-add* the very signals patchright removed. Use its recommended config as-is.
- **Tracks upstream Playwright:** it's a patch over Playwright releases, so a brand-new Playwright version may briefly lag. Pin a working version for a long-running scraper.
- **Same Chromium download weight** as Playwright (~hundreds of MB) on first `install`.

## Failure signals & fallback
Failure looks like: persistent CAPTCHA/JS-challenge interstitials, `403`/`429`, Cloudflare "checking your browser" loops, or a `cf_clearance`/challenge page in the DOM that never resolves. **If patchright still gets blocked: (1)** add a residential proxy and retry (most ④ blocks are now IP-based); **(2)** escalate to **Bright Data Web Unlocker** (② route, free 5k/mo Rapid, no card) which absorbs both fingerprint *and* IP-reputation; **(3)** for managed self-host, **crawl4ai** (③, docker MCP) wraps similar auto-anti-bot. For ordinary JS-render scrapes that aren't actually barrier-blocked, **Firecrawl** (②) or the already-connected **playwright MCP** (④) is simpler than scripting patchright.

## Last verified: 2026-06
