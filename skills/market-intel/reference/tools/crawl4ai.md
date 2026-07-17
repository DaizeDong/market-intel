# Tool: unclecode/crawl4ai

- **Domain(s):** browser-automation (also: web-scraping, trends-discovery)
- **Barrier route:** ③ · **Source tier:** L2 · **Ready MCP:** yes, docker MCP (also usable as a Python lib)
- **Cost:** free (open source, Apache-2.0). Self-host = zero API cost; LLM tokens only if you use the optional LLM-extraction strategy; proxies at scale.
- **Repo / Provider:** github.com/unclecode/crawl4ai, `unclecode/crawl4ai (68.1k★, gh-api 2026-06)`, Apache-2.0, pushed 2026-06
- **Top pick for its domain:** yes

## What it does / when to pick it
LLM-friendly crawler that renders pages and emits clean **Markdown / structured JSON** ready for an LLM, with **built-in anti-bot** (handles many Cloudflare/Akamai cases) at zero API cost. The zero-cost self-host crawl 首选. **Pick it over playwright MCP** for **bulk** crawling (many URLs, whole-site, or "fetch + clean to Markdown" pipelines) and when plain Playwright gets soft-blocked. Pick browser-use/stagehand instead for goal-driven interaction (login flows, clicking through a portal); crawl4ai is read/extract-oriented, not a click-the-buttons agent.

## Install
`pip install crawl4ai` then `crawl4ai-setup` (installs Playwright browsers), **or** run the Docker image which exposes a **ready MCP**, preferred for a clean, reproducible server (see `install-guide.md` Docker prereq). L1 line: `reference/volatile/pricing-install.md#browser-automation`. Docker/HTTP route is the Windows-friendly path (avoids native Playwright path quirks).

## Auth / keys
No service key for crawl4ai itself. Only needs an **LLM API key** if you opt into `LLMExtractionStrategy` (schema/NL extraction); the default CSS/XPath/Markdown extraction needs no key. Target auth = cookies/headers you pass. Key-bearing only in LLM-extraction mode: set the LLM key via env, keep it out of the transcript (see `install-guide.md` secret hygiene).

## Usage, call examples
```python
from crawl4ai import AsyncWebCrawler
async with AsyncWebCrawler() as c:
    r = await c.arun(url="https://site/page")
    print(r.markdown)        # clean LLM-ready markdown
```
For structured output use `JsonCssExtractionStrategy` (free, selector-based) or `LLMExtractionStrategy` (token-cost, schema-driven). Via Docker MCP: call the crawl tool with `{url, extraction_strategy}` and read back markdown/JSON.

## General experience & gotchas (踩坑)
- **Best free first hop for "fetch + clean to Markdown" at volume**, its anti-bot clears many soft Cloudflare/Akamai walls that stop plain Playwright, at zero per-request cost (unlike Firecrawl/Bright Data ②).
- **Prefer CSS/XPath extraction over LLM extraction** to stay free and deterministic, only reach for `LLMExtractionStrategy` when the page structure is irregular; it adds token cost per page.
- **Not an interaction agent.** It reads/extracts; it won't reliably log in, click through paginated portals, or fill forms. For that use browser-use/stagehand/skyvern.
- **Hard anti-bot still wins.** Aggressive DataDome / per-request CAPTCHA / heavy JS-fingerprinting will still block it, signal: 403, challenge HTML in `.markdown`, empty result. Then add patchright/camoufox, or hand it to Bright Data ② (provider absorbs the barrier). For e-commerce price work specifically, prefer the e-commerce shard's picks (Keepa ①, Bright Data ②) over raw crawling, Amazon returns 500/blocks to generic crawlers.
- Proxies are the hidden cost at scale; the software is free.

## Failure signals & fallback
Failed = 403 / challenge page text in the markdown / empty result, or you actually need to click/log in. Fallbacks: **patchright/nodriver/camoufox** (fingerprint), **browser-use/stagehand** (interaction needed), **Firecrawl ② or Bright Data ②** (let a provider absorb the anti-bot barrier).

## Last verified: 2026-06
