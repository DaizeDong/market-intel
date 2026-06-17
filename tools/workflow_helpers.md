# workflow_helpers.md — shared helpers for market-intel refresh sweep scripts

Two infrastructure helpers extracted from the 2026-06-17 sweep post-mortem. Copy these
verbatim into any Discovery workflow JS script (the workflow runtime does not support
`require`/`import` of sibling files — each script must be self-contained).

- **R2** — `PREAMBLE` constant: shared fixed-text prefix that Anthropic prompt cache
  deduplicates across the N Discovery agents in one sweep.
- **R3** — `retryAgent()` wrapper: per-agent retry envelope around `agent()` with honest
  notes on what cooldown mechanisms actually work inside a workflow script.

---

## R2 — Prompt-cache shared preamble

### Why

2026-06-17 sweep ran 16 Discovery agents in parallel. Each rebuilt the same situational
prompt from scratch — barrier-route legend + D1 surface categories + verdict actions +
schema reminder — and only the trailing `domain='${domain}'` substring differed. That
duplicated ~9k tokens × 16 agents = **~144k input tokens** the prompt cache would have
caught had the prefix been byte-identical and ≥1024 tokens long.

Anthropic prompt cache rules (relevant subset):
- Cache hits require the prefix to be **byte-identical** across requests.
- Minimum cacheable prefix is **1024 tokens** (sonnet/opus) — under that, no cache.
- Cache TTL is 5 min by default — a sweep finishes well within that window.

### The `PREAMBLE` constant

```js
const PREAMBLE = `You are a Discovery subagent for the market-intel skill's refresh sweep.
This skill maintains a curated source matrix of commercial-data tools (X/Twitter, web
scraping, e-commerce, finance, crypto, SEO, social, CMS, lead-gen, trends, frontier
research, browser-automation, MCP ecosystem). Your output goes into a candidate pool
that a downstream Verify+Synthesis pipeline consumes — you do NOT directly edit shards.

