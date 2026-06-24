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

> **Recurring / digest use:** this skill is one-shot by design. To watch a topic over time, wrap it
> in a user-owned `/schedule` routine (or `/loop`) — the routine owns cadence, watchlist, and
> delivery (`~/.claude/discord_relay/send.py` / the `feishu-notify` skill); market-intel just runs
> its normal workflow on each fire and emits its standard report. Do **not** build
> monitoring/distribution *into* the skill — that's an orchestration-product job, not the seam this
> skill owns (`PHILOSOPHY.md` P5).

## Workflow

### Step 1 — Triage

Identify which commercial domain(s) the topic touches. Read `reference/sources-index.md` (a thin
one-line-per-domain index, ~12 lines). Match the topic to 1–N of the **real** domains. **Do not
read the full domain shards yet.** If the topic maps to zero commercial domains, delegate per the
section above.

**Skip meta-domains during triage.** `sources-index.md` lists "Meta-domains" (currently:
`mcp-ecosystem`) — these are infrastructure shards consumed by the refresh sweep's Discovery phase
only. NEVER route a user research query to them. If a topic's only match is a meta-domain, the
topic is not in market-intel's scope (route to plain web search instead).

**Pick an invocation SCALE explicitly.** The single biggest failure mode here is
**under-calling** — too few tools, too few query angles → incomplete intel. The user may name
a tier or give numbers; **when in doubt for any genuine research ask, default to `deep`, not
`standard`** (reserve `standard`/`scan` for quick scoped checks).

| scale | domains | tools / domain | query angles / tool | stop condition |
|---|---|---|---|---|
| `scan` | 1 top | 1 top tool | 1 | fixed |
| `standard` | routed | 2–3 | 2 | fixed |
| `deep` (default for research / "comprehensive / 全面") | all relevant | **ALL available in domain** | 3+ | cross-checked to ≥2 independent sources |
| `exhaustive` | all relevant | **ALL available, no omission** | multi-angle until saturated | **SATURATION** — stop only when newly-called tools add no new facts |

Numeric override (user may specify directly): `scale = {domains: all|N, tools_per_domain: all|N,
queries_per_tool: M, stop: saturate|fixed}`.

**Three iron rules (`deep` & `exhaustive`):**
1. **No sampling.** Every *available* tool in a routed domain MUST be called — never a subset.
   A tool you cannot reach (cold MCP / missing key) is an **explicit gap** in the report, never
   a silent skip. (This is the "失败 = 显式 gap" guardrail applied to coverage.)
2. **Saturate, don't fixed-stop.** At `exhaustive`, keep fanning out across domains/tools until
   additional calls yield no new facts. "Comprehensive" means coverage-saturated — not "I hit N
   subagents." Use the combiner layer (Step 5) so wide fan-out doesn't blow context.
3. **Report coverage.** Every run states `tools invoked / tools available in scope` (per domain
   + total) and lists uncovered tools — so "comprehensive" is **verifiable, not asserted**.

**Absolute ceiling (cost guard, NOT a low default):** a hard cap of ~40 tool-calls / ~6 rounds
per run prevents true runaway (P5: no *infinite* fan-out). If `exhaustive` would exceed it,
surface the projected scope + the uncovered remainder as an **explicit gap** — never silently
truncate. Raising the ceiling is a deliberate, stated choice, not a default.

### Step 2 — Detect available sources (do NOT guess by tool name)

Run `claude mcp list` and parse the three-state health output — a source is only usable if it
shows `✓ Connected`. Treat `✗ Failed` and `! Needs authentication` as **not available** (they
will fail at call time). Tool-name prefix matching (`mcp__*twitter*`) is unreliable: deferred
tools, plugin prefixes, and dead connections all distort it — use it only as a cross-check, never
as the primary signal. Also note which research skills exist (`research-lit`, `deep-research`,
`exa-search`, `firecrawl`) as fallbacks.

If you must parse `~/.claude.json` directly, read it as UTF-8 (it contains non-ASCII paths;
default GBK decode crashes on Windows). Prefer `claude mcp list` / `claude mcp get` over raw JSON.

