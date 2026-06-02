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
