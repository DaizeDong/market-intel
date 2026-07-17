# Discovery state

Working scratchpad for the Discovery phase of `refresh-protocol.md`. Lightweight, append-only.
Promotion to `domains/` shards happens in the Verify & Diff phase.

## Inbox

Candidates surfaced by Discovery (Twitter polling, GitHub trending, blog scans, etc.).
Format: `[YYYY-MM-DD] @source: <one-line> <repo-or-url>`.

<!-- e.g. [2026-06-20] @jxnl: new instructor-mcp wraps eval harness over MCP https://github.com/... -->

### 2026-06-17 sweep, HOLD list (verified, awaiting human eyeballs)

| candidate | domain | reason for HOLD |
|---|---|---|
| BigGo Search MCP (Funmula-Corp/BigGo-MCP-Server) | ecommerce-arbitrage | Repo dormant 13.5 months (v0.2.0 on 2025-04-30, no commits since). APAC marketplace coverage (Shopee/Taobao/AliExpress) is confirmed and the only such MCP, but staleness needs a human call: test cert signup still issues working keys before relying. **Caught by gh-api check that 3-lens LLM verify alone missed (P4 lesson).** |

### 2026-06-17 sweep, Watch list (39 candidates demoted on adversarial verify)

These passed Discovery but failed at least one of the 3-lens verify (existence/freshness/top-pick-impact).
Keep tracking, re-evaluate next sweep if upstream activity resumes or top-pick changes.

**Refuted on top-pick-impact (marginal vs current top):**
- `the-convocation/twitter-scraper` (x-twitter), Node port, no top-pick impact
- `Altimis/Scweet` (x-twitter), 3rd-tier scraper, dupe of twscrape's row
- `nodriver` (web-scraping), async CDP, overlaps Patchright
- `scrapegraph-ai` (web-scraping), NL extraction, covered by Firecrawl/Crawl4AI
- `Apify Amazon Scraper actor` (ecommerce-arbitrage), overlaps Rainforest/Oxylabs
- `tinyfish-io/agentql-mcp` (ecommerce-arbitrage), semantic-selector ergonomics, doesn't fix Keepa gap
- `shopify-dev/storefront-mcp` (ecommerce-arbitrage), no price history; DTC has low arbitrage spreads
- `dexpaprika-mcp` (crypto-defi), overlaps GeckoTerminal/CoinGecko
- `Hyperliquid Python SDK` (crypto-defi), single-venue, ccxt covers multi-venue
- `heurist-mesh-mcp-server` (crypto-defi), wrapper-over-wrappers
- `Keywords Everywhere MCP` (seo-keywords), DataForSEO dominates this slot
- (plus ~20 more, see full sweep output for the complete list)

**Refuted on freshness:**
- `rebrowser-patches` (web-scraping), 13 months stale
- `brianellin/bsky-mcp-server` (reddit-community), dormant since Apr 2025
- `financial-datasets/mcp-server` (finance-markets), >12 months stale
- `Serper MCP variants` (seo-keywords), both candidates stale

## P2 trigger fired 2026-06-17

`feedback-bump.py` detected ≥3 distinct domains with `barrier_found` outcome in the 90-day
window, the ROADMAP `transport: brokerage` trigger is now ACTIVE, not reserved. See
`companion-config-spec.md` §3.1 (brokerage enum value lands in spec v1.3) and
`domains/web-scraping.md` for the activated brokerage entries.

## Twitter watchlist

Curated set of X/Twitter accounts polled weekly during Discovery to surface new MCPs,
agent tooling, scrapers, and adjacent infra. Goal is signal density, not coverage. Prune
aggressively when an account drifts off-topic for >2 sweeps.

All handles confirmed active as of 2026-06. Items tagged `(verify)` are ones I have
lower confidence in, re-check on first poll and drop if stale.

### A. Anthropic / MCP core (5)