#### Step 2b — Task-time availability gate (classify each relevant tool AT THIS MOMENT)

Detection isn't a yes/no list — it's a per-tool **state** decided *now*, for *this theme's*
routed tools only. Using query-side signals only (`claude mcp list` + companion-config presence —
**never** import a refresh/ops script; that breaks the P5 seam), sort each relevant tool into one
of three buckets:

| bucket | query-side signal (this moment) | what the run does with it |
|---|---|---|
| **available-now** | `claude mcp list` shows `✓ Connected`, **or** keyless/no-auth (GDELT, CoinGecko, SEC EDGAR), **or** a local lib already installed, **or** companion `registry.json` marks it `installed:true` + a matching `mcp_server_name` is Connected | fan out to it at the chosen SCALE (Step 4) |
| **configurable-with-setup** | not connected now, but a free/cheap activation path exists — companion repo has the tool but it's not applied, or `activation-recipes.md` lists a free-key/free-tier/install-no-key recipe for its slug | **do NOT call it this turn** (a fresh MCP only connects after `/mcp` restart). Surface a JIT, theme-tied config suggestion in the report (Step 4 + Coverage-gaps) |
| **hard-gap** | only a paid/enterprise tier unlocks it, or it's tombstoned (`D-404`/`D-PRICE`/`D-TOS`/dead repo per the shard / companion `deprecation_code`) | note as an explicit gap; suggest only if the theme genuinely needs the paid depth, flagged as paid |

This is **warn-level guidance, never a fail-closed gate** (Side A/B/C): the classifier informs
fan-out and what to recommend — it never refuses to run or silently drops a relevant tool. A tool
you can't reach right now is always an **explicit gap**, never a silent skip (iron rule 1). The
companion `registry.json` (`installed`, `tier`, `transport`, `mcp_server_name`, `health_last`) is
the authoritative "what the user has" read here; `claude mcp list` is the authoritative "what is
live right now." When they disagree, live state wins for *can-I-call-it-now*, and the registry tier
informs *is-it-free-to-activate*.

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

Never block on install. Prefer HTTP-transport sources on Windows (no local Node/uv needed; stdio
`npx`/`uvx` MCPs are flaky there).

