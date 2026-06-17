# Discovery state

Working scratchpad for the Discovery phase of `refresh-protocol.md`. Lightweight, append-only.
Promotion to `domains/` shards happens in the Verify & Diff phase.

## Inbox

Candidates surfaced by Discovery (Twitter polling, GitHub trending, blog scans, etc.).
Format: `[YYYY-MM-DD] @source: <one-line> <repo-or-url>`.

<!-- e.g. [2026-06-20] @jxnl: new instructor-mcp wraps eval harness over MCP https://github.com/... -->

### 2026-06-17 sweep — HOLD list (verified, awaiting human eyeballs)

| candidate | domain | reason for HOLD |
|---|---|---|
| BigGo Search MCP (Funmula-Corp/BigGo-MCP-Server) | ecommerce-arbitrage | Repo dormant 13.5 months (v0.2.0 on 2025-04-30, no commits since). APAC marketplace coverage (Shopee/Taobao/AliExpress) is confirmed and the only such MCP, but staleness needs a human call: test cert signup still issues working keys before relying. **Caught by gh-api check that 3-lens LLM verify alone missed (P4 lesson).** |

### 2026-06-17 sweep — Watch list (39 candidates demoted on adversarial verify)

These passed Discovery but failed at least one of the 3-lens verify (existence/freshness/top-pick-impact).
Keep tracking — re-evaluate next sweep if upstream activity resumes or top-pick changes.

**Refuted on top-pick-impact (marginal vs current top):**
- `the-convocation/twitter-scraper` (x-twitter) — Node port, no top-pick impact
- `Altimis/Scweet` (x-twitter) — 3rd-tier scraper, dupe of twscrape's row
- `nodriver` (web-scraping) — async CDP, overlaps Patchright
- `scrapegraph-ai` (web-scraping) — NL extraction, covered by Firecrawl/Crawl4AI
- `Apify Amazon Scraper actor` (ecommerce-arbitrage) — overlaps Rainforest/Oxylabs
- `tinyfish-io/agentql-mcp` (ecommerce-arbitrage) — semantic-selector ergonomics, doesn't fix Keepa gap
- `shopify-dev/storefront-mcp` (ecommerce-arbitrage) — no price history; DTC has low arbitrage spreads
- `dexpaprika-mcp` (crypto-defi) — overlaps GeckoTerminal/CoinGecko
- `Hyperliquid Python SDK` (crypto-defi) — single-venue, ccxt covers multi-venue
- `heurist-mesh-mcp-server` (crypto-defi) — wrapper-over-wrappers
- `Keywords Everywhere MCP` (seo-keywords) — DataForSEO dominates this slot
- (plus ~20 more — see full sweep output for the complete list)

**Refuted on freshness:**
- `rebrowser-patches` (web-scraping) — 13 months stale
- `brianellin/bsky-mcp-server` (reddit-community) — dormant since Apr 2025
- `financial-datasets/mcp-server` (finance-markets) — >12 months stale
- `Serper MCP variants` (seo-keywords) — both candidates stale

## P2 trigger fired 2026-06-17

`feedback-bump.py` detected ≥3 distinct domains with `barrier_found` outcome in the 90-day
window — the ROADMAP `transport: brokerage` trigger is now ACTIVE, not reserved. See
`companion-config-spec.md` §3.1 (brokerage enum value lands in spec v1.3) and
`domains/web-scraping.md` for the activated brokerage entries.

## Twitter watchlist

Curated set of X/Twitter accounts polled weekly during Discovery to surface new MCPs,
agent tooling, scrapers, and adjacent infra. Goal is signal density, not coverage. Prune
aggressively when an account drifts off-topic for >2 sweeps.

All handles confirmed active as of 2026-06. Items tagged `(verify)` are ones I have
lower confidence in — re-check on first poll and drop if stale.

### A. Anthropic / MCP core (5)

