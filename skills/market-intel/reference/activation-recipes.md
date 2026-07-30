# Activation recipes, turning cold / needs-key tools into usable ones

> **Why this file exists.** "A tool that can't be invoked = it doesn't exist." Run `python tools/console.py
> status` for the LIVE available count (illustrative: ~81/168 as of 2026-06; it drifts as you configure
> tools); the rest are blocked on `needs-install`, `cold-mcp` (configured-but-not-connected), or
> `needs-key`. This guide ranks the highest-value blockers by
> **value × ease-to-activate, free-first**, and gives a verified recipe for each. It does NOT fill in
> keys for you, per the "登录/付款交接" rule, the recipe stops at "USER pastes the key"; you only
> produce the recipe and run the keyless install steps.
>
> **Scope vs other files.** The *exact* install command + price lives in
> `reference/volatile/pricing-install.md` (time-stamped, rots fast) and per-tool gotchas in
> `reference/tools/<slug>.md`. This file is the **decision layer**: what to activate first and why.
> When a command and this guide disagree, the volatile file + the live provider page win, re-verify.
>
> **The mechanics every recipe assumes** (full detail: `reference/install-guide.md`):
> 1. `python tools/console.py connect <slug>` prints the `~/.claude.json` mcpServers template (it
>    never writes the file and never touches a key).
> 2. Secret hygiene (keys have leaked in real runs): never `browser_snapshot` a key page, never
>    `claude mcp add` a secret-bearing server (it echoes the key into the transcript), have the USER
>    paste the key into `~/.claude.json` directly, verify by length only.
> 3. A freshly added MCP does **not** take effect mid-turn, restart the session or run `/mcp`, then
>    `claude mcp list` should show it ✓ Connected.
> 4. `pip`/`uvx` libs: on the **first** `pip install` of a session, ask the user where it should land
>    (`reference/install-guide.md` "Python install target").

## Last verified: 2026-06

Every URL / free-tier quota / death-state below was checked against the provider or the matching
`reference/tools/<slug>.md` (each carries its own `Last verified: 2026-06`) during the 2026-06 sweep.
Items I could not independently confirm are tagged **`verify-before-signup`**, do not treat those as
guaranteed. No URL in this file was written from memory.

---

## 🕒 The 30-minute max-coverage clinic (do these first)

These are the highest coverage-per-minute moves: each one flips a **zero- or thin-coverage domain**
to "available now" for **free** (free-key or free-tier or no-key self-host). Ordered by gain.

