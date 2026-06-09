# Tool: ericosiu/ai-marketing-skills

- **Domain(s):** ready-skills (also: none — skill bundle, not an MCP)
- **Barrier route:** — (no data barrier; it's prompt/skill scaffolding) · **Source tier:** L2 · **Ready MCP:** no — installs as Claude *skills* via `git clone` + `pip` + `cp` (**NOT** `npx skills add`)
- **Cost:** free (MIT) [github.com/ericosiu/ai-marketing-skills, gh-api 2026-06]
- **Repo / Provider:** github.com/ericosiu/ai-marketing-skills — `ericosiu/ai-marketing-skills (2.6k★, gh-api 2026-06)`; active (pushed 2026-06-07, not archived, MIT)
- **Top pick for its domain:** no (specialist that fills the business-ops gap, not the default marketing reach)

## What it does / when to pick it
22+ install-and-go skills weighted toward **business-ops**: finance-ops, sales-pipeline, revenue-intelligence, outbound-engine, lead-dossier (plus growth-engine, content-ops, seo-ops, conversion-ops, autoresearch, deck-generator). **Decision rule:** the shard flags marketing/SEO/content skills as *abundant* but **business-ops depth + arbitrage as scarce** — pick this bundle specifically to fill that scarce business-ops gap (revenue intel, sales-pipeline, finance-ops, structured outbound). For the general marketing/competitor/content workflow shell, go to the shard default `coreyhaines31/marketingskills`; for SEO depth, `claude-seo`. Do **not** reach here first for plain copy/ads/email — it's the heavier ops-oriented sibling.

## Install
**Not** an `npx skills add` bundle (unlike `coreyhaines31/marketingskills`) — it is a Python repo you clone and wire per-skill:
```bash
git clone https://github.com/ericosiu/ai-marketing-skills.git
cd ai-marketing-skills/<skill-name>      # e.g. revenue-intelligence
pip install -r requirements.txt
cp .env.example .env                     # then edit .env with the keys that skill needs
```
Each skill category has its own README + requirements + `.env`. Exact one-liner is in shard `reference/domains/ready-skills.md` and `reference/volatile/pricing-install.md → ready-skills`. Skills take effect on session restart. L0 mechanics: `reference/install-guide.md`.

## Auth / keys
The skills themselves are scaffolding, but **unlike the no-key `marketingskills` bundle, several of these skills DO carry keys** — `.env.example → .env` is part of the standard setup, and business-ops skills (revenue-intel, outbound, lead-dossier) expect data-source/CRM/enrichment keys to be useful. Secret hygiene: have the **user** paste keys into `.env` themselves; `.env` is plaintext on disk — add it to `.gitignore` and never commit/screenshot it (`.env.example` ships only placeholders). The real ceiling, per shard "Judgment", is which data sources you wire behind each skill.

## Usage — call examples
After `pip install` + `.env` for a chosen category, restart, then invoke that skill (e.g. revenue-intelligence, sales-pipeline, finance-ops) on your account/topic. Minimal flow: clone → `cd revenue-intelligence` → `pip install -r requirements.txt` → `cp .env.example .env` (fill keys) → restart → invoke. Treat the output as a structured ops draft to be grounded against your real CRM/finance data, not finished numbers.

## General experience & gotchas (踩坑)
- **Install trap: this is NOT `npx skills add`** — the master/shard explicitly tag it `git clone + pip + cp (NOT npx)`. Trying the npx path silently does nothing; you must clone and pip-install per skill.
- **Per-skill setup, not one install** — each category has its own `requirements.txt` and `.env`; there's no single "install everything" command. Set up only the skill you need.
- **Keys live in `.env` on disk** (plaintext) — a different hygiene surface from MCP `~/.claude.json` keys; keep `.env` gitignored.
- **Python repo, not packaged skills** — heavier than the pip-free `coreyhaines31` bundle; the payoff is the scarce business-ops coverage, so only reach here when that's the actual need.
- Free MIT, 2.6k★, actively pushed (2026-06) — safe to recommend without a staleness caveat.

## Failure signals & fallback
Failure looks like: `npx skills add` doing nothing (wrong install path — use git clone); a skill erroring on a missing `.env` key; or ungrounded ops output (no CRM/finance source wired). **Fallbacks:** general marketing/competitor/content shell → `coreyhaines31/marketingskills`; SEO depth → `claude-seo`; packaged 6-stage market-research pipeline → `ishwarjha/claude-marketing-research-skill`; first-party CRM data behind it → `hubspot-mcp` / `salesforce-mcp` / `apollo`; can't find a skill → discovery via `ComposioHQ/awesome-claude-skills` catalog.

## Last verified: 2026-06
