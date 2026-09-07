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
| Altimis/Scweet | x-twitter | 1615★ (gh-api 2026-09-06; was 1569★, +46, same slow slope) | ④ curl_cffi TLS-fingerprint | distinct anti-detect angle, actively maintained, but growth flat and **no ready MCP** | 2026-06 |
| nirholas/XActions | x-twitter | 512★ (2026-09-06; 293→398→512, third accelerating interval) | ④/③ bundled MCP | notable acceleration this cycle, but README-churn/star-smell + HTML-dashboard product concerns from prior scan stand; recheck next sweep | 2026-06 |
| ythx-101/x-tweet-fetcher | x-twitter | 955★ (2026-09-06; +41, cooling further; 3 watchers vs 955★ = 318:1) | ④ | star-farming suspicion less acute (growth slowing) but still unproven E2E (users report fails #67/#66/#61) | 2026-06 |
| CloakHQ/CloakBrowser | browser-automation | 31233★ (2026-09-06; +8% this cycle, growth decelerating) | ④ stealth Chromium | still growing fast, but free tier ships only a closed binary (Pro/latest builds paywalled), trust concern persists; new MCP wrapper `swimmwatch/cloakbrowser-mcp` (29★) appeared around it | 2026-06 |
| lightpanda-io/browser | browser-automation | 34598★ (2026-09-07) | ① CDP-compatible engine | fast engine, but its MCP (`lightpanda-io/gomcp`) **re-confirmed archived** → still not MCP-ready | 2026-06 |
| saffron-health/libretto | browser-automation | 887★ (2026-09-06; +8%, slowing) | ④ | deterministic-code browser automation (vs runtime LLM agents); real growth, still HN-only adoption evidence | 2026-06 |
| browser-act/skills | browser-automation | 5734★ (2026-09-06; +24%, sharply decelerated from +107%) | ④ | 219 forks but only 4 contributors, concentration flag (D4 anti-inflation); commercial product (browseract.com), plausible marketing-driven growth, cannot confirm either way | 2026-06 |
| cosinusalpha/webctl | browser-automation | 415★ (2026-09-06, still last-pushed 2026-05-29 — 3.3mo unchanged) | ④ | momentum stopped since last scan; **demotion candidate next sweep if still stale** | 2026-06 |
| feder-cr/invisible_playwright | browser-automation | 1992★ (2026-09-06; +12%, pushed 2026-09-06) | ④ | source-patched **Firefox** (not Playwright despite the name) claiming to pass 5 major detection suites; real growth 0→1.8k★ in ~2mo but only 1 HN comment, no independent 3rd-party corroboration yet | 2026-07 |
| us/crw | web-scraping | 954★ (2026-09-06; **+657%**, but 2 subscribers = 477:1) | ① Firecrawl-API-compatible + built-in MCP | drop-in Firecrawl API single binary w/ MCP; "new ≠ good", only vendor-authored benchmarks | 2026-06 |
| germondai/trawl | web-scraping | 782★ (2026-09-04; +77%, subscribers 0→2 — adoption gap barely closed) | ③ FlareSolverr/Byparr drop-in | broadest CAPTCHA-class bypass claim (Cloudflare/Turnstile/reCAPTCHA/hCaptcha/GeeTest) in one proxy; AGPL, 22 forks, but 0 GitHub subscribers despite the star/fork count, adoption-signal gap | 2026-07 |
| mdowis/anansi | web-scraping | 112★ (2026-09-02; +12 in ~6wk, flattening) | ③/④ self-host, ships own MCP | self-healing selectors + TLS-fingerprint identity layer, MCP-native; genuinely novel capability but only 100★/2 subscribers | 2026-07 |
| 3441293738/creatorhub | web-scraping (CN) | 1896★ (2026-09-06; **+724%**, fastest on this list; ⚠ gh api now reports license:null, the AGPL claim below is unbacked) | ④ | multi-platform CN scraper (抖音/小红书/快手), AGPL, Playwright+FastAPI; single-maintainer, unverified adoption | 2026-07 |
| goat-sdk/goat | crypto-defi | 1007★ (2026-07-02; flat, -2) | ③ agentic toolkit | steady growth, but a dev framework not a plug-and-play source | 2026-06 |
| debridge-finance/debridge-mcp | crypto-defi | 32★ (was 31★, flat, stale >3.5mo) | ① no-key | cross-chain bridging capability gap, but growth stalled, trending toward SKIP | 2026-06 |
| tatumio/blockchain-mcp | crypto-defi | 15★ (was 14★, negligible growth) | ① key | overlaps Moralis/Covalent, no clear edge | 2026-06 |
| CoinStatsHQ/coinstats-mcp | crypto-defi | 16★ (was 14★, actively pushed 2026-07-10) | ① free key | maintained but still redundant w/ CoinGecko for price; portfolio-tracking niche only | 2026-06 |
| nextdev-labs/mcp (Agent Usability Index) | trends-discovery (meta) | 79★ (was 75★, slow growth) | ① | source-selection meta-tool, not a data feed; park until it proves a research use | 2026-06 |
| BlockRunAI/blockrun-mcp | crypto-defi / x-twitter / web-scraping (multi-domain) | 393★ (2026-09-05; **star count FELL 475→393**, consistent with an inflation unwind, not adoption) | ② x402 resale | broad multi-domain data MCP via x402 micropayments (search/research/markets/crypto/X); crypto is one slice not crypto-specific, verify crypto-data quality/pricing specifically before ADD | 2026-07 |
| Panniantong/Agent-Reach | reddit-community | 78457★ (2026-09-01; **+217%**; 284 watchers = 276:1 — needs adjudication next sweep) | ④ | multi-platform keyless reader CLI (Reddit/X/YT/Bili/XHS); high star:fork ratio + cookie-auth ToS risk; CLI not MCP | 2026-06 |
| ksanjeev284/reddit-universal-scraper | reddit-community | 569★ (created 2025-12-13, new this cycle) | ③ self-host, no MCP wrapper | fast-growing CLI scraper "works on any subreddit/user", but no MCP yet and no independent adoption evidence beyond stars | 2026-07 |
| omkarcloud/botasaurus | web-scraping | 5704★ (2026-07-26; +20%. **Correction: the "stale" label below is wrong** — pushed ~6wk ago, well inside the 12mo bar) | ③ | all-in-one anti-detect w/ Cloudflare bypass, but stale, force-pushed/squashed history, zero releases | 2026-06 |
| oxylabs/oxylabs-mcp | web-scraping | 96★ (2026-06, unchanged) | ② | official paid anti-bot scraper MCP; backup provider, no free tier, doesn't beat Bright Data | 2026-06 |
| Tosheroon MCP | ecommerce-arbitrage | n/a (closed SaaS) | ① | free MCP w/ 90d price history + 30d forecast 9 Amazon regions; closed-source paywalled, single-source adoption | 2026-06 |
| christian-ramos/mcp-amazon-sp-api | ecommerce-arbitrage | 2★ (still, pushed 2026-07-20) | ① | 55+ tools/19 SP-API scopes fills "SP-API no ready MCP" gap; still 2★/0 forks, unproven | 2026-06 |
| mansournorouzi/amazon-sp-mcp | ecommerce-arbitrage | 42★ (created 2026-02, new candidate) | ① official (LWA OAuth) | 21x more stars/forks than the above SP-API candidate, recently patched an axios CVE (maintenance signal), but **no license file** = real risk flag; no independent adoption evidence yet | 2026-07 |
| TickDB/tickdb-unified-realtime-marketdata-api | finance-markets | 410★ (2026-06, unchanged) | ① | adds HK/A-share/forex/commodity realtime (US-centric shard gap); free-tier/pricing unverified. **Weaker CN-gap candidate than akshare-one-mcp below** (thinner adoption evidence) | 2026-06 |
| zwldarren/akshare-one-mcp | finance-markets | 213★ (created 2025-04, 47 forks, new candidate) | ① free (akshare) | fills the CN A-share gap the US-centric baseline lacks; MIT + real fork-usage evidence beats TickDB's thin signal, but stale ~4mo since push, recheck activity before promoting | 2026-07 |
| augiemazza/varrd | finance-markets | 18★ (2026-06, unchanged) | ④ | backtesting/event-study/stat-validation MCP, distinct analysis route; unproven | 2026-06 |
| TipRanks/mcp | finance-markets | 10★ (created 2026-07-21, brand new) | ① official, hosted | official vendor MCP (analyst ratings/Smart Score/technicals), genuinely new capability class not in baseline; 1 day old, unproven | 2026-07 |
| Dune Analytics MCP (official) | crypto-defi | n/a (official `sim-api-mcp` confirmed archived, 3★; community `kukapay/dune-analytics-mcp` 41★ but >14mo stale) | ① | no viable Dune MCP this cycle, official dead, community alt too stale to admit | 2026-06 |
| kukapay/crypto-indicators-mcp | crypto-defi | 131★ (last push 2025-12-06 = 9mo stale; tombstone review due next sweep) | ② | TA-indicator computation pairing ccxt; flag for tombstone review next sweep if still silent | 2026-06 |
| nirholas/cryptocurrency.cv | crypto-defi | 304★ (2026-08-27) — **now SKIPped, see reject log**: repo-spray pattern (100+ repos on one account, ~20 created+pushed inside 11 minutes on 2026-09-03), 2 subscribers | ① | strongest mover in crypto-defi watchlist this cycle: real growth + active maintenance; still single-maintainer, no 3rd-party adoption evidence, priority-flag for next-cycle promotion check | 2026-06 |
| itsjwill/seoctopus | seo-keywords | 10★ (was 9★, still stale since 2026-02) | ④ | single-push-then-abandon pattern confirmed; trending toward SKIP next sweep if still silent | 2026-06 |
| GEORank (yaojingang/GEORank) | seo-keywords | 455★ (2026-08-26; +39%) | ① OSS self-host | GEO/AEO (generative-engine-optimization) ranking platform, healthy fork ratio; doesn't unseat GSC/DataForSEO on keyword-volume/SERP capability, part of a visible **emerging GEO/AEO tooling cluster** (GEORank, RankWise, orangeo-ai-visibility-skill), worth a dedicated angle next sweep if it recurs | 2026-07 |
| Google Trends API (official, alpha) | seo-keywords/trends-discovery | n/a | ② | still alpha-gated per 3 independent 2026 sources, no pricing/MCP; no change | 2026-06 |
| PHY041/claude-skill-reddit | social-publishing | 41★ (2026-07-03; +4 in 3mo, untouched 2.1mo, license:null) | ④ | free browser-act Reddit posting; single-commit macOS-only, still unproven | 2026-06 |
| typefully/agent-skills | social-publishing | 54★ (was 51★) | ① | official Typefully draft+schedule skills; thin vs Buffer, needs $8+/mo | 2026-06 |
| publora/skills | social-publishing | 46★ (2026-08-11) — **worry RESOLVED**: there are new commits; Publora pricing now verified at source and folded into the shard | ② | new 10-platform paid API+skills, plausible cheaper Ayrshare alt; pricing unverified | 2026-06 |
| trypostit/trypost | social-publishing | 593★ (2026-09-07; +45%, genuinely gaining) | ③ self-host, native MCP | 12-platform native publish + AI copilot, MCP-native OSS scheduler; doesn't clear REPLACE vs Postiz (12 vs 30+ platforms, 80x fewer stars) | 2026-07 |
| xueyc1f/turbopush-mcp | social-publishing (CN) | 32★ (2026-08-28; +10 in 2mo, 1 watcher — still fails adoption gate, and its capability gap is now largely filled by the social-auto-upload ADD) | ① MCP | MCP publishing to WeChat/Douyin/Bilibili/Xiaohongshu/20+ platforms in one server, genuine capability gap (no current MCP-native multi-CN-platform poster), but fails adoption≥1 admission gate | 2026-07 |
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

| **mahrtayyab/tweety** | x-twitter | 668★ (2026-08-26) | ③ cookie session | **HOLD, not ADD** — discovery proposed it as the fallback for the aging twikit; the verifier refuted it for benchmarking against the wrong incumbent (twscrape, not twikit, is the shard's live ③ row). Also license:null and its PyPI package is 13.7mo stale, so `pip install tweety-ns` ships a broken client | 2026-09 |
| PawiX25/twifork | x-twitter | 31★ (2026-08-31) | ③ drop-in twikit fork | a live MIT API-compatible fork of twikit, created one month after twikit went silent — lowest-migration-cost answer if it holds. 31★/1 watcher/11 dependents fails the adoption gate; its 10k/mo PyPI figure cannot be separated from mirror/CI traffic | 2026-09 |
| ihuzaifashoukat/x-use | x-twitter | 164★ (2026-08-18) | ④ bundled MCP | the only ④ X repo with a bundled MCP and non-trivial stars; 4 subscribers, 0 open issues, no dependents = adoption 0 | 2026-09 |
| jsilets/twscrape-twitter-mcp | x-twitter | 3★ (2026-09-06) | ③ MCP over twscrape | the natural successor to the dead adhikasp/mcp-twikit (wraps the *maintained* twscrape), which is why it is logged; 3★/219 dl-mo is far below the adoption gate | 2026-09 |
| public-clis/twitter-cli | x-twitter | 2900★ (2026-05-07) | ③ CLI | 42.5k monthly PyPI installs is inflation-resistant adoption, but 4mo unpushed through two known breaking X endpoint changes and no MCP; functional liveness unverified | 2026-09 |
| zedeus/nitter (upstream) | x-twitter | 14201★ (2026-09-06) | ③ self-host | **the shard tombstones public instances, but upstream is emphatically alive** and pushed daily. Not promoted: X Corp issued a cease-and-desist 2026-08-24 demanding takedown of instances and the repo — unresolved legal risk on the whole route | 2026-09 |
| Tencent/BrowserSkill | browser-automation | 1801★ (2026-09-04) | ④ | **HOLD** — pitched as reusing a real user profile rather than spoofing a fresh one; verifier refuted it because `nodriver` already documents `user_data_dir` reuse in this repo's own tool doc. No anti-detection claims, no concurrency, no MCP | 2026-09 |
| cdpdriver/zendriver | browser-automation | 1417★ (2026-08-16) | ④ | **HOLD** — an actively-maintained nodriver successor-fork, directly relevant now that nodriver is 3.8mo stalled. Held pending independent adoption evidence; re-check first next sweep | 2026-09 |
| Skyvern-AI/rustwright | browser-automation | 875★ (2026-09-05) | ④ | Rust Playwright peer from the maintainers of an existing shard row (skyvern); too new to read | 2026-09 |
| Bin-Huang/camoufox-cli | browser-automation | 341★ (2026-08-18) | ④ | CLI over the camoufox row the shard already carries; 2 subscribers, no HN/Reddit thread | 2026-09 |
| g1879/DrissionPage | browser-automation | 12425★ (2026-08-29) | ④ CN | absent from the shard because of an EN-source blind spot, not a quality judgment. Blocked on NOASSERTION licensing on both engine and MCP wrapper — the exact gate that rejected nottelabs/notte | 2026-09 |
| citrolabs/ego-lite | browser-automation | 15150★ (2026-09-06) | ④ | 15.1k★ vs 42 subscribers (360:1) is worse than the ratio that put obscura in the reject log, and its two Show HN posts scored 12 and 1 points, which does not explain 15k stars. Headline "2.5x faster than agent-browser" is author-published, unreplicated | 2026-09 |
| botswin/BotBrowser | browser-automation | 2604★ (2026-09-03) | ④ | MIT core, but profiles for build 150+ are subscription-gated — the free build does not defeat detection. Not a free route despite the license | 2026-09 |
| lexmount/moli | browser-automation | 1759★ (2026-09-06) | ④ engine | 1759★ in 27 days: observe, don't admit (D3 "new ≠ good") | 2026-09 |
| getmaxun/maxun | web-scraping | 17377★ (2026-09-05) | ③ self-host | no-code robot builder; large and alive, adjudication deferred (surfaced late in the sweep) | 2026-09 |
| 0xMassi/webclaw | web-scraping | 2324★ (2026-09-06) | ③ | 2324★ against **10 npm downloads/week** — stars not converting into installs is the cleanest "high stars ≠ adoption" case this sweep | 2026-09 |
| 0xchasercat/draco | web-scraping | 96★ (2026-09-05) | ③ Rust | **the weekly E5 poller's only relevant lead** (Show HN 2026-08-02, "self-hostable Firecrawl alternative"). Verified honestly: 1 contributor, 0 subscribers, and reading all 10 HN comments, **not one reports having run it**. Adoption 0 | 2026-09 |
| Johell1NS/browser-search | web-scraping | 513★ (2026-09-02) | ④ | orchestration-only wiring layer whose value is contingent on CloakBrowser, itself already trust-flagged above | 2026-09 |
| ProxyShard/ShardBrowser | web-scraping | 886★ (2026-09-03) | ④ | published by a proxy seller — the free browser funnels the paid proxies, i.e. the exact "hidden cost is proxies" pattern route ④ must flag | 2026-09 |
| brightbeanxyz/brightbean-studio | social-publishing | 2278★ (2026-08-13) | ③ self-host | one human wrote ~96% of commits ("built in 3 weeks with Claude and Codex" per the author's own Show HN) on a self-hosted publisher that holds your OAuth tokens. Bus factor 1 | 2026-09 |
| ZJU-REAL/Easel | social-publishing | 376★ (2026-09-06) | ③ | 9 days old, university lab, adoption 0. Too early to read either way | 2026-09 |
| HKUDS/Vibe-Trading | crypto-defi | 32837★ (2026-09-06) | ③ agentic | 184:1 star:watcher and a Trendshift badge, but 11k pypi downloads/mo is install traffic stars cannot fake → WATCH rather than SKIP | 2026-09 |
| duneanalytics/spellbook | crypto-defi | 1515★ (2026-09-04) | ① OSS | the curated Dune query layer; relevant because no viable Dune *MCP* exists (see the row above), but it is a dbt repo, not a queryable source | 2026-09 |
| **dawsbot/eth-labels** | crypto-defi | 296★ (2026-07-10) | ③ free | **HOLD** — proposed as a free replacement for Nansen ①; refuted because the discovery agent conceded there is no smart-money layer, no wallet PnL, no behavioural scoring. Nansen's labels are the by-product, not the product | 2026-09 |
| deepseek-ai/deepseek-harness | mcp-ecosystem (horizon) | 214054★ (2026-09-04) | n/a | the genuinely new thing in August, and CN-native (the discovery-cn blind spot). A *harness*, not a data territory → FOLD, and only as a class-A discovery surface to poll. Recheck before adding the surface; the 1000-3000★ plugin repos orbiting it are where inflated satellites will appear | 2026-09 |
| yaojingang/GEORank · ansvisor/ansvisor · AKzar1el/mcp-geo | seo-keywords (horizon) | 455★ · 106★ · 44★ (2026-08/09) | ① | the GEO/AEO cluster, now recurring at scan 2. Explicitly **not** proposed as a NEW-DOMAIN: it measures rank/citation on search-shaped surfaces, which is seo-keywords territory with different engines — a patch, not a new framework | 2026-09 |

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
| pinchtab/pinchtab | browser-automation | 10233★ | 10.2k★ / 41 subscribers (250:1) with only **6 open issues** — 10k stars generating six issues is not a shape real adoption produces. Rebutted at capability level by an independent third party: someone shipped "Unpinched", a detector for exactly its stealth injection and CDP bridge, i.e. the property it is sold on is fingerprintable | 2026-09 |
| Anakin-Inc/anakin | web-scraping | 2769★ | top contributor has **6 commits**; ~two dozen commits total behind a 2.7k★ repo = squashed/dumped history with no engineering trail. 553:1 star:watcher, worse than the obscura reject | 2026-09 |
| oxylabs/web-scraper-api | web-scraping | 492★ | 492★ / 1 fork / 0 subscribers; marketing repo for a hosted product with no runnable self-host artifact | 2026-09 |
| spider-rs/spider | web-scraping | 2698★ | fast and real, but no capability gap vs Crawl4AI and no ready MCP — a crawler component, not a source | 2026-09 |
| 6551Team/opentwitter-mcp | x-twitter | 1448★ | 套壳: MIT client over a closed vendor backend (ai.6551.io), no edge over the already-catalogued twitterapi.io ②. 1448★ against **1 subscriber** | 2026-09 |
| runesleo/x-reader | x-twitter | 960★ | X path just delegates to Jina Reader — strictly weaker than the incumbent FxEmbed for the same read-one-post job; 240:1 star:watcher | 2026-09 |
| fa0311/TwitterInternalAPIDocument | x-twitter | 711★ | not a data source: it documents X's internal API, it fetches nothing and cannot answer a research query | 2026-09 |
| Steph-ux/x-mcp-playwright · alarok/x-agent-sdk (+4 siblings) | x-twitter | 0–35★ | adoption ~0, weeks-old single-author repos, several with no license; one (proxidize/x-scraper) is vendor-authored by a proxy seller | 2026-09 |
| markrussinovich/Polypost | social-publishing | 214★ | it FORMATS, it does not transmit — cannot replace any part of Buffer/Ayrshare/Publora because it never posts. Star count is plausibly author-reputation-driven | 2026-09 |
| Anil-matcha/Free-AI-Social-Media-Scheduler | social-publishing | 502★ | exactly ONE contributor in 19 months; the repo name is the SEO phrase and the description name-drops three competitors — the "X alternative" repo-farm shape | 2026-09 |
| ndesv21/socialclaw | social-publishing | 86★ | CLI over each platform's official write API: removes a SaaS subscription but **not a single barrier** (X still bills per post incl. the $0.20 link fee). Same shape as the 2026-06 PostFast/BulkPublish cluster | 2026-09 |
| cosinusalpha/webctl | browser-automation | 415★ | **demoted from watchlist** as flagged last sweep: still last-pushed 2026-05-29 (3.3mo unchanged), 1 watcher, no license | 2026-09 |
| nirholas/cryptocurrency.cv | crypto-defi | 304★ | **demoted from watchlist.** Repo-spray: 100+ repos on one account, ~20 created *and* pushed inside 11 minutes on 2026-09-03; 304★ against 2 subscribers. The 2026-06 "strongest mover, priority promotion check" read was seeing a spray, not adoption | 2026-09 |
| 0xArchiveIO/0xarchive-mcp | crypto-defi | 11★ | `archived=true` per gh api, adoption 0 | 2026-09 |
| CoinLobster/coinlobster-mcp | crypto-defi | 14★ | 14★ / 0 forks / 0 watchers at 5 weeks old; "only MCP with live whale trades across 15 exchanges" is an uncorroborated vendor README claim | 2026-09 |
| cipher-rc5/UnofficialArkhamAPI (+ Arkham-MCP cluster) | crypto-defi | 7★ | stale >12mo, and the wrappers still require a paid Arkham key — no free route delivered | 2026-09 |
| nirholas/kol-quest (+ KOL-tracking cluster) | crypto-defi | ≤19★ | adoption 0 across the category; two highest entries come from the nirholas spray account above; the best-resourced one is 38 pay-per-call x402 endpoints, i.e. paid resale not free | 2026-09 |
| Ryze-AI-Adgent/open-seo-mcp-skills | seo-keywords | 542★ | **from the weekly E2 inbox** — 542★ with **ZERO subscribers** and 10 forks is the sharpest inflation shape seen this scan; composes GSC① + DataForSEO② which the shard already carries | 2026-09 |
| cinderline/northcinder | ecommerce-arbitrage | 1216★ | 1216★ / 8 forks (152:1) / 5 subscribers (243:1) — the exact ratio pattern D4 names; no push since 2026-08-22 | 2026-09 |
| RankSpotAI/awesome-geo-tools | seo-keywords | 75★ | created the same day, 75★ with 0 forks and 1 subscriber = seeded not organic; published under a GEO vendor org so its comparison table is self-interested | 2026-09 |

---

## New-angle watchlist (Horizon scan, needs to recur across ≥2 scans before any NEW-DOMAIN proposal)

Per H3 anti-bloat: a new angle stays here until it proves recurring + distinct + has ≥3 verifiable
sources. Default verdict is FOLD into an existing domain; NEW-DOMAIN/NEW-SKILL are human-approved.

| angle | scan(s) seen | verdict | disposition |
|---|---|---|---|
| **X API re-tier**, Owned Reads now $0.001/resource (confirmed at source: official `devcommunity.x.com` post, effective 2026-04-20); $0.20 URL-post fee confirmed live via real developer billing complaints | 2026-06, **2026-07 (2nd, source-verified)** | FOLD → x-twitter | Was auth-walled/unverified in June; now confirmed at the official source. Numbers already match social-publishing shard's $0.20 link-post line; x-twitter shard doesn't cite pricing directly so no shard edit needed, closing this item. |
| **Agent-memory as a capability class**, mem0ai/mem0, getzep/zep, new entrants `engram` (5623★), `mnemox-ai/tradememory-protocol` (1399★), Product Hunt #1 "Wolbarg" | 2026-06, 2026-07, **2026-09 (3rd)** | NEW-SKILL flag (human-only) | Genuinely new capability class, but it stores **agent state**, not a queryable commercial-data source → out of scope for this source matrix. Flag only; do not add a domain. |
| **MCP deployment shape shift**, MCP spec 2026-07-28 RC (stateless core, Tasks extension, MCP Apps) now locked and publishing | 2026-06, 2026-07, **2026-09 (3rd)** | FOLD → ready-skills / install notes | Plumbing for HOW MCP servers are wired, not WHAT data is reachable. No new/closed data source. |
| **Emerging consumer platforms**, Divine (Jack Dorsey Vine reboot) publicly launched 2026-04-29 w/ C2PA provenance gating | 2026-06, **2026-07 (2nd, partial)** | FOLD → x-twitter / social-publishing / trends-discovery (watch) | Still **no programmatic/API data-access route**, provenance gating if anything makes scraping harder. Fails H2 ≥3-verifiable-sources bar, stays WATCH. |
| **Web-scraping pricing refresh**, Firecrawl/Exa/Tavily/Bright Data tiers | 2026-06 (1st) | FOLD → web-scraping pricing | Not re-checked this cycle (out of scope for recurrence check); still needs official re-fetch before quoting, defer to monthly sweep. |
| **MaRGen / LLM-signal-triangulation** market-research methodologies (arXiv 2508.01370, 2605.19337) | 2026-06 (1st) | no action (methodology watch) | Academic/early; no new work found this cycle. Revisit if it produces a reusable workflow. |
| **Prediction-market odds as queryable alt-data** | 2026-06, 2026-07, **2026-09 (3rd, ecosystem still live)** | **NEW-DOMAIN proposal (human-approved-only)** | **PROMOTED THIS SWEEP.** Kalshi in talks at $40B valuation (8x growth <1yr, $17.9B monthly turnover); Polymarket $15B valuation; Meta directing a standalone "Arena" app to compete (NYT/Bloomberg/NPR 2026-06-23/24), a third independent major platform entering. ≥3 actively-maintained MCPs with commits in the last 2 weeks: `caiovicentino/polymarket-mcp-server` (597★, 45 tools), `OctagonAI/octagon-mcp-server` (143★, covers prediction markets + SEC/earnings), `9crusher/mcp-server-kalshi` (22★), `JamesANZ/prediction-market-mcp` (36★, unifies Polymarket/PredictIt/Kalshi). Doesn't fit finance-markets (not securities/SEC), crypto-defi (CFTC-regulated event contracts, not DeFi primitives), or trends-discovery (priced probability, not a trend feed). **NOT LANDED, this is a proposal only, per C9/H3 structural-change-needs-human-review; goes into the PR description for human approval, not auto-merged as a new `domains/prediction-markets.md`.** |
| **Agentic-payments / pay-per-call data acquisition** (x402) | 2026-06, 2026-07, **2026-09 (3rd, governance change)** | WATCH → FOLD crypto-defi + install notes | Ecosystem now large (`BlockRunAI/ClawRouter` 6665★, `solana-foundation/pay` 1740★, `xpaysh/awesome-x402` 266★, dozens of new x402-native frameworks). Still a payment RAIL not a queryable source. crypto-defi shard already gained Coinbase Agentic Wallet MCP this sweep (partial absorption); an explicit "x402 install route" note is increasingly warranted next sweep. |
| **Cross-validate sentiment vs prediction-market implied probability** (research methodology) | 2026-06 (1st) | WATCH → FOLD SKILL.md guardrails | Downstream of prediction-markets NEW-DOMAIN proposal above; no independent new evidence this cycle. |
| **TikTok-Shop short-video commerce data** | 2026-06, **2026-07 (2nd, minor)** | FOLD → ecommerce-arbitrage + trends-discovery | GMV Max ad formats + EU 200M-user expansion confirmed live, but still no free/OSS Shop-GMV API beyond existing paid L3 dashboards. |
| **Agentic-commerce product feeds** | 2026-06, **2026-07 (2nd, material update)** | FOLD → ecommerce-arbitrage | OpenAI actually **killed** in-chat Instant Checkout (deprecated ~2026-03-05, <30 Shopify merchants ever went live), pivoted to retailer-run ChatGPT apps; Google shipped a "Universal Cart" spanning Search/Gemini/YouTube/Gmail + AP2 payments. Confirms original verdict (volatile distribution layer, not a stable data territory), worth a one-line shard note that the checkout channel is less stable than assumed in June. |
| **Deep-research-as-a-service APIs** (OpenAI Deep Research, Perplexity Deep Research/Agent) | 2026-06 (1st) | FOLD → web-scraping / SKILL.md delegation | Not re-checked this cycle; defer to monthly sweep. |
| **Public Telegram channels as alt-data** | 2026-06 (1st) | FOLD → x-twitter / crypto-defi / trends-discovery | `chigwell/telegram-mcp` (1321★, pushed 2026-07-22) remains the most active reader, but still no new independent verification as a *research* source vs generic Telegram automation. Stays FOLD-pending-Discovery. |

**Placeholder-domain threshold check (2026-07 quarterly Horizon scan):** `regulatory-watch`, found active EU AI Act compliance-scanner MCPs (`ark-forge/mcp-eu-ai-act`, `SonnyLabs/EU_AI_ACT_MCP`), but these are developer code-compliance scanners, a different sub-niche from the placeholder's original scope (SEC 8-K trackers, legislative trackers), does **not** cross the ≥3-viable-tools-across-≥2-tiers threshold. The other five placeholders (`agent-marketplace`, `ai-data-licensing`, `voice-and-podcast-intel`, `synthetic-and-evals`, `on-chain-intel-private`) were not independently re-searched this cycle (budget); carry over to next quarterly scan.

**2026-09 light pulse (September is not a quarterly month, so this is H1 only, not the full H1-H4).**
Headline: **no new territory this month.** All four H1 classes were scanned and none produced a
platform API-policy change, a barrier route opening or closing, or an acquisition affecting
commercial data. The loudest scraping story in the window was ideological rather than technical, and
the new-repo flood was agent-harness/coding-tool, not data-acquisition.

Recurrence deltas against the rows above (all figures live `gh api`, 2026-09-06):
- **Agent-memory** (3rd scan), **MCP deployment shape** (3rd), **Prediction markets** (3rd),
  **x402 agentic payments** (3rd) all recur; **no verdict changes.** The prediction-markets
  NEW-DOMAIN proposal raised in 2026-07 **remains a proposal awaiting human approval** (C9/H3) and
  this run does not land it. Its ecosystem is still alive: `caiovicentino/polymarket-mcp-server`
  668★ (was 597★), `9crusher/mcp-server-kalshi` 27★, `OctagonAI/octagon-mcp-server` 147★.
- **x402 carries one material governance change:** the canonical repo now resolves as
  `x402-foundation/x402` (6582★, pushed 2026-09-05) — it has moved out of the Coinbase org to a
  neutral foundation. Verdict unchanged (a payment *rail*, not a queryable source), but the explicit
  x402 install-route note is now overdue.
- **No recurrence:** X API re-tier (closed at source in 2026-07), Divine/emerging consumer platforms,
  MaRGen methodology, sentiment-vs-prediction-market cross-validation.
- **Not re-checked, stated rather than left to read as confirmation:** web-scraping pricing refresh,
  TikTok-Shop commerce data, deep-research-as-a-service, public Telegram channels. Their recurrence
  counts are unchanged; a light pulse has no budget for official-pricing-page fetches.

Two angles are new this scan; **neither is proposable as a NEW-DOMAIN**, and both are logged above:
**(A) DeepSeek Harness as a second plugin-distribution surface** (1st scan) → FOLD into
mcp-ecosystem as a discovery surface, because it is a harness and makes no new data reachable.
**(B) GEO/AEO answer-engine visibility tracking** (2nd scan, so nominally eligible to argue) →
FOLD into seo-keywords, declined for NEW-DOMAIN on the generative test: it measures rank and
citation on search-shaped surfaces, which is the existing territory with different engines.

**Structural changes proposed by this run: none** beyond re-affirming the still-pending 2026-07
prediction-markets proposal. No new domain, no new sub-skill was created.
