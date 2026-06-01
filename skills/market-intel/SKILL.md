---
name: market-intel
description: >-
  Use when a research request needs specialized COMMERCIAL data sources — X/Twitter,
  e-commerce pricing, finance/markets, crypto, SEO/keywords, social media, news sentiment,
  lead-gen — and benefits from picking the right MCP source (and installing it if missing)
  before investigating. Triggers on market research, competitor analysis, product/selling
  research, arbitrage scouting, social/X sentiment, SEO intel, trend discovery. NOT for
  single-fact lookups or general web reports (use deep-research) or academic literature
  (use research-lit).
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill, WebSearch, WebFetch
---

# market-intel

A thin orchestration layer for commercial/market research. It does **only three things that
nothing else does**: (1) triage a commercial topic to the right data domains, (2) detect which
specialized MCP sources are actually connected and guide installing missing ones, (3) enforce
research quality guardrails. The heavy lifting — fan-out search, fetching, adversarial
verification, citation synthesis — is **delegated** to the existing `deep-research` harness or
`research-lit` skill. Do not re-implement those.

> **Design philosophy (governs all changes): root-cause design, not incremental patching** — change
> the assumption underneath a problem, not the symptom on top. This thin-delegation shape, the
> first-class browser route, and the monotonic anti-regression refresh all follow from it. Full
> statement in the repo's `PHILOSOPHY.md`; every change must pass "does it fix the framing, or just
> patch a symptom?"

## When to stop and delegate immediately

Before doing anything, decide if this skill even applies:

- **Single-fact lookup / quick query** → just use plain web search. Do not invoke this workflow.
- **General web-only deep report** (no specialized commercial source needed) → delegate to
  `deep-research` and exit.
- **Academic / scientific literature** → delegate to `research-lit` and exit.
- **Needs a specialized commercial source** (X data, real e-commerce prices, market/finance
  feeds, on-chain data, SEO metrics, social sentiment, lead data) → continue below. This is the
  only case where this skill earns its keep.

## Workflow

### Step 1 — Triage

Identify which commercial domain(s) the topic touches. Read `reference/sources-index.md` (a thin
one-line-per-domain index, ~12 lines). Match the topic to 1–N domains. **Do not read the full
domain shards yet.** If the topic maps to zero commercial domains, delegate per the section above.

Pick a depth budget and hold to its hard caps:

| depth | max subagents | max rounds | max verifiers | use when |
|---|---|---|---|---|
| quick | 3 | 1 | 1 | scoped question, one domain |
| standard (default) | 6 | 2 | 3 | typical multi-angle research |
| deep | 12 | 3 | 5 | explicit "comprehensive / thorough / 全面" |

When unsure, default to `standard`. Maintain a running count; **when a cap is hit, stop fanning
out and move to synthesis.** Never let "comprehensive" mean unbounded.

### Step 2 — Detect available sources (do NOT guess by tool name)

Run `claude mcp list` and parse the three-state health output — a source is only usable if it
shows `✓ Connected`. Treat `✗ Failed` and `! Needs authentication` as **not available** (they
will fail at call time). Tool-name prefix matching (`mcp__*twitter*`) is unreliable: deferred
tools, plugin prefixes, and dead connections all distort it — use it only as a cross-check, never
as the primary signal. Also note which research skills exist (`research-lit`, `deep-research`,
`exa-search`, `firecrawl`) as fallbacks.

If you must parse `~/.claude.json` directly, read it as UTF-8 (it contains non-ASCII paths;
default GBK decode crashes on Windows). Prefer `claude mcp list` / `claude mcp get` over raw JSON.

### Step 3 — Select sources + guide install (non-blocking)

For each triaged domain, read only its shard: `reference/domains/<domain>.md`. Pick the best
**available** source. **Prefer the free browser-automation / act-like-human route (④) over paid
APIs when it fits** — you already have the playwright MCP connected, plus free open-source repos
per platform (see `reference/domains/browser-automation.md`). A real logged-in browser often
returns **richer data** than a stripped/paid API, at zero cost. Reach for paid official ① / resale
② sources when you need history the browser can't backfill (e.g. Keepa price history), large-scale
reliability, or compliance (no ToS/ban risk). Note browser scraping needs a session/cookies and,
at scale, a proxy pool, and most platform scraping violates that platform's ToS — use throwaway
accounts for heavy/write work and respect the disconfirmation + source-tier guardrails.

If the topic clearly depends on a source that is missing or not connected:

> "This topic depends on <source> (e.g. real X tweet data). Recommend installing it:
> `claude mcp add -s user <...>` (exact command + cost in `reference/volatile/pricing-install.md`).
> **Note: a newly added MCP only takes effect after you restart the session or `/mcp` reconnect —
> it will NOT work this turn.** For now I'll proceed with a fallback source and flag the gap."

Never block on install. Never fill in or echo the user's API key — have the user run the
`-e KEY=$VAR` injection themselves; `~/.claude.json` stores keys in plaintext, so warn them not to
commit/screenshot it. Prefer HTTP-transport sources on Windows (no local Node needed).

### Step 4 — Delegate execution

Hand the selected sources + sub-questions to the heavy harness:

