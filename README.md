# market-intel

Triage a commercial topic across 15 data domains, auto-detect the right specialized source, then delegate the heavy research to the harness you already have.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Source Matrix](https://img.shields.io/badge/Source%20Matrix-15%20domains-green?style=flat)](skills/market-intel/reference/sources-index.md)
[![Tool docs](https://img.shields.io/badge/Tool%20docs-per--tool%20how--to-green?style=flat)](skills/market-intel/reference/tools/index.md)
[![Languages](https://img.shields.io/badge/Languages-EN%20%2F%20CN-blue?style=flat)](#languages)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.26.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ Read this first — the design philosophy

market-intel is built on one principle — **root-cause design, not incremental patching.** When
something is wrong, we change the assumption underneath it, not the symptom on top. That single idea
produced every decision here: browser-automation was promoted from footnote to a first-class route
(not "add a few free tools"); this is a thin delegation layer (not "another deep-research"); updates
run through a deterministic gate that can only let the matrix improve (not "set a reminder to
refresh"). **The philosophy outranks any individual feature** — every future change must pass one
test: *does it fix the framing, or just patch a symptom?*

📜 **[Read the full design philosophy → PHILOSOPHY.md](PHILOSOPHY.md)** (6 principles, each with the
patch-vs-root contrast and the real decision in this repo that it produced).

---

## What it is (and isn't)

Claude Code already has a `deep-research` harness (fan-out → fetch → verify → synthesize) and a `research-lit` skill. Those are great for **general web** and **academic** research. They fall short the moment your question needs a **specialized commercial source** behind an information barrier — real X/Twitter data, Amazon price history, on-chain feeds, SEO metrics, social sentiment, B2B lead data.

`market-intel` is the **thin layer** that fills exactly that gap. It does **only three things nothing else does**, and delegates everything else:

1. **Triage** — map a commercial topic to 1–N of 15 data domains.
2. **Detect + guide install** — check which specialized MCP sources are actually connected (via `claude mcp list`, not unreliable tool-name guessing), and if a key source is missing, hand you the exact `claude mcp add` command — or open its **per-tool how-to doc** ([`reference/tools/`](skills/market-intel/reference/tools/index.md)) for install + auth + usage + gotchas, guided by a multi-level [install guide](skills/market-intel/reference/install-guide.md).
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

## Quick start — install the free no-key bootstrap pack (3 minutes)

Want to try it without configuring API keys? Install these 3 free, no-key MCPs first — they cover
HN/Reddit-style community + market trends + AI papers at zero cost:

```bash
# 1. Hacker News (community)
claude mcp add -s user mcp-hn 'uvx mcp-hn'

# 2. GDELT (global news + trends, no key)
claude mcp add -s user gdelt 'uvx gdelt-mcp'

# 3. arXiv (research papers, no key)
claude mcp add -s user arxiv 'uvx arxiv-mcp-server'
```

Then **restart the Claude session** (`claude` → re-enter; MCPs only register on session start).

Now ask: `调研一下 AI agent 工具生态的趋势`. The skill will fan out research subagents that
use these three sources together — community signal + trends + papers — and produce a sourced
report. No keys, no signup, ~30s start-to-first-finding.

After this, the [60-second tour](#60-second-tour) below explains the **specialized MCPs**
(paid X data, Bright Data, Keepa, etc.) — these unlock the high-quality routes the skill is
really designed for.

### Now what? — installed it, what do I read first?

Three different "next steps" depending on intent. Pick one:

| If you want to… | Open this |
|---|---|
| **Use the skill** (just have it trigger automatically and run research for you) | Nothing else — the skill is loaded; type a research query. |
| **Install your first specialized MCP** (e.g. a real X data source, a finance API) | `skills/market-intel/reference/install-guide.md` — L0 install mechanics; then `skills/market-intel/reference/tools/<slug>.md` for the specific tool you picked from the source matrix below. |
| **Set up a private companion config repo** to persist your install state + secrets across machines (recommended for >1 tool) | `skills/market-intel/reference/companion-config-repo.md` — overview + tutorial. Then `companion-config-spec.md` (formal contract) and `companion-config-hardening.md` (GitHub-side lockdown BEFORE first push). |

Most users want path 2 first, then path 3 once they accumulate >1 tool / >1 machine.

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

### Try one of these as your first real query

After the Quick Start install, try invoking the skill on something concrete:

- `调研一下 AI agent 工具生态最近一个月的趋势` — exercises trends + community + frontier-research
- `compare the top 3 hosted MCP marketplaces (Smithery / Glama / PulseMCP) — coverage, pricing, signal-to-noise` — exercises mcp-ecosystem
- `find me 3 underrated open-source web-scraping tools released in 2026 with > 200 stars` — exercises web-scraping + GitHub velocity discovery
- `who's been launching credible LLM eval skills in the last 3 months` — exercises ready-skills + frontier-research

Each will fan out subagents, surface evidence with citations, and end with a "gaps if you connect <X> source" list. If a query produces only web-fallback output, that's the skill being honest about its coverage — see the install-guide to add a specialized MCP for deeper data.

---

## Skills at a glance

### The source matrix (15 domains)

The knowledge asset. Each domain shard names the best tool, its **barrier route**, how to detect it, and what to install. Thin index → load only the domain(s) you need. Each tool also has a **per-tool how-to doc** under [`reference/tools/`](skills/market-intel/reference/tools/index.md) (install + auth + usage + 踩坑), reached on-demand via the thin tool index.

| Domain | Top pick (barrier route) |
|---|---|
| [x-twitter](skills/market-intel/reference/domains/x-twitter.md) | twikit ④③ · twitterapi.io ② resale |
| [reddit-community](skills/market-intel/reference/domains/reddit-community.md) | HN MCP ① free · reddit-mcp-buddy ① |
| [web-scraping](skills/market-intel/reference/domains/web-scraping.md) | Tavily/Exa + Firecrawl + Bright Data |
| [ecommerce-arbitrage](skills/market-intel/reference/domains/ecommerce-arbitrage.md) | Keepa ① official (seller-side) |
| [finance-markets](skills/market-intel/reference/domains/finance-markets.md) | SEC EDGAR + FRED ① free |
| [crypto-defi](skills/market-intel/reference/domains/crypto-defi.md) | CoinGecko ① + ccxt |
| [seo-keywords](skills/market-intel/reference/domains/seo-keywords.md) | GSC ① free + DataForSEO ② |
| [social-publishing](skills/market-intel/reference/domains/social-publishing.md) | Buffer ① · Postiz OSS |
| [content-cms](skills/market-intel/reference/domains/content-cms.md) | Sanity / WordPress MCP ① |
| [leadgen-crm](skills/market-intel/reference/domains/leadgen-crm.md) | Apollo.io ① + Hunter ① |
| [trends-discovery](skills/market-intel/reference/domains/trends-discovery.md) | GDELT + Product Hunt MCP ① free |
| [frontier-research](skills/market-intel/reference/domains/frontier-research.md) | arXiv API + HF Daily Papers ① free |
| [ready-skills](skills/market-intel/reference/domains/ready-skills.md) | coreyhaines31/marketingskills |
| [browser-automation](skills/market-intel/reference/domains/browser-automation.md) | playwright MCP + browser-use / crawl4ai ④ |
| [consumer-price-compare](skills/market-intel/reference/domains/consumer-price-compare.md) | **delegates to sister skill** shopping-aggregator |

**Barrier routes:** ① official API (compliant, often paid) · ② resale API (provider absorbs the barrier, cheap, gray-area) · ③ self-host scrape (reverse-engineered API, free, accounts+proxies, ban risk) · ④ **browser automation / act-like-human** — real logged-in browser (playwright MCP + free OSS repos). **First-class, not a footnote:** often returns richer data (rendered/logged-in view, fields APIs hide) at zero API cost. The skill prefers route ④ over paid APIs when it fits, reaching for ①/② only for history it can't backfill (e.g. Keepa), scale reliability, or compliance.

Three install levels: [`install-guide.md`](skills/market-intel/reference/install-guide.md) (L0 mechanics) → [`pricing-install.md`](skills/market-intel/reference/volatile/pricing-install.md) (L1 per-domain commands + prices, `last_verified`-stamped) → [`tools/<slug>.md`](skills/market-intel/reference/tools/index.md) (L2 per-tool). Verify volatile prices against the official site before quoting.

### Sister skill — consumer-side specialization

For **consumer shopping price comparison** (Amazon / eBay / Walmart / Target / Taobao / JD price
compare + Keepa / Camelcamelcamel / 慢慢买 history + Capital One Shopping / Karma / 购物党
coupons + Honey 2026 trust event), market-intel defers to its sister skill:
**[`shopping-aggregator`](https://github.com/DaizeDong/shopping-aggregator)**. market-intel
handles broad commercial research + seller-side ecommerce-arbitrage; shopping-aggregator handles
the consumer buy decision. Both skills can coexist — see [`consumer-price-compare`
shard](skills/market-intel/reference/domains/consumer-price-compare.md) for the routing logic.

```
/plugin install github:DaizeDong/shopping-aggregator
```

---

## How to invoke

It auto-activates on phrases like `市场调研`, `competitor analysis`, `research this market`,
`find arbitrage opportunities`, `X/Twitter sentiment`, `SEO intel`, `product trends`,
`调研这个市场`, `竞品分析`, `找套利机会`, `X/推特舆情`, `SEO 情报`, `产品趋势`. To refresh the
source matrix, say `刷新工具库` / `refresh the market-intel source matrix`.

It deliberately steps aside for single-fact lookups or general web reports (use plain search /
`deep-research`) and defers academic literature to `research-lit`.

---

## Example output

A finished run is snapshot-dated, tier-tagged, and built from **structured evidence units**
(`claim · source · quote · tier · date · confidence`) rather than raw page dumps:

- Decision-grade claims carry ≥2 independent sources, each tagged confidence high/medium/low.
- A disagreement matrix surfaces conflicts instead of averaging them.
- A mandatory **Risks & counter-evidence** section (a reverse-search subagent hunts scam/failure/risk).
- An explicit **"configure source X for deeper data"** gap list where coverage fell back to web.

See the [60-second tour](#60-second-tour) for the step-by-step of what produces this.

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

## Limitations

- **The matrix decays** — APIs go paid, tools get acquired, prices move. The [refresh protocol](skills/market-intel/reference/refresh-protocol.md) re-sweeps each domain (one subagent per domain → structured diff → incremental shard edits → `CHANGELOG.md` + version bump). **Default cadence is monthly** (v0.17.0); **weekly** for the fast-moving set (`crypto-defi`, `browser-automation`, `frontier-research`, `mcp-ecosystem`); **quarterly** is reserved for the Horizon scan (cross-domain new-territory discovery). Trigger manually with `刷新工具库` / `refresh the market-intel source matrix`, or wire a scheduled headless run (see [ROADMAP](ROADMAP.md)).
- **Web fallback is honest, not magic** — if no specialized MCP is connected, the skill says so and flags the gap rather than pretending the web answer is as deep.
- **No reinvented engine** — the fan-out/verify/synthesize depth is delegated to `deep-research` / `research-lit`; market-intel is the routing + detection + guardrail seam, not a research engine of its own.

This skill is the product of a 12-subagent tool survey followed by a 5-subagent adversarial design review. The review killed the original "build another full deep-research" plan (it would have been a clone with a trigger conflict), proved that `claude mcp add` doesn't take effect until a session reconnect, and forced in the citation-verification gate, source tiers, and disconfirmation mandate.

---

## Languages

English (`README.md`, authoritative) · 中文 ([`README_CN.md`](README_CN.md)).

---

## Roadmap · Contributing · License

See [ROADMAP.md](ROADMAP.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [LICENSE](LICENSE) (MIT).

Want to add a tool, fix a broken entry, or propose a new domain? [CONTRIBUTING.md](CONTRIBUTING.md)
is a single-page guide covering the 3 contribution patterns, the 4-file sync rule, and the
verification gates your PR has to pass. Deeper design docs: [PHILOSOPHY.md](PHILOSOPHY.md) ·
[CONSTITUTION.md](CONSTITUTION.md) · [EVOLUTION.md](EVOLUTION.md).
