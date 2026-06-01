# market-intel

A thin orchestration skill for commercial/market research. It triages your topic, finds the right specialized data source (and helps you install it), then hands the heavy lifting to the research harness you already have — instead of reinventing it.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Domains](https://img.shields.io/badge/Source%20Matrix-12%20domains-green?style=flat)](skills/market-intel/reference/sources-index.md)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.1.0%20alpha-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## What it is (and isn't)

Claude Code already has a `deep-research` harness (fan-out → fetch → verify → synthesize) and a `research-lit` skill. Those are great for **general web** and **academic** research. They fall short the moment your question needs a **specialized commercial source** behind an information barrier — real X/Twitter data, Amazon price history, on-chain feeds, SEO metrics, social sentiment, B2B lead data.

`market-intel` is the **thin layer** that fills exactly that gap. It does **only three things nothing else does**, and delegates everything else:

1. **Triage** — map a commercial topic to 1–N of 12 data domains.
2. **Detect + guide install** — check which specialized MCP sources are actually connected (via `claude mcp list`, not unreliable tool-name guessing), and if a key source is missing, hand you the exact `claude mcp add` command.
3. **Quality guardrails** — citation verification, source tiers, multi-source corroboration, mandatory disconfirmation, explicit gaps.

The actual fan-out, fetching, adversarial verification, and citation synthesis are **delegated** to `deep-research` / `research-lit`. No reinvented engine, no trigger fights.

---

## Install

```
/plugin install github:DaizeDong/market-intel
```

Or clone manually:

```bash
git clone https://github.com/DaizeDong/market-intel.git ~/.claude/plugins/market-intel
```

It auto-activates on phrases like `市场调研`, `competitor analysis`, `research this market`, `find arbitrage opportunities`, `X/Twitter sentiment`, `SEO intel`, `product trends`. For single-fact lookups or general web reports it deliberately steps aside (use plain search / `deep-research`); for academic literature it defers to `research-lit`.

---

## 60-second tour

You say:

```
research the competitive landscape and X sentiment around <product>, then find any arbitrage angle
```

What runs:

1. **Triage** → maps to `x-twitter`, `trends-discovery`, `ecommerce-arbitrage`; picks a depth budget with hard caps (no runaway fan-out).
2. **Detect** → runs `claude mcp list`, sees you have none of the X/ecommerce MCPs connected, notes it.
3. **Guide install** (non-blocking) → "This depends on real X data. Install twitterapi.io: `claude mcp add -s user ...` — note it only works after a session reconnect. For now I'll use web fallback and flag the gap."
4. **Delegate** → fans out subagents / invokes `deep-research`, each returning a **structured evidence unit** (`claim · source · quote · tier · date · confidence`), not raw page dumps.
5. **Guardrails** → independent verifier re-fetches each cited URL; decision-grade claims need ≥2 independent sources; a dedicated reverse-search subagent hunts risks/failures.
6. **Report** → snapshot-dated, tier-tagged, with a disagreement matrix, a mandatory **Risks & counter-evidence** section, and an explicit **"configure source X for deeper data"** gap list.

---

## The source matrix (12 domains)

The knowledge asset. Each domain shard names the best tool, its **barrier route**, how to detect it, and what to install. Thin index → load only the domain(s) you need.

| Domain | Top pick (barrier route) |
|---|---|
| [x-twitter](skills/market-intel/reference/domains/x-twitter.md) | twitterapi.io ② resale |
| [reddit-community](skills/market-intel/reference/domains/reddit-community.md) | HN MCP ① free · Reddit API ① |
| [web-scraping](skills/market-intel/reference/domains/web-scraping.md) | Tavily/Exa + Firecrawl + Bright Data |
| [ecommerce-arbitrage](skills/market-intel/reference/domains/ecommerce-arbitrage.md) | Keepa ① official |
| [finance-markets](skills/market-intel/reference/domains/finance-markets.md) | SEC EDGAR + FRED ① free |
| [crypto-defi](skills/market-intel/reference/domains/crypto-defi.md) | CoinGecko ① + ccxt |
| [seo-keywords](skills/market-intel/reference/domains/seo-keywords.md) | GSC ① free + DataForSEO ② |
| [social-publishing](skills/market-intel/reference/domains/social-publishing.md) | Buffer ① · Postiz OSS |
| [content-cms](skills/market-intel/reference/domains/content-cms.md) | Sanity/WordPress MCP ① |
| [leadgen-crm](skills/market-intel/reference/domains/leadgen-crm.md) | Apollo.io ① + Hunter ① |
| [trends-discovery](skills/market-intel/reference/domains/trends-discovery.md) | GDELT + Product Hunt MCP ① free |
| [ready-skills](skills/market-intel/reference/domains/ready-skills.md) | coreyhaines31/marketingskills |

**Barrier routes:** ① official API (compliant, often paid) · ② resale API (provider absorbs the barrier, cheap, gray-area) · ③ self-host scrape (free, you supply accounts+proxies, ban risk) · ④ headless browser (your session, most fragile).

Exact install commands and prices live in [`pricing-install.md`](skills/market-intel/reference/volatile/pricing-install.md), each line `last_verified`-stamped — verify against the official site before quoting.

---

## Quality guardrails

Hard rules applied during synthesis (see [SKILL.md](skills/market-intel/SKILL.md)):

- **Citation verification gate** — an independent verifier re-fetches every cited URL and confirms the page contains the value (verbatim quote). Dead links dropped; quote-less numbers demoted to "unverified."
- **≥2 independent sources** for decision-grade claims; each tagged confidence high/medium/low.
- **Source tiers** L1 first-party → L5 fallback/inference; vendor self-claims can't be sole support.
- **No silent degradation** — falling back from a barrier source to web is flagged in-line.
- **Timestamp volatile data** — every price/policy carries fetched + published dates.
- **Disconfirmation mandate** — a reverse-search subagent hunts scam/failure/risk; arbitrage gets an explicit execution-friction section.
- **Surface conflicts, don't average them**; **failures become explicit coverage gaps.**

---

## Keeping it current

The matrix decays — APIs go paid, tools get acquired, prices move. The [refresh protocol](skills/market-intel/reference/refresh-protocol.md) re-sweeps each domain (one subagent per domain → structured diff → incremental shard edits → `CHANGELOG.md` + version bump). Default cadence quarterly; monthly for fast-moving domains (x-twitter, web-scraping, social-publishing, crypto-defi). Trigger manually with `刷新工具库` / `refresh the market-intel source matrix`, or wire a scheduled headless run (see [ROADMAP](ROADMAP.md)).

---

## Design notes

This skill is the product of a 12-subagent tool survey followed by a 5-subagent adversarial design review. The review killed the original "build another full deep-research" plan (it would have been a clone with a trigger conflict), proved that `claude mcp add` doesn't take effect until a session reconnect, and forced in the citation-verification gate, source tiers, and disconfirmation mandate. See [ROADMAP.md](ROADMAP.md) for what's next.