- `@AnthropicAI`, official; ships MCP spec changes, Claude Code release notes, model launches. Filter: only MCP/Claude Code/tool-use threads.
- `@alexalbert__`, Anthropic devrel; high signal on Claude Code features and prompting patterns.
- `@mlpowered` (Erik Schluntz), Claude Code eng lead-adjacent; ships demos of agent loops with MCP.
- `@sauers_` (Sam Bowman / Anthropic) `(verify)`, flagged because the handle for the policy/research Sam Bowman has shifted before; confirm it's the Anthropic person still posting MCP/agent content.
- `@dhh`, not Anthropic, but the `modelcontextprotocol` org account `@modelctxprotocol` `(verify)`, I'm not confident a dedicated org handle exists vs. just posts under @AnthropicAI; check first poll, drop if it's a squatter.

### B. AI tooling builders (11)

- `@hwchase17` (Harrison Chase, LangChain), orchestration framework launches, agent patterns, eval tooling.
- `@jxnl` (Jason Liu), Instructor maintainer; structured-output + eval pipelines + MCP wrappers.
- `@swyx` (Shawn Wang), Latent Space podcast; aggregator-style signal on what tools shipped this week.
- `@simonw` (Simon Willison), `llm` CLI, datasette, hands-on MCP / tool-use writeups; high noise-to-signal.
- `@karpathy`, only on relevant topics; surfaces architectural shifts that drive new tooling.
- `@sama`, only when announcing OpenAI tool/agent infra (which then spawns clones in MCP ecosystem).
- `@dharmesh` (Dharmesh Shah), agent.ai builder, talks about agent marketplaces and infra picks.
- `@mathemagic1an` (Jay Hack), agent infra commentary, often early on new MCP servers.
- `@yoheinakajima`, BabyAGI lineage; surfaces minimal-agent patterns and new orchestration libs.
- `@jerryjliu0` (Jerry Liu, LlamaIndex), RAG + agent tool stacks; LlamaIndex's MCP integrations.
- `@virattt` (Virat Singh), ships financial-agent MCPs; useful proxy for the "agent + commercial data" niche this skill targets. `(verify)`, confirm handle still active and on-topic.

### C. Scraping / browser-automation specialists (6)

- `@browser_use`, browser-use project account; ships releases and integrations.
- `@gregor_zunic` (Gregor / browser-use co-founder) `(verify)`, co-founder identity / handle spelling; confirm.
- `@unclecode` (Hamza / crawl4ai maintainer), crawl4ai releases, anti-detection notes, LLM-scraper patterns.
- `@skyvern_ai`, Skyvern (vision-based browser automation) launches and benchmarks.
- `@Steel_dev` (Steel.dev), managed browser infra for agents; signals what scraping bottlenecks are commercializing.
- `@ScrapingBee`, proxy/managed-scrape vendor account; price/anti-bot trend signal, low builder-signal, keep on probation.

Note: patchright / camoufox / nodriver maintainers are largely GitHub-only with no active X
presence I can verify. Track those via GitHub releases, not this watchlist.

### D. China bridge (3)

- `@deepseek_ai`, DeepSeek official EN account; model + tool-calling release notes.
- `@Alibaba_Qwen`, Qwen team EN account; Qwen-Agent and tool-use releases.
- `@zhouwenmeng` (Zhou Wenmeng / Moonshot / Kimi) `(verify)`, uncertain whether a real EN-active handle exists; confirm and drop if posts are CN-only or inactive.

**Uncertain / dropped from consideration:**
- ByteDance has no single high-signal EN AI-tooling face I can confidently name; skip rather than guess.
- `@modelcontextprotocol` as a literal org handle, flagged above, may not exist as a distinct account.

**Count summary:** A=5, B=11, C=6, D=3 → **25 handles**, of which **6** are flagged `(verify)`.
Target was ~30 but I'd rather ship 25 verified than pad with guesses. Add more as the weekly
poll surfaces high-signal accounts via retweets/quotes from this seed set.

## Polling protocol

- **Cadence:** weekly, as part of the Discovery phase weekly light pass.
- **Tool:** `mcp__twitterapi-mcp__get_user_last_tweets` per handle. twitterapi.io MCP is
  already connected; no install step.
- **Window:** last 7 days of tweets per account (or since last poll timestamp, whichever
  is shorter).