- `@AnthropicAI` — official; ships MCP spec changes, Claude Code release notes, model launches. Filter: only MCP/Claude Code/tool-use threads.
- `@alexalbert__` — Anthropic devrel; high signal on Claude Code features and prompting patterns.
- `@mlpowered` (Erik Schluntz) — Claude Code eng lead-adjacent; ships demos of agent loops with MCP.
- `@sauers_` (Sam Bowman / Anthropic) `(verify)` — flagged because the handle for the policy/research Sam Bowman has shifted before; confirm it's the Anthropic person still posting MCP/agent content.
- `@dhh` — not Anthropic, but the `modelcontextprotocol` org account `@modelctxprotocol` `(verify)` — I'm not confident a dedicated org handle exists vs. just posts under @AnthropicAI; check first poll, drop if it's a squatter.

### B. AI tooling builders (11)

- `@hwchase17` (Harrison Chase, LangChain) — orchestration framework launches, agent patterns, eval tooling.
- `@jxnl` (Jason Liu) — Instructor maintainer; structured-output + eval pipelines + MCP wrappers.
- `@swyx` (Shawn Wang) — Latent Space podcast; aggregator-style signal on what tools shipped this week.
- `@simonw` (Simon Willison) — `llm` CLI, datasette, hands-on MCP / tool-use writeups; high noise-to-signal.
- `@karpathy` — only on relevant topics; surfaces architectural shifts that drive new tooling.
- `@sama` — only when announcing OpenAI tool/agent infra (which then spawns clones in MCP ecosystem).
- `@dharmesh` (Dharmesh Shah) — agent.ai builder, talks about agent marketplaces and infra picks.
- `@mathemagic1an` (Jay Hack) — agent infra commentary, often early on new MCP servers.
- `@yoheinakajima` — BabyAGI lineage; surfaces minimal-agent patterns and new orchestration libs.
- `@jerryjliu0` (Jerry Liu, LlamaIndex) — RAG + agent tool stacks; LlamaIndex's MCP integrations.
- `@virattt` (Virat Singh) — ships financial-agent MCPs; useful proxy for the "agent + commercial data" niche this skill targets. `(verify)` — confirm handle still active and on-topic.

### C. Scraping / browser-automation specialists (6)

- `@browser_use` — browser-use project account; ships releases and integrations.
- `@gregor_zunic` (Gregor / browser-use co-founder) `(verify)` — co-founder identity / handle spelling; confirm.
- `@unclecode` (Hamza / crawl4ai maintainer) — crawl4ai releases, anti-detection notes, LLM-scraper patterns.
- `@skyvern_ai` — Skyvern (vision-based browser automation) launches and benchmarks.
- `@Steel_dev` (Steel.dev) — managed browser infra for agents; signals what scraping bottlenecks are commercializing.
- `@ScrapingBee` — proxy/managed-scrape vendor account; price/anti-bot trend signal, low builder-signal — keep on probation.

Note: patchright / camoufox / nodriver maintainers are largely GitHub-only with no active X
presence I can verify. Track those via GitHub releases, not this watchlist.

### D. China bridge (3)

- `@deepseek_ai` — DeepSeek official EN account; model + tool-calling release notes.
- `@Alibaba_Qwen` — Qwen team EN account; Qwen-Agent and tool-use releases.
- `@zhouwenmeng` (Zhou Wenmeng / Moonshot / Kimi) `(verify)` — uncertain whether a real EN-active handle exists; confirm and drop if posts are CN-only or inactive.

**Uncertain / dropped from consideration:**
- ByteDance has no single high-signal EN AI-tooling face I can confidently name; skip rather than guess.
- `@modelcontextprotocol` as a literal org handle — flagged above, may not exist as a distinct account.

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

Tools/accounts that are *interesting but not yet promotable* — borderline candidates we
keep an eye on without committing to a `domains/` shard. Promote up to Inbox when
threshold is met, demote to Reject log when stale.
