# Discovery state — watchlist · reject log · new-angle watchlist

> Produced by the Discovery phase + Horizon scan of the refresh protocol (see `refresh-protocol.md`
> §Discovery D5 and §Horizon H3/H4). Purpose: stop the matrix re-discovering the same candidates
> every run, track new-but-unproven tools until they prove out (or expire), and record cross-scan
> new-territory signals so a NEW-DOMAIN proposal only fires when a thing **recurs across ≥2 scans**.
>
> Nothing here is in the live matrix. WATCH = frontier-but-unproven (revisit next scan). SKIP =
> failed an admission gate / reject filter (don't re-surface). All stars are real `gh api` values at
> the noted date — never from memory (CONSTITUTION C1).

---

## Watchlist (frontier, not yet admitted — revisit next scan)

Promote to the matrix only when it gains independent adoption AND clears a capability bar vs the
current top pick (Discovery D3/D5). `first_seen` lets us measure "is it gaining or stalling?".

| candidate | domain | stars (gh-api 2026-06-01) | route | why watch (not yet ADD) | first_seen |
|---|---|---|---|---|---|
| Altimis/Scweet | x-twitter | 1514★ (active 2026-05-19) | ④ curl_cffi TLS-fingerprint | distinct anti-detect angle, actively maintained, but < twikit adoption and **no ready MCP** | 2026-06 |
| nirholas/XActions | x-twitter | 293★ (2026-05-07) | ④/③ bundled MCP | bundles browser-route MCP, but created 2024 (not new), README-churn/star-smell, HTML-dashboard product | 2026-06 |
| CloakHQ/CloakBrowser | browser-automation | 22965★ (created 2026-02, MIT wrapper) | ④ stealth Chromium | could displace paid anti-detect/Web-Unlocker, BUT ships a **closed ~200MB binary** (supply-chain trust) and only clusters mid-pack vs nodriver in indep. benchmark; 22.9k★ in ~3mo = verify adoption | 2026-06 |
| Kaliiiiiiiiii-Vinyzu/patchright | browser-automation | 3351★ (Apache-2.0, active) | ① undetected Playwright | permissive license, keeps full Playwright API; loses to nodriver on protocol-level detection per benchmark — ADD-as-option at most, not REPLACE | 2026-06 |
| lightpanda-io/browser | browser-automation | 30717★ (AGPL-3.0, very active) | ① CDP-compatible engine | fast headless engine (claims 9× less RAM), but its MCP server (lightpanda-io/gomcp) is **archived** → not MCP-ready; it's an engine, not an agent | 2026-06 |
| us/crw | web-scraping | 126★ (created 2026-03, AGPL-3.0) | ① Firecrawl-API-compatible + built-in MCP | drop-in Firecrawl API as single binary w/ MCP; "new ≠ good" — 126★, only vendor-authored benchmarks | 2026-06 |
| Base MCP (hosted) | crypto-defi | n/a (hosted; legacy repo base/base-mcp-legacy 347★, **archived**) | ① OAuth, non-custodial | first-party Base DeFi execution layer (Morpho/Uniswap/Aerodrome…), launched 2026-05-26; no install path beyond in-client OAuth yet → WATCH until a wireable endpoint exists | 2026-06 |
| goat-sdk/goat | crypto-defi | 993★ (MIT, active) | ③ agentic toolkit | highest-traction new on-chain agent toolkit, but a dev framework not a plug-and-play source | 2026-06 |
| debridge-finance/debridge-mcp | crypto-defi | 31★ (MIT) | ① no-key (bridge needs wallet) | cross-chain bridging MCP = capability the matrix lacks; adoption tiny | 2026-06 |
| tatumio/blockchain-mcp | crypto-defi | 14★ (MIT) | ① key | overlaps Moralis/Covalent multi-chain; no clear edge | 2026-06 |
| Philidor-Labs/philidor-mcp | crypto-defi | 4★ (MIT, no-key) | ① no-key | novel niche (DeFi vault risk scoring, 700+ vaults) not in matrix; far too new | 2026-06 |
| CoinStatsHQ/coinstats-mcp | crypto-defi | 14★ (MIT, free key) | ① free key | redundant w/ CoinGecko MCP for price/market; only edge = portfolio tracking | 2026-06 |
| ythx-101/x-tweet-fetcher | x-twitter | 862★ | ④ | discovery ADD→WATCH (skeptic): revives self-host Nitter+Playwright, but maintainer README admits fetch not proven E2E; users report fails (#67/#66/#61); 83% stars front-loaded in 5wk = star-farming smell | 2026-06 |
| Panniantong/Agent-Reach | reddit-community | 24768★ | ④ | multi-platform keyless reader CLI (Reddit/X/YT/Bili/XHS); high star:fork ratio + cookie-auth ToS risk; CLI not MCP | 2026-06 |
| omkarcloud/botasaurus | web-scraping | 4756★ | ③ | discovery ADD→WATCH: all-in-one anti-detect w/ Cloudflare bypass, but 83-day stale, force-pushed/squashed history, zero releases | 2026-06 |
| oxylabs/oxylabs-mcp | web-scraping | 96★ | ② | official paid anti-bot scraper MCP; backup provider, no free tier, doesn't beat Bright Data | 2026-06 |
| Tosheroon MCP | ecommerce-arbitrage | n/a (closed SaaS) | ① | discovery ADD→WATCH: free MCP w/ 90d price history + 30d forecast 9 Amazon regions; closed-source paywalled, single-source adoption | 2026-06 |
| christian-ramos/mcp-amazon-sp-api | ecommerce-arbitrage | 2★ | ① | discovery ADD→WATCH: 55+ tools/19 SP-API scopes fills "SP-API no ready MCP" gap; 2★/0 forks/<3mo unproven | 2026-06 |
| TickDB/tickdb-unified-realtime-marketdata-api | finance-markets | 410★ | ① | adds HK/A-share/forex/commodity realtime (US-centric shard gap); free-tier/pricing unverified | 2026-06 |
| augiemazza/varrd | finance-markets | 18★ | ④ | backtesting/event-study/stat-validation MCP, distinct analysis route; 18★ unproven | 2026-06 |
| Dune Analytics MCP (official) | crypto-defi | n/a (sim-api-mcp archived 2★) | ① | discovery ADD→WATCH: official live MCP on-chain SQL 100+ chains; only official repo archived, free-credit claim unverified, SQL friction | 2026-06 |
| vooi-app/mcp | crypto-defi | 8★ | ① | perp funding-arb Hyperliquid/Lighter/Aster/Kinetiq; would supersede stale funding-rates-mcp; created 2026-06-08, unproven | 2026-06 |
| kukapay/crypto-indicators-mcp | crypto-defi | 126★ | ② | TA-indicator computation pairing ccxt; ~6mo since push, marginal over rolling own indicators | 2026-06 |
| nirholas/cryptocurrency.cv | crypto-defi | 236★ | ① | free no-key crypto news aggregator+MCP (news/sentiment gap); single-maintainer, verify data quality | 2026-06 |
| itsjwill/seoctopus | seo-keywords | 9★ | ④ | MCP+CLI 23 tools (rank/GA/audit/kw) self-host; 9★ single push 2026-02 possible abandon | 2026-06 |
| Google Trends API (official, alpha) | seo-keywords/trends-discovery | n/a | ② | Google's own Trends API (alpha) — authoritative if GA, could displace SerpApi/pytrends; still alpha, gated, no pricing/MCP | 2026-06 |
| PHY041/claude-skill-reddit | social-publishing | 33★ | ④ | free browser-act Reddit posting (platform no shard posts to); single-commit macOS-only unproven | 2026-06 |
| typefully/agent-skills | social-publishing | 51★ | ① | official Typefully draft+schedule skills (X/LI/Threads/BS/Masto); thin vs Buffer, needs $8+/mo | 2026-06 |
| publora/skills | social-publishing | 30★ | ② | new 10-platform paid API+skills, plausible cheaper Ayrshare alt; pricing unverified, 30★ | 2026-06 |
| Storyblok/microCMS/Kontent.ai MCP | content-cms | n/a (not gh-verified) | ① | additional headless-CMS MCPs on PulseMCP/Glama; coverage frontier, repos unverified this scan | 2026-06 |
| sales-skills/sales | leadgen-crm | 45★ | ④ | Claude Code GTM/outbound/enrichment skill bundle to orchestrate existing MCPs; created 2026-03, unproven | 2026-06 |
| generect/generect_mcp | leadgen-crm | 1★ | ① | official MCP for Generect B2B lead/company API; 1★, no install evidence, paywalled | 2026-06 |
| IlyaGusev/academia_mcp | frontier-research | 90★ | ① | unifies arXiv+ACL Anthology+Semantic Scholar+HF datasets; ACL fills NLP-venue gap; 90★ prove first | 2026-06 |
| fermionoid/paper-fetcher | frontier-research | 35★ | ① | full-text fetch via Open Access+arXiv+EZproxy (full-text-PDF gap); 35★ unproven | 2026-06 |
| kostja94/marketing-skills | ready-skills | 588★ | ④ | 160+ skills multi-tool no-lock-in; broader breadth than coreyhaines but lower adoption | 2026-06 |
| AgriciDaniel/claude-blog | ready-skills | 1016★ | ④ | 30 sub-skills dual-optimized Google+AI citations, deeper long-form blog ops; narrow scope | 2026-06 |
| saffron-health/libretto | browser-automation | 648★ | ④ | generates DETERMINISTIC browser automation as inspectable code (vs runtime LLM agents); HN front page, early | 2026-06 |
| browser-act/skills | browser-automation | 2237★ | ④ | agent browser CLI w/ anti-bot break, human-handoff, parallel multi-account isolation; adoption depth unproven | 2026-06 |
| cosinusalpha/webctl | browser-automation | 413★ | ④ | CLI browser automation humans+agents (HN front page); agent-browser dominates same niche | 2026-06 |

Useful registries to diff next run: `royyannick/awesome-blockchain-mcps` (35★, 2026-03-17),
`demcp/awesome-web3-mcp-servers` (~608★ per discovery, re-verify).

---

## Reject log (failed a gate / reject filter — do NOT re-surface)

| candidate | domain | stars | reject reason (Discovery D4) | date |
|---|---|---|---|---|
| DataWhisker/x-mcp-server | x-twitter | 68★ | undocumented (null desc), modest adoption, no differentiating capability vs adhikasp/mcp-twikit | 2026-06 |
| Barresider/x-mcp | x-twitter | 8★ | stale (2026-01) + near-zero adoption | 2026-06 |
| miles0sage/twitter-mcp · JohannesHoppe/x-autonomous-mcp · jakemeany523/buffer-mcp · azeemkafridi/bulkpublish-api · AutomateLab-tech/content-distribution-mcp | x-twitter / social-publishing | 0–2★ | ~0 adoption, "new ≠ good" — none warrants even WATCH | 2026-06 |
| itbrowser-net/undetectable-fingerprint-browser | browser-automation | 765★ | stale >1yr (last push 2025-04), no license | 2026-06 |
| nottelabs/notte | browser-automation | 1968★ | copyleft-restrictive (NOASSERTION/SSPL per writeups), created 2024 (not new) | 2026-06 |
| Scrapybara | web-scraping | 73★/20★ | managed-cloud-first, low OSS traction, predates window | 2026-06 |
| Xquik (x-twitter-scraper) | x-twitter | 111★ | paywalled proprietary metered API wrapper; star-inflation smell (sibling SDK spam repos 0-3★) | 2026-06 |
| eliasbiondo/reddit-mcp-server | reddit-community | 141★ | single-commit-day repo, no maint since 2026-03; superseded by reddit-mcp-buddy | 2026-06 |
| jordanburke/reddit-mcp-server | reddit-community | 126★ | no differentiated capability vs reddit-mcp-buddy | 2026-06 |
| h4ckf0r0day/obscura | web-scraping | 14631★ | star-inflation: 14.6k★/48 watchers (305:1), 2mo-old anon repo, unverifiable adoption | 2026-06 |
| vakra-dev/reader | web-scraping | 531★ | undifferentiated firecrawl clone, low adoption, stale ~1mo | 2026-06 |
| alsk1992/Flip-God | ecommerce-arbitrage | 4★ | 4★ single-author huge cross-platform-arbitrage claim = star-poor vaporware | 2026-06 |
| narumiruna/yfinance-mcp | finance-markets | 154★ | duplicate of higher-star yahoo-finance-mcp, no edge | 2026-06 |
| mrgoonie/vnstock-agent | finance-markets | 95★ | Vietnam-only single-market niche, low general applicability | 2026-06 |
| getbeton/beton-ai (Beton) | leadgen-crm | 72★ | discovery ADD→SKIP: repo DEPRECATED by author (redirects to getbeton/inspector); "Clay/waterfall/LeadMagic" framing invented | 2026-06 |
| egebese/dataseo-mcp | seo-keywords | 181★ | ToS-violating Ahrefs scraper needing paid CAPTCHA solver (not free); matches existing avoid-label | 2026-06 |
| Registry SEO-MCP flood (CalmSEO/TransformSEO/VibeSEO/EzBiz/MetricSpot/SEOcrawl/truss-seo/seoptic) | seo-keywords | 0-low | paid-SaaS wrappers / single-source unverifiable; overlap GSC①+DataForSEO②, no new route | 2026-06 |
| PostFast/BulkPublish/Status200/Upload-Post/PostAll/Bemo/PostEverywhere | social-publishing | 0-1★ | cluster of paid-SaaS-wrapper MCPs, single-vendor, no edge over Buffer/Blotato | 2026-06 |
| Meerkats-Ai/Prospeo MCP | leadgen-crm | 1★ | 1★ paywalled wrapper, stale >12mo (2025-04) | 2026-06 |
| enzoemir1/leadpipe-mcp | leadgen-crm | 0★ | 0★ thin wrapper over Leadpipe SaaS; redundant with Apollo+Hunter+CRM | 2026-06 |
| archoor/painspotter-mcp | trends-discovery | 0★ | adoption=0, overlaps idea-reality-MCP, opaque likely-paywalled backend | 2026-06 |
| briangaoo/totem | trends-discovery | 64★ | off-domain (Whoop fitness data, not market trends) | 2026-06 |
| matsjfunke/paperclip | frontier-research | 27★ | archived/abandoned 2025-12; superseded by openags/paper-search-mcp | 2026-06 |
| reetp14/openalex-mcp | frontier-research | 5★ | 5★ negligible adoption, stale >10mo; OpenAlex already covered by local `openalex` skill | 2026-06 |
| zubair-trabzada/ai-marketing-claude | ready-skills | 1843★ | frozen (no commits since 2026-03-02); fork/star anomaly (588 forks/1843★) | 2026-06 |
| OpenClaudia/openclaudia-skills | ready-skills | 455★ | strict subset of coreyhaines, no unique capability, lower adoption | 2026-06 |

---

## New-angle watchlist (Horizon scan — needs to recur across ≥2 scans before any NEW-DOMAIN proposal)

Per H3 anti-bloat: a new angle stays here until it proves recurring + distinct + has ≥3 verifiable
sources. Default verdict is FOLD into an existing domain; NEW-DOMAIN/NEW-SKILL are human-approved.

| angle | scan(s) seen | verdict | disposition |
|---|---|---|---|
| **X API re-tier (Apr 2026)** — pay-per-use only path for new devs; secondary sources report Writes $0.015/post, URL-posts $0.20, Following/Likes/Quote-Posts moved to Enterprise-only | 2026-06 (1st) | FOLD → x-twitter | **Primary source (devcommunity.x.com) is auth-walled/403 — unverified at source.** $0.20 link-post already in social-publishing shard. Do NOT change matrix numbers until an official page confirms; re-check next scan. |
| **Agent-memory as a capability class** — mem0ai/mem0 (57251★), getzep/zep (4626★); "memory as attack surface" security thread | 2026-06 (1st) | NEW-SKILL flag (human-only) | Genuinely new capability class, but it stores **agent state**, not a queryable commercial-data source → out of scope for this source matrix. Flag only; do not add a domain. |
| **MCP deployment shape shift** — Anthropic MCP tunnels (research preview) + self-hosted sandboxes (Cloudflare/Daytona/Modal/Vercel); MCP spec 2026-07-28 RC | 2026-06 (1st) | FOLD → ready-skills / install notes | Plumbing for HOW MCP servers are wired, not WHAT data is reachable. No new/closed data source. |
| **Emerging consumer platforms** — Divine/Vine relaunch, Threads >300M MAU, Lemon8 (US), IG "Instants" | 2026-06 (1st) | FOLD → x-twitter / social-publishing / trends-discovery (watch) | None has a verifiable public data-access route at scale yet → watch-list, not NEW-DOMAIN (fails H2 ≥3-verifiable-sources bar). |
| **Web-scraping pricing refresh (verified by discovery agent, re-confirm at source before quoting)** — Firecrawl free 1000 credits/mo + Hobby $16/mo; Exa free 1000/mo, $7/1k; Tavily free 1000/mo; Bright Data Web Unlocker $1.5/1K PAYG | 2026-06 (1st) | FOLD → web-scraping pricing | Agent-cited official URLs; not personally re-fetched this run → left out of the shard per C5/C6. Verify firecrawl.dev/pricing, exa.ai/pricing, tavily.com/pricing, brightdata.com/pricing/web-unlocker next refresh. |
| **MaRGen / LLM-signal-triangulation** market-research methodologies (arXiv 2508.01370, 2605.19337) | 2026-06 (1st) | no action (methodology watch) | Academic/early; revisit if it produces a reusable workflow. |
| **Prediction-market odds as queryable alt-data** (Polymarket/Kalshi/PredictIt/Manifold; JamesANZ/prediction-market-mcp 34★, aarora4/Awesome-Prediction-Market-Tools 467★) | 2026-06 (1st) | WATCH ⚑ strongest future NEW-DOMAIN | Genuinely outside all 14 domains; meets ≥3-source half but fails recurrence (1st sighting) + MCP adoption thin. Re-check next sweep; promote to NEW-DOMAIN proposal only if it recurs with a maintained no-key MCP. |
| **Agentic-payments / pay-per-call data acquisition** (x402 now Linux-Foundation-governed, Stripe MPP, x402 Bazaar) | 2026-06 (1st) | WATCH → FOLD crypto-defi + install notes | New capability class but it's a payment RAIL, not a queryable source; partly absorbed (CMC x402 note). Watch if data marketplaces become a primary acquisition route → may need an x402 install route. |
| **Cross-validate sentiment vs prediction-market implied probability** (research methodology) | 2026-06 (1st) | WATCH → FOLD SKILL.md guardrails | Novel money-weighted cross-validation signal; downstream of prediction-markets territory, unproven 1st sighting. |
| **TikTok-Shop short-video commerce data** (FastMoss/Kalodata/EchoTik; Seym0n/tiktok-mcp 163★) | 2026-06 (1st) | FOLD → ecommerce-arbitrage + trends-discovery | TikTok already covered (TikTok-Api 6.4k★); new wrinkle = Shop GMV in paid L3 dashboards; OSS Shop MCPs thin. |
| **Agentic-commerce product feeds** (OpenAI/Stripe ACP "Instant Checkout"; Shopify/Etsy merchant feeds) | 2026-06 (1st) | FOLD → ecommerce-arbitrage | distribution/checkout channel, not a new alt-data territory; overlaps x402 watch item. |
| **Deep-research-as-a-service APIs** (OpenAI Deep Research, Perplexity Deep Research/Agent) | 2026-06 (1st) | FOLD → web-scraping / SKILL.md delegation | heavy-harness layer the skill already DELEGATES to; treat new providers as alt back-ends for the existing delegation step. |
