# Tool: botasaurus (anti-detection scraping framework)

- **Domain(s):** browser-automation (also: web-scraping, ecommerce-arbitrage)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** no, it's a Python library, drive from your own script.
- **Cost:** free, MIT [github.com/omkarcloud/botasaurus, fetched 2026-06]
- **Repo / Provider:** `omkarcloud/botasaurus (5.6k★, gh-api 2026-08-01)`. MIT, active.
- **Top pick for its domain:** no, playwright MCP is the default ④ route; botasaurus is the **library-of-record** for omkarcloud's catalog of single-target scrapers (amazon-scraper, google-maps-scraper, etc.). Reach for it when you're cloning one of those repos or writing a quick anti-detection scraper without spinning up a full playwright wrapper.

## What it does / when to pick it
Drop-in Python framework for writing scrapers that pass most anti-bot stacks (Cloudflare, DataDome, Akamai). Wraps a stealthed Chromium driver with built-in proxy rotation, captcha solving, and a `@request`/`@browser` decorator API. **Decision rule:** if you're cloning `omkarcloud/<X>-scraper` (the omkarcloud Amazon / Maps / etc. repos), you need botasaurus installed as their foundation. For standalone use, prefer **patchright** (more current undetected-Playwright patch) unless you specifically want botasaurus's batteries-included proxy + captcha plumbing.

## Install
`pip install botasaurus`. Python ≥ 3.10. First run downloads its Chromium. To use one of omkarcloud's single-target scrapers: `git clone https://github.com/omkarcloud/<scraper>-scraper && python main.py`. The scrapers are repos, not pip packages, only the framework ships on PyPI.

## Auth / keys
None for the framework. The scrapers built on top may need site cookies (Amazon scraper for `Buy Box` data, etc.), keep those out of git per `install-guide.md` secret hygiene.

## Usage, call examples
```python
from botasaurus.browser import browser, Driver

@browser(headless=False, block_images=True)
def scrape(driver: Driver, link):
    driver.google_get(link, bypass_cloudflare=True)
    return driver.get_text("h1")

scrape("https://target.example/product/123")
```

## General experience & gotchas (踩坑)
- **Heavy install:** Chromium download + framework deps add ~500MB.
- **omkarcloud's PyPI namesakes are decoy/stale.** `pip install amazon-scraper` is NOT omkarcloud's, it's a 2020 unrelated package that pins `requests<2.30` and breaks your env. omkarcloud's scrapers are **git-clone only**.
- **Proxy pool sold separately.** Built-in residential-proxy plumbing exists but you bring the proxies. Cloudflare-bypass mode lights up the proxy code path even when not needed.
- **Pace yourself.** Default to throttled scraping; the framework can fan out fast and trip rate limits even on stealthed connections.

## Last verified: 2026-06