| # | activate | class | unlocks (domain: 0→usable) | minutes | recipe ↓ |
|---|---|---|---|---|---|
| 1 | **FRED MCP** + **Finnhub** | free-key | finance-markets, macro + quotes/alt-data on top of the already-free SEC EDGAR | ~5 | [F1](#f1-fred) [F2](#f2-finnhub) |
| 2 | **Tavily** (or **Exa**) | free-tier | web-scraping, agent-grade search layer over WebFetch/WebSearch (1,000 free/mo) | ~3 | [W1](#w1-tavily--exa) |
| 3 | **Firecrawl** | free-tier | web-scraping, JS-render scrape/crawl/extract (1,000 free credits/mo) | ~3 | [W2](#w2-firecrawl) |
| 4 | **Etherscan** + **CoinMarketCap** | free-key | crypto-defi, on-chain reads + quotes (CoinGecko already free; these add depth) | ~5 | [C1](#c1-etherscan) [C2](#c2-coinmarketcap) |
| 5 | **Product Hunt MCP** | free-key | trends-discovery, launch tracking (free PH dev token; install-no-key for GDELT already done) | ~4 | [T1](#t1-product-hunt) |
| 6 | **crawl4ai** (self-host) + **SearXNG** (self-host) | install-no-key | web-scraping + seo-keywords, zero-cost crawl + a private SERP API | ~10 (Docker) | [W4](#w4-crawl4ai) [S3](#s3-searxng) |
| 7 | **Hunter.io** | free-tier | leadgen-crm (0/16!), email find+verify, 25 searches+50 verifies/mo free | ~3 | [L1](#l1-hunter) |
| 8 | **twikit** (lib, no key) | install-no-key | x-twitter (0/4!), free X read+write via cookies (throwaway acct) | ~5 | [X1](#x1-twikit) |

**Honest gain math.** Items 1 to 5 are the fastest *available-now* flips because they're free and
mostly hosted-HTTP (Windows-friendly, no local process). Items 6 to 8 take longer (Docker / pip / a
throwaway account) but they're the only way to put a **dent in the three 0%-coverage domains**
(leadgen-crm 0/16, x-twitter 0/4, ecommerce-arbitrage 0/9). The single biggest free win for
ecommerce-arbitrage is **install-no-key** (`amazon-scraper` / `discount-bandit` / playwright) because
its only ①-route picks (Keepa) are paid, see [E-block](#ecommerce-arbitrage-the-free-route-is-route-).

> **Top-5 unlock summary (for the report):** FRED (finance, free-key) · Tavily (web-scraping,
> free-tier) · Firecrawl (web-scraping, free-tier) · Etherscan (crypto, free-key) · Hunter
> (leadgen-crm 0→usable, free-tier). All five are free; none requires payment.

---

## Activation classes (legend)

- **free-key**, free signup yields an API key, no card, real usable quota.
- **free-tier**, a SaaS with a genuine free plan/credits (no card) plus paid tiers above.
- **install-no-key**, `pip` / `uvx` / `docker` self-host, no provider account at all (target-site
  cookies/proxies may still be needed for scrapers).
- **paid**, costs money to activate; price noted. Listed only when it's the realistic unlock for a
  domain with no free route.

---

## Finance-markets (currently 3/12 → free path to ~6/12)

The free start is **SEC EDGAR (already usable) + FRED + Finnhub**, then Twelve Data as the realtime leg.

### F1 · FRED
- **Unlocks:** 800k+ macro series (GDP, CPI, rates, unemployment), the macro backdrop a single
  ticker can't give. `cold-mcp` today (template exists, not connected).
- **Class:** free-key. FRED is a public St. Louis Fed source; key is free + instant, no paid tier.
- **Key source:** request at **fred.stlouisfed.org** → account → API keys. *(verified, see
  `tools/fred-mcp.md`)*
- **Steps:** `python tools/console.py connect fred-mcp` → USER puts `FRED_API_KEY` in the printed
  stdio config (or `~/.claude.json`) → `/mcp`. Series are keyed by FRED codes (`CPIAUCSL`, `GDP`,
  `UNRATE`, `DGS10`), search first, then pull. Exact `uvx` command: `pricing-install.md → finance-markets`.

### F2 · Finnhub
- **Unlocks:** quotes + fundamentals + **alt-data** (news / Reddit / Twitter sentiment, congress
  trades). Best free rate limit in the domain (**60 req/min**). `cold-mcp` today.
- **Class:** free-key.
- **Key source:** **finnhub.io** → signup → dashboard. *(verified, `tools/finnhub.md`)*. Paid tiers
  above: `verify-before-signup` at https://finnhub.io/pricing.
- **Steps:** `python tools/console.py connect finnhub` → USER sets `FINNHUB_API_KEY`. **Gotcha:**
  create the cache dir (`FINNHUB_STORAGE_DIR`) before first run or the stdio process exits silently.

### F3 · Twelve Data, realtime leg
- **Unlocks:** multi-asset realtime (stocks/forex/crypto). `needs-install` (lib).
- **Class:** free-key. **Free 800 req/day (8/min)** *(verified, `tools/twelve-data.md`)*.
- **Key source:** **twelvedata.com** (pricing https://twelvedata.com/pricing). Paid Grow $79 / Pro $229.

### F4 · FMP, pre-parsed financials/valuation
- **Class:** free-key. **Free 250 req/day (US stocks)** *(verified, `tools/fmp.md`)*.
- **Key source:** **site.financialmodelingprep.com** (pricing page 403s to bots; web-corroborated 2026-06).
- Note: REST only, no MCP, wrap it or call REST directly.

### F5 · Polygon.io / "Massive", the paid upgrade
- **Class:** paid (free 5 req/min exists but is thin). Polygon rebranded to **Massive** (massive.com,
  301 redirect; keys unchanged). Paid $29 / $79 / $199. Reach for it only when the free trio isn't
  enough for deep history / WebSocket realtime. `needs-key`. `tools/polygon.md` + `polygon.auto.md`.

> **Already free, no activation needed:** SEC EDGAR (User-Agent only), yahoo-finance-mcp (no key, but
> yfinance scrapes Yahoo, not for prod). **Dead, don't try:** IEX Cloud (sunset 2024-08-31),
> Alpha Vantage free is 25/day (worst free tier in class). See `domains/finance-markets.md`.

---

## Web-scraping (currently 1/9 → free path to ~5/9), the highest-leverage domain

WebFetch (no JS, your IP) + WebSearch (title+url only) are weak floors. Layer these on top.

### W1 · Tavily / Exa, the search layer
- **Unlocks:** agent-ranked semantic search with date/domain filters. `needs-key` (Tavily) / `needs-key` (Exa).
- **Class:** free-tier.
  - **Tavily:** free **1,000 credits/mo, no card**, **tavily.com** (pricing https://www.tavily.com/pricing). *(verified, `tools/tavily.md`)*. Hosted HTTP MCP (Windows-friendly).
  - **Exa:** free **1,000 req/mo with key** (or ~150/day no-key), **exa.ai** + ready skill `exa-search`. *(verified, `tools/exa.md`)*. Gotcha: signup has a Cloudflare challenge before Google OAuth; the onboarding wizard offers $10 credit but gates the `/api-keys` page until done.
- **Steps:** `python tools/console.py connect tavily` (or `exa`) → USER pastes the key (Tavily rides
  it in the URL `?tavilyApiKey=...`; do NOT `claude mcp add` it, edit `~/.claude.json`) → `/mcp`.
- **Limit:** search/extract only, neither defeats anti-bot; hand hard targets to W2/W3.

### W2 · Firecrawl, the JS-render scrape layer
- **Unlocks:** `scrape` to clean markdown, `crawl` a site, `map` URLs, `extract` structured JSON.
- **Class:** free-tier. Free **1,000 credits/mo** *(verified, `tools/firecrawl.md`; was 500 one-time,
  refreshed 2026-06)*. **firecrawl.dev** (pricing https://www.firecrawl.dev/pricing). Ready skill `firecrawl`.
- **Steps:** ready skill is present, prefer it. Raw MCP: `npx -y firecrawl-mcp`, key from firecrawl.dev.

### W3 · Bright Data, the barrier-breaker (free tier exists)
- **Unlocks:** Web Unlocker (beats Cloudflare/DataDome/CAPTCHA), unlocks Amazon/Taobao/Reddit, plus
  curated datasets. `cold-mcp` today.
- **Class:** free-tier, **free 5,000 req/mo (Rapid, no card)** *(verified, `tools/brightdata.md`)*.
  Token from **brightdata.com** dashboard → Settings → "Users and API keys". Pricing
  https://brightdata.com/pricing.
- **HARD secret note:** the token is shown PLAINTEXT in the table and **leaked in real runs**, USER
  copies it, never `browser_snapshot`, write the URL by direct `~/.claude.json` edit (hosted HTTP
  `mcp.brightdata.com/mcp?token=...`), verify masked.

### W4 · crawl4ai, free self-host crawl
- **Unlocks:** LLM-friendly crawler with built-in anti-bot (handles many Cloudflare/Akamai cases) at
  **zero API cost**. `needs-install` today.
- **Class:** install-no-key (LLM key only if you opt into LLM-extraction). Apache-2.0, `unclecode/crawl4ai`.
- **Steps:** `pip install crawl4ai && crawl4ai-setup`, **or** the Docker image (exposes a ready MCP,
  preferred on Windows). `pricing-install.md → web-scraping`.

### W5 · DataForSEO, cheap bulk SERP
- **Class:** paid-but-cheap (~$0.0006/query; **$1 trial + free Sandbox** of mock data; $50 min for
  production) *(verified, `tools/dataforseo.md`)*. **dataforseo.com**. `cold-mcp`. **Gotcha:** the
  "password" is the dashboard **API password**, not the account login password (silent 401 otherwise).

> **Already free, no activation needed:** patchright (`pip install patchright`, undetected-Playwright,
> free), and the connected playwright MCP. **Real-run lesson:** for live e-commerce prices skip
> Firecrawl/WebFetch (Amazon 500s, Taobao login-walls), go straight to playwright(④)/Bright Data.

---

## Crypto-defi (currently 6/13 → free path to ~8/13)

CoinGecko (keyless), DefiLlama/Barker/Blockscout/GeckoTerminal already usable. Add keyed depth:

### C1 · Etherscan
- **Unlocks:** on-chain reads across 60+ EVM chains, balances, tx, contract source/ABI, gas. The
  first pick for on-chain analysis. `needs-key`.
- **Class:** free-key. Free key from **etherscan.io** → account → API keys *(verified, `tools/etherscan-mcp.md`)*.
- **Steps:** `python tools/console.py connect etherscan-mcp` → USER pastes key as bearer (hosted HTTP
  `mcp.etherscan.io/mcp`) → `/mcp`. **2026-05 free-tier cut:** ~10% of chains dropped from free;
  verified-contract + ABI endpoints stay free on all chains. For a dropped chain, **don't pay, use
  Blockscout MCP** (already free, no key, 3000+ chains). A **July-2026** change drops max records 10k→1k.

### C2 · CoinMarketCap
- **Unlocks:** quotes, TA, derivatives, narratives. `needs-key`.
- **Class:** free-key. Free Basic = ~**30 to 50 req/min + ~10 to 15k credits/mo** (sources conflict on the
  exact credit cap, `verify-before-signup` on the dashboard) *(corroborated, `domains/crypto-defi.md`)*.
- **Key source:** **pro.coinmarketcap.com/signup**. `python tools/console.py connect coinmarketcap-mcp` → key → `/mcp`.

### C3 · Moralis, cross-chain portfolio
- **Class:** free-key, generous free tier **40k Compute Units/day (~1.2M CU/mo), 40 RPS**
  *(verified, `tools/moralis.md`)*. **moralis.com** (pricing https://moralis.com/pricing/). Pick it
  for normalized wallet/portfolio across 100+ chains; for single-chain raw tx, Etherscan/Blockscout
  are simpler + free.

---

## Trends-discovery (currently 3/11 → free path to ~5/11)

GDELT, app/play-store scrapers, Trends MCP already usable.

### T1 · Product Hunt MCP
- **Unlocks:** posts/topics/votes, new-launch tracking (SaaS/dev-tool/AI niche). `cold-mcp`.
- **Class:** free-key, PH v2 API is free; you supply a **Developer Token**.
- **Key source:** create a developer application at **producthunt.com/v2/oauth/applications**
  *(verified, `tools/product-hunt-mcp.md`)*. **Gotcha:** the env wants the **Developer Token** shown
  on the app page, NOT the "API Key"/"API Secret" pair. `pip install product-hunt-mcp` (package name
  keeps old hyphenation; correct repo is `jaipandya/producthunt-mcp-server`, the old
  `jaipandya/product-hunt-mcp` path is **404 dead**).

### T2 · GDELT, already free
- **Class:** install-no-key / no-auth at all. GDELT is 100% free, no key, no quota, global news
  tone/events in 100+ langs, 15-min refresh *(verified, `tools/gdelt-mcp.md`)*. If it shows
  `needs-key` in console, that's a bridge-table artifact; it needs no auth. Plain REST (DOC 2.0) works
  without the MCP.

> **No permanent free tier (paid only):** Exploding Topics (trial-only), Sensor Tower (pricey ST sub).

---

## SEO-keywords (currently 3/12 → free path to ~5/12)

### S1 · Google Search Console MCP
- **Unlocks:** your own site's real clicks/impressions/CTR/position, ground truth no estimator
  matches. `cold-mcp`.
- **Class:** free-key (free GSC API). Auth = Google **OAuth or a service-account JSON** (service
  account is simpler for an agent) *(verified, `tools/gsc-mcp.md`)*. `npx -y mcp-server-gsc`. Create
  the service account in Google Cloud Console, enable the Search Console API, add its email as a user
  on the property. Only sees sites you control, for competitor SERP use S3/DataForSEO.

### S2 · SerpApi, clean structured SERP/Trends JSON
- **Class:** free-tier, **free 250 searches/mo** *(verified, `tools/serpapi.md`)*. **serpapi.com**.
  Starter $25/mo (1k). `cold-mcp`/`needs-key`. Pricey at scale, for bulk, prefer DataForSEO or S3.

### S3 · SearXNG, free self-host private SERP
- **Unlocks:** a private SerpApi at zero cost, aggregates dozens of engines, returns JSON SERP.
  `needs-install`.
- **Class:** install-no-key. `searxng/searxng` (AGPL). Docker:
  `docker run --rm -d -p 8080:8080 -v "${PWD}/searxng:/etc/searxng" searxng/searxng`, then enable
  `json` under `search.formats:` in `settings.yml` *(verified, `tools/searxng.md`)*. Query
  `localhost:8080/search?q=...&format=json` from playwright/Bash. Pair with **serpbear**
  (`towfiqi/serpbear`, install-no-key) for rank tracking.

> **Real cost is the underlying sub, not the MCP:** Ahrefs / Semrush MCPs consume your paid plan,
> no meaningful free API tier (Ahrefs needs Lite+; Semrush entry Pro ~$140/mo). `verify-before-signup`
> for any "free Ahrefs" claim.

---

## Leadgen-crm (currently 0/16, pick ONE free entry to break zero)

The whole domain is dark. Two cheap ways in:

### L1 · Hunter.io
- **Unlocks:** email finder + verifier + light enrichment, the precise-email specialist. `needs-key`.
- **Class:** free-tier, free **50 credits/mo** (confirmed 25 searches + 50 verifies/mo) *(verified,
  `tools/hunter.md`)*. **hunter.io** → API keys at `/api-keys`. **Gotcha:** Google-OAuth signup fails
  unless first+last name are typed before clicking "Sign up with Google".
- **Steps:** hosted HTTP MCP `mcp.hunter.io/mcp`, header `X-API-KEY: <key>` (USER pastes; do NOT
  `claude mcp add`).

### L2 · Apollo.io
- **Unlocks:** find + enrich contacts, ICP prospecting. `needs-key`.
- **Class:** free-tier, **free Starter plan (forever) + trial credits** *(verified, `tools/apollo.md`)*.
  **apollo.io** native Claude connector (OAuth). **⚠ Turn OFF Claude model training before connecting.**

### L3 · ZeroBounce, verify slot
- **Class:** free-tier, **100 free verifications/mo** (business-domain signup) *(verified,
  `tools/zerobounce.md`)*. **zerobounce.net**. Official MCP (key).

### L4 · gosom/google-maps-scraper, free local B2B leads
- **Class:** install-no-key, local-business name/phone/site/**email**, far lower legal risk than
  LinkedIn. `needs-install`. `gosom/google-maps-scraper` *(see `domains/leadgen-crm.md`)*. This is the
  **free** way to break 0/16 without any key.

> **Compliance red line:** LinkedIn cookie-scraping = high ban rate + GDPR/CCPA exposure, prefer
> Google Maps leads or Bright Data. **Dead, don't rely:** Smartlead MCP repo archived (see tombstone
> in `domains/leadgen-crm.md`); the Smartlead *product* is still alive, drive its REST API directly.

---

## X-twitter (currently 0/4, free entry exists)

### X1 · twikit
- **Unlocks:** free X read **and write** (search, users, followers, post, reply, DM) via a logged-in
  account's cookies, no API key, no X dev account. `needs-install`.
- **Class:** install-no-key. `pip install twikit` (lib) + optional ready MCP `adhikasp/mcp-twikit`
  *(verified, `tools/twikit.md`)*. Use a **throwaway** X account (ban risk); protect the cookie file.
- **Reality check (shard):** X is **low-signal for consumer-demand** research, use twikit for
  tech/crypto/founder discourse and named-account tracking, not "do people buy X". For richer fields,
  drive the connected **playwright MCP** as a logged-in human.

### X2 · twitterapi.io, paid, provider absorbs upkeep
- **Class:** paid (pay-per-use $0.15/1k tweets, $0.18/1k profiles; **$0.1 free credit, no card**;
  .edu 50% rebate) *(verified, `tools/twitterapi-io.md`)*. **twitterapi.io** (Google login, no X dev
  account). Hosted MCP `mcp.twitterapi.io/mcp`, read-only. Pick it only when you want the provider to
  carry account/proxy/login-wall cost.

> **Dead, do not attempt:** X official free API (write-only, tier closed to new signups 2026-02),
> snscrape (broken against X), public Nitter (collapsed), see tombstones in `domains/x-twitter.md`.

---

## Social-publishing (currently 2/17, free official entry)

### SP1 · Buffer
- **Unlocks:** schedule/publish across ~11 platforms. `needs-key`.
- **Class:** free-tier, **API + hosted MCP work on the Free plan** (launched 2026-05-27) *(verified,
  `tools/buffer.md`)*. **buffer.com**. The only official aggregator whose API+MCP work free.
- **Steps:** key from Buffer dashboard → official MCP → `/mcp`. Front-load free platforms
  (Bluesky/Mastodon/Threads) directly via `atproto` / `Mastodon.py` (install-no-key, already usable).

> **Cost trap:** X link-posts cost $0.20 each on any route that uses the paid X write API.

---

## Ecommerce-arbitrage (currently 0/9), the free route is route ④

Every ①-route pick here needs a **paid** key (Keepa €49/mo+, Rainforest $23/mo, PriceAPI €99/mo,
eBay/Shopify need app registration). The honest free unlock is **install-no-key**:

### EA1 · amazon-scraper / discount-bandit / playwright
- **Class:** install-no-key. `omkarcloud/amazon-scraper` (24 Amazon sites) and
  `Cybrarist/Discount-Bandit` (self-built multi-store tracker) are `needs-install`; the connected
  **playwright MCP** reads a live Amazon price in one shot.
- **Hard limit:** the free route **cannot backfill historical price/BSR**, it only accrues from your
  deploy day. For years of price history, **Keepa ① (paid) is irreplaceable**, that's the one place
  paying is the only option. See `domains/ecommerce-arbitrage.md`.

---

## Content-cms (currently 1/10), mostly cold-mcp self-host or OAuth

- **install-no-key / self-host:** WordPress MCP (`WordPress/mcp-adapter`, App Password), Ghost MCP
  (`MFYDev/ghost-mcp`, Admin API key), Directus/Webflow official MCPs (OAuth), all `cold-mcp`,
  activate via `console.py connect <slug>` + the provider's own token. Free.
- **Already free, no platform fee:** Static blog (Hugo/Astro + claude-blog skill + git + Vercel).
- These are lower-priority for *research* (they're publishing targets), activate on demand, not in
  the 30-min clinic. See `domains/content-cms.md`.

---

## Reddit-community (currently 3/11, already strong, one free add)

- **reddit-mcp-buddy** (`cold-mcp`) is **zero-auth on the anon tier** (10 req/min, no creds):
  `npx -y reddit-mcp-buddy` → `/mcp`. install-no-key, instant. Pair with **reddit-research-mcp**
  (hosted OAuth, no creds) for subreddit discovery. mcp-hn / praw / stackexchange already usable.
- **Watch:** GummySearch is shutting down (commercial close 2025-11, full data-deletion 2026-12), its
  free successor **subscope** (`dancolta/subscope`, install-no-key) is in the registry. See
  `domains/reddit-community.md`.

---

## Frontier-research (currently 11/15, near-complete, free-key polish)

- **Semantic Scholar:** works keyless (throttled); a **free key** (semanticscholar.org/product/api)
  only lifts the rate limit. arXiv / HF read / OpenReview are free no-key and already usable.
- **Dead, documented gap:** Papers with Code API (Meta sunset 2025-07, redirects to HF Papers), the
  benchmark-SOTA-leaderboard signal is lost; no clean free replacement. See `domains/frontier-research.md`.

---

## What this guide deliberately does NOT cover

- The ~12 `ready-skills` (they're `npx skills add` / `/plugin` installs, not MCPs, see
  `domains/ready-skills.md`; install on demand).
- Enterprise-only paid tools with no free tier and no research-critical uniqueness (ZoomInfo, Nansen
  god-mode, Ahrefs/Semrush full, Sensor Tower), activate only when a specific run needs them and the
  user accepts the cost.
- Anything I could not verify is tagged `verify-before-signup` above rather than asserted.