- Mixed/general or when a connected commercial MCP exists → fan out subagents (Agent tool), one
  per sub-question, **each told to load its target MCP via ToolSearch first** (subagents inherit
  the session's MCPs but only in deferred form). Or invoke `deep-research` for the web portion.
- For source-routed retrieval, `research-lit`'s `— sources:` mechanism already does
  detect-or-skip routing; reuse it rather than rewriting fan-out.

Require every subagent to return a **structured evidence unit**, not free prose:
`{ status: ok|partial|empty|failed, claims: [{claim, source_url, quote, source_tier, date, confidence}], coverage_notes }`
with a length cap per field. The main agent reduces these units — it does **not** read raw page
dumps. If fan-out exceeds ~5, insert a combiner layer (each combiner merges 3–4 workers) so the
main context never holds N long reports.

## Quality guardrails (HARD rules — apply during synthesis)

1. **Citation verification gate.** Before a number/claim enters the report, an independent
   verifier must actually fetch the cited URL and confirm the page contains that value (verbatim
   quote). Mark each `✓verified / ⚠unverifiable / ✗dead`. Drop `✗dead`; demote quote-less numbers
   to "unverified." A plausible URL is not a verified source.
2. **≥2 independent sources for decision-grade claims.** "Independent" = not syndicated from the
   same origin. Label confidence: high = ≥2 independent L1/L2 sources + verified; medium = 2
   sources incl. secondary, or 1 primary; low = single/secondary/unverified.
3. **Source tiers.** Tag every source L1 first-party/official · L2 independent third-party ·
   L3 interested party (vendor/marketing) · L4 UGC/anonymous · L5 fallback web / model inference.
   Vendor self-claims (L3) cannot be the sole support for a performance/profit claim.
4. **No silent degradation.** When a barrier source (X, real prices, social) is unavailable and
   you fall back to web, the relevant section must say so: "⚠ intended source unavailable, based
   on [L?] fallback, reliability reduced." Never swap silently.
5. **Timestamp volatile data.** Every price/policy/ranking/rate carries `[fetched YYYY-MM-DD |
   published ____]`. Missing publish date → mark "date unknown, treat as stale." Never present an
   undated precise figure. State a snapshot date at the report top.
6. **Disconfirmation mandate (esp. arbitrage/investing).** Run a dedicated reverse-search subagent
   (terms: scam/failure/loss/banned/expired/risk/regulation). Report must include a "Risks &
   counter-evidence" section and, for arbitrage, "execution friction" (fees, slippage, capacity,
   time window, compliance). Empty → "actively reverse-searched, none found — not proof of no risk."
7. **Surface conflicts, don't average them.** When sources disagree, present a disagreement matrix
   (source A says X vs source B says Y, likely cause, which side and why) — do not silently pick or
   average. Mark each key claim `confirmed / disputed / unresolved`.
8. **Failures become explicit gaps.** Any subagent that returns `failed/empty` triggers one query
   rewrite + retry; if still empty, list it in an explicit "Not covered / insufficient data"
   section. A report must never look complete while hiding a missing dimension.

## Output

Synthesize per `reference/report-template.md`: snapshot date, executive summary, per-domain
findings with tiered+dated+confidence-tagged claims, cross-verification verdicts, disagreement
matrix, risks & counter-evidence, explicit coverage gaps + "configure source X for deeper data",
full source list.

## Close the feedback loop (Step 5 — write what you observed)

The refresh mechanism is open-loop unless real usage feeds back. So at the end of a real research
run, append one line per source you actually touched to the repo's `metrics/live-runs.jsonl` (this
reuses verdicts the guardrails above already produced — near-zero extra cost). This is the highest-
value error signal: it tells the next refresh which matrix entries the real world just proved
right or wrong.

```jsonc
{ "ts":"<UTC>", "domain":"x-twitter", "source":"d60/twikit", "route":"④",
  "outcome":"verified|unverifiable|dead|fallback_used|price_mismatch",
  "detail":"<what diverged, e.g. official price now $X vs shard $Y>",
  "user_correction": null }   // set when the user manually corrected an entry — highest-weight truth
```

If you can't write the file (e.g. the repo isn't checked out), note the observations in your reply
so they aren't lost. The refresh then reads these to prioritise which domains/sources to re-verify
first (a source flagged `dead` in real use gets auto-nominated for the C4 deletion path next sweep).

## Progressive loading rules

- SKILL.md (this file) is always loaded — keep it the only frequently-loaded content.
- Read `reference/sources-index.md` at triage (thin).
- Read `reference/domains/<domain>.md` only for triaged domains. **Never read the whole domains/
  directory.**
- Read `reference/volatile/pricing-install.md` only when actually guiding an install — prices and
  commands there are time-stamped and may be stale; verify against the official site before use.

## Maintenance

The source matrix decays. When asked to "refresh the market-intel source matrix / 刷新工具库", or on
a scheduled sweep, follow `reference/refresh-protocol.md`: fan out one subagent per domain to find
new/changed/dead tools since each shard's `last_verified`, apply the same quality guardrails, edit
shards incrementally, record the diff in `CHANGELOG.md`, and bump the plugin version.