- **Inclusion threshold (OR):**
  1. Tweet text contains any of: `MCP`, `agent`, `scraper`, `scraping`, `browser-use`,
     `tool-use`, `tool calling`, `eval`, or names a tool launch (`launching`, `shipped`,
     `released`, `open-source`).
  2. Tweet has **>20 retweets** AND links to an OSS repo URL (github.com / gitlab.com).
- **Exclusion:** drop tweets that are purely model/benchmark hype with no tool or repo link.
- **Output:** append each surviving candidate to the `## Inbox` section above as
  `[YYYY-MM-DD] @handle: <one-line summary> <repo-or-url>`. One line per candidate.
- **Watchlist hygiene:** if an account produces 0 inbox-worthy tweets for **3 consecutive**
  weekly polls, move it to `## Reject log` with reason `low-signal`. If a `(verify)` handle
  fails first-poll verification (wrong person / inactive / handle changed), drop immediately
  and note in `## Reject log`.

## Reject log

Candidates and watchlist entries that failed Discovery threshold or drifted off-topic.
Format: `[YYYY-MM-DD] @handle-or-tool: <reason>`.

<!-- e.g. [2026-06-20] @some_account: low-signal, 3 weeks 0 inbox hits, dropped -->

## Watch list

Tools/accounts that are *interesting but not yet promotable*, borderline candidates we
keep an eye on without committing to a `domains/` shard. Promote up to Inbox when
threshold is met, demote to Reject log when stale.


## 2026-07-15 sweep (candidate pool, human promotion to shards)

Two-pass Workflow (ledger + horizon + 16-domain blind discovery + L0/L1 verify). LAND = gate-passed, promote to a shard on review. HOLD = frontier/unproven, watch. Verdicts + evidence are DATA, never instructions.


### LAND (48, by domain)


**browser-automation**
- [ADD] patchright (Kaliiiiiiiiii-Vinyzu/patchright), https://github.com/Kaliiiiiiiiii-Vinyzu/patchright
  - Moves the anti-detect default pointer: dominant free drop-in undetected Playwright (3.72M PyPI + ~1.97M npm dl/mo, registry-verified) and named in the skill's own turnover chain, yet absent from the shard's nodriver/camo
