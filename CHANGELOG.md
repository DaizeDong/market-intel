# Changelog

## [0.10.4] — 2026-06-15

Sister-skill integration: cross-references to **[DaizeDong/shopping-aggregator](https://github.com/DaizeDong/shopping-aggregator)**, a newly-authored consumer-shopping-price-compare orchestration skill that fills a gap surfaced by the 2026-06-15 user research run. Net: +1 domain (routing-only), +1 ready-skills row, +2 README cross-links, no tool churn, no shard breakage.

- **`reference/domains/consumer-price-compare.md`** (new) — routing-only shard. Documents the boundary: market-intel handles broad commercial research + seller-side ecommerce-arbitrage; shopping-aggregator handles the consumer buy decision (multi-retailer landed-cost, history via Keepa/Camelcamelcamel/慢慢买, coupon stacks via Capital One Shopping/Karma/购物党, deal discovery via Slickdeals/Flipp/什么值得买, Honey 2026 trust event). When triage hits this domain, defer to the sister skill rather than fan out — per P5 (delegate, don't reinvent).
- **`reference/sources-index.md`** — added consumer-price-compare row (15 domains total).
- **`reference/domains/ready-skills.md`** — added a top row for shopping-aggregator with install command; reframed the ecosystem judgment line ("consumer shopping was a gap until 2026-06").
- **`README.md` + `README_CN.md`** — added a "Sister skill" callout section above the source matrix, bumped the matrix count badge to 15, added the consumer-price-compare row to the matrix table, added a Sister-skill shield badge. The seller-side ecommerce-arbitrage row is annotated "(seller-side)" to make the consumer/seller split explicit.
- No tool-doc changes; no tools added/removed/retombstoned. The matrix is monotonic (+1 domain, +0 dead, +0 silent change) per P3.

## [0.10.3] — 2026-06-15

Minor doctrine-aligned edits prompted by a review of the Horizon (Thysrael/Horizon) news-aggregator — which **confirmed the skill's boundary rather than expanding it**. Net: **0 new features**; 1 watchlist entry + 2 one-line guardrail/doc sharpenings. Rejected (with reasons): OpenBB as a tool (aggregator over in-matrix providers yfinance/FRED/FMP → trips the D4 套壳工具 filter, duplicates the skill's own delegation role per P5); an AI relevance-scoring/threshold prune (conflicts head-on with guardrails #4/#7/#8 + P6 — silent degradation, and an LLM 0–10 with no deterministic check is the P4 confident-fabrication failure mode); a built-in digest/monitor mode (P5 scope creep — reconstructs Horizon's orchestration+distribution spine and duplicates `/schedule` + `discord_relay` + `feishu-notify`; per H3 a new mode is human-approval-only). Established doctrine for a Horizon-shaped orchestration product is to FOLD it as a delegation back-end (`discovery-state.md` "Deep-research-as-a-service" precedent), not clone it.

- **`reference/volatile/discovery-state.md`** — logged "public Telegram channels as alt-data" to the new-angle watchlist (FOLD candidate; verdict deferred to the next Discovery sweep per H2/H3 + C9). Telegram is genuinely uncovered as a *data source* (in-matrix only as a notification channel), but a new social/messaging territory is human-PR-gated on ≥3 API-verified readers + recurrence — not a hand-add.
- **`SKILL.md` guardrail #2** — one-clause sharpening: byline/wire-service reprints (AP/Reuters/PR-Newswire pickups, identical verbatim quotes, same press release) count as **one** source; corroboration count must reflect the merge. Enforces the existing "independent = not syndicated from the same origin" rule without adding a synthesis pass.
- **`SKILL.md`** — added a 3-line note that recurring/digest use is achieved by wrapping the one-shot skill in a user-owned `/schedule`/`/loop` routine (routine owns cadence + delivery), keeping monitoring/distribution out of the thin layer per P5.

## [0.10.2] — 2026-06-09

Closes the last tracking gap: **non-GitHub SaaS tools** (59 of 151) now have a deterministic net too.

- **`reference/tools/registry.json`** — a machine-readable authoritative tool registry: every tool
  (89 repo + 59 saas + 3 lib) as `{slug, name, kind, repo, domain, top_pick}`. Derived from
  index.md + the docs (not hand-written), so it can't drift.
- **Gate (`tools/verify_matrix.py`) — new REGISTRY check (BLOCK)**: enforces `registry.json` ↔
  `tools/index.md` ↔ `tools/*.md` three-way consistency. Because SaaS tools are listed in the
  registry by slug, they can no longer lose their doc or fall out of the index without a hard BLOCK —
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

## [0.10.1] — 2026-06-09

Anti-rot hardening so the new L2 doc layer can't silently decay or lose tracking across future
refreshes (the failure mode of an unattended self-maintaining system). No matrix content change.

- **Gate (`tools/verify_matrix.py`) — 3 new safety nets:**
  - **FRESH now covers tool docs**: every `tools/<slug>.md` must carry a `Last verified: YYYY-MM`;
    a future date is a BLOCK (prevents "looks fresh, isn't"). Missing line = WARN.
  - **STALE (WARN)**: a tool doc not re-verified in >9 months is named (oldest first) so the next
    sweep re-checks it — closes the silent-rot gap (docs were freshness-untracked before).
  - **DOCCOVER (WARN)**: a github repo in a LIVE (non-tombstone) shard row with no per-tool doc is
    flagged — catches "added a shard tool but forgot its doc", the lost-tracking gap that the
    index↔doc TOOLS check couldn't see.
- **Refresh protocol — new `文档层防腐协议 (anti-rot)` section (R1–R4):** R1 add/remove a tool = an
  atomic 3-file op (shard + index + doc); R2 each sweep re-verifies the swept domain's EXISTING docs
  (not just changed ones) and bumps `Last verified` only when actually re-checked (honest dates, C8);
  R3 death = tombstone-not-delete (keeps the tracking trail; rebrand ≠ death); R4 gotchas must come
  from real runs / shard lessons / `live-runs.jsonl` — never invented, with an independent zero-context
  audit subagent spot-checking shard↔doc↔index↔pricing each sweep.
- **Version 0.10.0 → 0.10.1.**

## [0.10.0] — 2026-06-09

Two big moves in one release: (1) a **new L2 per-tool documentation layer** — every tool in the
matrix now has its own install + usage + 踩坑 how-to doc, plus a multi-level **install guide**; and
(2) a **full 14-domain refresh sweep** (discovery + freshness + horizon) that corrected several
broken/dead pointers and refreshed prices. Built and adversarially verified with parallel subagents.

### New: per-tool docs + install guide (the "how-to" layer)

- **`reference/tools/<slug>.md` — one how-to doc per matrix tool** (~130, growing). Each carries:
  what-it-does/when-to-pick, exact install, auth/keys (+ secret hygiene for key-bearing), call
  examples, **General experience & gotchas (踩坑)**, and failure-signals/fallback. Every repo + star
  count is gh-api-verified; every price points at an official URL. Progressive-loading preserved:
  read **only** the one tool doc you need, via the thin `reference/tools/index.md`.
- **`reference/install-guide.md` — L0 install overview** (prerequisites, MCP transport types, the
  `claude mcp add` vs direct-`~/.claude.json` mechanics, secret hygiene, Windows notes, per-domain
  entry points). Three levels: L0 overview → L1 per-domain (`pricing-install.md`) → L2 per-tool doc.
- **`reference/tools/index.md`** — thin tool index (slug → doc → domain → route → top-pick).
- **Gate upgrade (`tools/verify_matrix.py`): new `TOOLS` check** enforces `tools/index.md` ↔
  `tools/*.md` coverage (missing doc = BLOCK), and the existing **REPO/STAR** existence+tolerance
  checks now also scan every tool doc — a hallucinated repo inside a doc 404s → BLOCK like any shard.
- **SKILL.md + refresh-protocol.md**: progressive-loading rules + a refresh step (3b) so future
  sweeps keep the per-tool docs and install guide in sync with the matrix.

### Refresh sweep — confirmed matrix changes (verify-corrected; skeptic audit overrides discovery)

- **3 REPLACEs (all fixed broken/dead pointers):**
  - reddit-community: top pick **GridfireAI/reddit-mcp → karanb192/reddit-mcp-buddy** (702★, zero-setup
    anon/app-id/login tiers; old pick stale 2025-03, read-only — **D-SUPERSEDED**, kept as fallback row).
  - content-cms: **WordPress MCP pointer → WordPress/mcp-adapter** (1236★, official Abilities-API MCP);
    old gaupoit (0★, stale) / Automattic/wordpress-mcp (archived) — **D-SUPERSEDED**.
  - content-cms: **Ghost MCP → MFYDev/ghost-mcp** (199★, ~45 tools); old ryukimin/ghost-mcp returns
    **404 — D-404**.
- **18 ADDs** across domains, e.g.: DefiLlama free TVL/yields REST (crypto), yahoo-finance-mcp free
  no-key route (finance), paper-search-mcp + PaperQA2 (frontier, fills biomed/full-text gaps),
  vercel-labs/agent-browser + jo-inc/camofox-browser (browser), directus/mcp + webflow/mcp-server
  (CMS), king-of-the-grackles/reddit-research-mcp (semantic subreddit discovery), Patchright
  (anti-detect), Google Suggest + respectaso/ASO (seo), trend-pulse + google-news-trends-mcp (trends),
  postiz-agent + langchain social-media-agent (social), ericosiu/ai-marketing-skills +
  digital-marketing-pro (ready-skills). Each has a new `tools/<slug>.md`.
- **Deaths / supersessions (death-coded):** Papers-with-Code API **sunset by Meta — D-404** (SOTA-
  leaderboard signal lost; flagged as a gap, HF Papers trending = weak proxy); Polygon.io **rebranded
  to Massive** (a rename — same API/keys, still the live Pro pick, NOT a death); ryukimin/ghost-mcp
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
  candidates the skeptic downgraded — x-tweet-fetcher, Botasaurus, Tosheroon, mcp-amazon-sp-api,
  Beton→SKIP), and 6 new-angle Horizon signals.

### Horizon scan (proposals only — human review; nothing auto-created)

- **Prediction-market odds as queryable alt-data** (Polymarket/Kalshi/Manifold) → **WATCH**, the
  strongest future NEW-DOMAIN candidate; promote only if it recurs next sweep with a maintained
  no-key MCP. **Agentic-payments / x402** → WATCH (a payment rail, not a queryable source). All other
  signals FOLD into existing domains. 0 NEW-DOMAIN, 0 NEW-SKILL auto-created (burden-of-proof unmet on
  first sighting per anti-bloat H3).

- **Version bump 0.9.0 → 0.10.0** (new doc layer + full refresh).

## [0.9.0] — 2026-06-09

Added a new **frontier-research** domain — the skill's first non-commercial shard — filling the
academic/paper gap. Previously the skill delegated ALL academic literature to `research-lit` with no
source routing of its own; now AI-frontier scouting gets its own discovery layer (and still hands
off deep synthesis to `research-lit`).

- **New domain shard `domains/frontier-research.md`** (11-source table): arXiv API (+ blazickjp
  arxiv-mcp-server), Hugging Face Daily Papers + Hub API (official HF MCP), Semantic Scholar Graph
  API (citation velocity), Papers with Code (SOTA leaderboards), OpenReview (pre-publication reviewer
  scores), GitHub trending (star velocity = adoption proxy), official AI-lab blogs
  (OpenAI/Anthropic/DeepMind/Meta AI/Mistral/Qwen/DeepSeek), AINews (smol.ai) / The Batch / Import AI
  roundups, alphaXiv / arxiv-sanity-lite, Connected Papers / ResearchRabbit — plus an explicit
  **delegation row to the `research-lit` skill** for deep multi-paper synthesis (this domain is
  SOURCE ROUTING/discovery, not a re-implementation of lit-review). Real-run lesson baked in: the
  L1/L2 floor is arXiv + HF Daily Papers + official lab blogs + GitHub trending; X/social is L4 (a
  lead, not evidence — cross-check via Semantic Scholar / Papers-with-Code, not retweet count).
- **`sources-index.md`**: added the `frontier-research` triage row (AI/ML papers, arXiv, SOTA, new
  models, conference, citations, 论文/前沿研究 → arXiv API + HF Daily Papers ① free).
- **`pricing-install.md`**: added the `frontier-research` install section (`last_verified: 2026-06`)
  — most sources are free / no-key (arXiv, HF read, Papers with Code, OpenReview); Semantic Scholar's
  free key only lifts rate limits.
- **Version bump 0.8.0 → 0.9.0** (new domain = minor); plugin.json description now notes the academic
  frontier-research domain alongside the 12 commercial domains.

## [0.8.0] — 2026-06-02

Hardened the skill from real-run experience (patio-heaters research + tool configs) so the next
user is faster and safer:

- **Secret-handling HARD rules in SKILL.md Step 3** (we leaked keys 3× — now prevented for others):
  never `browser_snapshot` a page that shows a key (dashboards/rotation pages render it plaintext —
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
- **gate fix (verify_matrix.py C4)**: distinguish a MODIFIED table row (remove+add same source name) from a real DELETION — editing a row no longer false-trips the death-code block; genuine deletions still blocked (self-tested).


All notable changes to the source matrix and skill are recorded here. Each refresh sweep appends a
dated entry with per-domain added/removed/changed tools.

## [0.7.1] — 2026-06-01

**Monthly volatile refresh** (June → volatile domains only: x-twitter, web-scraping,
social-publishing, crypto-defi, browser-automation + light this-month Horizon pulse). Discovery phase
ran 4 blind-scan agents; every repo/star/price below was independently API-verified (`gh api`) or
fetched from the official page — never from recall (C1). The deterministic gate passes clean.

- **Re-verification (no changes needed):** all 33 star-annotated volatile-domain repos re-checked via
  GitHub API — every one is alive (no 404/archived) and every star annotation is accurate within the
  gate's tolerance. **No deletions, no star corrections.** This is the honest, common outcome for a
  matrix verified the same day; recorded so the clean result is visible, not silently skipped (C9).
- **crypto-defi — added:** **Blockscout MCP** (`blockscout/mcp-server`, 39★, official, MIT) — free
  read-only on-chain data across 3000+ chains, no key for dev. Added as the free multi-chain fallback.
- **crypto-defi — changed:** Etherscan row flags the verified free-tier change — official page
  confirms ~10% free chain-coverage cut (verified-contract + ABI endpoints stay free on all networks;
  "Lite" plan at 25% of prior lowest tier; info.etherscan.com, updated 2026-05-31). Detail in
  `pricing-install.md`. The specific dropped chains / record-cap reported only by secondary sources
  are **not** asserted (C5/C6).
- **social-publishing — changed:** Buffer row — public API + hosted MCP officially launched
  2026-05-27 (buffer.com/resources/buffer-api-is-here), on every plan incl. Free.
- **pricing-install — changed:** added Blockscout MCP install line + Etherscan free-tier note;
  advanced `x-twitter` section `last_verified` 2026-05 → 2026-06 (twitterapi.io pricing re-verified
  stable at the official site; twikit repo re-verified via API) (C8).
- **discovery-state — new file:** created `volatile/discovery-state.md`, the watchlist + reject log +
  new-angle watchlist that `refresh-protocol.md` references but that did not previously exist. Seeded
  with 12 API-verified WATCH candidates (Scweet 1514★, CloakBrowser 22965★, Patchright 3351★,
  Lightpanda 30717★, CRW 126★, Base MCP, GOAT 993★, deBridge/Tatum/Philidor/CoinStats MCPs), 6
  reject-log entries, and 6 Horizon new-angle items — all stars real `gh api` values.
- **Horizon pulse (May 2026):** no new data territory; scanned H1 1–4. Proposals held for human
  review (not auto-created): agent-memory hardening (mem0 57251★ / zep 4626★) = NEW-SKILL flag but
  it's **agent infrastructure, not a queryable commercial-data source** → not a domain; MCP
  tunnels/sandboxes = deployment plumbing (FOLD → ready-skills); emerging platforms (Divine/Vine,
  Threads 300M, Lemon8) lack verifiable access routes (watch, not NEW-DOMAIN); X API Apr-2026 re-tier
  = FOLD → x-twitter but **unverified at source** (devcommunity.x.com auth-walled) → matrix numbers
  left unchanged, logged to watchlist for next scan.
- **No structural changes:** no domains/skills auto-created; all candidates either landed as
  verified incremental rows or were held in discovery-state per C7/C9 + Horizon H3 anti-bloat.

## [0.7.0] — 2026-06-01

**Stage C (part 1) — CI authority + liveness** (auto-merge intentionally still OFF):
- `.github/workflows/gate.yml`: runs `verify_matrix.py` on every PR to main, independently of the
  local machine that proposed the change — moving go/no-go authority off the proposer (P4 at the
  infrastructure level). Set as a required status check to make a red gate block merge. Auto-merge is
  deliberately NOT enabled yet: per EVOLUTION.md/red-team, it waits for Stage A's root fix
  (machine-readable mirror block + cross-model audit) so the gate is a fact-gate, not a format-gate.
- `.github/workflows/heartbeat.yml`: on the 5th monthly, if no refresh commit touched the matrix
  that month (e.g. the local machine was off), opens an issue so the missed run is visible (P6).

Remaining: Stage A root fix (mirror block + cross-model audit) → then Stage C auto-merge (tiered) →
Stage D meta-loop. Ordering preserved: trust the gate before removing the human.

## [0.6.0] — 2026-06-01

Toward the full closed loop — implementing the EVOLUTION.md stages in dependency order. This ships
**Stage A (core)** + **Stage B**.

**Stage A — make the gate a fact-gate (mechanize P2-violated clauses):**
- `verify_matrix.py` now enforces **C7** (a shard with >40% of lines changed = rewrite, not
  incremental → BLOCK, route to human) and **C4** (removing a source row requires a death-code
  D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED in the CHANGELOG or an Avoid(dead) line → else BLOCK).
  These were previously enforced only by LLM intention; now they are mechanism. Verified: a deletion
  without a death-code is blocked; clean state passes.

**Stage B — close the measurement loop (add the sensor):**
- `tools/emit_metrics.py` (deterministic, no LLM/network) appends a per-refresh quality snapshot to
  `metrics/history.jsonl` — per-domain source counts, free/④ route share, last_verified.
- `tools/check_drift.py` reads the series and flags **slow degradation** via cross-period operators
  (source-count crash, ≥3-period stagnation, monotonic decline, free-route erosion over the horizon)
  — the rot a single run always looks fine for.
- `SKILL.md` Step 5: at the end of a real research run, append live-run verdicts (source
  verified/dead/price_mismatch/fallback + user corrections) to `metrics/live-runs.jsonl`. The refresh
  reads these to prioritise re-verification and auto-nominate repeatedly-dead sources for C4 deletion.
- Refresh script wired to emit metrics + run drift check (surfaced in the Discord digest) each run.

Remaining (per EVOLUTION.md): Stage A root fix (machine-readable mirror block for full BLOCK-level
repo existence + cross-model audit gate) · Stage C (CI required-check + tiered auto-merge) · Stage D
(self-improving meta-loop). Order preserved: sense and trust the gate before removing the human.

## [0.5.1] — 2026-06-01

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
  staged path to a full closed loop — A: fact-gate + cross-model audit · B: feedback sensor
  (live-run telemetry + drift metrics) · C: CI-as-required-check + tiered auto-merge + safety nets ·
  D: self-improving meta-loop with an immutable core. Names the v0.5.1 slug-net as an interim patch;
  the framing fix (machine-readable mirror block) is Stage A.

## [0.5.0] — 2026-06-01

**Horizon scan** — the refresh now evolves the matrix's *scope*, not just its *content*. Beyond
finding better tools within the existing 13 domains (Discovery phase), it actively looks for NEW
territories, tool categories, and research angles the current map doesn't cover — applying
PHILOSOPHY.md P1 (fix/expand the framing) to the skill's own scope so it keeps pace with the field.

- New **Horizon scan** section in `refresh-protocol.md`: H1 what-to-scan (this-month events / new
  platforms / new tool categories / novel research methodologies — cross-domain, trend-level), H2
  fold-vs-new-domain-vs-new-skill decision gate, H3 anti-bloat guardrail (new ≠ needs-a-domain;
  watchlist must recur across ≥2 scans; passes the generative test), H4 proposal output.
- Runs on every full sweep (Jan/Apr/Jul/Oct) + a light monthly "this-month pulse"; structural
  additions (new domain / sub-skill) are proposal-only and always go to human review — never
  auto-created. Constrains P1 with P3: scope grows when justified, bloat is treated as decay.
- Refresh script + Procedure wired to run Horizon scan first.

## [0.4.0] — 2026-06-01

Crystallized the **design philosophy** as the project's organizing principle, made concrete and
prominent — *root-cause design, not incremental patching.*

- **`PHILOSOPHY.md`** (bilingual): 6 principles — fix-the-framing-not-the-symptom · mechanisms-not-
  intentions · monotonic-evolution-against-decay · facts-over-recall · delegate-depth-own-the-seam ·
  honest-boundaries. Each stated as patch-vs-root with the real decision in this repo it produced,
  plus a generative test every future change must pass ("does it fix the framing, or just patch a
  symptom?"). The philosophy explicitly outranks any individual feature.
- Surfaced it prominently at the **top of both READMEs** (before Install), reframed `CONSTITUTION.md`
  as the embodiment of principle P2, and added a governing one-liner to `SKILL.md`.

## [0.3.0] — 2026-06-01

Self-evolution / anti-regression machinery — designed by a 5-subagent co-design pass, ensuring
automated refreshes **monotonically improve** (never silently degrade). "LLM proposes, a
deterministic gate disposes; bad updates never reach main."

- **`CONSTITUTION.md`**: 10 immutable clauses (C1–C10) injected as hard constraints into every
  headless run — API-verified facts, free/④ route preference, deletion-needs-evidence, incremental
  edits, time-monotonic, bad-updates-never-reach-main. Automation may not edit it.
- **`tools/verify_matrix.py`**: deterministic anti-regression gate (pure stdlib + `gh`/`git`).
  Checks STRUCT (index↔shards), REPO (every github repo exists via `gh api`, fail-closed), STAR
  (annotation within 25% of real), FRESH (no future/backward `last_verified`), METH (methodology
  markers intact), COVER (no >10% global / >30% per-shard source-row drop vs main), CONST
  (constitution unmodified). Verified: blocks hallucinated repos + star lies; current matrix passes
  (28 repos checked). Final veto over landing — an LLM can only make it more conservative.
- **`tools/deploy_skill.sh`**: syncs repo→live skill only after a merged, gate-green main.
- **Refresh script rewired to branch + gate + PR** (no direct main push): works on `refresh/<date>`,
  injects the constitution, scope-guards against out-of-bounds edits, runs the gate, opens a PR on
  pass / discards on fail, and notifies via Discord either way.
- **`refresh-protocol.md`**: added the 防退化协议 (mandatory) section codifying the above.

## [0.2.0] — 2026-06-01

Elevated the **browser-automation / act-like-human route (④)** from last-resort footnote to a
first-class option preferred over paid APIs when it fits — leveraging the already-connected
playwright MCP plus free open-source repos that access sites with a real logged-in browser (often
richer data than stripped/paid APIs, at zero cost).

- New domain shard `browser-automation.md`: general AI-browser frameworks (browser-use 96k★,
  stagehand 23k★, skyvern 22k★, crawl4ai 67k★, crawlee 24k★, scrapegraph-ai 27k★) + anti-detection
  (nodriver, camoufox, steel-browser). All stars verified via GitHub API 2026-06-01.
- Added per-platform free OSS repos to shards: x-twitter (twikit + mcp-twikit), social-publishing
  (instagrapi, linkedin-mcp-server, TikTok-Api, xiaohongshu-mcp 14k★, MediaCrawler 50k★, atproto,
  Mastodon.py), ecommerce (Discount-Bandit = self-built Keepa, amazon-scraper), seo-keywords
  (searxng 31k★, serpbear, ddgs), leadgen-crm (gosom/google-maps-scraper — low-risk B2B leads),
  trends-discovery (trendspyg, google-play/app-store-scraper), reddit-community (MediaCrawler, yt-dlp).
- SKILL.md source-selection now prefers route ④ over paid APIs where it fits; routes ①/② reserved
  for un-backfillable history, scale reliability, or compliance.
- Noted limits: browser route can't backfill historical price/BSR (Keepa still needed); needs
  session/cookies + proxies at scale; most platform scraping violates ToS (use throwaway accounts).
- Removed dead repos: tomquirk/linkedin-api (404), pytrends (archived), snscrape (停更),
  elizaOS/agent-twitter-client (下架).

## [0.1.0] — 2026-06-01

Initial release. Source matrix built from a 12-subagent commercial-tool survey (last_verified
2026-05) and hardened by a 5-subagent adversarial design review.

- 12 domain shards: x-twitter, reddit-community, web-scraping, ecommerce-arbitrage, finance-markets,
  crypto-defi, seo-keywords, social-publishing, content-cms, leadgen-crm, trends-discovery,
  ready-skills.
- Thin source index, isolated volatile pricing/install file, report template, refresh protocol.
- 8 quality guardrails baked into SKILL.md.
