# Changelog

## [0.29.0], 2026-07-22

Scheduled monthly refresh, July trigger month so this is a FULL 13-domain sweep + quarterly Horizon
scan. Step -1 ledger consumed first (`~/.market-intel-config/data/metrics/live-runs.jsonl`, 49
entries since last refresh); weekly E1-E6 surface inbox triaged (4 GitHub candidates gh-api
verified, rest low-signal HF/YouTube noise, ignored per protocol). 12 parallel Discovery subagents
(one per domain-group) + 1 Horizon-scan agent, each reading the 5 mandatory files before scanning.

AUDIT: independent-subagent-per-domain verdict=pass (each domain's ADD/REPLACE verdict was produced
by a blind-scanning subagent that read only its own domain's baseline + the 5 mandatory shared
files, gh-api-verified every star/date cited; this refresh's main agent then synthesized without
re-deriving numbers from memory, matching the editor!=verifier split P4 asks for).

### Step -1, live-run ledger triage (all resolved this sweep)
- `PA-API 5.0 retirement` (ecommerce-arbitrage, flagged `dead`): **false alarm, mixup between two
  different Amazon APIs.** PA-API (Associates/affiliate) is deprecating 2026-05-15 -> Creators API
  (10 sales/30d gate); the shard's SP-API row (sellers, private-app OAuth) is a different product
  entirely and unaffected. Verified both claims directly against `webservices.amazon.com` and
  `developer-docs.amazon` (L1). Added a disambiguation note to the SP-API row so this doesn't
  recur.
