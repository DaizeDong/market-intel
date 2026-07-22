# Discovery state, watchlist · reject log · new-angle watchlist

> Produced by the Discovery phase + Horizon scan of the refresh protocol (see `refresh-protocol.md`
> §Discovery D5 and §Horizon H3/H4). Purpose: stop the matrix re-discovering the same candidates
> every run, track new-but-unproven tools until they prove out (or expire), and record cross-scan
> new-territory signals so a NEW-DOMAIN proposal only fires when a thing **recurs across ≥2 scans**.
>
> Nothing here is in the live matrix. WATCH = frontier-but-unproven (revisit next scan). SKIP =
> failed an admission gate / reject filter (don't re-surface). All stars are real `gh api` values at
> the noted date, never from memory (CONSTITUTION C1).

---

## Watchlist (frontier, not yet admitted, revisit next scan)

Promote to the matrix only when it gains independent adoption AND clears a capability bar vs the
current top pick (Discovery D3/D5). `first_seen` lets us measure "is it gaining or stalling?".

| candidate | domain | stars (gh-api 2026-07-22 unless noted) | route | why watch (not yet ADD) | first_seen |
|---|---|---|---|---|---|
| Altimis/Scweet | x-twitter | 1569★ (was 1514★ 2026-06, +55, slow) | ④ curl_cffi TLS-fingerprint | distinct anti-detect angle, actively maintained, but growth flat and **no ready MCP** | 2026-06 |
| nirholas/XActions | x-twitter | 398★ (was 293★, +105 in ~6wk, accelerating) | ④/③ bundled MCP | notable acceleration this cycle, but README-churn/star-smell + HTML-dashboard product concerns from prior scan stand; recheck next sweep | 2026-06 |
| ythx-101/x-tweet-fetcher | x-twitter | 914★ (was 862★, growth cooling) | ④ | star-farming suspicion less acute (growth slowing) but still unproven E2E (users report fails #67/#66/#61) | 2026-06 |
| CloakHQ/CloakBrowser | browser-automation | 28878★ (was 22965★, +26% in 7wk) | ④ stealth Chromium | still growing fast, but free tier ships only a closed binary (Pro/latest builds paywalled), trust concern persists; new MCP wrapper `swimmwatch/cloakbrowser-mcp` (29★) appeared around it | 2026-06 |
| lightpanda-io/browser | browser-automation | 32059★ (was 30717★) | ① CDP-compatible engine | fast engine, but its MCP (`lightpanda-io/gomcp`) **re-confirmed archived** → still not MCP-ready | 2026-06 |
| saffron-health/libretto | browser-automation | 823★ (was 648★, +27%) | ④ | deterministic-code browser automation (vs runtime LLM agents); real growth, still HN-only adoption evidence | 2026-06 |
| browser-act/skills | browser-automation | 4629★ (was 2237★, **+107% in 7wk**) | ④ | 219 forks but only 4 contributors, concentration flag (D4 anti-inflation); commercial product (browseract.com), plausible marketing-driven growth, cannot confirm either way | 2026-06 |
| cosinusalpha/webctl | browser-automation | 412★ (was 413★, flat/stalled, last push 2026-05-29) | ④ | momentum stopped since last scan; **demotion candidate next sweep if still stale** | 2026-06 |
| feder-cr/invisible_playwright | browser-automation | 1784★ (created 2026-05, new this cycle) | ④ | source-patched **Firefox** (not Playwright despite the name) claiming to pass 5 major detection suites; real growth 0→1.8k★ in ~2mo but only 1 HN comment, no independent 3rd-party corroboration yet | 2026-07 |
| us/crw | web-scraping | 126★ (2026-06, unchanged) | ① Firecrawl-API-compatible + built-in MCP | drop-in Firecrawl API single binary w/ MCP; "new ≠ good", only vendor-authored benchmarks | 2026-06 |
| germondai/trawl | web-scraping | 441★ (created 2026-06-26, new) | ③ FlareSolverr/Byparr drop-in | broadest CAPTCHA-class bypass claim (Cloudflare/Turnstile/reCAPTCHA/hCaptcha/GeeTest) in one proxy; AGPL, 22 forks, but 0 GitHub subscribers despite the star/fork count, adoption-signal gap | 2026-07 |
| mdowis/anansi | web-scraping | 100★ (created 2026-05-14, new) | ③/④ self-host, ships own MCP | self-healing selectors + TLS-fingerprint identity layer, MCP-native; genuinely novel capability but only 100★/2 subscribers | 2026-07 |
| 3441293738/creatorhub | web-scraping (CN) | 230★ (created 2026-07-03, new) | ④ | multi-platform CN scraper (抖音/小红书/快手), AGPL, Playwright+FastAPI; single-maintainer, unverified adoption | 2026-07 |
| goat-sdk/goat | crypto-defi | 1009★ (was 993★, +68 open issues = real engagement) | ③ agentic toolkit | steady growth, but a dev framework not a plug-and-play source | 2026-06 |
| debridge-finance/debridge-mcp | crypto-defi | 32★ (was 31★, flat, stale >3.5mo) | ① no-key | cross-chain bridging capability gap, but growth stalled, trending toward SKIP | 2026-06 |
| tatumio/blockchain-mcp | crypto-defi | 15★ (was 14★, negligible growth) | ① key | overlaps Moralis/Covalent, no clear edge | 2026-06 |
| CoinStatsHQ/coinstats-mcp | crypto-defi | 16★ (was 14★, actively pushed 2026-07-10) | ① free key | maintained but still redundant w/ CoinGecko for price; portfolio-tracking niche only | 2026-06 |
| nextdev-labs/mcp (Agent Usability Index) | trends-discovery (meta) | 79★ (was 75★, slow growth) | ① | source-selection meta-tool, not a data feed; park until it proves a research use | 2026-06 |
| BlockRunAI/blockrun-mcp | crypto-defi / x-twitter / web-scraping (multi-domain) | 475★ (created 2026-01-12, active 2026-07-21) | ② x402 resale | broad multi-domain data MCP via x402 micropayments (search/research/markets/crypto/X); crypto is one slice not crypto-specific, verify crypto-data quality/pricing specifically before ADD | 2026-07 |
| Panniantong/Agent-Reach | reddit-community | 24768★ (2026-06, unchanged) | ④ | multi-platform keyless reader CLI (Reddit/X/YT/Bili/XHS); high star:fork ratio + cookie-auth ToS risk; CLI not MCP | 2026-06 |
| ksanjeev284/reddit-universal-scraper | reddit-community | 569★ (created 2025-12-13, new this cycle) | ③ self-host, no MCP wrapper | fast-growing CLI scraper "works on any subreddit/user", but no MCP yet and no independent adoption evidence beyond stars | 2026-07 |
| omkarcloud/botasaurus | web-scraping | 4756★ (2026-06, unchanged) | ③ | all-in-one anti-detect w/ Cloudflare bypass, but stale, force-pushed/squashed history, zero releases | 2026-06 |
| oxylabs/oxylabs-mcp | web-scraping | 96★ (2026-06, unchanged) | ② | official paid anti-bot scraper MCP; backup provider, no free tier, doesn't beat Bright Data | 2026-06 |
| Tosheroon MCP | ecommerce-arbitrage | n/a (closed SaaS) | ① | free MCP w/ 90d price history + 30d forecast 9 Amazon regions; closed-source paywalled, single-source adoption | 2026-06 |
| christian-ramos/mcp-amazon-sp-api | ecommerce-arbitrage | 2★ (still, pushed 2026-07-20) | ① | 55+ tools/19 SP-API scopes fills "SP-API no ready MCP" gap; still 2★/0 forks, unproven | 2026-06 |
| mansournorouzi/amazon-sp-mcp | ecommerce-arbitrage | 42★ (created 2026-02, new candidate) | ① official (LWA OAuth) | 21x more stars/forks than the above SP-API candidate, recently patched an axios CVE (maintenance signal), but **no license file** = real risk flag; no independent adoption evidence yet | 2026-07 |
| TickDB/tickdb-unified-realtime-marketdata-api | finance-markets | 410★ (2026-06, unchanged) | ① | adds HK/A-share/forex/commodity realtime (US-centric shard gap); free-tier/pricing unverified. **Weaker CN-gap candidate than akshare-one-mcp below** (thinner adoption evidence) | 2026-06 |
| zwldarren/akshare-one-mcp | finance-markets | 213★ (created 2025-04, 47 forks, new candidate) | ① free (akshare) | fills the CN A-share gap the US-centric baseline lacks; MIT + real fork-usage evidence beats TickDB's thin signal, but stale ~4mo since push, recheck activity before promoting | 2026-07 |
| augiemazza/varrd | finance-markets | 18★ (2026-06, unchanged) | ④ | backtesting/event-study/stat-validation MCP, distinct analysis route; unproven | 2026-06 |
| TipRanks/mcp | finance-markets | 10★ (created 2026-07-21, brand new) | ① official, hosted | official vendor MCP (analyst ratings/Smart Score/technicals), genuinely new capability class not in baseline; 1 day old, unproven | 2026-07 |
| Dune Analytics MCP (official) | crypto-defi | n/a (official `sim-api-mcp` confirmed archived, 3★; community `kukapay/dune-analytics-mcp` 41★ but >14mo stale) | ① | no viable Dune MCP this cycle, official dead, community alt too stale to admit | 2026-06 |
| kukapay/crypto-indicators-mcp | crypto-defi | 130★ (was 126★, >7.5mo stale, drifting toward D-STALE) | ② | TA-indicator computation pairing ccxt; flag for tombstone review next sweep if still silent | 2026-06 |
| nirholas/cryptocurrency.cv | crypto-defi | 265★ (was 236★, +29, pushed **today**) | ① | strongest mover in crypto-defi watchlist this cycle: real growth + active maintenance; still single-maintainer, no 3rd-party adoption evidence, priority-flag for next-cycle promotion check | 2026-06 |
| itsjwill/seoctopus | seo-keywords | 10★ (was 9★, still stale since 2026-02) | ④ | single-push-then-abandon pattern confirmed; trending toward SKIP next sweep if still silent | 2026-06 |
| GEORank (yaojingang/GEORank) | seo-keywords | 328★ (created 2026-06-17, new) | ① OSS self-host | GEO/AEO (generative-engine-optimization) ranking platform, healthy fork ratio; doesn't unseat GSC/DataForSEO on keyword-volume/SERP capability, part of a visible **emerging GEO/AEO tooling cluster** (GEORank, RankWise, orangeo-ai-visibility-skill), worth a dedicated angle next sweep if it recurs | 2026-07 |
| Google Trends API (official, alpha) | seo-keywords/trends-discovery | n/a | ② | still alpha-gated per 3 independent 2026 sources, no pricing/MCP; no change | 2026-06 |
| PHY041/claude-skill-reddit | social-publishing | 37★ (was 33★) | ④ | free browser-act Reddit posting; single-commit macOS-only, still unproven | 2026-06 |
| typefully/agent-skills | social-publishing | 54★ (was 51★) | ① | official Typefully draft+schedule skills; thin vs Buffer, needs $8+/mo | 2026-06 |
| publora/skills | social-publishing | 40★ (was 30★, star growth without new commits since 2026-03-25) | ② | new 10-platform paid API+skills, plausible cheaper Ayrshare alt; pricing unverified | 2026-06 |
| trypostit/trypost | social-publishing | 409★ (created 2026-01-17, new) | ③ self-host, native MCP | 12-platform native publish + AI copilot, MCP-native OSS scheduler; doesn't clear REPLACE vs Postiz (12 vs 30+ platforms, 80x fewer stars) | 2026-07 |
| xueyc1f/turbopush-mcp | social-publishing (CN) | 22★ (created 2026-02-21, new) | ① MCP | MCP publishing to WeChat/Douyin/Bilibili/Xiaohongshu/20+ platforms in one server, genuine capability gap (no current MCP-native multi-CN-platform poster), but fails adoption≥1 admission gate | 2026-07 |
| sales-skills/sales | leadgen-crm | 85★ (was 45★, **nearly doubled in 5wk**, pushed today) | ④ | orchestration skill-bundle over existing MCPs (not a new data source), but adoption trajectory real, possible future ADD as a workflow-layer entry, not a top-pick replacement | 2026-06 |
| generect/generect_mcp | leadgen-crm | 1★ (unchanged, some maintenance activity 2026-07-20) | ① | official MCP for Generect B2B lead/company API; adoption unchanged, near-SKIP | 2026-06 |
| nando0x/ProspectOS | leadgen-crm | 168★ (created 2026-07-08, new) | ④ self-host scrape | Google Maps + Instagram lead scraping + AI-generated outreach; fills free/self-host local-biz + social-lead niche Apollo/Hunter don't cover; fast growth (2wks) too new to confirm non-inflated adoption | 2026-07 |
| ozhehkovski/geoleadscraper | leadgen-crm | 38★ (created 2026-06-11, new) | ④ free, no-key | multi-map-provider (Google Maps+Yandex+2GIS) lead scraper, Chrome extension; low stars, unproven at scale | 2026-07 |
| IlyaGusev/academia_mcp | frontier-research | 90★ (unchanged, push now 6mo old) | ① | unifies arXiv+ACL Anthology+Semantic Scholar+HF datasets; adoption still unproven, activity score weakening | 2026-06 |
| fermionoid/paper-fetcher | frontier-research | 36★ (was 35★, flat growth) | ① | full-text fetch via Open Access+arXiv+EZproxy; still unproven, no independent mention found | 2026-06 |
| OvOhao/auto-paper-collecter | frontier-research | 54★ (created 2026-06-25, new) | ① | arXiv+Crossref+Semantic Scholar+GitHub+RSS aggregator, "personal research radar"; stalled since 2026-06-28 (no push 3+wk), 9 forks vs 54★ mild smell, no evidence of superiority over arXiv API + HF Daily Papers | 2026-07 |
| kostja94/marketing-skills | ready-skills | 753★ (was 588★, +165 in ~6wk) | ④ | continues growing but no push in 6wk (viral-but-maybe-unmaintained); still broader (160+ skills) than coreyhaines31 but lower per-skill adoption depth | 2026-06 |
| AgriciDaniel/claude-blog | ready-skills | 1440★ (was 1016★, **+42% in a month**, pushed 5 days ago) | ④ | sustained growth AND active maintenance (unlike marketing-skills above); already underpins content-cms's "Default pick" static-blog route but isn't a formal `ready-skills.md` row, **lean ADD next verify cycle** | 2026-06 |
| coreyhaines31/makerskills | ready-skills | 207★ (created 2026-06-03, new) | ④ | different, newer, smaller repo from the same trusted maintainer as the existing top pick (marketingskills); "personal operator" skills (decisions/research/second-brain), too new/thin to ADD but may fold into or extend the existing pick | 2026-07 |
| caiovicentino/polymarket-mcp-server | prediction-markets (proposed NEW-DOMAIN, see below) | 597★ (pushed 2026-06-23, 45 tools) | ① | top candidate for the prediction-markets NEW-DOMAIN proposal; Polymarket-only, single-platform | 2026-06 |

Useful registries to diff next run: `royyannick/awesome-blockchain-mcps` (35★, 2026-03-17),
`demcp/awesome-web3-mcp-servers` (~608★ per discovery, re-verify).

---

## Reject log (failed a gate / reject filter, do NOT re-surface)

| candidate | domain | stars | reject reason (Discovery D4) | date |
|---|---|---|---|---|
| DataWhisker/x-mcp-server | x-twitter | 68★ | undocumented (null desc), modest adoption, no differentiating capability vs adhikasp/mcp-twikit | 2026-06 |
| Barresider/x-mcp | x-twitter | 8★ | stale (2026-01) + near-zero adoption | 2026-06 |
| miles0sage/twitter-mcp · JohannesHoppe/x-autonomous-mcp · jakemeany523/buffer-mcp · azeemkafridi/bulkpublish-api · AutomateLab-tech/content-distribution-mcp | x-twitter / social-publishing | 0 to 2★ | ~0 adoption, "new ≠ good", none warrants even WATCH | 2026-06 |
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
| **JesusRS1/stock-trade-finance-api** | finance-markets | 142★ | **security red flag**: latest commit added unused dependency `ioredis-xyz` (npm typosquat of `ioredis`, throwaway-looking publisher, no code reason to depend on it); 1,027 forks show bot-pattern fork-farm (repeating account names, ~3min creation cadence, zero pushes), star growth (91★→142★/wk) explained by the farm, not organic adoption. **Do not re-surface even if star count keeps climbing.** | 2026-07 |
| Cesarjoquin/Marketing-Skills | ready-skills | 145★ | star:fork ratio inverted and extreme (1233 forks vs 145★, 8.5:1), same fork-farming pattern that killed zubair-trabzada/ai-marketing-claude above | 2026-07 |
| farukkolip/xtapdown-mcp | x-twitter | 2★ | near-zero adoption, doesn't compete on domain's core capability (search/monitor), just adjacent creator tooling | 2026-07 |
| veezeehq/veezee-mcp | x-twitter | 0★ | zero adoption, 12 days old, "new≠good" trap | 2026-07 |
| poloniki/purefeed-mcp | x-twitter | 1★ | stale (no commits since creation day) + near-zero adoption | 2026-07 |
| fluyeporlaweb/mcp-x-intelligence | x-twitter | 48★ | D4 套壳: thin wrapper over already-catalogued twitterapi.io②, undisclosed-affiliate-link marketing smell | 2026-07 |
| storyblok/mcp-server | content-cms | 8★ | official repo now **archived** (confirmed dead, resolves prior "unverified" watchlist item) | 2026-07 |
| mbarinov/okx-mcp | crypto-defi | 4★ | negligible adoption (2 forks) | 2026-07 |
| daniel3303/roicai-mcp-server (roicai/mcp-server) | finance-markets | 2★ | unverifiable adoption, no differentiation from Finnhub/FMP already in baseline | 2026-07 |
| 19-84/redd-archiver | reddit-community | 339★ | star:watcher imbalance (18 forks/1 watcher) smells thin adoption; archival-HTML generator not a queryable research source, off-domain fit | 2026-07 |
| Kymo-MCP/mcpcan | reddit-community | 725★ | off-domain: generic MCP-hosting platform, not a Reddit-specific tool, mis-tagged by keyword collision | 2026-07 |
| Arindam200/reddit-mcp | reddit-community | 294★ | stale (no push since 2025-12), no differentiated capability vs baseline | 2026-07 |

---

## New-angle watchlist (Horizon scan, needs to recur across ≥2 scans before any NEW-DOMAIN proposal)

Per H3 anti-bloat: a new angle stays here until it proves recurring + distinct + has ≥3 verifiable
sources. Default verdict is FOLD into an existing domain; NEW-DOMAIN/NEW-SKILL are human-approved.

| angle | scan(s) seen | verdict | disposition |
|---|---|---|---|
| **X API re-tier**, Owned Reads now $0.001/resource (confirmed at source: official `devcommunity.x.com` post, effective 2026-04-20); $0.20 URL-post fee confirmed live via real developer billing complaints | 2026-06, **2026-07 (2nd, source-verified)** | FOLD → x-twitter | Was auth-walled/unverified in June; now confirmed at the official source. Numbers already match social-publishing shard's $0.20 link-post line; x-twitter shard doesn't cite pricing directly so no shard edit needed, closing this item. |
| **Agent-memory as a capability class**, mem0ai/mem0, getzep/zep, new entrants `engram` (5623★), `mnemox-ai/tradememory-protocol` (1399★), Product Hunt #1 "Wolbarg" | 2026-06, **2026-07 (2nd, strengthening)** | NEW-SKILL flag (human-only) | Genuinely new capability class, but it stores **agent state**, not a queryable commercial-data source → out of scope for this source matrix. Flag only; do not add a domain. |
| **MCP deployment shape shift**, MCP spec 2026-07-28 RC (stateless core, Tasks extension, MCP Apps) now locked and publishing | 2026-06, **2026-07 (2nd, landing this week)** | FOLD → ready-skills / install notes | Plumbing for HOW MCP servers are wired, not WHAT data is reachable. No new/closed data source. |
| **Emerging consumer platforms**, Divine (Jack Dorsey Vine reboot) publicly launched 2026-04-29 w/ C2PA provenance gating | 2026-06, **2026-07 (2nd, partial)** | FOLD → x-twitter / social-publishing / trends-discovery (watch) | Still **no programmatic/API data-access route**, provenance gating if anything makes scraping harder. Fails H2 ≥3-verifiable-sources bar, stays WATCH. |
| **Web-scraping pricing refresh**, Firecrawl/Exa/Tavily/Bright Data tiers | 2026-06 (1st) | FOLD → web-scraping pricing | Not re-checked this cycle (out of scope for recurrence check); still needs official re-fetch before quoting, defer to monthly sweep. |
| **MaRGen / LLM-signal-triangulation** market-research methodologies (arXiv 2508.01370, 2605.19337) | 2026-06 (1st) | no action (methodology watch) | Academic/early; no new work found this cycle. Revisit if it produces a reusable workflow. |
| **Prediction-market odds as queryable alt-data** | 2026-06, **2026-07 (2nd, evidence now clears the bar)** | **NEW-DOMAIN proposal (human-approved-only)** | **PROMOTED THIS SWEEP.** Kalshi in talks at $40B valuation (8x growth <1yr, $17.9B monthly turnover); Polymarket $15B valuation; Meta directing a standalone "Arena" app to compete (NYT/Bloomberg/NPR 2026-06-23/24), a third independent major platform entering. ≥3 actively-maintained MCPs with commits in the last 2 weeks: `caiovicentino/polymarket-mcp-server` (597★, 45 tools), `OctagonAI/octagon-mcp-server` (143★, covers prediction markets + SEC/earnings), `9crusher/mcp-server-kalshi` (22★), `JamesANZ/prediction-market-mcp` (36★, unifies Polymarket/PredictIt/Kalshi). Doesn't fit finance-markets (not securities/SEC), crypto-defi (CFTC-regulated event contracts, not DeFi primitives), or trends-discovery (priced probability, not a trend feed). **NOT LANDED, this is a proposal only, per C9/H3 structural-change-needs-human-review; goes into the PR description for human approval, not auto-merged as a new `domains/prediction-markets.md`.** |
| **Agentic-payments / pay-per-call data acquisition** (x402) | 2026-06, **2026-07 (2nd, exploding)** | WATCH → FOLD crypto-defi + install notes | Ecosystem now large (`BlockRunAI/ClawRouter` 6665★, `solana-foundation/pay` 1740★, `xpaysh/awesome-x402` 266★, dozens of new x402-native frameworks). Still a payment RAIL not a queryable source. crypto-defi shard already gained Coinbase Agentic Wallet MCP this sweep (partial absorption); an explicit "x402 install route" note is increasingly warranted next sweep. |
| **Cross-validate sentiment vs prediction-market implied probability** (research methodology) | 2026-06 (1st) | WATCH → FOLD SKILL.md guardrails | Downstream of prediction-markets NEW-DOMAIN proposal above; no independent new evidence this cycle. |
| **TikTok-Shop short-video commerce data** | 2026-06, **2026-07 (2nd, minor)** | FOLD → ecommerce-arbitrage + trends-discovery | GMV Max ad formats + EU 200M-user expansion confirmed live, but still no free/OSS Shop-GMV API beyond existing paid L3 dashboards. |
| **Agentic-commerce product feeds** | 2026-06, **2026-07 (2nd, material update)** | FOLD → ecommerce-arbitrage | OpenAI actually **killed** in-chat Instant Checkout (deprecated ~2026-03-05, <30 Shopify merchants ever went live), pivoted to retailer-run ChatGPT apps; Google shipped a "Universal Cart" spanning Search/Gemini/YouTube/Gmail + AP2 payments. Confirms original verdict (volatile distribution layer, not a stable data territory), worth a one-line shard note that the checkout channel is less stable than assumed in June. |
| **Deep-research-as-a-service APIs** (OpenAI Deep Research, Perplexity Deep Research/Agent) | 2026-06 (1st) | FOLD → web-scraping / SKILL.md delegation | Not re-checked this cycle; defer to monthly sweep. |
| **Public Telegram channels as alt-data** | 2026-06 (1st) | FOLD → x-twitter / crypto-defi / trends-discovery | `chigwell/telegram-mcp` (1321★, pushed 2026-07-22) remains the most active reader, but still no new independent verification as a *research* source vs generic Telegram automation. Stays FOLD-pending-Discovery. |

**Placeholder-domain threshold check (2026-07 quarterly Horizon scan):** `regulatory-watch`, found active EU AI Act compliance-scanner MCPs (`ark-forge/mcp-eu-ai-act`, `SonnyLabs/EU_AI_ACT_MCP`), but these are developer code-compliance scanners, a different sub-niche from the placeholder's original scope (SEC 8-K trackers, legislative trackers), does **not** cross the ≥3-viable-tools-across-≥2-tiers threshold. The other five placeholders (`agent-marketplace`, `ai-data-licensing`, `voice-and-podcast-intel`, `synthetic-and-evals`, `on-chain-intel-private`) were not independently re-searched this cycle (budget); carry over to next quarterly scan.
