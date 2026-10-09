# market-intel

Select specialized sources for commercial research across 15 data domains, verify their availability, and delegate retrieval and synthesis to an existing research workflow.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Source Matrix](https://img.shields.io/badge/Source%20Matrix-15%20domains-green?style=flat)](skills/market-intel/reference/sources-index.md)
[![Tool docs](https://img.shields.io/badge/Tool%20docs-per--tool%20how--to-green?style=flat)](skills/market-intel/reference/tools/index.md)
[![Languages](https://img.shields.io/badge/Languages-EN%20%2F%20CN-blue?style=flat)](#languages)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.30.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## Design philosophy

Commercial research often fails at source selection: a general search result cannot replace
the required transaction history, platform data or authenticated operation. The tool owns source
triage, setup guidance and evidence requirements, while the existing research harness performs
retrieval and synthesis. Browser access is one supported route alongside official APIs and other
sources; its availability must be checked in the active session.

This division keeps the research engine small, but makes coverage depend on the installed host,
permissions and source behavior. Configuration, discovery, a successful call and usable content
are separate evidence levels. A missing level stays visible as a setup need or coverage gap.
Browsing the catalog needs no live probe; collecting current inventory is an explicit operation
that writes only to a verified PRIVATE companion.

Matrix changes pass deterministic checks for declared invariants and retain source evidence.
Those checks can reject known forms of regression; they do not prove every recommendation is
better or every provider is currently usable. Refreshes now require manual initiation, so their
dates and coverage must remain visible to the reader.

See [PHILOSOPHY.md](PHILOSOPHY.md) for the seven principles behind source selection,
delegation, evidence, update controls and progressive loading.

---

## Scope

Use market-intel when a commercial question needs specialized data such as X/Twitter
content, Amazon price history, on-chain feeds, SEO metrics, social sentiment or B2B leads.
The skill handles three parts of that workflow:

1. **Triage:** map the topic to 1 to N of the 15 data domains.
2. **Source selection and setup:** verify the selected operation in the active Claude or
   Codex session, including exposure, execution, authentication and usable content. Use
   the [per-tool docs](skills/market-intel/reference/tools/index.md) for missing setup.
3. **Evidence requirements:** verify citations, classify sources, seek independent
   corroboration and counter-evidence, and report conflicts and coverage gaps.

Retrieval, fan-out and synthesis use the available `deep-research` or `research-lit`
workflow. Routing for general web and academic questions is listed under
[How to invoke](#how-to-invoke).

---

## Install

```
/plugin install github:DaizeDong/market-intel
```

Or clone manually:

```bash
git clone --recurse-submodules https://github.com/DaizeDong/market-intel.git ~/.claude/plugins/market-intel
```

For Python maintenance commands, run `python -m pip install -r requirements.txt`
from the checkout. Use `requirements-dev.txt` for the offline test suite. Catalog,
source collection and deterministic checks need no model package. The optional
incident and changelog draft helpers use the operator's configured `llmcall`
interface; follow [model adapter setup](CONFIG.md#model-adapter) before using them.

---

## Config

Resolve the full consumer checkout before running maintenance commands. Replace
`<absolute-market-intel-checkout>` with that absolute directory and confirm its
`tools/console.py` and `.claude-plugin/plugin.json` exist. Plugin installation does
not make these scripts relative to the current project.

`market-intel` is **config-bearing**, it reads per-user state (keys, installed-tool registry) from a
**separate, private** companion config repo. Repo-root contract: [CONFIG.md](CONFIG.md); authoritative
deep spec: [`companion-config-spec.md`](skills/market-intel/reference/companion-config-spec.md) (v1.3, STABLE).

- **Mount:** `MARKET_INTEL_CONFIG` → `MARKET_INTEL_CONFIG_DIR` → shared Guards discovery. `MARKET_INTEL_DATA_DIR` must belong to the same companion. See [CONFIG.md](CONFIG.md#discovery-convention-e2) for the exact layout and fallback order.
- **First time:** Empty `tools: []` remains NOT READY. Fill installed tool identities and both templates before the doctor; initialize companion data/ before runtime writes.
  ```bash
  python "<absolute-market-intel-checkout>/scripts/init_config.py"        # stamp a conformant skeleton (deterministic)
  export MARKET_INTEL_CONFIG=~/.market-intel-config  # or pass --out <dir> to init
  python "<absolute-market-intel-checkout>/scripts/verify_config.py"       # doctor: PASS/FAIL, names what is missing
  ```
- **Switch configs (hot-swap):** point the env var at another config dir, configs are self-contained,
  clear or update the DATA override with it: `export MARKET_INTEL_CONFIG=~/configs/work` ↔ `~/configs/personal`.
- **Secrets:** follow the companion's declared storage mode. Mode A versions credentials only in
  verified PRIVATE Git; Mode B ignores them and requires a separate backup. The bundled initializer
  supports Mode B only. Both modes keep secrets out of this public source; see [CONFIG.md](CONFIG.md#secrets-and-storage-modes-e6).

---

## Catalog and current operation readiness

The maintenance console preserves `status`, `tool <slug>` and `connect <slug>`
without DATA initialization, inventory probes or writes. Pass `--capability` to
select an operation for the catalog's `source_id` (default: its `capability_id`). Current evidence comes from
`MARKET_INTEL_HOST`, `MARKET_INTEL_SESSION_ID` and `MARKET_INTEL_CAPABILITIES`.
The [schema v1 guide](skills/market-intel/reference/host-capabilities.md) explains
`available-now`, `setup` reasons and evidence-supported `hard-gap` results.

Only explicit `--refresh` collects machine inventory and writes it to a verified
PRIVATE versioned companion. Storage failures return nonzero and preserve the
previous snapshot. Offline regression tests do not establish live research,
installed-host acceptance or provider readiness.

## Quick start, install the free no-key bootstrap pack (3 minutes)

These three free, no-key MCPs provide routes for Hacker News discussions, global
news and trends, and research papers:

```bash
# 1. Hacker News (community)
claude mcp add -s user mcp-hn -- uvx mcp-hn

# 2. GDELT (global news + trends, no key)
claude mcp add -s user gdelt -- uvx gdelt-mcp

# 3. arXiv (research papers, no key)
claude mcp add -s user arxiv -- uvx arxiv-mcp-server
```

Then **restart the Claude session** and verify the source operation in that session.
For **Codex**, configure the source through Codex MCP settings or its installed app,
reconnect Codex, and inspect the tools exposed there. Claude settings do not prove
Codex availability. See the [host evidence guide](skills/market-intel/reference/host-capabilities.md).

After setup, ask `调研一下 AI agent 工具生态的趋势`. The workflow can combine community
signals, trends and papers from sources that pass current operation and content checks.

The [60-second tour](#60-second-tour) shows how specialized sources such as paid X
data, Bright Data and Keepa fit into a research run.

### Documentation by task

| If you want to… | Open this |
|---|---|
| **Use the skill** (just have it trigger automatically and run research for you) | Enter a research query after the host has loaded the skill. |
| **Install your first specialized MCP** (e.g. a real X data source, a finance API) | `skills/market-intel/reference/install-guide.md`, L0 install mechanics; then `skills/market-intel/reference/tools/<slug>.md` for the specific tool you picked from the source matrix below. |
| **Set up a private companion config repo** to persist your install state + secrets across machines (recommended for >1 tool) | `skills/market-intel/reference/companion-config-repo.md`, overview + tutorial. Then `companion-config-spec.md` (formal contract) and `companion-config-hardening.md` (GitHub-side lockdown BEFORE first push). |

---

## 60-second tour

You say:

```
research the competitive landscape and X sentiment around <product>, then find any arbitrage angle
```

What runs:

1. **Triage** → maps to `x-twitter`, `trends-discovery`, `ecommerce-arbitrage`; picks a depth budget with hard caps (no runaway fan-out).
2. **Detect** → inspects tools exposed in the active host session, then verifies the selected X/ecommerce operation and reports any setup gap.
3. **Guide install** (non-blocking) → "This depends on real X data. Install twitterapi.io: `claude mcp add -s user ...`, note it only works after a session reconnect. For now I'll use web fallback and flag the gap."
4. **Delegate** → fans out subagents / invokes `deep-research`, each returning a **structured evidence unit** (`claim · source · quote · tier · date · confidence`), not raw page dumps.
5. **Guardrails** → independent verifier re-fetches each cited URL; decision-grade claims need ≥2 independent sources; a dedicated reverse-search subagent hunts risks/failures.
6. **Report** → snapshot-dated, tier-tagged, with a disagreement matrix, a mandatory **Risks & counter-evidence** section, and an explicit **"configure source X for deeper data"** gap list.

### Try one of these as your first real query

After the Quick Start install, try invoking the skill on something concrete:

- `调研一下 AI agent 工具生态最近一个月的趋势`, exercises trends + community + frontier-research
- `compare the top 3 hosted MCP marketplaces (Smithery / Glama / PulseMCP) — coverage, pricing, signal-to-noise`, exercises trends-discovery + web-scraping
- `find me 3 underrated open-source web-scraping tools released in 2026 with > 200 stars`, exercises web-scraping + GitHub velocity discovery
- `who's been launching credible LLM eval skills in the last 3 months`, exercises ready-skills + frontier-research

The report identifies the sources used and any missing specialized access. Use the
installation guide when a listed setup step would improve the requested coverage.

---

## Skills at a glance

### The source matrix (15 domains)

Each domain shard records recommended sources, barrier routes, detection and installation.
Load the relevant domains, then the selected [tool documentation](skills/market-intel/reference/tools/index.md)
for installation, authentication, usage and troubleshooting.

| Domain | Top pick (barrier route) |
|---|---|
| [x-twitter](skills/market-intel/reference/domains/x-twitter.md) | twscrape ③ · playwright ④ · twitterapi.io ② resale |
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

For X, twikit remains a conditional fallback after a fresh operation check; see the
[domain notes](skills/market-intel/reference/domains/x-twitter.md) for its staleness limits.

**Barrier routes:** ① official API (compliant, often paid) · ② resale API (provider absorbs the barrier, cheap, gray-area) · ③ self-host scrape (reverse-engineered API, free, accounts+proxies, ban risk) · ④ **browser automation / act-like-human**, real logged-in browser (playwright MCP + free OSS repos). Browser access can expose rendered or logged-in fields that an API omits, without an API fee. The skill prefers route ④ over paid APIs when it fits, reaching for ①/② only for history it can't backfill (e.g. Keepa), scale reliability, or compliance.

Three install levels: [`install-guide.md`](skills/market-intel/reference/install-guide.md) (L0 mechanics) → [`pricing-install.md`](skills/market-intel/reference/volatile/pricing-install.md) (L1 per-domain commands + prices, `last_verified`-stamped) → [`tools/<slug>.md`](skills/market-intel/reference/tools/index.md) (L2 per-tool). Verify volatile prices against the official site before quoting.

### Sister skill, consumer-side specialization

For **consumer shopping price comparison** (Amazon / eBay / Walmart / Target / Taobao / JD price
compare + Keepa / Camelcamelcamel / 慢慢买 history + Capital One Shopping / Karma / 购物党
coupons + Honey 2026 trust event), market-intel defers to its sister skill:
**[`shopping-aggregator`](https://github.com/DaizeDong/shopping-aggregator)**. market-intel
handles broad commercial research + seller-side ecommerce-arbitrage; shopping-aggregator handles
the consumer buy decision. Both skills can coexist, see [`consumer-price-compare`
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

The [report template](skills/market-intel/reference/report-template.md) organizes the
snapshot date, per-domain findings, confidence levels, disagreement matrix, **Risks &
counter-evidence**, source list and **configure source X for deeper data** gaps.
Workers return structured evidence units (`claim · source · quote · tier · date · confidence`)
for synthesis. The checks below govern which claims enter the report.

---

## Quality guardrails

Hard rules applied during synthesis (see [SKILL.md](skills/market-intel/SKILL.md)):

- **Citation verification gate**, an independent verifier re-fetches every cited URL and confirms the page contains the value (verbatim quote). Dead links dropped; quote-less numbers demoted to "unverified."
- **≥2 independent sources** for decision-grade claims; each tagged confidence high/medium/low.
- **Source tiers** L1 first-party → L5 fallback/inference; vendor self-claims can't be sole support.
- **No silent degradation**, falling back from a barrier source to web is flagged in-line.
- **Timestamp volatile data**, every price/policy carries fetched + published dates.
- **Disconfirmation mandate**, a reverse-search subagent hunts scam/failure/risk; arbitrage gets an explicit execution-friction section.
- **Surface conflicts, don't average them**; **failures become explicit coverage gaps.**

---

## Limitations

- Coverage depends on the connected sources and their verified operations. Web fallback
  remains explicitly labelled when specialized access is unavailable.
- Catalog entries, prices and policies can become stale. The monthly refresh and weekly
  surface poll were retired on 2026-10-01; refreshes now run manually through the
  [refresh protocol](skills/market-intel/reference/refresh-protocol.md). The review
  frequencies in [ROADMAP.md](ROADMAP.md#maintenance-cadence) are planning guidance.
- Deterministic checks cover declared invariants. Live research, source readiness and
  recovery require evidence from the operation concerned.

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