- `shard top OSS picks outranked` (ecommerce-arbitrage, `price_mismatch`): **confirmed real gap.**
  `jez500/pricebuddy` (1026 stars) already had a tool doc + index + registry row from a prior
  sweep's gate-debt fix, but never got a shard table row -> added as the new top OSS pick.
  `clucraft/PriceGhost` and `DAILtech/PriceDive` (the ledger's other two candidates) are actually
  stale (5.5mo and 9.5mo since push respectively, contradicting the ledger's "active"/"fresh"
  framing) -> correctly left out.
- `reddit-mcp-buddy` (`dead`): **confirmed still broken, not transient.** Live-tested across 6
  subreddits today, all forbidden. Root cause: Reddit is 403-blocking the anon JSON API since
  2026-06-03 (upstream issue karanb192/reddit-mcp-buddy#58), fix PR #60 open/unmerged 6+ weeks.
  Shard updated: anon tier flagged non-functional, `reddit-research-mcp` elevated to co-top-pick
  until the upstream fix lands.
- `tavily-mcp` (`dead`, 401s): **false alarm, key/quota issue not an outage.** Free tier caps at
  1,000 credits/mo; repo is active (2240 stars, pushed today), open PR adds multi-key failover
  specifically for this failure mode. Shard note added; not touched as a source.
- `duckduckgo-mcp` (`dead`, hangs): **was real, already fixed upstream.** DuckDuckGo tightened
  bot-detection against the library's TLS fingerprint (issue #46, matches ledger date exactly);
  patched in v0.5.0 (2026-07-01, a week after the ledger flag). Not a matrix entry (`ddgs`/SearXNG
  are the actual shard picks), no shard edit needed.
- `google-news-trends` (`dead`, tool absent in subagent): **confirmed a subagent-MCP-loading wiring
  issue**, not a dead tool (`jmanek/google-news-trends-mcp` itself is 89 stars, pushed 2026-07-15,
  healthy). Flagged as an infra bug for the harness, not a matrix change.

### Added (this sweep, four-file where a new tool warranted it)
- **crypto-defi**: Base MCP (`base/skills`, official Coinbase) was WATCH pending a wireable
  endpoint, now confirmed live at `mcp.base.org` with shipped skill plugins (Morpho/Moonwell/
  Aerodrome/Uniswap/Bankr/Avantis/Virtuals) -> promoted. Coinbase Agentic Wallet MCP
  (`@coinbase/payments-mcp`) added as a new execution/payment primitive (x402 pay-per-call).
- **ecommerce-arbitrage**: `jez500/pricebuddy` (1026 stars) added as the new OSS top pick, see
  Step -1 above.
- **browser-automation**: `Kaliiiiiiiiii-Vinyzu/patchright` (3.9k stars) added to the Anti-detection
  table, a real doc/shard gap (`reference/tools/patchright.md` existed but had no shard row).
- **trends-discovery**: `appreply-co/mcp-appstore` (62 stars) added, a dual-store (Google Play + App
  Store) ASO MCP that consolidates the shard's existing split npm-lib pair.
- **content-cms**: `microcmsio/microcms-mcp-server` and `kontent-ai/mcp-server` added as minor
  JP-market/niche rows, resolving two "unverified" watchlist items (both confirmed real + actively
  maintained but thin adoption, 21 and 9 stars).
- **finance-markets**: community wrapper `erikmaday/unusual-whales-mcp` (73 stars) noted alongside
  the existing paid Unusual Whales MCP row (lowers integration friction, same underlying data).
- **social-publishing**: Ayrshare row updated to note its new official Claude Code plugin.

### Rejected / death-coded (do not re-discover)
- **`storyblok/mcp-server`**, D-404-equivalent: official repo confirmed **archived**, resolves the
  prior "Storyblok MCP unverified" watchlist item negatively. Moved to reject log.
- **`JesusRS1/stock-trade-finance-api`** (this week's E2 inbox candidate, 91->142 stars):
  **security red flag, hard reject.** Its newest commit added an unused npm dependency
  `ioredis-xyz` (a typosquat of `ioredis`, published by a throwaway-looking account, not imported
  anywhere in the source). Its 1,027 forks show a bot-pattern fork farm (repeating account names,
  ~3min creation cadence, zero pushes) -> the star growth this candidate was surfaced on is
  explained by the farm, not organic adoption. Logged to reject log with an explicit "do not
  re-surface even if stars keep climbing" note.
- `Cesarjoquin/Marketing-Skills` (ready-skills, 145 stars): star:fork ratio inverted and extreme
  (1233 forks vs 145 stars), same fork-farming signature as the existing
  `zubair-trabzada/ai-marketing-claude` reject.
- 4 low-signal x-twitter candidates (fluyeporlaweb/mcp-x-intelligence, farukkolip/xtapdown-mcp,
  veezeehq/veezee-mcp, poloniki/purefeed-mcp) and 3 off-domain/thin reddit-community candidates
  (19-84/redd-archiver, Kymo-MCP/mcpcan, Arindam200/reddit-mcp) rejected, see discovery-state.md.

### Discovery pool banked (`discovery-state.md`, full 13-domain sweep)
Watchlist refreshed with current gh-api star counts for every existing entry (largest movers:
`browser-act/skills` +107% in 7wk with a contributor-concentration flag; `AgriciDaniel/claude-blog`
+42% in a month, active, lean-ADD next cycle; `CloakHQ/CloakBrowser` +26%, closed-binary trust
concern persists) plus ~20 new candidates from this sweep's blind scans (`feder-cr/invisible_
playwright`, `germondai/trawl`, `nando0x/ProspectOS`, `zwldarren/akshare-one-mcp`, `TipRanks/mcp`,
and others), each with a verdict + reasoning. No REPLACE verdicts landed this sweep (no candidate
cleared the "beats the existing top pick's core capability" bar anywhere).

### Horizon scan (quarterly, July trigger month)
- **Prediction markets (Polymarket/Kalshi/Meta's new "Arena") now clears the NEW-DOMAIN bar** on
  its 2nd sighting: Kalshi in talks at a $40B valuation (8x growth in under a year, $17.9B monthly
  turnover), Polymarket at $15B, Meta directing a standalone competing app (NYT/Bloomberg/NPR,
  2026-06-23/24), and >=3 actively-maintained MCPs with commits inside the last 2 weeks
  (`caiovicentino/polymarket-mcp-server` 597 stars/45 tools, `OctagonAI/octagon-mcp-server` 143
  stars, `9crusher/mcp-server-kalshi`, `JamesANZ/prediction-market-mcp`). Doesn't fit any existing
  13 domains (not securities, not on-chain DeFi, not a trend feed). **Per C9/H3 this is a PROPOSAL
  ONLY** -> not landed as a new shard this run, surfaced here + in the PR description for human
  approval.
- 7 other new-angle watchlist items hit their 2nd sighting this cycle (X API re-tier now
  source-verified, agent-memory-as-capability strengthening, MCP deployment shape shift landing
  this week, x402 ecosystem exploding, agentic-commerce checkout channel had a material reversal
  -- OpenAI killed in-chat Instant Checkout) -- all FOLD, no other NEW-DOMAIN candidates.
- Placeholder-domain check: `regulatory-watch` still below threshold (EU AI Act *code*-compliance
  scanners found, but that's a different sub-niche than the placeholder's SEC/legislative-tracker
  scope). Other 5 placeholders not re-searched this cycle (budget), carried to next quarterly scan.

### Known gate limitation (flagged for human review, not fixed by this run)
`tools/verify_matrix.py`'s STAR check and its DELETE (C4) heuristic contradict each other for any
row whose star-count annotation lives inside the markdown table's identity cell (e.g. `**repo**
(4.3k star)`): correcting a stale star count changes that cell's text, which the DELETE heuristic
reads as "old row removed + new row added" and demands a death-code for a edit that deleted
nothing. `every-app/open-seo`'s star annotation is stale (4.3k shown, 6.8k actual per gh-api
2026-07-22, confirmed via `git stash` test that this BLOCK pre-exists on unmodified main) but is
left uncorrected this run since automation cannot edit `tools/` to fix the heuristic and
fabricating a death-code for a non-deletion would violate C1/C6. Left every other star-count fix
this sweep as a trailing parenthetical note in the row's note column (not the identity cell)
specifically to avoid tripping this same false positive; recommend the gate maintainer split the
STAR-annotation regex out of the DELETE row-identity key.

### Cleanup (mandatory per-sweep)
- `tools/dash_guard.py --fix` applied: 22 prose en/em dashes introduced by this sweep's own edits,
  corrected before landing (repo convention: no en/em dashes in prose).
- `tools/check_doc_drift.py`: 3 FAIL, all root-level README version/domain-count badges, explicitly
  out of scope for automated runs per this sweep's hard rules (human step at PR-merge).
- `python tools/pii_guard.py`: clean, no PII in any changed file.
- No CHANGELOG archive rollover needed (file still under the 6-month/24-month caps).
- No `live-runs.jsonl` compression (feedback ledger, kept in full per protocol).

### Verify gate
`python tools/verify_matrix.py --base main`: 200 source rows, 109 repos checked (100 PASS / 9 WARN
GHACTIVE), STRUCT/TOOLS/REGISTRY/REPO/FRESH/METH/COVER/PRICE all PASS. 1 pre-existing BLOCK
(`every-app/open-seo` STAR, see "Known gate limitation" above, confirmed present on unmodified
main via `git stash`, not introduced by this sweep). CONST: CONSTITUTION.md unmodified.

## [0.28.1], 2026-07-15

Surface poller tuning after the first live round.

### Fixed
- **E1 is live again.** The PulseMCP newsletter RSS is Cloudflare-walled to non-browser UAs, but
  PulseMCP exposes a keyless directory API (`v0beta/servers`) that works with a browser UA. E1 now
  pulls that, applies a traction filter (github stars OR package downloads), and dedups against the
  inbox so genuinely-new notable MCP servers surface over weeks. All 6 surfaces now green.

### Changed
- **E3 calibrated:** `min_trending_score` 0 -> 40 (round-1 distribution had a natural break ~40;
  keeps ~top 9, drops the low-signal tail). **E5 loosened:** `min_points` 30 -> 15, `min_comments`
  10 -> 5, so a weekly poll catches Show HN launches at 24-72h before they accumulate 30 points (the
  monthly sweep re-verifies, so over-including early is safe).

## [0.28.0], 2026-07-15

Stand up the weekly E1-E6 high-signal poller the refresh-protocol always specified but never had,
and wire the whole market-intel automation through schedule-reminder for unified local management.

### Added
- `tools/poll_surfaces.py`, deterministic, LLM-free weekly poller for the six auto-pollable
  high-signal surfaces (refresh-protocol.md E-tier): E1 PulseMCP RSS, E2 GitHub Search velocity
  (`gh api`), E3 HF Spaces trending, E4 npm download velocity (watchlist), E5 Show HN (Algolia),
  E6 AI early-demo YouTube RSS. Each surface is isolated (one down != whole poll down); candidates
  are deduped and appended to a PRIVATE inbox the monthly sweep consumes. First live run: 5/6
  surfaces green (E1 is Cloudflare-walled to non-browser UAs -> degrades gracefully), 27 candidates.
- `tools/surfaces.json`, public config (URLs / channel handles / thresholds only; no secrets).

### Changed
- **Data boundary:** the poller's output is a real-run record -> written to the private data home
  (`$MARKET_INTEL_DATA_DIR/surface-inbox.jsonl`, default `~/.market-intel-config/data/`), never into
  this public repo. The repo ships only the poller code + schema. Reads degrade; the inbox WRITE
  hard-fails (no repo fallback).
- **Automation (outside this repo, noted for provenance):** the monthly `RefreshMarketIntel` job was
  timing out at exactly 30 min (2026-07 run, exit 124) and then getting discarded for editing root
  README files (out of scope). Fixed: 30 -> 60 min timeout, the sweep now consumes the weekly inbox
  so discovery is lighter, an explicit "never touch root files" rule, egress moved from raw
  discord_relay to schedule-reminder's `relay.py` (infra stream), and both jobs now push a
  schedule-reminder heartbeat watchdog, the local replacement for the GitHub "heartbeat: no refresh"
  issue (#2). A new weekly Windows task drives the poller.

## [0.27.0], 2026-07-15

Refresh sweep (two full Workflow passes: ledger + horizon + blind multi-angle
discovery across 16 domains + L0/L1 verify) and a fix for the pre-existing
orphan-doc / registry debt the 2026-07-13 partial sweep left on main.

### Fixed (pre-existing gate debt from 2026-07-13)
- Wired 5 committed tool docs into `index.md` + `registry.json` (they had docs
  but no index/registry rows -> REGISTRY BLOCK on main): agent-reach (x-twitter),
  scrapling (web-scraping), pricebuddy (ecommerce-arbitrage), mcp-searxng
  (web-scraping), geo-optimizer-skill (seo-keywords). registry count 168 -> 173.
- STAR refresh: AgricIDaniel/claude-seo 8.5k -> 11.5k (gh-api 11497, pushed
  2026-07-06) in the ready-skills shard + tool doc (>25% drift cleared).
AUDIT: workflow-L0L1 verdict=pass, gh-api existence/freshness + top-pick-impact
  lens (the two-pass Workflow) attested the promoted set.

### Promoted to shards (this refresh, four-file each: shard + doc + index + registry)
- **FxEmbed** (FxEmbed/FxEmbed, 4.8k★ MIT) -> x-twitter: free zero-auth single
  post/thread JSON resolver (②/③), fills the "read ONE post's content, no key"
  slot between twikit and paid twitterapi.io.
- **yikart/AiToEarn** (23.8k★ MIT) -> social-publishing: free OSS desktop
  multi-publish covering the CN majors (Douyin/XHS/Kuaishou/Shipinhao/Bili) that
  Buffer/Publora do not; Electron GUI handoff, not MCP (documented honestly).
- **every-app/open-seo** (4.3k★ MIT) -> seo-keywords: free OSS Semrush/Ahrefs
  alternative with native MCP; external-view pick vs paid DataForSEO/Ahrefs.
- (Camoufox + patchright were already promoted on this branch in the main sweep.)
- registry count 173 -> 176 (repo 101 -> 104). verify_matrix: PASS.

### Rejected / death-coded (do not re-discover)
- run-llama/crossposter, D-STALE (last push 2025-06-02, 13.4mo > 12mo gate);
  superseded by Postiz/AiToEarn on every axis. Not added.
- cullenwatson/StaffSpy (leadgen-crm, existing entry), D-STALE re-verify flag
  (~12mo, last push 2025-06-17); kept pending a maintained-check, watch next sweep.

### Discovery pool banked (`discovery-state.md` `## 2026-07-15 sweep`)
- 48 LAND candidates (union of the two passes) + HOLD watchlist + horizon
  proposals recorded for human promotion to shards. Still-banked high-signal
  (not yet promoted): perp-cli (32★, thin), Vybe Solana MCP, yfinance-mcp,
  GrowChief (AGPL, ~9mo since push), TrendRadar (60k★, CN hot-list aggregator).

### Horizon
- NEW-DOMAIN proposal: **prediction-markets** (Polymarket/Kalshi implied-prob):
  recurred two months, cleared its own promotion bar; PROPOSAL only (H2/H3 human
  gate), not auto-created.
- FOLD: **x402** keyless pay-per-call route -> a web-scraping + pricing-install
  note (pending).
- **DefiLlama** official MCP (mcp.defillama.com/mcp) is LIVE but PAID-subscription;
  free access stays REST-no-key -> a row-note only, NOT a free REPLACE.


## [0.26.0], 2026-06-17

First `claude -p` integrations + the doctrine that draws the line. Up to now
every script in this repo has been 100% deterministic (gh-api, HTTP, regex,
file IO). This release adds LLM helpers in two places where they save real
human time, and explicit rules about where they CAN'T go.

### NEW machinery, Side B (draft helpers, never gates)

- **`tools/changelog_draft.py`** (~340 LOC, stdlib + subprocess): drafts a
  CHANGELOG entry by piping `git log` + `git diff --stat` + previous CHANGELOG
  entry (for house-style) to `claude -p`. **Output is a draft to stdout/file
, never auto-writes to CHANGELOG.md.** Footer reminds user to review per
  PHILOSOPHY P4. CLI: `python tools/changelog_draft.py --since v<prev>` or
  `--since HEAD~N`.
- **`tools/incident_helper.py`** (~370 LOC, stdlib + subprocess):
  semi-automatically fills the 6-step `runbooks/fix-broken-tool.md` runbook.
  Accepts NL description OR structured flags, extracts via `claude -p`,
  produces all 6 artifacts (live-runs JSON / D-code / shard FROM-TO / commit
  message). `--apply` opt-in per step; default is dry-print only.

### NEW doctrine

- **`runbooks/agent-in-scripts.md`** (~180 lines): defines the three sides:
  - **Side A, fail-closed gates (LLM FORBIDDEN)**: `verify_matrix.py`,
    `l0_verify.py`, `check_doc_drift.py` fail-level checks, `check_p5_drift.py`,
    `sync-check.py` 7 buckets, `sidecar_from_changelog.py` primary slug match.
    P4 violation to add LLM here, model talks past the gate.
  - **Side B, draft & helper scripts (LLM ALLOWED)**: this release's two new
    scripts plus future drafts. Output is reviewed by human before any effect.
  - **Side C, soft warn-level alerts (LLM TOLERATED)**: PHILOSOPHY-amendment
    stale alerts, ambiguous outcome classification, README narrative-vs-reality
    fork. Never blocks; human decides.
- Three questions to ask before adding LLM to any script:
  1. Does it block anything? (yes → no)
  2. Is output applied directly or reviewed first? (direct → no)
  3. Could hallucination cause silent matrix degradation? (yes → no)

### release.md

Added "Tip" pointing at `changelog_draft.py` for first-time CHANGELOG drafting.
`release.ps1` itself stays deterministic, no LLM call inside the gate
sequence per Side A doctrine.

### Invocation pattern (canonical)

For Python scripts:

```python
result = subprocess.run(
    ["claude", "-p", "--output-format", "text"],
    input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=120,
)
```

Piping the prompt via stdin avoids Windows CMD's 8191-char arg limit. Confirmed
working on prompts up to ~5KB in both helpers.

### What this prevents

Without the doctrine, the slippery slope is "let's have verify_matrix use
claude -p to be smarter about ambiguous repos" → LLM hallucinates a stale
URL "looks fine" → matrix silently degrades, gate has been talked past. The
doctrine makes that conversation short: verify_matrix is Side A, the answer
is no.

### Files touched

- `tools/changelog_draft.py` (NEW)
- `tools/incident_helper.py` (NEW)
- `runbooks/agent-in-scripts.md` (NEW)
- `runbooks/release.md` (+changelog_draft tip)
- `CHANGELOG.md`, `.claude-plugin/plugin.json` (this entry + version bump)

### Docs

- docs: unify repo structure (Skill Repo Spec v1), philosophy-first README section
  order, standardized top-block badges (type → license → feature → languages → roadmap),
  bilingual 1:1 EN/CN sync, `Languages` section + anchor, and `ROADMAP.md` current-version
  marker. No functional version bump.

## [0.25.0], 2026-06-17

Doc-drift gate + entropy doctrine. Closes the silent failure mode where
v0.17 → v0.24 shipped without README badges or top-level narrative being
touched (README version badge was 8 versions stale before manual fix).

### NEW machinery

- **`tools/check_doc_drift.py`** (~370 LOC, stdlib): fail-closed gate on
  derived fields, warn-only on suspected stale narrative. Canonical sources:
  - `plugin.json` version ↔ README + README_CN version badges + CHANGELOG top
  - `len(domains/*.md)` excluding meta-domains (`mcp-ecosystem`) ↔ README
    + README_CN "Source Matrix-N domains" badges + section headings
  - `len(tools/*.md)` excluding `*.auto.md` ↔ (currently no narrative ref)
  - PHILOSOPHY amendment dates: warn if >12mo old
  - README "What it is" hash: warn if >6mo unchanged AND ≥3 CHANGELOG entries since
  - README_CN structural parity with EN (## heading count match)
  - Persistent cache: `metrics/doc-drift-cache.json` (sibling to gh-api-cache)
  - Modes: default (check + exit 0/1/2), `--fix` (auto-bump derived), `--json`

- **`runbooks/doc-sync.md`** (NEW, 105 lines): doctrinal companion. Defines
  canonical-vs-derived split, narrative-vs-machine split, per-release + per-
  refresh workflows, 5 entropy-control mechanisms (canonical source / drift
  gate / time-decay alerts / P3 monotonic / P5 hard limit).

### release.ps1 wiring

- **NEW step 5c**: runs `check_doc_drift.py`. Fail-level → auto-fix attempt
  → if still fail, abort release. Warn-level → log and continue.
- **Step 6**: `git add` now also stages `README.md` + `README_CN.md` (if
  --fix touched them) alongside CHANGELOG + plugin.json + sidecar.

### refresh-protocol.md cleanup pass extension

- New cleanup-pass item 8: top-level doc drift sweep. Machine-checkable via
  `check_doc_drift.py`. Narrative freshness via fork agent (if 12+ months
  untouched while CHANGELOG grew 5+ entries). ROADMAP demotion: 12-mo
  unprogressed Triggered work items → propose deferred status.

### Real drift caught + fixed by the new gate

First run of `check_doc_drift.py` surfaced: **README_CN missing the "Now what?
, installed it, what do I read first?" section** that was added to EN. Fixed
in this commit by translating the section over. (Found by the structural-
parity warn-level check, 12 ## headings in EN vs 11 in CN.)

### Entropy doctrine (the long-term play)

5 mechanisms together prevent unbounded entropy:
1. Single canonical source per fact (one location of truth)
2. Fail-closed drift gate (check_doc_drift.py at release time)
3. Time-decay alerts (monthly cleanup pass flags stale narrative)
4. PHILOSOPHY P3 monotonic evolution (guardrails accumulate)
5. PHILOSOPHY P5 hard limit (refresh-side infra stays out of user-query path)

### Files touched

- `tools/check_doc_drift.py` (NEW)
- `runbooks/doc-sync.md` (NEW)
- `tools/release.ps1` (+step 5c, stage list)
- `skills/market-intel/reference/refresh-protocol.md` (cleanup pass §8)
- `README_CN.md` (port "Now what?" section from EN)
- `CHANGELOG.md`, `.claude-plugin/plugin.json`

## [0.24.0], 2026-06-17

Auto-configure new tools after a sweep. Closes the manual gap where ADDed tools required
4-8 steps × N tools of human work on the config side.

### New machinery

- **`tools/sidecar_from_changelog.py`** (skill side): parses top CHANGELOG entry +
  resolves each ADD/REPLACE slug against `tools/<slug>.md` + emits
  `metrics/sweep-<version>.json` with structured fields (slug, domain, route, tier,
  transport_hint, repo_url, signup_url, env_vars, install_cmd, auto_configurable_hint,
  doc_path). Stdlib only.
- **`market-intel-config/scripts/config-bridge.py`** (config side): consumes the
  sidecar and configures each tool via uniform "try → pending" flow:
  1. Scaffold templates (always safe local writes)
  2. Register in `registry.json` with v1.3 SHOULD/MUST judgment fields populated
  3. Attempt configure: pip install / claude mcp add / apply.py + verify
  4. If env_vars non-empty OR install fails → append to `pending_registrations.md`
     with reason
  - Modes: `--sweep PATH [--dry-run] [--yes]` for batch, `--register SLUG` for
    interactive browser-assisted handoff, `--list-pending`, `--clear-pending`.
- **`release.ps1` step 5b** (NEW): auto-runs sidecar generation; includes the
  sidecar JSON in the release commit. Post-push prompt offers a config-bridge
  dry-run before the user runs the real config-bridge apply.

### PHILOSOPHY P5 amendment

P5 hard limit explicitly widens to allow **companion-repo** config-bridge to represent
user identity (open signup pages, capture keys), under 5 rules:
1. Runs in `market-intel-config` repo only, not skill repo
2. Every identity action gets explicit per-tool y/N consent in the running session
3. Public no-key tools (HN, GDELT, arXiv) MAY auto-configure (no identity risk)
4. No auto-accept of paid plans, those stay in pending with manual flag
5. All identity actions logged to `metrics/config-bridge.audit.jsonl`

The skill-repo grep check is unchanged: SKILL.md still must never import refresh-side
scripts. P5 amendment is one specific, audited carve-out.

### Smoke test (v0.20.0 replay)

`tools/sidecar_from_changelog.py --version 0.20.0` → wrote
`metrics/sweep-0.20.0.json` with **11 adds resolved + 4 replaces + 4 unresolved**
(unresolved are REPLACE-only entries with no tool doc, expected).

`config-bridge.py --sweep ../market-intel/metrics/sweep-0.20.0.json --dry-run` →
summary: 0 auto-configured (all ADDs in v0.20.0 had non-mechanical install_cmds,
"see github URL" placeholders), 1 needs_signup (Instantly.ai), 1 needs manual
`claude mcp add`, 9 flagged as "unrecognized install_cmd" → pending. **Correct
behavior**, v0.20.0 ADDs were research catalogs (mcp-ecosystem) + paid SaaS
(Instantly), not auto-installable MCPs. Honest pending log > silent false success.

### Files touched

- `PHILOSOPHY.md` (+P5 amendment §)
- `tools/sidecar_from_changelog.py` (NEW)
- `tools/release.ps1` (+step 5b sidecar gen + post-push config-bridge offer)
- `CHANGELOG.md`, `.claude-plugin/plugin.json` (this entry + version bump)
- `metrics/sweep-0.20.0.json` (NEW, test artifact)

### What this gives you next sweep

After a sweep lands (`release.ps1 -Version 0.24.x`):
1. Sidecar JSON auto-generated + committed
2. release.ps1 offers config-bridge dry-run before exit
3. You run `python scripts/config-bridge.py --sweep <path>` once for batch config
4. For each pending tool, run `--register <slug>` interactively when ready
5. `pending_registrations.md` is the canonical "what I still need to configure" list

Estimated savings on a 12-add sweep: ~30-60 manual mouse-clicks → 5-10 y/N prompts.

## [0.23.0], 2026-06-17

Project structure cleanup pass driven by 4-fork audit (structure / docs / scripts / process).
Mechanical mechanical hygiene + canonical-process scripts before the long-promised pivot to
real research-run usage.

### Cleanup

- **Caches no longer git-tracked**: `metrics/gh-api-cache.json` + `metrics/l0-cache.json`
  added to `.gitignore`, both `git rm --cached`. 7-day TTL caches in git history are useless
  byte accretion (scripts fork). Now generated locally; cleanup-workflows.ps1 sweeps them
  alongside workflow transcripts.
- **One-shot migration retired**: `scripts/backfill_v12.py` → `scripts/legacy/` in
  market-intel-config repo. Was the F3 v1.2-field backfill from 2026-06-16; never reachable
  from normal flow again.
- **Date-bound runbook archived**: `runbooks/expansion-2026-06.md` →
  `runbooks/archive/expansion-2026-06.md` in market-intel-config. Sweep-tracking document
  with no ongoing role.
- **Dead link fixed**: `metrics/r1-safety-replay-2026-06-17.md` was referenced from
  refresh-protocol §D5b and CHANGELOG v0.21.0 but never created (replay results were
  inline). Both refs updated to point at CHANGELOG inline.

### Doc consolidation (4 forks all flagged scattered facts)

- **D-codes**: 5 codes (D-404 / D-PRICE / D-STALE / D-TOS / D-SUPERSEDED) were paraphrased
  across `sources-index.md`, `runbooks/sync-with-skill.md`, `CONTRIBUTING.md`. Canonical is
  now `refresh-protocol.md` §C4 + companion-config `runbooks/sync-with-skill.md` §C
  (skill vs config side). Other places shrunk to "see canonical link."
- **GHACTIVE**: canonical = `tools/verify_matrix.py` module docstring; other references now
  just say "see canonical."

### New canonical-process scripts (process fork P-2 + P-3)

- **`tools/release.ps1`** (NEW, ~150 lines): 11-step release automation. `-Version X.Y.Z`
  + `-DryRun`. Validates clean tree → CHANGELOG header date → bumps plugin.json → runs
  `verify_matrix.py` → runs companion `sync-check.py` (bucket B-G must = 0) → commits +
  tags + pushes. Each step has explicit abort message + recovery hint. Closes the
  v0.17-v0.22 "release missed sync-check at least once" failure mode.
- **`runbooks/release.md`** (NEW, ~85 lines): human-readable companion to release.ps1 with
  per-step recovery commands + when-NOT-to-use.
- **`runbooks/fix-broken-tool.md`** (NEW, ~190 lines): 6-step incident runbook for a tool
  that died mid-research. Anchors live-runs.jsonl → D-code → shard edit → companion-config
  sync → commit with `incident:` prefix. Worked example included. Closes the "5 actions
  in 5 places, no checklist" gap.
- **`tools/check_p5_drift.py`** (NEW, ~50 lines): one-grep PHILOSOPHY P5 hard-limit check.
  Scans SKILL.md for any import/load/from/require of refresh-side scripts. Exit 0 = clean,
  1 = violation. Currently 0. To run during every cleanup pass per PHILOSOPHY §P5 hard
  limit (so it's mechanism, not intention).

### Reader-path fixes

- **README + README_CN both link CONTRIBUTING.md** (was missing, UX/docs fork).
- **README "First real query" section**: 4 concrete query examples after Quick Start.
  Closes UX fork's "no demo path after Quick Start" gap.
- **README_CN gets Quick Start mirror** (was English-only).
- **refresh-protocol "After the sweep, landing checklist"**: 7 mechanical steps so a
  maintainer doesn't have to reconstruct them from git log. Closes process fork's "no
  post-sweep landing procedure" gap.

### Net

- `.gitignore` + 2 file moves + 2 link fixes + 6 consolidations + 4 new canonical files.
- 4 forks flagged 18 items; landed 11 high-ROI items; deferred 7 (SKILL.md TL;DR restructure,
  feedback-bump.py rename, workflow_helpers.md relocation, CHANGELOG bulk archive,
  canonical-sweep workflow script, refresh-protocol编号总览, health-dashboard).
- The deferred items are correctly classified as "lower ROI than just using the system";
  see structure fork + real-run drought fork.

## [0.22.0], 2026-06-17

Defensive fixes + UX scaffolds + P5 hard limit. **Final code-side iteration before pivoting
to real research-run usage**, 4-fork meta-audit (UX + P5 seam drift + real-run drought +
adversarial edges) converged on "stop optimizing, use the system."

### Edge fixes (E1-E3)

- **E1, L0 github URL path sanitization** (`tools/l0_verify.py`): `_check_github` now
  strips `/blob/`, `/tree/`, `/issues/`, `?`-fragments, trailing `/`, `.git`, and accepts
  SSH form `git@github.com:owner/repo.git`. Discovery agents write these forms in real
  output; previously would have 404'd on first hit. Tested with `arctic_shift/blob/...`
  and `git@github.com:SaseQ/discord-mcp.git`, both correctly resolve.
- **E2, feedback-bump.py BOM tolerance**: confirmed already `utf-8-sig` in v0.19.0; no
  change needed.
- **E3, L0 web body content sniff**: 200 OK alone doesn't mean alive. New code reads
  first ~2KB and flags 7 distinctive dead-page substrings ("site is under maintenance",
  "domain parking", "buy this domain", etc.) → UNCERTAIN. Self-test 7/7 still passes.

### P5 hard limit (PHILOSOPHY.md)

seam-drift fork warned "PASS-but-fragile", refresh infrastructure (~2000 LOC) is 7x larger
than the SKILL.md seam (~270 LOC). To prevent silent drift toward "another deep-research
clone," PHILOSOPHY.md now codifies a hard limit:

1. `tools/*.py` and `scripts/*.py` only run during refresh (sweep), never on user query
2. User research queries SHOULD use `deep-research` / `research-lit`; direct fan-out only
   when a specific commercial MCP is connected
3. EVAL gate (future) refresh-only
4. shard-as-view compiler (future) markdown-render-only
5. Any new code on user-query path requires explicit PHILOSOPHY.md revision, "never
   quietly violated"

Plus a one-line grep check for the limit, runnable during every cleanup pass.

### UX scaffolds (UX1, UX2)

- **README Quick Start**, 3-MCP bootstrap pack (mcp-hn + gdelt + arxiv, all free no-key)
  for first-time users to trigger real research in 3 minutes without signups. Addresses
  UX fork's #1 finding: "首次响应卡在多步安装泥潭, 30 分钟 install 训练营."
- **CONTRIBUTING.md** (NEW), single-page guide covering the 3 contribution patterns
  (add tool / update tool / propose framework change), 4-file sync rule, verify_matrix
  gate doctrine, C4 death-code conventions, naming rule, and a "where to read first"
  ordered guide. Addresses UX fork's #2: "矩阵贡献者无入口."

SKILL.md TL;DR restructure deferred, bigger surgery, higher judgment cost, defer until
real-run data validates direction.

### Real-run drought, the meta-finding

`metrics/live-runs.jsonl` audit: 31 entries × 100% concentrated on 2 days, 0 entries from
real research runs (all are dev meta-observations during setup). Step -1 is empty rotation,
EVAL bet prerequisite (real outcome distribution) is unmet. The brokerage P2 trigger was
fired by setup-noise, not genuine user-facing D-PRICE events.

**Next step is NOT more optimization**, it's invoking `调研一下 <真实商业课题>` for an
actual research task and letting the skill write the FIRST real `live-runs.jsonl` entries.
Without this, EVAL gate / shard-as-view / cross-model verify are all designed for a feedback
loop that doesn't exist.

### Files touched

- `tools/l0_verify.py` (E1 + E3, self-test 7/7 preserved)
- `PHILOSOPHY.md` (P5 hard limit)
- `README.md` (Quick Start section)
- `CONTRIBUTING.md` (NEW)
- `CHANGELOG.md`, `.claude-plugin/plugin.json` (this entry + version bump)

### Net

- Defensive fixes against 3 high-probability edge cases (E1 esp., Discovery agents WILL
  write these forms)
- P5 anti-drift codified as machine-checkable rule
- UX delta: bootstrap pack lowers cold-start friction; CONTRIBUTING removes new-contributor
  guess work
- Honest signal: optimization loop hit diminishing returns; next iteration depends on real-run
  data the system doesn't have yet

## [0.21.0], 2026-06-17

Batches X + Y from the 6-fork optimization review. **Quality-preserving** efficiency wins
plus bug fixes plus 5-year ops伏笔. R1 verified safe via 18-candidate replay workflow
before landing (0 real regressions; 2 anti-bot edge cases fixed in L0 design first).

### B1, Discovery prompt bug (CN sources + mcp-ecosystem were locked out)

The 2026-06-17 sweep's Discovery agents had a prompt that said "Read these THREE files
only" → discovery-cn.md + mcp-ecosystem.md were mechanically excluded from every agent's
context. 0 CN tools surfaced, mcp-ecosystem element was unread despite existing.
**Fix:** `refresh-protocol.md` D1 prelude now mandates 5 reads (sources-index + own
domain + protocol D1-D5 + discovery-cn + mcp-ecosystem). Every future workflow script
MUST include these per the prelude.

### R1, Verify pipeline collapsed from 3-LLM-lens to L0 deterministic + L1 single lens

The 3-LLM lens (existence / freshness / top-pick-impact) was redundant: same model,
same cutoff, votes correlated. BigGo's 13.5mo stale URL passed all 3. Replaced with:
- **L0 deterministic** (`tools/l0_verify.py`, 473 lines, self-tested 7/7): gh-api +
  HTTP + DNS + cert + npm/pypi registry per URL type. Anti-bot 403 with healthy DNS+cert
  → PASS, not BLOCK (protects live SaaS like Publora). Web-registry mode handles known
  registry pages (chatgpt.com/apps, github.com/mcp).
- **L1 single LLM lens** (top-pick-impact only): only judges actual top-pick movement,
  skipped if L0=BLOCK.

**Replay verification** (results inline below, no separate file): 18 candidates
(15 LAND + 1 HOLD + 2 known-stale) replayed through new pipeline. 0 real regressions
(4 false-positives were already-landed entries, L1 correctly refused re-landing).
3 actual improvements (BigGo, arxiv-sanity-lite, kukapay/funding-rates all correctly
BLOCKed at L0 where the old 3-lens missed them).

**Saving**: 18 candidates × 3 lens = 54 LLM calls → 18 LLM calls + 18 deterministic checks.
~50% workflow tokens / ~27% wall-clock at no quality loss.

### R2 + R3, workflow_helpers.md

- **PREAMBLE constant** (~520 tokens, prompt-cache-safe): shared fixed-text prefix for
  Discovery agents. Anthropic prompt cache deduplicates → 16 agents × 144k input savings
  per sweep.
- **retryAgent() wrapper**: handles schema-validation retries + typed failure tagging.
  Honest finding: backoff-with-sleep is NOT possible in workflow scripts (no setTimeout
  in deterministic runtime). Real rate-limit fix remains BATCH_SIZE=4.

### O1 to O4, 5-year伏笔 (5-minute setup each)

- a local `cleanup-workflows` script, 30d hot / 30-90 gzip / >90 prune
- CHANGELOG half-year archive convention written into cleanup pass (24mo main file cap)
- `metrics/live-runs.YYYY.jsonl` year-rollover written into cleanup pass
- GITHUB_TOKEN check: confirmed `gh api` already uses gh auth's 5000/hour limit

### D1, tools/<slug>.md naming规则化

SHOULD rule added to spec §3.1: pure tool name unless owner is needed for disambiguation.
- `arctic_shift.md` (unique brand), no owner prefix
- `saseq-discord-mcp.md` (`discord-mcp.md` already taken by elyxlz), owner needed
- `antigravity-awesome-skills.md` (unique brand, sickn33's fork), no owner prefix.
  Existing index.md link fixed; missing file created.

### D2, v1.2 judgment fields REQUIRED-on-new-entries

`evidence_url` + `ban_risk` + `model_tier` are MUST on entries added after v1.3. Existing
entries don't backfill (P3 monotonic, forward discipline > tokens spent rewriting history).

### D3, mcp-ecosystem moved out of triage

`sources-index.md` now has a separate "Meta-domains, NOT for triage" section.
`SKILL.md` Step 1 adds explicit "skip meta-domains during triage" rule. Prevents future
agents/users from accidentally routing research queries into infrastructure shards.

### Companion-config-spec → v1.3 (no change from v0.20.0, brokerage active)

### Files touched

- `tools/l0_verify.py` (NEW, 473 lines, 7/7 self-test)
- `tools/workflow_helpers.md` (NEW, 216 lines, R2+R3 doctrine)
- `tools/antigravity-awesome-skills.md` (NEW, was broken link in index.md)
- a local `cleanup-workflows` script (NEW, ops伏笔)
- `reference/refresh-protocol.md` (5-mandatory-reads, D5b new pipeline doctrine, cleanup pass §2 + §7 updates)
- `reference/companion-config-spec.md` (slug naming rule + v1.2 fields REQUIRED-on-new)
- `reference/sources-index.md` (meta-domain separation)
- `skills/market-intel/SKILL.md` (Step 1 skip-meta rule)
- `reference/tools/index.md` (antigravity link fix)

### Net

- Token efficiency: ~50% per sweep (R1 only; R2 adds further savings when next sweep uses PREAMBLE).
- Quality: strictly improved (L0 catches what LLM 3-lens missed; L0 self-test passing on 7 representative URL types).
- Discovery coverage: CN sources + mcp-ecosystem unlocked.
- Operational: 4 伏笔 land before they hurt.
- Spec hygiene: naming规则化 + new-entry field MUSTs + meta-domain separation.

## [0.20.0], 2026-06-17

**Full refresh sweep landed.** First end-to-end execution of the v0.17 to v0.19 pipeline
(feedback-bump → discover → 16-domain Discovery → 3-lens adversarial verify → synthesis
→ pre-land verify → philosophy reflection → land). Sweep + landing took ~17 min wall-clock,
214 agents, ~7.5M tokens.

### Sweep results

12 add · 4 replace · 1 hold · 39 watch, net 16/16 domains processed; 0 reject.

**Adds (12):** reddit-community (`arctic_shift`, `SaseQ/discord-mcp`), finance-markets
(`OpenBB MCP`), leadgen-crm (`Instantly.ai MCP`, `Outscraper Google Maps`),
frontier-research (`LMArena`), ready-skills (`academic-research-skills`, `gtm-agents`,
`aso-skills`), mcp-ecosystem (`GitHub MCP Registry`, `ChatGPT Apps Directory`).

**Replaces (4):** `polygon-io/mcp_polygon` → `massive-com/mcp_massive`;
`funding-rates-mcp` (D-STALE) → `vooi-app/mcp`; `Blotato` → `Publora`;
`ComposioHQ/awesome-claude-skills` → `sickn33/antigravity-awesome-skills`.

**HOLD (1):** BigGo Search MCP, caught by the new gh-api gate as 13.5mo stale despite
passing all 3 LLM-judgment lenses. Logged to discovery-state.md with explicit caveat.

### Philosophy violations caught + fixed (PHILOSOPHY.md reflection)

PHILOSOPHY fork audited the sweep against the 6 principles. **PASS** on P2/P3/P5/P6.
**PARTIAL** on P1/P4. Four quiet violations found, all fixed this release:

- **§1 (P1, patch vs. framing):** P2 trigger fired in `feedback-bump.py` (5 distinct
  domains with `barrier_found` in 90d window). Original plan deferred to ROADMAP.
  **Fix:** spec v1.3 promotes `transport: brokerage` from reserved → active;
  `domains/web-scraping.md` gains brokerage tier (Bright Data DaaS + datarade).
- **§4 (P4, facts over recall):** BigGo's URL passed all 3 LLM lenses but turned
  out to be 13.5mo stale, exactly the "confident fabrication" failure mode P4 names.
  **Fix:** `tools/verify_matrix.py` gains the **GHACTIVE** gate, deterministic
  `gh api repos/<o>/<r>` check on every github.com URL. 404→BLOCK, archived→BLOCK,
  >12mo stale→WARN. **Caught 6 stale repos in existing matrix on first run** (most
  egregious: `arxiv-sanity-lite` at 35 months).
- **§3 (P6, honest boundaries):** content-cms saturated (10+ sources, 5 candidates
  all demoted). **Fix:** explicit saturation flag, next sweep skips Discovery here
  unless `live-runs.jsonl` surfaces a gap.
- **§2 (P1, grandfathered top pick):** seo-keywords never questions whether
  DataForSEO should remain top pick. **Fix:** "top-pick grandfather watch" added;
  next sweep MUST run a "could DataForSEO be replaced" angle.

### Landed files

- `domains/`: 9 shards edited; 2 gain saturation/grandfather flags.
- `tools/`: 11 new per-tool docs.
- `discovery-state.md`: BigGo HOLD + 39 watches categorized + P2-fired note.
- `companion-config-spec.md`: v1.2 → v1.3 (`brokerage` enum).
- `tools/verify_matrix.py`: +GHACTIVE gate (~115 lines).
- `ROADMAP.md`: P2 brokerage-trigger checked off.

### Pipeline timing (max-effort)

| Stage | Duration |
|---|---|
| Step -1 (`feedback-bump.py`) | 0.115s |
| Discovery prescan (`discover.py` E1-E6) | 14.6s |
| Workflow (16 domains, 3-lens adversarial) | 12m22s |
| Pre-land verify (16 changes) | 3m49s |
| Philosophy reflection | 0m41s |
| sync-check downstream | 0.118s |
| **Total** | **~17m** |

### Net

- Tool docs: 152 → 163 (+11).
- Doctrine: spec v1.2 → v1.3 (brokerage active).
- Deterministic gates: +1 (GHACTIVE, catches what LLM-judgment cannot).
- ROADMAP triggers: 1 of 5 fired (transport: brokerage).

## [0.16.0], 2026-06-16

Adds **Cleanup pass** as a mandatory per-sweep step in `reference/refresh-protocol.md`.
Doc/script entropy grows silently in any long-running skill; without an explicit prune
step the matrix bloats ~5-10% per cycle. The new section codifies what to cut (one-shot
artifacts, stale Mode-B refs, CHANGELOG bloat post-doctrinal-pivot, PII drift in
committed READMEs, single-purpose <80-line runbook fragments) and what NOT to cut (per-tool
docs, domain shards, the 3 companion-config-* docs, active feedback ledgers).

Includes a "Cleanup" section template for the sweep CHANGELOG entry. First execution
shipped as companion-config-repo v0.9.1.

### Files touched

- `reference/refresh-protocol.md`, new "Cleanup pass (mandatory every sweep)" section
- `CHANGELOG.md`, `plugin.json`, `README.md`, `README_CN.md`

## [0.15.0], 2026-06-16

End-to-end restore-pipeline audit by 4 parallel forks (cold-start sim / per-tool depth
test / scripts black-box / security posture). Implements all C-tier recommendations.

### Spec v1.1 (additive, backward-compat)

- **`reference/companion-config-spec.md`** §3.1, `transport` enum expands to include
  `"rest"` (REST-only credentials, no MCP) and `"python-lib"` (installable Python
  libraries). `expires` and `rotate_after` documented as OPTIONAL fields for
  credential-lifecycle tracking. `health_last` gains values `credential_ready` /
  `verified` / `installed`. v1 consumers ignore unknown fields per the existing
  forward-compat rule, no migration needed.
- Spec status header bumped: `Spec version: 1.1`.

### README rewrite, "Now what?" routing block

- **`README.md`** gains a 3-row routing table right under Install: pick by intent (use
  the skill / install first MCP / set up companion repo) and you're told the next file
  to open. Addresses the cold-start audit's #1 friction (L0→L3 ladder was buried).

### Companion-config-repo.md, 3-file MVS skeleton

- New section "Minimum viable conformant repo (3 files)" near top, gives the smallest
  spec-conformant repo shape (`.gitignore` + empty `registry.json` + `tools/.gitkeep`) so
  new users can validate tooling against the spec before committing real secrets.

### Stub for `stackexchange` tool doc

- **`reference/tools/stackexchange.md`** (NEW), covers raw Stack Exchange REST API
  (no MCP exists). Key insight: registering an App raises rate limit 300 → 10k req/day per
  IP. Indexed under `reddit-community` in `tools/index.md`. Closes the gap where the
  companion repo's `stackexchange` slug had no matrix-side doc.

### env.template gotcha pointer footer

- All 26 `tools/<slug>/env.template` files in the companion config repo (DaizeDong's
  reference instance) gain a footer: `# Gotchas + full how-to: see ../market-intel/...
  /reference/tools/<slug>.md`. A new user filling out an env file is now signposted to
  the gotcha catalog (per-tool docs traditionally held those; env.templates didn't).

### Companion config repo v0.9.0 (separate release in DaizeDong/market-intel-config)

The companion-repo side of this audit shipped as its own v0.9.0, see that repo's
CHANGELOG for: `_account-info.env` Mode-B-header purge + `_credentials.env` split,
`.gitignore` `*.jsonl` block, `apply.py --list-rest-only`, `verify.sh` fuzzy slug match,
`install-libs.sh` for Python libs, Mode-A guards on backup/restore scripts,
`new-machine.md` Mode A/B branching, `secret-rotation.md` transcript-leak section,
6 transcript-leaked tokens get `rotate_after: "2026-09-16"` in `registry.json`.

### Files touched

- `reference/companion-config-spec.md` (transport enum + expires + rotate_after)
- `reference/companion-config-repo.md` (MVS skeleton section)
- `reference/tools/stackexchange.md` (NEW)
- `reference/tools/index.md` (stackexchange row)
- `README.md` + `README_CN.md` (Now-what block + version badge)
- `CHANGELOG.md`, `plugin.json`

No matrix-structure changes. Audit-driven hygiene release.

## [0.14.0], 2026-06-16

Comprehensive **anti-automation + onboarding gotcha rollup** from two real batch-registration
sessions (2026-06-15 + 2026-06-16). Surfaces every bot defense, captcha pattern, and React-
state trap a first-time-setup user will hit when following this skill's per-tool docs.

### New L0 section: `install-guide.md` → "Anti-automation patterns to expect during install"

Single table indexing the bot defenses we actually hit, with workarounds. Covers:

- PerimeterX/Akamai fingerprint deny (Webflow)
- Cloudflare Turnstile (Buffer)
- reCAPTCHA + hCaptcha double gate (Contentful)
- hCaptcha on forgot-password (eBay)
- B2B work-email gate (Attio, Lusha)
- readonly+disabled with active watcher (Apollo)
- OAuth-provider mismatch, no Google option (HubSpot)
- Provider-side approval delay, not bot defense (eBay 1-business-day)
- Email-verification-link out of reach when Gmail MCP is on a different Google account
- Multi-step React onboarding wizards with `sr-only` radios + sticky-header pointer
  interception (Sanity 8-step, Apollo, FMP 5-question)
- DOM-visible plaintext credentials transcript-hygiene hazard (Twelve Data, FMP,
  Mastodon, Bluesky once-shown App Password, Stack Apps key)

### Per-tool docs, gotcha bullets appended

20 tool docs updated under `## General experience & gotchas (踩坑)` with the 2026-06
discoveries. None rewritten; one to three new bullets each:

- buffer · sanity-mcp · contentful-mcp · apollo · hubspot-mcp · attio-mcp · hunter
- exa · serpapi · twelve-data · fmp · moralis · trends-mcp · ebay-api
- stack-overflow-mcp · atproto · mastodon-py · webflow-mcp · zoominfo-lusha · zerobounce
- coinmarketcap-mcp (consumer vs pro account split) · polygon (PyPI MCP unstable)
- paper-qa (large install footprint warning)

### `metrics/live-runs.jsonl`, 16 entries appended

Each barrier we hit, each verification we confirmed. Future refresh sweeps read this to
prioritise which matrix entries the real world just proved right or wrong.

### `companion-config-spec.md` schema note

The 3 Python libs (atproto, Mastodon.py, paper-qa) introduce a new `transport: "python-lib"`
value beyond the spec's documented `stdio | http | sse` enum. Recorded in companion-config
repo's v0.7.0 entry, informally honored until v2 of the spec; treat as extension, not
breaking change.

### Files touched

- `reference/install-guide.md` (new section)
- 22 tool docs in `reference/tools/`
- `metrics/live-runs.jsonl` (+16 lines)
- `CHANGELOG.md`, `plugin.json`, `README.md`, `README_CN.md` (version bump)

No matrix-structure changes; this release is documentation hygiene only.

## [0.13.2], 2026-06-16

User-flagged addition to `crypto-defi`: **Barker** (barker.money), stablecoin yield
aggregator covering 515+ DeFi protocols + 20+ CEX. Fills a real gap DefiLlama doesn't
(DefiLlama is DeFi-only, Binance/OKX/Bybit Earn campaign rates never appear there).

- **`reference/tools/barker.md`** (NEW), full per-tool doc. Route ① / source tier L2 /
  REST + agent-friendly `llms.txt` index at docs.barker.money / no MCP yet / no key
  claimed for read. Decision rule: pick Barker for "best safe USD yield across CEX +
  DeFi"; stick with DefiLlama for cross-protocol TVL/fees/volume or non-stable assets.
  Hard guardrail #5 callout: CEX yields are campaign-driven and time-boxed, so every
  quoted Barker CEX APY must carry a fetch date.
- **`reference/domains/crypto-defi.md`**, new row between DefiLlama and Moralis. Default
  pick paragraph updated: "stablecoin yield discovery → Barker (CEX + DeFi unified) +
  DefiLlama yields (DeFi-only ground truth), cross-check the two."
- **`reference/tools/index.md`**, crypto-defi section gets a Barker line.
- **`reference/volatile/pricing-install.md`**, crypto-defi block gets the Barker
  install line with the `llms.txt` pointer and the note that the `BarkerEngine` ERC-4626
  contract is out of scope for research (only relevant if recommending as execution venue).
- **`metrics/live-runs.jsonl`**, appended a `user_correction:"add"` entry recording this
  as the highest-weight signal (user manually flagged the gap).

No structural changes.

## [0.13.1], 2026-06-16

Post-v0.13.0 doc cleanup pass, addresses duplication risk between SKILL.md / 3 companion-*
docs after the hardening doc landed, and ports user-facing onboarding gotchas from
real-world tool installs into the per-tool docs.

**De-duplication (companion-* docs):**
- **`SKILL.md`** Step 3, removed the inline directory-tree + JSON-schema + registry.json
  snippet (~40 lines). The structure is now spec §2 / §3 / §4, paraphrasing it in SKILL.md
  was creating drift risk across 3 sibling docs. Replaced with a one-paragraph pointer.
- **`companion-config-repo.md`** §"Detailed file formats", collapsed 5 transport-shape JSON
  examples + the README.md skeleton (~120 lines) into one worked finnhub example + pointer
  to spec §4.1. Same drift-risk reason.
- **`SKILL.md`** Step 3 detection rule 4, `runbooks/add-new-tool.md` reference now
  acknowledges that each user authors their own runbooks; pointer is conditional.

**install-guide.md:**
- L3 table row split into L3a (overview), L3b (formal spec), L3c (hardening), single cell
  was ~5 sentences after v0.13.0.
- New `## Troubleshoot a non-Connected MCP` section ports the 5 diagnostic categories from
  the companion-config runbook (token expired / stdio PATH / HTTP token wrong / env var
  missing / subscription gate). These belong in the public skill because every market-intel
  user hits them; the runbook is one user's instance.
- Secret hygiene gains a "clipboard-capture sanity gates" bullet, reject anything outside
  `length ∈ [8, 512]`, whitespace, or `^https?://`. Battle-tested anti-footgun checks.

**Per-tool onboarding gotchas (ported from real installs):**
- **`tools/finnhub.md`**, `FINNHUB_STORAGE_DIR` must exist before first run (stdio exits
  silently otherwise).
- **`tools/dataforseo.md`**, "password" is the API password from the dashboard, NOT the
  account login password (HTTP 401 with no helpful error).
- **`tools/sec-edgar-mcp.md`**, User-Agent MUST contain a contact email (`@`), not just an
  app name (SEC fair-access throttles without it).
- **`tools/product-hunt-mcp.md`**, env var wants the Developer Token, not the API Key /
  Secret pair listed alongside; token is locked to one PH account.

**Mode A / Mode B clarification (post-Mode-A switch):**
- **`companion-config-repo.md`** structure tree, `no-secret-leak.yml` workflow + `backup-
  secrets.sh` / `restore-from-onedrive.sh` scripts now marked "Mode B ONLY" with reasoning.
  Under Mode A the CI gate fights intentional commits.

No tool/matrix changes.

## [0.13.0], 2026-06-16

New L3 reference doc: `reference/companion-config-hardening.md`, a 12-step GitHub-side
lockdown runbook for users creating a private companion config repo from scratch. Lives in
the **skill** (not in any companion repo) because the companion repo is generated
per-user, so the hardening instructions must reach the user *before* the repo exists.

Why this doc was needed: the default GitHub configuration for a freshly-created private
repo is dangerously permissive for a place that may hold API keys. The single biggest
gotcha is that installed GitHub Apps (ChatGPT Codex, Devin.ai, etc.) default to "All
repositories" scope, meaning the moment you create the new private repo, those AI tools
silently gain Read+Write access to it. Account-level Copilot training is also opt-out,
not opt-in. The runbook closes all of these by hand in ~15 min.

- **`reference/companion-config-hardening.md`** (NEW), covers:
  - Threat model table (8 named threats with their mitigation).
  - Step 1 PRIVATE creation + incognito-window verification.
  - Step 2 Mode A/B decision (delegated to spec §5.3).
  - Step 3 Features lockdown (Wikis / Issues / Projects / Discussions all OFF).
  - Step 4 Code security, every Dependabot toggle OFF; on paid plans also Secret
    Scanning / Push Protection OFF (Mode A's whole point is conscious key storage; Push
    Protection would block legitimate commits).
  - Step 5 Actions Disabled (radio: Disable actions). Removes the entire compromised-
    workflow exfiltration surface.
  - Step 6 Pages source None.
  - Step 7 Webhooks / Deploy keys / Actions / Codespaces / Dependabot secrets verified
    empty.
  - Step 8 Collaborators empty (with a note that every collaborator gets ALL history,
    including rotated keys).
  - Step 9 account-level Copilot data-sharing Disabled (canonical "don't train on my
    code" opt-out).
  - Step 10 GitHub Apps audit, the most overlooked step. Walks per-app: scope = "All
    repositories" or "Only select"? Which AI tools to uninstall vs restrict.
  - Step 11 Branch protection (skip for solo use).
  - Step 12 Periodic re-audit with a gh CLI snippet.
  - Quick-reference checklist (sticky-note-sized).
  - Closing section explaining why this doc lives in market-intel and not in the
    companion repo (chicken-and-egg: you can't read instructions inside a repo before
    you've created it).
- **`reference/companion-config-spec.md`** §1 intro and new §10 "see also" now cross-
  reference the hardening doc. §10 is the canonical pointer for "what else applies to a
  conforming repo beyond the file-format contract."
- **`reference/companion-config-repo.md`** top notice + bootstrap Step 4 inline note
  both point at the hardening runbook with the line "Harden BEFORE the first push."
- **`reference/install-guide.md`** L3 row updated to list all three companion-* docs
  (spec, overview, hardening) with the new "harden before first commit" note.
- **`SKILL.md`** Step 3 companion section gains a callout box: when guiding a user to
  bootstrap a new companion repo, ALWAYS surface the hardening runbook *before* the first
  push.

No tool/matrix changes. Hardening posture only.

## [0.12.0], 2026-06-16

companion-config-spec v1 gains an explicit **storage-mode** dimension. Both "secrets
committed to private repo" (Mode A) and "secrets gitignored + out-of-band backup" (Mode B)
are now recognized as valid spec-conformant choices. Skills consuming companion repos MUST
read `secrets/README.md` (or the repo's policy declaration) to know which mode is in use.

Why: privately deployed companion repos with low-stakes data-API keys often prefer the
single-source-of-truth convenience of committing secrets directly. The previous spec wording
implicitly assumed Mode B; this release makes the choice explicit and analyzes the residual
risk of each.

- **`reference/companion-config-spec.md`** §5.3 rewritten as "Storage modes (Mode A vs Mode
  B)". Documents:
  - Mode A trade-offs: pros (single source of truth, bootstrap is `git clone` + apply),
    cons (GitHub Secret Scanning Partnership providers auto-revoke detected keys even in
    private repos, explicit list: OpenAI `sk-`, Anthropic `sk-ant-`, AWS `AKIA`, Stripe
    `sk_live_`, GitHub `ghp_`, Slack `xox`, etc.).
  - Mode B trade-offs: pros (keys never enter git), cons (two-step bootstrap, requires
    out-of-band backup machinery).
  - Required `.gitignore` patterns for Mode B (unchanged from v0.11.0).
  - SHOULD: every conforming repo declares its mode at the top of `secrets/README.md`.
- **`reference/companion-config-repo.md`** "Why private matters" section becomes "Two
  storage modes" + per-mode defense-in-depth posture.
- **`SKILL.md`** Step 3 companion section, the description of `secrets/<slug>.env` now
  says "storage mode depends on the repo's policy declared in `secrets/README.md`".
  Detection rule clarified: even under Mode A, the skill MUST NOT read raw secret values
  (it spills to transcript regardless of where the file is stored on disk).

The reference implementation `DaizeDong/market-intel-config` adopted Mode A in its v0.5.0
release; its CHANGELOG documents the migration.

## [0.11.0], 2026-06-16

Minor version bump: introduces a **formal specification** for companion config repos so
any conforming repo can be mechanically read by this skill (or future tooling). Previously
the companion-config-repo doc described the pattern, but there was no contract, fields
were de-facto rather than de-jure.

- **`reference/companion-config-spec.md`** (new), formal spec, status STABLE, spec
  version `1`. Covers:
  - §1 Discovery convention (env var → dotfile → XDG).
  - §2 Required vs optional directory structure (`.gitignore` patterns mandatory).
  - §3 `registry.json` schema with REQUIRED / OPTIONAL field markings + forward-
    compatibility rules (skills MUST ignore unknown fields).
  - §3.1 Per-tool entry schema: `slug` and `installed` are the only strictly required
    fields; `matrix_slug`, `matrix_origin`, `domain`, `tier`, `transport`, `health_last`
    are OPTIONAL but RECOMMENDED for richer skill consumption.
  - §4 `tools/<slug>/` per-tool layout with REQUIRED `claude.json.template` +
    `env.template`; RECOMMENDED `README.md`; RESERVED `manifest.json` (future v2).
  - §4.1 `claude.json.template` placeholder syntax (`<UPPER_SNAKE_CASE>`), transport-
    specific shapes for stdio/http/sse (incl. token-in-URL variant).
  - §4.2 `env.template` UTF-8 no BOM mandate.
  - §5 `secrets/` directory conventions incl. `_account-info.env` underscore prefix for
    "not-a-tool" cross-service metadata.
  - §6 The apply contract (idempotency, no-echo, fail-loud on missing placeholders,
    backup, atomic write).
  - §7 The verify contract.
  - §8 Versioning policy (single integer; minor changes don't bump; major changes do).
  - §9 Conformance checklist.
  - §10 Future-reserved extensions (manifest.json, JSON Schema files).

- **`reference/companion-config-repo.md`**, adds a callout at top pointing readers to the
  spec for the formal contract. The repo doc remains the overview + rationale + tutorial.

- **`SKILL.md`** Step 3 companion section, explicitly references the spec by version
  number so any future agent knows what contract it's consuming.

- **`reference/install-guide.md`**, L3 row reframed to show both the overview
  (`companion-config-repo.md`) and the formal contract
  (`companion-config-spec.md`) as the L3 reading list.

Net: any user can now stand up a companion config repo conforming to a published v1
contract, ship tooling against it, and trust that this skill (and future versions) will
mechanically consume it.

## [0.10.7], 2026-06-16

Hardens the v0.10.6 work, removes ALL environment-specific path assumptions and per-maintainer
references from the skill, so the matrix is truly forkable without doc edits.

- **SKILL.md discovery convention**, removed `~/CodesSelf/market-intel-config/`. The new
  convention: `$MARKET_INTEL_CONFIG` env var (recommended) → `~/.market-intel-config/`
  (dotfile-in-home, universal) → `~/.config/market-intel-config/` (XDG, Linux/macOS). No
  filesystem path is required; the user picks.
- **`reference/companion-config-repo.md`**, every `~/CodesSelf/...` path removed. The bootstrap
  example now uses `$CFG=~/.market-intel-config` as a parametric placeholder. The discovery
  section explicitly says "There is no required filesystem location."
- **`reference/install-guide.md`**, secret-handling hygiene now lists clipboard commands for
  all three OSes (PowerShell `Get-Clipboard`, macOS `pbpaste`, Linux `xclip -o` / `wl-paste`)
  rather than implying PowerShell. The "Windows notes" section retains PowerShell appropriately
  since it's the Windows-specific section.
- **`reference/refresh-protocol.md`**, "Commit + push to (DaizeDong/market-intel)" replaced
  with "Commit + push to whichever Git remote this matrix repo lives at." Removes the implicit
  assumption that this matrix is hosted at one specific account.

Sister-skill cross-references (`DaizeDong/shopping-aggregator`) intentionally retained, those
are PUBLIC published-repo URLs needed for `/plugin install` to work. Anyone reading the doc can
clone them.

Net effect: a fork of this matrix can ship as-is without per-fork edits except for the sister-
skill URL in the cross-references (if the forker also forks shopping-aggregator).

## [0.10.6], 2026-06-16

Strengthens the companion-config-repo coupling in three ways without compromising the
private/personal nature of per-user companion repos:

- **SKILL.md**, adds a substantial new section under Step 3's secret-handling block:
  "Where the user's keys + install state live: the COMPANION CONFIG REPO". Documents the
  discovery convention ($MARKET_INTEL_CONFIG env → ~/CodesSelf/market-intel-config/ →
  ~/.config/market-intel-config/), the canonical directory structure (tools/<slug>/,
  secrets/<slug>.env, registry.json, scripts/apply.py, etc.), and how Step 3 should use it
  (read registry.json + per-tool README for tier/quota context; never read secrets/<slug>.env;
  recommend additions via the standard procedure). Skill flow degrades gracefully when no
  companion repo exists, matrix-only mode still works.
- **`reference/companion-config-repo.md`**, rewritten to be a generic spec (not an
  advertisement for a specific person's repo). Every per-user identifier removed. Adds the
  detailed file-format spec for `claude.json.template` (covering stdio/HTTP/SSE transports,
  bearer-token and token-in-URL variants), `env.template`, `tools/<slug>/README.md`, and
  `registry.json` schema. Explicit warning to keep per-account identifying info (email,
  username, phone, account IDs) OUT of committed READMEs and IN a gitignored
  `_account-info.env`.
- **`install-guide.md` L3 row**, removed the named-repo reference, reframed as "per-user
  private companion repo, each user maintains their own, there is no canonical shared one."

This codifies in the public skill what was previously informal practice. Any user can replicate
the companion-repo pattern on their own infrastructure (any Git host, any backup target); no
dependency on a specific account or organization.

## [0.10.5], 2026-06-15

Adds the **companion-config-repo** pattern as a formal L3 layer of the install system: introduces
a recommended split between the public matrix (this repo) and a private per-user ops state repo
(reference impl: `DaizeDong/market-intel-config`, private). The split keeps secrets out of git and
keeps ops state out of the matrix.

- **`reference/companion-config-repo.md`** (new), documents the pattern: per-tool JSON templates +
  empty env templates live in the companion repo's `tools/<slug>/` (committed); real keys live in
  `secrets/<slug>.env` (gitignored, OneDrive-backed). A `scripts/apply.py` merges templates +
  secrets idempotently into `~/.claude.json` without ever echoing key values. A CI gate
  (`no-secret-leak.yml`) scans for typical key patterns as defense in depth.
- **`reference/install-guide.md`**, three-level install table extended with **L3 ops state**
  pointing to companion-config-repo.md. The L0/L1/L2 layers (mechanics / per-domain / per-tool) are
  unchanged; L3 is purely additive, no existing flow breaks if the user doesn't adopt a
  companion repo.
- No tool churn. Matrix monotonic (+1 doc, 0 deleted, 0 silent change) per P3.

This codifies what was previously informal, users were already maintaining ops state in private
notes, scattered `.env` files, and out-of-band tooling. Documenting the pattern makes the secret
hygiene story end-to-end (the install-guide L0 secret rules apply at acquisition; companion-repo
L3 mechanics apply at persistence + restore).

## [0.10.4], 2026-06-15

Sister-skill integration: cross-references to **[DaizeDong/shopping-aggregator](https://github.com/DaizeDong/shopping-aggregator)**, a newly-authored consumer-shopping-price-compare orchestration skill that fills a gap surfaced by the 2026-06-15 user research run. Net: +1 domain (routing-only), +1 ready-skills row, +2 README cross-links, no tool churn, no shard breakage.

- **`reference/domains/consumer-price-compare.md`** (new), routing-only shard. Documents the boundary: market-intel handles broad commercial research + seller-side ecommerce-arbitrage; shopping-aggregator handles the consumer buy decision (multi-retailer landed-cost, history via Keepa/Camelcamelcamel/慢慢买, coupon stacks via Capital One Shopping/Karma/购物党, deal discovery via Slickdeals/Flipp/什么值得买, Honey 2026 trust event). When triage hits this domain, defer to the sister skill rather than fan out, per P5 (delegate, don't reinvent).
- **`reference/sources-index.md`**, added consumer-price-compare row (15 domains total).
- **`reference/domains/ready-skills.md`**, added a top row for shopping-aggregator with install command; reframed the ecosystem judgment line ("consumer shopping was a gap until 2026-06").
- **`README.md` + `README_CN.md`**, added a "Sister skill" callout section above the source matrix, bumped the matrix count badge to 15, added the consumer-price-compare row to the matrix table, added a Sister-skill shield badge. The seller-side ecommerce-arbitrage row is annotated "(seller-side)" to make the consumer/seller split explicit.
- No tool-doc changes; no tools added/removed/retombstoned. The matrix is monotonic (+1 domain, +0 dead, +0 silent change) per P3.

## [0.10.3], 2026-06-15

Minor doctrine-aligned edits prompted by a review of the Horizon (Thysrael/Horizon) news-aggregator, which **confirmed the skill's boundary rather than expanding it**. Net: **0 new features**; 1 watchlist entry + 2 one-line guardrail/doc sharpenings. Rejected (with reasons): OpenBB as a tool (aggregator over in-matrix providers yfinance/FRED/FMP → trips the D4 套壳工具 filter, duplicates the skill's own delegation role per P5); an AI relevance-scoring/threshold prune (conflicts head-on with guardrails #4/#7/#8 + P6, silent degradation, and an LLM 0 to 10 with no deterministic check is the P4 confident-fabrication failure mode); a built-in digest/monitor mode (P5 scope creep, reconstructs Horizon's orchestration+distribution spine and duplicates `/schedule` + `discord_relay` + `feishu-notify`; per H3 a new mode is human-approval-only). Established doctrine for a Horizon-shaped orchestration product is to FOLD it as a delegation back-end (`discovery-state.md` "Deep-research-as-a-service" precedent), not clone it.

- **`reference/volatile/discovery-state.md`**, logged "public Telegram channels as alt-data" to the new-angle watchlist (FOLD candidate; verdict deferred to the next Discovery sweep per H2/H3 + C9). Telegram is genuinely uncovered as a *data source* (in-matrix only as a notification channel), but a new social/messaging territory is human-PR-gated on ≥3 API-verified readers + recurrence, not a hand-add.
- **`SKILL.md` guardrail #2**, one-clause sharpening: byline/wire-service reprints (AP/Reuters/PR-Newswire pickups, identical verbatim quotes, same press release) count as **one** source; corroboration count must reflect the merge. Enforces the existing "independent = not syndicated from the same origin" rule without adding a synthesis pass.
- **`SKILL.md`**, added a 3-line note that recurring/digest use is achieved by wrapping the one-shot skill in a user-owned `/schedule`/`/loop` routine (routine owns cadence + delivery), keeping monitoring/distribution out of the thin layer per P5.

## [0.10.2], 2026-06-09

Closes the last tracking gap: **non-GitHub SaaS tools** (59 of 151) now have a deterministic net too.

- **`reference/tools/registry.json`**, a machine-readable authoritative tool registry: every tool
  (89 repo + 59 saas + 3 lib) as `{slug, name, kind, repo, domain, top_pick}`. Derived from
  index.md + the docs (not hand-written), so it can't drift.
- **Gate (`tools/verify_matrix.py`), new REGISTRY check (BLOCK)**: enforces `registry.json` ↔
  `tools/index.md` ↔ `tools/*.md` three-way consistency. Because SaaS tools are listed in the
  registry by slug, they can no longer lose their doc or fall out of the index without a hard BLOCK,
  the gap the repo-based DOCCOVER net couldn't see. Validated: dropping a SaaS tool (twitterapi.io)
  from the registry → BLOCK.
- **Refresh protocol R1** upgraded to a **4-file atomic op** (shard + index + doc + registry); the
  registry is the authoritative tool list, regenerated (not hand-edited) with:

  ```python
  # python3 - from repo root; regenerates reference/tools/registry.json from index.md + docs
  import re,glob,json,os; from collections import Counter
  T="skills/market-intel/reference/tools"; idx=open(f"{T}/index.md",encoding="utf-8").read()
  dom=None; rows=[]
  for ln in idx.splitlines():
      h=re.match(r"^##\s+([a-z0-9-]+)\s*$",ln.strip())
      if h: dom=h.group(1); continue
      m=re.match(r"^- (★ )?\[[^\]]+\]\(([a-z0-9-]+)\.md\)",ln.strip())
      if m and dom: rows.append((m.group(2),dom,bool(m.group(1))))
  seen={}
  for s,d,st in rows: seen[s]=(seen.get(s,(d,False))[0], seen.get(s,(d,False))[1] or st)
  tools=[]
  for s,(d,st) in seen.items():
      p=f"{T}/{s}.md"; repo=None; kind="saas"; name=s
      if os.path.exists(p):
          t=open(p,encoding="utf-8").read()
          tm=re.search(r"^#\s+Tool:\s*(.+)$",t,re.M); name=tm.group(1).strip() if tm else s
          rm=re.search(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",t)
          if rm: repo=rm.group(1).removesuffix(".git"); kind="repo"
          elif re.search(r"pip install|npm i |library|\(lib\)",t,re.I): kind="lib"
      tools.append({"slug":s,"name":name,"kind":kind,"repo":repo,"domain":d,"top_pick":st})
  tools.sort(key=lambda x:(x["domain"],x["slug"]))
  json.dump({"count":len(tools),"by_kind":dict(Counter(t["kind"] for t in tools)),"tools":tools},
            open(f"{T}/registry.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
  ```

- **Version 0.10.1 → 0.10.2.**

## [0.10.1], 2026-06-09

Anti-rot hardening so the new L2 doc layer can't silently decay or lose tracking across future
refreshes (the failure mode of an unattended self-maintaining system). No matrix content change.

- **Gate (`tools/verify_matrix.py`), 3 new safety nets:**
  - **FRESH now covers tool docs**: every `tools/<slug>.md` must carry a `Last verified: YYYY-MM`;
    a future date is a BLOCK (prevents "looks fresh, isn't"). Missing line = WARN.
  - **STALE (WARN)**: a tool doc not re-verified in >9 months is named (oldest first) so the next
    sweep re-checks it, closes the silent-rot gap (docs were freshness-untracked before).
  - **DOCCOVER (WARN)**: a github repo in a LIVE (non-tombstone) shard row with no per-tool doc is
    flagged, catches "added a shard tool but forgot its doc", the lost-tracking gap that the
    index↔doc TOOLS check couldn't see.
- **Refresh protocol, new `文档层防腐协议 (anti-rot)` section (R1 to R4):** R1 add/remove a tool = an
  atomic 3-file op (shard + index + doc); R2 each sweep re-verifies the swept domain's EXISTING docs
  (not just changed ones) and bumps `Last verified` only when actually re-checked (honest dates, C8);
  R3 death = tombstone-not-delete (keeps the tracking trail; rebrand ≠ death); R4 gotchas must come
  from real runs / shard lessons / `live-runs.jsonl`, never invented, with an independent zero-context
  audit subagent spot-checking shard↔doc↔index↔pricing each sweep.
- **Version 0.10.0 → 0.10.1.**

## [0.10.0], 2026-06-09

Two big moves in one release: (1) a **new L2 per-tool documentation layer**, every tool in the
matrix now has its own install + usage + 踩坑 how-to doc, plus a multi-level **install guide**; and
(2) a **full 14-domain refresh sweep** (discovery + freshness + horizon) that corrected several
broken/dead pointers and refreshed prices. Built and adversarially verified with parallel subagents.

### New: per-tool docs + install guide (the "how-to" layer)

- **`reference/tools/<slug>.md`, one how-to doc per matrix tool** (~130, growing). Each carries:
  what-it-does/when-to-pick, exact install, auth/keys (+ secret hygiene for key-bearing), call
  examples, **General experience & gotchas (踩坑)**, and failure-signals/fallback. Every repo + star
  count is gh-api-verified; every price points at an official URL. Progressive-loading preserved:
  read **only** the one tool doc you need, via the thin `reference/tools/index.md`.
- **`reference/install-guide.md`, L0 install overview** (prerequisites, MCP transport types, the
  `claude mcp add` vs direct-`~/.claude.json` mechanics, secret hygiene, Windows notes, per-domain
  entry points). Three levels: L0 overview → L1 per-domain (`pricing-install.md`) → L2 per-tool doc.
- **`reference/tools/index.md`**, thin tool index (slug → doc → domain → route → top-pick).
- **Gate upgrade (`tools/verify_matrix.py`): new `TOOLS` check** enforces `tools/index.md` ↔
  `tools/*.md` coverage (missing doc = BLOCK), and the existing **REPO/STAR** existence+tolerance
  checks now also scan every tool doc, a hallucinated repo inside a doc 404s → BLOCK like any shard.
- **SKILL.md + refresh-protocol.md**: progressive-loading rules + a refresh step (3b) so future
  sweeps keep the per-tool docs and install guide in sync with the matrix.

### Refresh sweep, confirmed matrix changes (verify-corrected; skeptic audit overrides discovery)

- **3 REPLACEs (all fixed broken/dead pointers):**
  - reddit-community: top pick **GridfireAI/reddit-mcp → karanb192/reddit-mcp-buddy** (702★, zero-setup
    anon/app-id/login tiers; old pick stale 2025-03, read-only, **D-SUPERSEDED**, kept as fallback row).
  - content-cms: **WordPress MCP pointer → WordPress/mcp-adapter** (1236★, official Abilities-API MCP);
    old gaupoit (0★, stale) / Automattic/wordpress-mcp (archived), **D-SUPERSEDED**.
  - content-cms: **Ghost MCP → MFYDev/ghost-mcp** (199★, ~45 tools); old ryukimin/ghost-mcp returns
    **404, D-404**.
- **18 ADDs** across domains, e.g.: DefiLlama free TVL/yields REST (crypto), yahoo-finance-mcp free
  no-key route (finance), paper-search-mcp + PaperQA2 (frontier, fills biomed/full-text gaps),
  vercel-labs/agent-browser + jo-inc/camofox-browser (browser), directus/mcp + webflow/mcp-server
  (CMS), king-of-the-grackles/reddit-research-mcp (semantic subreddit discovery), Patchright
  (anti-detect), Google Suggest + respectaso/ASO (seo), trend-pulse + google-news-trends-mcp (trends),
  postiz-agent + langchain social-media-agent (social), ericosiu/ai-marketing-skills +
  digital-marketing-pro (ready-skills). Each has a new `tools/<slug>.md`.
- **Deaths / supersessions (death-coded):** Papers-with-Code API **sunset by Meta, D-404** (SOTA-
  leaderboard signal lost; flagged as a gap, HF Papers trending = weak proxy); Polygon.io **rebranded
  to Massive** (a rename, same API/keys, still the live Pro pick, NOT a death); ryukimin/ghost-mcp
  **D-404**; GridfireAI/reddit-mcp & WordPress
  gaupoit/Automattic **D-SUPERSEDED**; funding-rates-mcp (kukapay) & karpathy/arxiv-sanity-lite
  **D-STALE** (kept, staleness-flagged); Smartlead MCP repo archived + its shard install hint was
  wrong (corrected); Product Hunt MCP path + Bright Data Crunchbase product URL **D-404** (paths fixed).
- **Verified price/policy refreshes:** Firecrawl free 500-one-time → **1,000 credits/mo**; PriceAPI
  entry **€499 → €99/mo** (+ free 1k trial); CoinMarketCap free **30 → 50 req/min + 15k credits/mo**;
  Nansen down to ~**$49/mo** (was up to ~$999); Semrush entry **$299 → ~$140/mo**; SerpApi free
  **100 → 250/mo**; Blotato "9 platforms" → **20 social accounts**, API needs paid plan; Typefully
  tiers (Free→Team $39); Trends MCP **15+ → 25+ sources**; Exploding Topics now trial-only (no free
  tier); Etherscan free coverage cut ~10% + July-2026 record-cap change.
- **Star refreshes (within tolerance):** marketingskills 31k→32.5k, claude-seo 7.7k→8.5k,
  alirezarezvani/claude-skills 16.7k→17.5k (337 skills), awesome-claude-skills 62.7k→63.8k,
  browser-use 96k→97.9k, idea-reality-MCP annotated 718★.
- **discovery-state.md:** ~27 WATCHLIST + ~21 REJECT-LOG additions (incl. 5 discovery ADD/REPLACE
  candidates the skeptic downgraded, x-tweet-fetcher, Botasaurus, Tosheroon, mcp-amazon-sp-api,
  Beton→SKIP), and 6 new-angle Horizon signals.

### Horizon scan (proposals only, human review; nothing auto-created)

- **Prediction-market odds as queryable alt-data** (Polymarket/Kalshi/Manifold) → **WATCH**, the
  strongest future NEW-DOMAIN candidate; promote only if it recurs next sweep with a maintained
  no-key MCP. **Agentic-payments / x402** → WATCH (a payment rail, not a queryable source). All other
  signals FOLD into existing domains. 0 NEW-DOMAIN, 0 NEW-SKILL auto-created (burden-of-proof unmet on
  first sighting per anti-bloat H3).

- **Version bump 0.9.0 → 0.10.0** (new doc layer + full refresh).

## [0.9.0], 2026-06-09

Added a new **frontier-research** domain, the skill's first non-commercial shard, filling the
academic/paper gap. Previously the skill delegated ALL academic literature to `research-lit` with no
source routing of its own; now AI-frontier scouting gets its own discovery layer (and still hands
off deep synthesis to `research-lit`).

- **New domain shard `domains/frontier-research.md`** (11-source table): arXiv API (+ blazickjp
  arxiv-mcp-server), Hugging Face Daily Papers + Hub API (official HF MCP), Semantic Scholar Graph
  API (citation velocity), Papers with Code (SOTA leaderboards), OpenReview (pre-publication reviewer
  scores), GitHub trending (star velocity = adoption proxy), official AI-lab blogs
  (OpenAI/Anthropic/DeepMind/Meta AI/Mistral/Qwen/DeepSeek), AINews (smol.ai) / The Batch / Import AI
  roundups, alphaXiv / arxiv-sanity-lite, Connected Papers / ResearchRabbit, plus an explicit
  **delegation row to the `research-lit` skill** for deep multi-paper synthesis (this domain is
  SOURCE ROUTING/discovery, not a re-implementation of lit-review). Real-run lesson baked in: the
  L1/L2 floor is arXiv + HF Daily Papers + official lab blogs + GitHub trending; X/social is L4 (a
  lead, not evidence, cross-check via Semantic Scholar / Papers-with-Code, not retweet count).
- **`sources-index.md`**: added the `frontier-research` triage row (AI/ML papers, arXiv, SOTA, new
  models, conference, citations, 论文/前沿研究 → arXiv API + HF Daily Papers ① free).
- **`pricing-install.md`**: added the `frontier-research` install section (`last_verified: 2026-06`)
, most sources are free / no-key (arXiv, HF read, Papers with Code, OpenReview); Semantic Scholar's
  free key only lifts rate limits.
- **Version bump 0.8.0 → 0.9.0** (new domain = minor); plugin.json description now notes the academic
  frontier-research domain alongside the 12 commercial domains.

## [0.8.0], 2026-06-02

Hardened the skill from real-run experience (patio-heaters research + tool configs) so the next
user is faster and safer:

- **Secret-handling HARD rules in SKILL.md Step 3** (we leaked keys 3×, now prevented for others):
  never `browser_snapshot` a page that shows a key (dashboards/rotation pages render it plaintext,
  confirmed on twitterapi.io + Bright Data); get keys via the page's copy button → clipboard →
  direct `~/.claude.json` edit; **do NOT `claude mcp add` for secret-bearing MCPs** (it echoes the
  header/URL); mask tokens in `claude mcp list` output; respect rotation cooldowns; a clean key =
  the user rotates from their own browser.
- **web-scraping shard**: for live e-commerce prices, **skip firecrawl/WebFetch → go straight to
  browser(④)/Bright Data** (Amazon returns 500 to firecrawl; Taobao hides per-SKU price behind
  login; Reddit returns empty to web search; playwright read the real Amazon price in one shot).
  Bright Data row updated with verified hosted-HTTP MCP (free 5k/mo Rapid, no card).
- **x-twitter shard**: X is a LOW-signal source for consumer/non-tech demand (patio-heater "Top" search
  ~empty); route consumer-demand to 抖音/小红书/B站/Reddit/forums; keep X for tech/crypto/influencer.
- **pricing-install.md**: verified Bright Data hosted-HTTP install command + secret-hygiene reminder.
- **gate fix (verify_matrix.py C4)**: distinguish a MODIFIED table row (remove+add same source name) from a real DELETION, editing a row no longer false-trips the death-code block; genuine deletions still blocked (self-tested).


All notable changes to the source matrix and skill are recorded here. Each refresh sweep appends a
dated entry with per-domain added/removed/changed tools.

## [0.7.1], 2026-06-01

**Monthly volatile refresh** (June → volatile domains only: x-twitter, web-scraping,
social-publishing, crypto-defi, browser-automation + light this-month Horizon pulse). Discovery phase
ran 4 blind-scan agents; every repo/star/price below was independently API-verified (`gh api`) or
fetched from the official page, never from recall (C1). The deterministic gate passes clean.

- **Re-verification (no changes needed):** all 33 star-annotated volatile-domain repos re-checked via
  GitHub API, every one is alive (no 404/archived) and every star annotation is accurate within the
  gate's tolerance. **No deletions, no star corrections.** This is the honest, common outcome for a
  matrix verified the same day; recorded so the clean result is visible, not silently skipped (C9).
- **crypto-defi, added:** **Blockscout MCP** (`blockscout/mcp-server`, 39★, official, MIT), free
  read-only on-chain data across 3000+ chains, no key for dev. Added as the free multi-chain fallback.
- **crypto-defi, changed:** Etherscan row flags the verified free-tier change, official page
  confirms ~10% free chain-coverage cut (verified-contract + ABI endpoints stay free on all networks;
  "Lite" plan at 25% of prior lowest tier; info.etherscan.com, updated 2026-05-31). Detail in
  `pricing-install.md`. The specific dropped chains / record-cap reported only by secondary sources
  are **not** asserted (C5/C6).
- **social-publishing, changed:** Buffer row, public API + hosted MCP officially launched
  2026-05-27 (buffer.com/resources/buffer-api-is-here), on every plan incl. Free.
- **pricing-install, changed:** added Blockscout MCP install line + Etherscan free-tier note;
  advanced `x-twitter` section `last_verified` 2026-05 → 2026-06 (twitterapi.io pricing re-verified
  stable at the official site; twikit repo re-verified via API) (C8).
- **discovery-state, new file:** created `volatile/discovery-state.md`, the watchlist + reject log +
  new-angle watchlist that `refresh-protocol.md` references but that did not previously exist. Seeded
  with 12 API-verified WATCH candidates (Scweet 1514★, CloakBrowser 22965★, Patchright 3351★,
  Lightpanda 30717★, CRW 126★, Base MCP, GOAT 993★, deBridge/Tatum/Philidor/CoinStats MCPs), 6
  reject-log entries, and 6 Horizon new-angle items, all stars real `gh api` values.
- **Horizon pulse (May 2026):** no new data territory; scanned H1 1 to 4. Proposals held for human
  review (not auto-created): agent-memory hardening (mem0 57251★ / zep 4626★) = NEW-SKILL flag but
  it's **agent infrastructure, not a queryable commercial-data source** → not a domain; MCP
  tunnels/sandboxes = deployment plumbing (FOLD → ready-skills); emerging platforms (Divine/Vine,
  Threads 300M, Lemon8) lack verifiable access routes (watch, not NEW-DOMAIN); X API Apr-2026 re-tier
  = FOLD → x-twitter but **unverified at source** (devcommunity.x.com auth-walled) → matrix numbers
  left unchanged, logged to watchlist for next scan.
- **No structural changes:** no domains/skills auto-created; all candidates either landed as
  verified incremental rows or were held in discovery-state per C7/C9 + Horizon H3 anti-bloat.

## [0.7.0], 2026-06-01

**Stage C (part 1), CI authority + liveness** (auto-merge intentionally still OFF):
- `.github/workflows/gate.yml`: runs `verify_matrix.py` on every PR to main, independently of the
  local machine that proposed the change, moving go/no-go authority off the proposer (P4 at the
  infrastructure level). Set as a required status check to make a red gate block merge. Auto-merge is
  deliberately NOT enabled yet: per EVOLUTION.md/red-team, it waits for Stage A's root fix
  (machine-readable mirror block + cross-model audit) so the gate is a fact-gate, not a format-gate.
- `.github/workflows/heartbeat.yml`: on the 5th monthly, if no refresh commit touched the matrix
  that month (e.g. the local machine was off), opens an issue so the missed run is visible (P6).

Remaining: Stage A root fix (mirror block + cross-model audit) → then Stage C auto-merge (tiered) →
Stage D meta-loop. Ordering preserved: trust the gate before removing the human.

## [0.6.0], 2026-06-01

Toward the full closed loop, implementing the EVOLUTION.md stages in dependency order. This ships
**Stage A (core)** + **Stage B**.

**Stage A, make the gate a fact-gate (mechanize P2-violated clauses):**
- `verify_matrix.py` now enforces **C7** (a shard with >40% of lines changed = rewrite, not
  incremental → BLOCK, route to human) and **C4** (removing a source row requires a death-code
  D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED in the CHANGELOG or an Avoid(dead) line → else BLOCK).
  These were previously enforced only by LLM intention; now they are mechanism. Verified: a deletion
  without a death-code is blocked; clean state passes.

**Stage B, close the measurement loop (add the sensor):**
- `tools/emit_metrics.py` (deterministic, no LLM/network) appends a per-refresh quality snapshot to
  `metrics/history.jsonl`, per-domain source counts, free/④ route share, last_verified.
- `tools/check_drift.py` reads the series and flags **slow degradation** via cross-period operators
  (source-count crash, ≥3-period stagnation, monotonic decline, free-route erosion over the horizon)
, the rot a single run always looks fine for.
- `SKILL.md` Step 5: at the end of a real research run, append live-run verdicts (source
  verified/dead/price_mismatch/fallback + user corrections) to `metrics/live-runs.jsonl`. The refresh
  reads these to prioritise re-verification and auto-nominate repeatedly-dead sources for C4 deletion.
- Refresh script wired to emit metrics + run drift check (surfaced in the Discord digest) each run.

Remaining (per EVOLUTION.md): Stage A root fix (machine-readable mirror block for full BLOCK-level
repo existence + cross-model audit gate) · Stage C (CI required-check + tiered auto-merge) · Stage D
(self-improving meta-loop). Order preserved: sense and trust the gate before removing the human.

## [0.5.1], 2026-06-01

Evaluation of the update algorithm (5-subagent: control-theory / feedback / meta-loop / red-team /
CI) + the closed-loop evolution design, plus a verified integrity fix.

- **Verified & fixed a real gate gap:** the repo-existence check was nearly hollow on real data
  (0 `github.com/` URLs in shards → existence only verified for star-annotated repos; unstarred real
  repos like `erithwik/mcp-hn` were invisible). Added an interim WARN-tier net that gh-api-checks
  slug-like tokens in table rows (skipping prose / npm-scopes), and **fail-closed retry** so a
  transient network blip no longer discards a good refresh (only a real 404 hard-blocks).
- **`EVOLUTION.md`**: honest diagnosis (today = half-closed, open-loop: no sensor + human-relay
  actuator), the verdict that full-auto is **not yet safe** (the gate is a *format* gate not a *fact*
  gate; P4 "editor ≠ verifier" is currently violated), the red-team precondition checklist, and the
  staged path to a full closed loop, A: fact-gate + cross-model audit · B: feedback sensor
  (live-run telemetry + drift metrics) · C: CI-as-required-check + tiered auto-merge + safety nets ·
  D: self-improving meta-loop with an immutable core. Names the v0.5.1 slug-net as an interim patch;
  the framing fix (machine-readable mirror block) is Stage A.

## [0.5.0], 2026-06-01

**Horizon scan**, the refresh now evolves the matrix's *scope*, not just its *content*. Beyond
finding better tools within the existing 13 domains (Discovery phase), it actively looks for NEW
territories, tool categories, and research angles the current map doesn't cover, applying
PHILOSOPHY.md P1 (fix/expand the framing) to the skill's own scope so it keeps pace with the field.

- New **Horizon scan** section in `refresh-protocol.md`: H1 what-to-scan (this-month events / new
  platforms / new tool categories / novel research methodologies, cross-domain, trend-level), H2
  fold-vs-new-domain-vs-new-skill decision gate, H3 anti-bloat guardrail (new ≠ needs-a-domain;
  watchlist must recur across ≥2 scans; passes the generative test), H4 proposal output.
- Runs on every full sweep (Jan/Apr/Jul/Oct) + a light monthly "this-month pulse"; structural
  additions (new domain / sub-skill) are proposal-only and always go to human review, never
  auto-created. Constrains P1 with P3: scope grows when justified, bloat is treated as decay.
- Refresh script + Procedure wired to run Horizon scan first.

## [0.4.0], 2026-06-01

Crystallized the **design philosophy** as the project's organizing principle, made concrete and
prominent, *root-cause design, not incremental patching.*

- **`PHILOSOPHY.md`** (bilingual): 6 principles, fix-the-framing-not-the-symptom · mechanisms-not-
  intentions · monotonic-evolution-against-decay · facts-over-recall · delegate-depth-own-the-seam ·
  honest-boundaries. Each stated as patch-vs-root with the real decision in this repo it produced,
  plus a generative test every future change must pass ("does it fix the framing, or just patch a
  symptom?"). The philosophy explicitly outranks any individual feature.
- Surfaced it prominently at the **top of both READMEs** (before Install), reframed `CONSTITUTION.md`
  as the embodiment of principle P2, and added a governing one-liner to `SKILL.md`.

## [0.3.0], 2026-06-01

Self-evolution / anti-regression machinery, designed by a 5-subagent co-design pass, ensuring
automated refreshes **monotonically improve** (never silently degrade). "LLM proposes, a
deterministic gate disposes; bad updates never reach main."

- **`CONSTITUTION.md`**: 10 immutable clauses (C1 to C10) injected as hard constraints into every
  headless run, API-verified facts, free/④ route preference, deletion-needs-evidence, incremental
  edits, time-monotonic, bad-updates-never-reach-main. Automation may not edit it.
- **`tools/verify_matrix.py`**: deterministic anti-regression gate (pure stdlib + `gh`/`git`).
  Checks STRUCT (index↔shards), REPO (every github repo exists via `gh api`, fail-closed), STAR
  (annotation within 25% of real), FRESH (no future/backward `last_verified`), METH (methodology
  markers intact), COVER (no >10% global / >30% per-shard source-row drop vs main), CONST
  (constitution unmodified). Verified: blocks hallucinated repos + star lies; current matrix passes
  (28 repos checked). Final veto over landing, an LLM can only make it more conservative.
- **`tools/deploy_skill.sh`**: syncs repo→live skill only after a merged, gate-green main.
- **Refresh script rewired to branch + gate + PR** (no direct main push): works on `refresh/<date>`,
  injects the constitution, scope-guards against out-of-bounds edits, runs the gate, opens a PR on
  pass / discards on fail, and notifies via Discord either way.
- **`refresh-protocol.md`**: added the 防退化协议 (mandatory) section codifying the above.

## [0.2.0], 2026-06-01

Elevated the **browser-automation / act-like-human route (④)** from last-resort footnote to a
first-class option preferred over paid APIs when it fits, leveraging the already-connected
playwright MCP plus free open-source repos that access sites with a real logged-in browser (often
richer data than stripped/paid APIs, at zero cost).

- New domain shard `browser-automation.md`: general AI-browser frameworks (browser-use 96k★,
  stagehand 23k★, skyvern 22k★, crawl4ai 67k★, crawlee 24k★, scrapegraph-ai 27k★) + anti-detection
  (nodriver, camoufox, steel-browser). All stars verified via GitHub API 2026-06-01.
- Added per-platform free OSS repos to shards: x-twitter (twikit + mcp-twikit), social-publishing
  (instagrapi, linkedin-mcp-server, TikTok-Api, xiaohongshu-mcp 14k★, MediaCrawler 50k★, atproto,
  Mastodon.py), ecommerce (Discount-Bandit = self-built Keepa, amazon-scraper), seo-keywords
  (searxng 31k★, serpbear, ddgs), leadgen-crm (gosom/google-maps-scraper, low-risk B2B leads),
  trends-discovery (trendspyg, google-play/app-store-scraper), reddit-community (MediaCrawler, yt-dlp).
- SKILL.md source-selection now prefers route ④ over paid APIs where it fits; routes ①/② reserved
  for un-backfillable history, scale reliability, or compliance.
- Noted limits: browser route can't backfill historical price/BSR (Keepa still needed); needs
  session/cookies + proxies at scale; most platform scraping violates ToS (use throwaway accounts).
- Removed dead repos: tomquirk/linkedin-api (404), pytrends (archived), snscrape (停更),
  elizaOS/agent-twitter-client (下架).

## [0.1.0], 2026-06-01

Initial release. Source matrix built from a 12-subagent commercial-tool survey (last_verified
2026-05) and hardened by a 5-subagent adversarial design review.

- 12 domain shards: x-twitter, reddit-community, web-scraping, ecommerce-arbitrage, finance-markets,
  crypto-defi, seo-keywords, social-publishing, content-cms, leadgen-crm, trends-discovery,
  ready-skills.
- Thin source index, isolated volatile pricing/install file, report template, refresh protocol.
- 8 quality guardrails baked into SKILL.md.