#### Secret-handling hygiene — HARD rules (learned the hard way; real runs leaked keys 3×)
Configuring the tool yourself is fine and often expected — but a key must **never leak into the
transcript** (it may sync to the user's cloud backup). Follow exactly:
- **NEVER `browser_snapshot` a page that displays a key.** Provider dashboards and post-rotation
  pages render the API key in **plaintext in the DOM** → the snapshot captures it. (Confirmed on
  twitterapi.io rotation page AND Bright Data's API-keys table.) Instead: have the user click the
  page's **copy button**, then read the OS clipboard (`powershell Get-Clipboard`) and pipe it;
  verify by **length only**, never print the value.
- **For secret-bearing MCPs, do NOT use `claude mcp add`** — it **echoes the `--header`/URL (with
  the key) to stdout**. Edit `~/.claude.json` directly: a tiny python script reads the clipboard and
  writes `mcpServers.<name>.headers.Authorization` (or the token-in-URL), with no echo.
- **Mask tokens when verifying**: token-in-URL servers print the token in `claude mcp list` → pipe
  through `sed -E 's/token=[^ &]*/token=***/'`.
- **Rotation cooldowns**: if a key leaks, rotate it — but check the provider's cooldown (e.g.
  twitterapi.io = once/24h). A truly transcript-clean key = the **user** rotates from their own
  browser, not the agent.
- Keys land plaintext in `~/.claude.json` — never commit/screenshot it. **The skill holds the
  procedure, not the key.**

#### Where the user's keys + install state live: the COMPANION CONFIG REPO

The user's per-machine ops state — which MCPs they installed, their per-tool tier, their API
keys, their rotation history — does **not** live in this matrix repo. It belongs in a **separate,
private companion config repo**. This is a hard architectural rule; see
`reference/companion-config-repo.md` for the rationale.

The exchange between this skill and any companion config repo follows a **formal spec**
([`reference/companion-config-spec.md`](reference/companion-config-spec.md), spec version 1).
As an agent, **assume one may exist on the user's machine**, and treat it as the authoritative
source of "what the user has installed." The spec defines: discovery convention, required
directory layout, `registry.json` schema, per-tool template formats, conformance checklist,
and versioning policy.

> 🔒 **When guiding the user to bootstrap a new companion repo, ALWAYS surface the
> hardening runbook ([`reference/companion-config-hardening.md`](reference/companion-config-hardening.md))
> BEFORE the first push.** A freshly-created GitHub repo defaults to "All repositories"
> access for installed GitHub Apps (ChatGPT Codex, Devin.ai, etc.) and account-level
> Copilot training is opt-out, not opt-in. The runbook is a 12-step lockdown that closes
> these by hand; ~15 min the first time. Skipping it means the user's API keys may be
> visible to third-party AI agents and used as future training data the moment the repo
> exists.

**Discovery convention (try in order):**

1. **`$MARKET_INTEL_CONFIG`** env var — explicit path, highest priority and the recommended way.
2. **`~/.market-intel-config/`** — dotfile-in-home fallback (works on all OSes).
3. **`~/.config/market-intel-config/`** — XDG-style fallback (Linux/macOS).

Each user picks where to place their companion repo and either sets the env var or uses one of
the fallbacks. There is no required filesystem location.

If found, the repo follows the layout defined in
[`reference/companion-config-spec.md`](reference/companion-config-spec.md) §2 — `registry.json`
at root, `tools/<slug>/` per-tool dirs with `claude.json.template` + `env.template`, and
`secrets/<slug>.env` (committed under Mode A, gitignored under Mode B per spec §5.3).
**The spec is the canonical structure reference — don't paraphrase it here.**

**How to use it from this skill (Step 2 detection enhancement):**

1. After running `claude mcp list` (still primary signal), also check whether a companion
   config repo exists at one of the paths above.
2. If yes, read its `registry.json` to learn which tools the user has *configured*, and read
   the specific `tools/<slug>/README.md` only when you need tier/rate-limit context for that
   tool.
3. **Never** read `secrets/<slug>.env` files even when they're committed in the repo (Mode
   A) — reading them spills key values into the transcript regardless of where they're
   stored. apply.py handles substitution into `~/.claude.json`; you never need to look at
   the raw value.
4. When a tool the user would benefit from is NOT in their companion repo, recommend
   adding it using the standard procedure: if the user's companion repo includes
   `runbooks/add-new-tool.md`, follow that (each user authors their own runbooks);
   otherwise summarize the procedure from `reference/companion-config-repo.md` here.

**Rotation triggers:** if a key turns out to have leaked (the user pasted it into chat by
mistake, or you find evidence of unauthorized usage in a dashboard), tell them to:
- Rotate the key at the provider's dashboard.
- Use the companion repo's `scripts/capture-key.ps1 -Slug <slug> -Var <VARNAME>` to refresh
  `secrets/<slug>.env` via clipboard with no echo.
- Re-run `python3 scripts/apply.py --tool <slug>`.
- Restart the Claude session.

**What this skill does NOT need to do:** none of the above is required for the matrix to be
useful. Users without a companion repo just install MCPs ad-hoc via `claude mcp add` and lose
the durable ops state. The companion pattern is the recommended, audit-friendly way; the
skill's flow degrades gracefully when it's absent.

### Step 4 — Delegate execution (to available-now tools only) + JIT-surface the rest

Fan out **only to the `available-now` bucket** from Step 2b, at the chosen SCALE. Do not waste a
subagent on a tool that isn't live this turn — it would just fail. Hand the selected
available-now sources + sub-questions to the heavy harness:

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

#### JIT config-gap surfacing — recommend configuration at task-time, driven by the theme