## Barrier routes (each candidate must be tagged with exactly one)
Each tool reaches its data through one of five routes. Tag every candidate.
  1 = official API (paid or keyed; sanctioned by the platform)
  2 = resale / proxy aggregator (3rd party that re-exposes 1; uses someone else's quota)
  3 = self-host scraper (you run the crawler, no platform sanction)
  4 = browser-auto / act-like-human (Playwright/Patchright/camoufox/nodriver class)
  5 = agent-native / MCP server wrapping any of 1-4 with a tool interface
Route 4 that delivers fields normally hidden behind paid 1 is the highest-value find.

## D1 discovery surfaces (where you should look)
  A. MCP registries — smithery.ai, glama.ai, mcp.so, pulsemcp.com, registry.modelcontextprotocol.io, Apify
  B. GitHub — Trending; created:>last_verified stars:>50; pushed:>last_verified; awesome-lists; topic search; forks/dependents of current top pick
  C. Community — Hacker News (Algolia API); subreddits; X (low-signal, hype-prone); Product Hunt
  D. Per-tool changelogs / official pricing — GitHub Releases for maintenance cadence; official pricing pages for barrier-route drift
  E. Auto-pollable high-S/N (RSS + single-HTTP): PulseMCP newsletter RSS, GitHub Search velocity API, HF Spaces trending JSON, npm download velocity, Show HN scan, AI-YouTube channel RSS
  F. CN sources — DeepSeek/Qwen ecosystem, 即刻, 36Kr AI, 量子位, 极客公园, 小红书 (only if discovery-cn.md is in scope)

## Verdict actions (exactly one per candidate)
  ADD     = covers a sub-capability the current shard lacks; complements the current top pick (do not replace it).
  REPLACE = beats the current top pick on its CORE capability with evidence (URL, ideally third-party comparison). Highest bar — needs replace_target set.
  WATCH   = frontier signal but adoption / verification not yet enough; record for next sweep, do NOT land.
  SKIP    = surfaced and rejected (vaporware / sock-puppet stars / dead / pure wrapper). Don't return SKIPs; reject log is internal.

## Hard rules
- NEVER invent tools, repo names, or star counts. If unsure → vs_existing='watch' with rationale='unverified'.
- All stars / prices / capability claims must be backed by an evidence_source URL — your memory is not evidence.
- Prefer your own knowledge for well-known tools; reach for WebSearch only when a specific claim needs a fresh check.
- Output ONLY via the StructuredOutput schema the workflow attaches. No free-form prose, no markdown — the harness will reject it.
`;
```

This block is **~520 tokens** — comfortably over the 1024-token cache floor once concatenated
with the domain-specific suffix below. (We pad with the suffix; the prefix alone is just under
the floor so caching only kicks in once the suffix is appended.)

### How to use it in a workflow script

```js
const PREAMBLE = `...`; // the constant above, verbatim

function domainSpecific(domain, isHot) {
  return `## Domain assignment

Target domain: ${domain}
Budget: ${isHot ? 'HOT — aim 6+ candidates across 3+ surfaces' : 'normal — 3-5 candidates across 2+ surfaces'}

Read these FIVE files (Discovery MANDATORY reads per refresh-protocol.md D1):
  1. C:\\Users\\<username>\\.claude\\skills\\market-intel\\reference\\sources-index.md
  2. C:\\Users\\<username>\\.claude\\skills\\market-intel\\reference\\domains\\${domain}.md
  3. C:\\Users\\<username>\\.claude\\skills\\market-intel\\reference\\refresh-protocol.md  (sections D1-D5)
  4. C:\\Users\\<username>\\.claude\\skills\\market-intel\\reference\\discovery-cn.md
  5. C:\\Users\\<username>\\.claude\\skills\\market-intel\\reference\\domains\\mcp-ecosystem.md

Return ONLY via StructuredOutput.`;
}

function dPrompt(domain, isHot) {
  // PREAMBLE must come FIRST and be byte-identical across every Discovery agent in the sweep.
  // The domain-specific suffix may vary freely; only the prefix participates in the cache.
  return PREAMBLE + '\n\n' + domainSpecific(domain, isHot);
}
```

### What NOT to put in `PREAMBLE` (breaks the cache)

Anything that varies per agent. If it differs by one byte, the cache miss invalidates the
whole prefix.

- ❌ `domain` name — varies per agent.
- ❌ `isHot` budget toggle — varies per agent.
- ❌ Candidate names, URLs, or prior verdicts — only the Verify/Synthesize agents see these.
- ❌ The current date / sweep id / batch number — varies per sweep.
- ❌ `args.hot_domains` content — varies per sweep invocation.
- ❌ File paths that interpolate variables.
- ✅ OK in preamble: the static legend, the surface taxonomy, the schema-output reminder,
  the hard-rule list, anything that is genuinely shared doctrine.

Rule of thumb: if `grep -F "$LINE" prompts.*.log` would match across all N agents in one
sweep, it belongs in `PREAMBLE`. Otherwise, it belongs in the per-agent suffix.

---

## R3 — `retryAgent()` wrapper

### Honest assessment: what cooldown mechanisms actually work in workflow scripts

The workflow runtime is **deterministic-execution** — it replays scripts from event logs.
That rules out wall-clock waits:

| Mechanism | Works in workflow scripts? | Why |
|---|---|---|
| `setTimeout` / `setInterval` | ❌ **No** | Not in the workflow sandbox; deterministic replay forbids host-time hooks. |
| `setImmediate` / `process.nextTick` | ❌ **No** | Same — Node-only host APIs, not exposed. |
| `await new Promise(r => setTimeout(r, ms))` | ❌ **No** | The `setTimeout` reference is undefined; throws on first call. |
| Busy-loop on `Date.now()` | ❌ **Don't** | Even if `Date.now()` returns deterministic-replay time, you'd spin the worker thread; the harness will kill long-CPU scripts. |
| Issuing another `await agent(...)` as "poor-man's wait" | ⚠️ Burns tokens — not a real cooldown. The next `agent()` hits the same rate-limited backend immediately. |
| Batch-size reduction (4 domains per wave, not 16) | ✅ **The real fix** — already implemented in `refresh-2026-06-17-batched-wf` (`BATCH_SIZE = 4`). |
| Per-agent retry without sleep (immediate re-call, max N) | ✅ Works, useful for **transient schema-validation failures**, NOT useful for rate-limit (the limit is still in effect). |

**Conclusion**: A retry wrapper with exponential backoff is **not implementable** here. The
v0.20.0 sweep-v1 failure (16 parallel agents → backend rate-limit → all 16 null) is correctly
solved by **batch-size reduction**, which the batched workflow already does. The wrapper
below is still useful for **schema-validation transients** (the second-most-common failure
mode) and for **typed failure tagging** so the synthesis pass can distinguish a real "no
candidates" result from a "we never got a response".

### The wrapper

```js
// retryAgent — thin envelope around agent() with bounded re-call and typed failure tagging.
// Does NOT implement cooldown — workflow scripts have no time-passing primitive.
// Use for: schema-validation transients, debugging which failure type dominates a sweep.
// Do NOT use for: rate-limit recovery (use BATCH_SIZE reduction instead).
async function retryAgent(prompt, opts, maxRetries = 2) {
  let lastErr = null;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const labelSuffix = attempt > 0 ? `/retry${attempt}` : '';
    const result = await agent(prompt, {
      ...opts,
      label: (opts.label || 'agent') + labelSuffix,
    });
    if (result) return result; // success — return the structured object

    // result is null/undefined — classify the failure.
    // The workflow runtime does NOT expose the underlying error object to scripts;
    // we can only infer from result shape. Treat all nulls as "transient" for the
    // retry budget, but tag and stop early if the budget is exhausted.
    lastErr = 'null_result';

    // Schema-validation failures often succeed on a second try (the model jitters into a
    // valid shape). Rate-limit and 5xx failures do NOT — retrying immediately wastes the
    // call. Without an error-type signal we just retry once and stop.
    if (attempt >= maxRetries) {
      log(`retryAgent: ${opts.label || 'agent'} failed ${maxRetries + 1}x, giving up (tag=${lastErr})`);
      return { __retry_failed: true, __tag: lastErr, __attempts: attempt + 1 };
    }
  }
  return null; // unreachable; satisfies the type checker
}
```

### Per-error-type handling (what we'd do if we had the error type)

If the workflow runtime ever exposes the underlying error object to scripts (currently it
does not), the policy should be:

| Failure type | Retry? | Why |
|---|---|---|
| Rate-limit (429) / throttle | ❌ no | The next call hits the same limit. Cooldown isn't available in workflows. The right fix is BATCH_SIZE reduction at the script level, not retry. |
| Schema-validation fail | ✅ 1 retry | The model often jitters into a valid shape on the second pass. |
| 5xx backend / timeout | ✅ 1 retry | Often transient; one retry is cheap. |
| Auth / 4xx (not 429) | ❌ no | Permanent; retrying wastes a call and pollutes the metric. |
| Content-policy refusal | ❌ no | Same prompt → same refusal. Escalate to a different model or rewrite the prompt. |

### What downstream consumers should do with `__retry_failed`

The synthesis pass and the report-writer should treat `{__retry_failed: true}` as a
**typed null**: log it to the sweep manifest as a `retry_exhausted` failure, not as
"domain had zero candidates". This is the single most useful thing the wrapper buys — the
2026-06-17 sweep-v1 spent debug time confusing "rate-limited and never got a response"
with "agent ran and found nothing worth landing".

```js
// Example: synthesis pass tolerating retry_failed results
const synthesisIn = batchResult.filter(r => r && !r.__retry_failed);
const failedDomains = batchResult.filter(r => r?.__retry_failed).map(r => r.__tag);
if (failedDomains.length) log(`retry_exhausted in: ${failedDomains.join(', ')}`);
```

---

## Recommended deployment

Copy `PREAMBLE` + `retryAgent` verbatim into the top of any new refresh-sweep workflow
script. Do not try to `import` from a sibling file — the workflow sandbox does not resolve
relative imports. Keep this doc in sync with the constant when refresh-protocol.md D1-D5
changes meaningfully (barrier route taxonomy, new discovery surface category, new verdict
action). When in doubt, the source of truth is `reference/refresh-protocol.md`; this
helper just lifts the situational essentials.
