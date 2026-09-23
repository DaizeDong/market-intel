# Tool: Firecrawl (skill `firecrawl`)

- **Domain(s):** web-scraping (also: none)
- **Barrier route:** ② resale API · **Source tier:** L2 · **Ready MCP:** yes, `npx -y firecrawl-mcp`; CLI and skill `firecrawl` provide a separate usable route
- **Cost:** free **1,000 credits/mo** (firecrawl.dev, refreshed 2026-06, was "500 one-time"), cheapest paid Hobby ~$16/mo; confirm current tiers at https://www.firecrawl.dev/pricing [fetched 2026-06]
- **Repo / Provider:** github.com/firecrawl/firecrawl, `firecrawl/firecrawl (176.4k★, gh-api 2026-06)`; active (pushed 2026-06-09, not archived, AGPL-3.0, verified gh-api 2026-06-09)
- **Top pick for its domain:** yes (the default JS-render SCRAPE/crawl pick)

## What it does / when to pick it
Hosted JS-rendering scraper: `scrape` one page to clean markdown, `crawl` a whole site, `map` its URLs, and `extract` structured JSON via a schema/prompt. **Decision rule:** pick Firecrawl when you need the *rendered content* of a normal (non-hardened) site, docs, blogs, marketing pages, catalogs that load via JS. Its hosted stealth handles many sites the built-in WebFetch can't (WebFetch runs no JS, uses your IP). Step UP to **Bright Data** (②) when the target actively blocks you (Cloudflare/DataDome/CAPTCHA, Amazon/Taobao/Reddit). The `firecrawl` skill claims to take over all web ops, route general web through it, but keep Tavily/Exa for SERP and Bright Data for barrier work (shard).

## Install
Hosted scraper behind an MCP. Ready skill `firecrawl` is present, prefer it. Raw MCP: `npx -y firecrawl-mcp` (stdio; flaky on Windows, see L0). Exact command + key origin: `reference/volatile/pricing-install.md → web-scraping`. The repo is AGPL-3.0 if you self-host (note the copyleft); the shard warns **self-host is weak vs WAF**, use the hosted API for hard targets. L0 mechanics: `reference/install-guide.md`. Restart / `/mcp` reconnect after adding.

## Auth / keys
Free key from firecrawl.dev (1,000 credits/mo as of 2026-06; was 500 one-time). **Secret hygiene (one line):** edit `~/.claude.json` from clipboard instead of `claude mcp add` for the key-bearing form, and never `browser_snapshot` the key page, `reference/install-guide.md`.

## Usage, call examples
For the CLI, inspect `firecrawl --status` and `<command> --help`, then make a small request.
Save real results under the private companion DATA directory, never inside the public skill repo.
`firecrawl search "<query>" --limit 3 --scrape --json -o <private-output>` returns search evidence;
`firecrawl scrape "<url>" -o <private-output>` fetches a known page. CLI authentication may live in
its own credential file, separately from MCP/API environment files. Include it in the private
account inventory and recovery manifest. Installation success is not content validation.

MCP tools: `firecrawl_scrape(url, formats:["markdown"])`, `firecrawl_crawl(url, limit)`, `firecrawl_map(url)`, `firecrawl_extract(urls, schema|prompt)`, `firecrawl_search(query)`. Minimal: `firecrawl_scrape` a single URL → clean markdown. For structured fields use `extract` with a JSON schema rather than post-parsing markdown.

## General experience & gotchas (踩坑)
- **Interface update checked 2026-09-23:** the July 22 search update returns relevance-scored excerpts.
  Excerpts can omit dates and qualifications; fetch the original before making a dated claim.
  See https://www.firecrawl.dev/blog/introducing-our-most-accurate-search-yet.
- The March 2026 interact workflow extends a scrape into a page session. Use it only when interaction
  is necessary, and preserve full browser authentication state through the host's established flow.
  https://docs.firecrawl.dev/features/interact documents the capability; it is not an account-stability guarantee.
- Benchmark improvements advertised by the provider remain interested-party evidence.
- **Real-run lesson (shard, 2026-06): Amazon product pages return HTTP 500 to Firecrawl/WebFetch (anti-bot).** Do NOT spend fan-out rounds trying Firecrawl on Amazon/Taobao/Tmall live prices, go straight to playwright(④)/Bright Data. Taobao/Tmall also hide the real per-SKU price behind a login wall Firecrawl can't pass.
- **Reddit returns empty** to this layer (shard), use a Reddit-API tool, not Firecrawl.
- **Self-host is weak vs WAF** (shard), the OSS version lacks the hosted stealth/proxy pool; for protected sites you must use the hosted API (which spends credits) or escalate to Bright Data.
- The free 1,000 credits/mo can still be burned fast by a single large `crawl`, cap `limit` and prefer `scrape`/`map` over blind full-site crawls.
- `crawl` is async/long-running and can stall on large sites or infinite-scroll; `extract` with a tight schema is cheaper and more reliable than crawling then parsing.
- AGPL-3.0: fine for self-use, but the copyleft matters if you embed it in a distributed product.

## Failure signals & fallback
Failure looks like: HTTP 500 / blocked / CAPTCHA page returned as "content", empty markdown on a JS page, or a crawl that never completes. **Fallback ladder:** anti-bot/CAPTCHA/Amazon/Taobao/Reddit → **Bright Data** Web Unlocker (②, strongest barrier-breaker); a single interactive/login-walled page → already-connected **playwright MCP** (④); finding URLs in the first place → **Tavily/Exa** (②); zero-cost self-host crawler → **crawl4ai** (③).

## Last verified: 2026-06

Search/CLI interface checked 2026-09-23. The older price, repository and platform-specific
observations above retain their original dates; this scoped update does not re-verify them.