For every relevant tool that Step 2b put in `configurable-with-setup` (or a theme-critical
`hard-gap`), **do not silently skip it**. Configuration is recommended *at task-time, driven by the
theme* — not pre-done. For each, emit a one-line, **theme-specific** suggestion that names the
concrete thing the missing tool would deepen, the cost class, and the exact activation path. Read
the tool's recipe in `reference/activation-recipes.md` (and its `tools/<slug>.md` only if you need
tier/gotcha detail) to fill the path. Template:

> "To deepen **<this theme aspect>**, configure **<tool>** (<free-key | free-tier | install-no-key
> | paid $X>) — `python tools/console.py connect <slug>` (canonical, resolves by slug), or see
> `reference/activation-recipes.md` for the key source; then `/mcp` reconnect (won't help this turn)."

Examples: an X-sentiment theme with `x-twitter` dark → "configure twikit (install-no-key) to add
real X founder/crypto discourse"; a macro-backdrop theme without FRED → "configure FRED MCP
(free-key) for the rates/CPI series this thesis leans on." These lines feed straight into the
report's **Coverage-gaps → Configure for deeper data** block (Output / `report-template.md`) — so
the gate's output is a concrete, theme-tied next step the user can act on, never a buried omission.

## Quality guardrails (HARD rules — apply during synthesis)

1. **Citation verification gate.** Before a number/claim enters the report, an independent
   verifier must actually fetch the cited URL and confirm the page contains that value (verbatim
   quote). Mark each `✓verified / ⚠unverifiable / ✗dead`. Drop `✗dead`; demote quote-less numbers
   to "unverified." A plausible URL is not a verified source.
2. **≥2 independent sources for decision-grade claims.** "Independent" = not syndicated from the
   same origin — treat byline/wire-service reprints (AP/Reuters/PR-Newswire pickups, identical
   verbatim quotes, the same press release) as **one** source, not several; the corroboration count
   must reflect that merge. Label confidence: high = ≥2 independent L1/L2 sources + verified; medium = 2
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
matrix, risks & counter-evidence, explicit coverage gaps + the Step 2b/Step 4 JIT
"configure source X to deepen <theme aspect>" suggestions (available-now vs
configurable-with-setup vs hard-gap), full source list.

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
- Read `reference/tools/index.md` (thin) to find a picked tool's doc slug; then read
  `reference/tools/<slug>.md` **only for the specific tool you're about to use** — per-tool install +
  auth + usage + 踩坑. **Never read the whole `tools/` directory** (that breaks progressive loading
  — the whole point of per-tool docs is on-demand, one-at-a-time loading). The shard decides *which*
  tool; the tool doc is the *how-to*.
- **Install docs are 3-tiered** (L0 / L1 / L2) — read top-down only when you actually need that
  level of detail:
  - **L0** = `reference/install-guide.md` — universal mechanics (prerequisites, MCP transport
    choice on Windows, secret hygiene, BOM rules, Python install target). Read when bootstrapping
    a fresh machine or onboarding any new tool category.
  - **L1** = `reference/volatile/pricing-install.md` — per-domain, time-stamped exact commands +
    current prices. Read when actually guiding an install for a specific domain. **Prices rot —
    re-verify the live site before quoting.**
  - **L2** = `reference/tools/<slug>.md` (judgment) and optionally `reference/tools/<slug>.auto.md`
    (mechanical, spec §11.1 split). Read for the specific tool you're about to install/use. The
    `.auto.md` sibling, when present, holds install command + auth + pricing snapshot — that's the
    file to consult for "exactly what to type". The bare `<slug>.md` always exists; `.auto.md`
    is opt-in per tool.
  When a user asks "how do I install X", the right read order is **L2 first** (the auto.md if
  present, else slug.md "Install" section), fall back to **L1** for time-stamped exact commands,
  and only reach **L0** if a generic mechanic is unclear (PATH issue, BOM, env target).

## Maintenance

The source matrix decays. When asked to "refresh the market-intel source matrix / 刷新工具库", or on
a scheduled sweep, follow `reference/refresh-protocol.md`: fan out one subagent per domain to find
new/changed/dead tools since each shard's `last_verified`, apply the same quality guardrails, edit
shards incrementally, record the diff in `CHANGELOG.md`, and bump the plugin version.