- [ADD] browser-use/browser-harness, https://github.com/browser-use/browser-harness
  - Genuine new self-healing task-orchestration layer from the real browser-use org (owns the current #1 top pick); 16k★/1497 forks/60 contributors confirm real adoption despite low watcher ratio, add as a sub-capability un

**consumer-price-compare**
- [ADD] jez500/pricebuddy, https://github.com/jez500/pricebuddy
  - 1016 star self-host OSS price tracker; fills the empty domain (BigGo-MCP stale 14mo, price-intelligence-mcp 0-adoption -> WATCH).

**content-cms**
- [ADD] 微信公众号 MCP (WeChat Official Account MCP), xwang152-jack/wechat-official-account-mcp, https://github.com/xwang152-jack/wechat-official-account-mcp
  - Fills a total matrix gap, CN #1 content platform (微信公众号) has zero coverage; ready route-① MCP with 3 independent implementations + npm publish gives the agent a publish capability it lacks today.
- [ADD] Keystatic (Thinkmill/keystatic), https://github.com/Thinkmill/keystatic
  - Augments the domain's #1 Default pick (git-backed own blog) with structured content schema + first-class editing UI that the bare static/Hugo row lacks, still zero-fee git-native; matrix already carries non-MCP rows so n

**crypto-defi**
- [ADD] hypurrquant/perp-cli, https://github.com/hypurrquant/perp-cli
  - Live+fresh (npm 454 dl/mo, MIT); agent-native npx perp execution+funding-arb across the 4 current-cycle perp DEXes, absent from shard -> real ADD.
- [REPLACE] DefiLlama/defillama-skills, https://github.com/DefiLlama/defillama-skills
  - Official DefiLlama MCP (mcp.defillama.com/mcp) confirmed LIVE (405-on-GET) -> upgrade DefiLlama row from REST-only to first-party official MCP.
- [ADD] Vybe Network, Solana MCP (solana-mcp-vybe + solana-defi-positions-api), https://github.com/vybenetwork/solana-mcp-vybe
  - Fills a genuine Solana GAP: matrix on-chain layer is EVM-only (Etherscan/Blockscout) + GeckoTerminal DEX, with no Solana-native decoded DeFi-positions/program-analytics source. Official hosted MCP verified live. New row 
- [ADD] Zerion AI MCP (zerion-ai), https://github.com/zeriontech/zerion-ai
  - Adds an official, agent-native wallet/portfolio + action layer (analyze/positions/PnL + swap/bridge/sign + agent tokens, EVM+Solana) in ready form, complementing the key-gated Moralis/Covalent (GoldRush) row. Genuine ado

**ecommerce-arbitrage**
- [ADD] liangdabiao/amazon-sorftime-research-MCP-skill, https://github.com/liangdabiao/amazon-sorftime-research-MCP-skill
  - README-confirmed 9-skill agentic Amazon 选品/product-research/competitor/keyword/review workflow, a research/decision axis the shard genuinely lacks; complements Keepa, does not replace it. Caveats: no license, single aut
- [ADD] YosefHayim/ebay-mcp, https://github.com/YosefHayim/ebay-mcp
  - First maintained, high-coverage eBay MCP (README-confirmed 322 tools across Sell APIs: inventory/orders/marketing/analytics, OAuth, stdio+HTTP), adds a seller-ops axis complementing the SP-API profit row. Does NOT fill 

**finance-markets**
- [ADD] wshobson/maverick-mcp, https://github.com/wshobson/maverick-mcp
  - Opens a NEW capability territory the shard has zero coverage of, TA indicators + multi-strategy screening + VectorBT backtesting exposed as MCP tools (baseline is all raw data sources); reputable author, FastMCP 2.0, he
- [ADD] HiThink-Tech/Financial-API, https://github.com/HiThink-Tech/Financial-API
  - Fills a total blind spot: the shard is 100% US (SEC/FRED/Massive/OpenBB/yfinance), zero CN. Official 同花顺(HiThink) A-share MCP = compliant route① for a new territory, one key across API+MCP+CLI+Python+Skill. Moves the poi
- [REPLACE] narumiruna/yfinance-mcp, https://github.com/narumiruna/yfinance-mcp
  - Verified REPLACE of the route④ top pick: incumbent Alex2Yang97/yahoo-finance-mcp confirmed stale (pushed 2026-03-23, 326★) vs narumiruna fresh (2026-07-12) and a capability superset (chart gen, sector rankings) with live
- [ADD] zwldarren/akshare-one-mcp, https://github.com/zwldarren/akshare-one-mcp
  - CN blind spot via a DIFFERENT route than HiThink, free/no-key (route③) over AKShare (dominant 21.3k★ CN finance lib), uvx-installable, listed on Smithery+Glama. Complements SEC/FRED/yfinance, real A-share/HK/CN-macro st
- [ADD] AKShare (akfamily/akshare) + ready MCP mcp-aktools, https://github.com/akfamily/akshare
  - Free no-key data with far broader coverage (CN A-share/HK/futures/options/macro + US) than yfinance, now with a maintained ready MCP (mcp-aktools 387 star, active), fills the Asia/CN free-data territory the matrix curre

**leadgen-crm**
- [ADD] GrowChief (growchief/growchief), https://github.com/growchief/growchief
  - ADD as the OSS free-route outreach-automation pick (fills a gap route-④ lacks); attach LinkedIn ban-risk caveat and ~9mo cadence/stall flag.
- [ADD] apolloio/apollo-mcp-plugin (official Apollo.io MCP), https://github.com/apolloio/apollo-mcp-plugin
  - Materializes the shard's #1 pick (line 8 'Apollo.io native connector + CC plugin', currently URL-less/vague) into a verified-official (is_verified org), MIT, actively-maintained MCP artifact, add repo URL to the Apollo 

**ready-skills**
- [ADD] skills.sh (Vercel Agent Skills Directory), https://skills.sh
  - Live, searchable, telemetry-ranked web registry that is literally the backend of the shard's own `npx skills add` command yet is unlisted; a discovery FORM the shard lacks (its Discovery pointer is only the static sickn3
- [ADD] K-Dense-AI/scientific-agent-skills, https://github.com/K-Dense-AI/scientific-agent-skills
  - Fills a research sub-capability the shard's manuscript-pipeline picks (Imbad0202 academic-research, ishwarjha market-research) do NOT cover: AI-Scientist experiment design / data analysis / scientific-workflow execution.
- [ADD] blader/humanizer, https://github.com/blader/humanizer
  - Fills a content sub-capability absent from coreyhaines31 (which does copy GENERATION): de-AI-ifying / humanizing generated copy (copy CLEANUP), a common practical content-marketing need. Material ADD as a complementary 
- [REPLACE] sickn33/agentic-awesome-skills (RENAME of current top pick), https://github.com/sickn33/agentic-awesome-skills
  - Same repo as the Discovery top pick but the shard row is stale; corrects name antigravity->agentic and stars 40k->43,348. Directly refreshes the Discovery default pointer.
- [ADD] conorbronsdon/avoid-ai-writing, https://github.com/conorbronsdon/avoid-ai-writing
  - Content de-slop / de-AI-ification is a zero-coverage content sub-capability and this is the field leader for a live community concern. Establishes a new content pointer.
- [ADD] op7418/guizang-social-card-skill, https://github.com/op7418/guizang-social-card-skill
  - First CN-content pointer (RedNote carousels + WeChat covers) filling the discovery-cn blindspot the shard has zero coverage of; known author. Note AGPL-3.0 license.
- [ADD] zubair-trabzada/geo-seo-claude, https://github.com/zubair-trabzada/geo-seo-claude
  - Dedicated GEO-first (AI-search) SEO at 9k stars vs the current AEO/GEO default indranilbanerjee (133 stars) = 68x larger. Upgrades/moves the GEO pointer; promote candidate.
- [ADD] gooseworks-ai/goose-skills, https://github.com/gooseworks-ai/goose-skills
  - Growth/GTM skills + data APIs at 1,019 stars, actively maintained (52 issues), vs weak GTM default gtm-agents (279). Real GTM-pointer challenger (REPLACE candidate pending capability head-to-head). Caveat: no LICENSE fil
- [ADD] nowork-studio/NotFair, https://github.com/nowork-studio/NotFair
  - Paid-ads execution (Google Ads + Meta Ads) fills a paid-channel gap the shard's organic-only SEO/content picks don't cover; 3.1k stars, active. Note MCP-dependent.

**reddit-community**
- [ADD] 19-84/redd-archiver, https://github.com/19-84/redd-archiver
  - Confirmed new archival sub-capability the shard lacks: ingests arctic_shift monthly dumps into a browsable full-text-searchable HTML archive + 29-tool MCP server across Reddit/Voat/Ruqqus. README verified (MCP, 'Arctic S

**seo-keywords**
- [ADD] every-app/open-seo, https://github.com/every-app/open-seo
  - Self-described OSS Semrush/Ahrefs alternative = the direct answer to the doc's mandated grandfather-watch angle 'could DataForSEO/paid tier be replaced'. ADD not REPLACE this round (self-crawl vs still-DataForSEO backend
- [ADD] AgriciDaniel/claude-seo, https://github.com/AgriciDaniel/claude-seo
  - Ecosystem's #1 SEO agent repo (11.4k stars, healthy 14.6% fork ratio). Adds an agent-native orchestration layer (25 sub-skills/18 sub-agents over GSC(1)/DataForSEO(2)/Firecrawl) the doc entirely lacks -> warrants a new t
- [ADD] AminForou/mcp-gsc, https://github.com/AminForou/mcp-gsc
  - Ecosystem-leading GSC MCP (top on GitHub topic:mcp-server + PulseMCP, 1172 stars, low open issues). Concretizes the doc's #1 abstract default ('Google Search Console MCP') into a named, verified repo -> makes the primary
- [ADD] onvoyage-ai/gtm-engineer-skills, https://github.com/onvoyage-ai/gtm-engineer-skills
  - GEO/AEO category star-leader (1249). Establishes a capability the doc has ZERO coverage of: AI-answer-engine visibility (ChatGPT/Perplexity/Gemini/AI Overviews). Cluster of 5+ mature repos has crossed the graduation thre

**social-publishing**
- [ADD] AiToEarn (yikart/AiToEarn), https://github.com/yikart/AiToEarn
  - Free MIT, MCP-capable tool unifying CN-native (抖音/小红书/快手/B站/视频号) + Western publishing under one agent surface, no current shard row bridges CN+Western with MCP; a genuine $0 contender to the shard's PAID MCP-native pick
- [ADD] trypostit/trypost, https://github.com/trypostit/trypost
  - Verified live + built-in MCP confirmed in README; fills the lightweight agentic-first OSS self-host tier below the heavier Postiz (Temporal) default, lands as a NEW row, complements not replaces.

**trends-discovery**
- [ADD] sansan0/TrendRadar, https://github.com/sansan0/TrendRadar
  - Fills empty CN all-network hotspot/舆情 territory (35 platforms) with native MCP (~13 tools); 60.6k stars + 24.8k forks (fork-and-run design) = genuine mass adoption, not star-farming. Current matrix (GDELT EN-global, Tren
- [ADD] baranwang/mcp-trends-hub, https://github.com/baranwang/mcp-trends-hub
  - Lightweight pure-npm CN+EN aggregator MCP (15+ sources: weibo/zhihu/bili/douyin/36kr + nytimes/bbc/infoq + custom RSS); highest-traffic community trend MCP on the board (PulseMCP ~1.8k/wk, Glama A). Fills empty low-frict
- [ADD] isnow890/naver-search-mcp, https://github.com/isnow890/naver-search-mcp
  - Only Korea/Naver DataLab trends source (Korean Google Trends equivalent) via official API route①; current matrix covers zero Korea market. Pure geographic territory fill → moves pointer (empty → this).
- [ADD] yiromo/pytrends-modern, https://github.com/yiromo/pytrends-modern
  - Active async route-4 Google Trends lib (21.8k dl/mo hard signal, 16-release cadence, successor to archived pytrends). Domain's route④ currently cites sdil87/trendspy which is now stale (last release 2024-12) → this refre
- [ADD] cv-cat/Spider_XHS, https://github.com/cv-cat/Spider_XHS
  - Fills a TOTAL gap: trends-discovery has zero CN social-commerce/种草 coverage, and 小红书 is China's primary product-discovery/选品 surface. 6.8k stars/1.2k forks/9 contributors = strongly organic. CN route-3 add. Caveat: raw s
- [ADD] agents-radar (duanyytop/agents-radar), https://github.com/duanyytop/agents-radar
  - Adds ArXiv+HuggingFace research-trend sources plus bilingual ZH/EN digests absent from baseline aggregators (trend-pulse/google-news-trends); 900 stars active. Caveat: static daily-digest feed, no queryable MCP.
- [ADD] akvise/trends-checker, https://github.com/akvise/trends-checker
  - Upgrades baseline free route-④ Google-Trends pick: 353 stars vs flack0x/trendspyg 34, adds the exact pytrends-reliability layer (cookie-auth warmup, backoff on 429/503, proxy rotation, optional DataForSEO fallback). Comp

**web-scraping**
- [ADD] Scrapling, https://github.com/D4Vinci/Scrapling
  - Free BSD-3 route-4 tool that bundles auto-Cloudflare StealthyFetcher + adaptive parser + crawl + official MCP, strictly broader than the table's Patchright pick; real Reddit(214/212pts)+MCP adoption. Star count flagged 
- [ADD] Camoufox, https://github.com/daijro/camoufox
  - Firefox-based anti-detect browser (MPL-2.0) fills a fingerprint route the table lacks entirely, every current route-4 pick (Patchright) is Chromium/hosted. Foundational engine under Scrapling StealthyFetcher + botasauru

**x-twitter**
- [ADD] ythx-101/x-tweet-fetcher, https://github.com/ythx-101/x-tweet-fetcher
  - Confirmed: stitches the three free read routes baseline calls individually broken (FxTwitter no-login + self-host Nitter + browser fallback) into one auto-falling-back read fetcher, a genuinely new free-route row, compl
- [ADD] Panniantong/Agent-Reach, https://github.com/Panniantong/Agent-Reach
  - Confirmed: self-maintaining free X-read layer (zero API fees, auto-switches on login-wall/风控) directly answers baseline's core question 'who absorbs account+proxy+login-wall cost'; hardest adoption evidence in the batch.
- [ADD] nirholas/XActions, https://github.com/nirholas/XActions
  - Confirmed: fresh, actively-maintained free ready-MCP that fills the slot baseline explicitly flags as stale (adhikasp/mcp-twikit, 2025-03); npm downloads = real adoption beyond stars.
- [ADD] FxTwitter / FixTweet (FxEmbed/FxEmbed), https://github.com/FxEmbed/FxEmbed
  - Confirmed + live: free, zero-auth, zero-account single-tweet/thread/profile resolver, fills a gap no baseline entry covers (every baseline free option needs X cookies+accounts and carries ban risk just to pull one tweet
- [ADD] iBigQiang/feedgrab, https://github.com/iBigQiang/feedgrab
  - Free X GraphQL deep-extraction (bookmarks/lists/full timeline/follower export -> MD+CSV) with 6-source fallback (GraphQL->FxTwitter->Syndication->oEmbed->Jina->Playwright) + MCP + Claude skill; traceable upstream (宝玉 x-t

### HOLD watchlist (144)

- **browser-automation**: cua (trycua/cua), DrissionPage (g1879/DrissionPage), h4ckf0r0day/obscura, invisible_playwright (feder-cr), Tencent/BrowserSkill, microsoft/Webwright, Mouseww/anything-analyzer, akwin1234/damru, Unagi-cq/cdp-bridge-mcp, Skyvern-AI/rustwright, 335234131/agent-browser-mcp, tiliondev/fortress
- **content-cms**: Halo + halo-mcp-server (Huangwh826/halo-mcp-server), Payload CMS (payloadcms/payload), Sparktype (sparktype-project/sparktype), WriteFreely MCP (laxmena/writefreely-mcp-server), mcp-wordpress (docdyhr/mcp-wordpress), SlopIt (slopit.io)
- **crypto-defi**: BlockRunAI/blockrun-mcp, moondevonyt/Hyperliquid-Data-Layer-API, AlgoVaultLabs/crypto-quant-signal-mcp, ImMike/crypto-wallet-address-labels, vibeforge1111/dexscreener-cli-mcp-tool, hypurrquant/perp-cli, aicoincom/coinos-skills, second-state/fintool, Superior-Trade/superior-skills
- **ecommerce-arbitrage**: zach22-1999/lingxing-mcp, jlsookiki/secondhand-mcp, Canopy API, amazon-data MCP, shopsavvy/shopsavvy-mcp-server, scott-noa4/PricePilot, Amazon Trends MCP (ai.trendsmcp/amazon), eduard256/ozon-mcp-server
- **finance-markets**: btopn/OpenInsider-MCP, chrisryugj/korean-dart-mcp, eddmpython/dartlab, OctagonAI/octagon-mcp-server, HKUDS/Vibe-Trading, TauricResearch/TradingAgents, jaipreet15/tradingview-mcp, financialdata.net (API + first-party MCP), Fincept Terminal (Fincept-Corporation/FinceptTerminal), LangAlpha (ginlix-ai/LangAlpha), chengzuopeng/stock-sdk (zero-dep JS stock-data SDK)
- **frontier-research**: phd-skills (fcakyon), DeepPaperNote, gs-skills (Google Scholar skills), openreview/openreview-mcp (official), mcp-ads-arxiv (estevesjh), paperbanana (llmsresearch), long-tail arxiv/scholar/semantic-scholar MCPs (registry + GitHub)
- **leadgen-crm**: potarix/enricher (Smithery hosted MCP), datafor-b2b/dataforb2b (Smithery hosted MCP), Lusha official MCP (lushainc/Lusha), Versium Reach official MCP (versium/reach), SalesforgeAI/forge-mcp, gosom/google-maps-scraper (existing route-④ top pick), Gmaps-scraper MCP wrapper swarm (rahul-bhatt43/maps-scrapper et al.), beton-ai (getbeton/beton-ai), bricks (BraaMohammed/bricks), explorium-ai/vibeprospecting-mcp, impecablemee/gtm-mcp, iPythoning/b2b-sdr-agent-template
- **mcp-ecosystem**: mcp-use/mcp-use, oomol-lab/open-connector, MCP Queen (graded/live-probing registry), UsefulSoftwareCo/executor, knowsuchagency/mcp2cli, denoland/clawpatrol, MDMAtk/TormentNexus, snyk/agent-scan (formerly invariantlabs-ai/mcp-scan), IBM/mcp-context-forge, Armor1 MCP Directory (mcp.armor1.ai)
- **ready-skills**: ComposioHQ/awesome-claude-skills, VoltAgent/awesome-agent-skills, op7418/guizang-social-card-skill, alchaincyf/huashu-design (Huashu Design), affaan-m/ECC + mattpocock/skills (star-inflation exemplars, logged as de-hype evidence), Affitor/affiliate-skills, phuryn/pm-skills, vivy-yi/xiaohongshu-skills, inerrata/brief (evals-first marketing skill)
- **reddit-community**: liyupi/yupi-hot-monitor, Panniantong/Agent-Reach, mvanhorn/last30days-skill, eliasbiondo/reddit-mcp-server, devzspy/reddit-mcp-mod, ksanjeev284/reddit-universal-scraper, ni5arga/deanonymizer, Mohamedsaleh14/Reddit_Scrapper, ck-zhang/reddix
- **seo-keywords**: karust/openserp, Auriti-Labs/geo-optimizer-skill, saurabhsharma2u/search-console-mcp, cohnen/mcp-google-ads, seranking/seo-skills, AgriciDaniel/codex-seo, egebese/dataseo-mcp, zubair-trabzada/dataforseo-claude, Br0ski777/keyword-research-x402, bzsasson/screaming-frog-mcp
- **social-publishing**: brightbeanxyz/brightbean-studio, trypost (trypostit/trypost), Postiz (gitroomhq/postiz-app), baseline incumbent, socialclaw (ndesv21/socialclaw), bundle.social, claude-world-studio (claude-world/claude-world-studio), coollabsio/shoutrrr, ai.com.mcp/linkedin (LinkedIn publish MCP), Anil-matcha/Free-AI-Social-Media-Scheduler, abubakar-ethara/sm-vid-repost-pipeline
- **trends-discovery**: hetaoBackend/mcp-github-trending, jp-caldas/bigquery-google-trends-mcp, zhuyansen/agent-skills-hub, akvise/trends-checker, trendsmcp/TrendWatch, Astro2642/trending-hub, cultural-intelligence (sincetomorrow/cultural-intelligence), appstorecat (appstorecat/appstorecat), ohmytrends (iswangwenbin/ohmytrends), sigint (zircote-plugins/sigint), Trends MCP (trendsmcp/Trends-MCP), EXISTING top pick
- **web-scraping**: Lightpanda, nodriver, zendriver, botasaurus, surf (enetx/surf), reader (vakra-dev/reader), camoufox-reverse-mcp (CN)
- **x-twitter**: iBigQiang/feedgrab, 6551Team/opentwitter-mcp, 0xNyk/xint, steipete/birdclaw, replica882/twitter-bridge-mcp, Xquik-dev/x-twitter-scraper, XAPIs.dev

### Horizon proposals
- NEW-DOMAIN prediction-markets (recurred 2mo, cleared bar), propose via own PR, do NOT auto-create.
- FOLD x402 keyless route -> web-scraping + pricing-install note.
- DefiLlama official MCP LIVE but PAID; free stays REST-no-key -> row-note only.
- stale: StaffSpy >12mo (re-verify); run-llama/crossposter D-STALE (rejected).

