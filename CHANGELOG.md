# Changelog

All notable changes to the source matrix and skill are recorded here. Each refresh sweep appends a
dated entry with per-domain added/removed/changed tools.

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
