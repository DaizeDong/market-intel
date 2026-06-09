# Tool: claude-world/trend-pulse

- **Domain(s):** trends-discovery (also: none)
- **Barrier route:** ① official (free, no auth — self-host) · **Source tier:** L2 · **Ready MCP:** yes — self-host MCP server, no key
- **Cost:** free — no key, no quota, unlimited (you pay only your own hosting) [https://github.com/claude-world/trend-pulse, fetched 2026-06]
- **Repo / Provider:** github.com/claude-world/trend-pulse — `claude-world/trend-pulse (41★, gh-api 2026-06)` (MIT; not archived; last push 2026-04-13)
- **Top pick for its domain:** no — GDELT/Trends MCP/Product Hunt lead; trend-pulse is the free-unlimited aggregator alternative

## What it does / when to pick it
Self-host MCP that aggregates ~20 public sources into one normalized trend feed, computing per-topic **velocity** and a **lifecycle label (EMERGING / PEAK / DECLINING)**. **Decision rule:** pick it over **Trends MCP** when you want the same "what's accelerating across many platforms" signal but need *unlimited* calls and *zero cost* — Trends MCP normalizes 25+ sources with a cleaner growth-rate but caps the free tier at 100/mo, whereas trend-pulse is free no-key but thinner (single-author, 41★). Use **GDELT** for news tone, **Product Hunt MCP** for product launches, **idea-reality-MCP** for "is this saturated." Treat trend-pulse as the high-volume scout, not the source of record.

## Install
Self-host: `git clone https://github.com/claude-world/trend-pulse`, install deps per its README, then register the local MCP server. Exact command lives in the volatile L1 line `reference/volatile/pricing-install.md → trends-discovery` (claude-world/trend-pulse, self-host, free no-key). No secret to leak, so `claude mcp add` is safe here. On Windows, stdio self-host MCPs are flaky (path/shell) — use absolute paths and test in a plain shell first; prefer running it as a local HTTP server if the repo supports it. Restart / `/mcp` reconnect before use. L0 mechanics: `reference/install-guide.md`.

## Auth / keys
None. No API key, no account, no quota — the secret-hygiene script does **not** apply. The only limits are the upstream sources' own rate limits (it scrapes/aggregates public feeds), so be polite.

## Usage — call examples
After connecting, the MCP exposes tools to pull the aggregated trend list and per-topic detail (velocity + lifecycle stage). Typical flow: fetch the ranked trend feed → filter to `EMERGING` with high velocity → cross-check each candidate against a source of record (Trends MCP / GDELT / Product Hunt) before acting. List the exact tool names with your client after connecting — do not assume signatures from memory.

## General experience & gotchas (踩坑)
- **Thin / single-author project (41★, MIT).** It works, but there is little community hardening; if an upstream source changes its HTML/feed the corresponding connector can silently go empty. Verify a live call returns non-empty data before trusting a run.
- **It is an aggregator over public sources — not an authority.** "Velocity" is computed from whatever each connector scrapes; a spike can be one noisy source. Always confirm a hot topic against a second source before claiming it's trending.
- **Lifecycle labels (EMERGING/PEAK/DECLINING) are heuristic, not validated demand.** Good for ranking/triage, weak as a standalone "this will sell" claim — pair with real search-volume or sales-proxy data.
- **You carry the upkeep.** Free software, but you run it: dead connectors, dependency rot, and upstream rate-limits are yours to babysit. The hosted, maintained alternative is Trends MCP (paid past 100/mo).
- **L1 free, route ①** — per CONSTITUTION C2, reach for it (and other free routes) before any paid trend source.

## Failure signals & fallback
Failure looks like: server connects but the trend feed is empty or stale (a connector broke upstream), or only a couple of the ~20 sources return data. **Fallbacks:** for normalized cross-platform acceleration with maintenance behind it use **Trends MCP** (trendsmcp.ai, free 100/mo); for Google-native trending terms use **jmanek/google-news-trends-mcp** (free no-key); for news tone use **GDELT MCP**; for product launches **Product Hunt MCP**.

## Last verified: 2026-06
