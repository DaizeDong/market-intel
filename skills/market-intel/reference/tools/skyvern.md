# Tool: Skyvern-AI/skyvern

- **Domain(s):** browser-automation (also: none)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** yes, self-host + API (run the Skyvern server, drive via its API/MCP)
- **Cost:** free (open source, AGPL-3.0) to self-host; LLM tokens for the vision/LLM planner + proxies at scale. A paid Skyvern Cloud also exists (separate billing).
- **Repo / Provider:** github.com/Skyvern-AI/skyvern, `Skyvern-AI/skyvern (21.9k★, gh-api 2026-06)`, AGPL-3.0, pushed 2026-06
- **Top pick for its domain:** no

## What it does / when to pick it
Uses an LLM **+ computer vision** to run whole browser *workflows* (multi-step forms, portals, dashboards) that stay robust when the **UI/layout changes**, it looks at the rendered page like a human rather than relying on brittle selectors. **Pick it over playwright/browser-use** when the target redesigns often or selectors keep breaking, or for repeatable form-filling/login workflows across many similar sites. Skip it for one-off reads or bulk static crawling (heavier to stand up than playwright MCP / crawl4ai).

## Install
Self-host: `git clone` the repo and run via Docker / `docker compose` (server + UI), then drive through its REST API or MCP. Needs Docker (see `install-guide.md` prereqs). Heavier setup than a one-line MCP, stand it up only when vision-robust workflows justify it. Exact compose steps live in the repo README; L1 pointer in `reference/volatile/pricing-install.md#browser-automation`. ⚠ **AGPL-3.0**, note the license before embedding in anything you redistribute.

## Auth / keys
Self-host server has no service key, but the planner **needs an LLM API key** (OpenAI/Anthropic vision-capable model) set in the server env. Target-site auth = credentials/cookies you provide to the workflow. Key-bearing: put the LLM key in the server's env file, never in the transcript (see `install-guide.md` secret hygiene); Skyvern Cloud adds its own API key if you use the hosted option.

## Usage, call examples
Run a task via REST (exact path/fields unverified, confirm against the API spec at docs.skyvern.com): the current cloud API is `POST https://api.skyvern.com/v1/run/tasks` taking a single natural-language `prompt` (+ optional `url`, `webhook_url`); the legacy self-host route was `POST /api/v1/tasks` with `navigation_goal`/`data_extraction_goal` fields, your self-hosted version may expose either, so check its `/docs` (OpenAPI) before scripting. Or define a reusable **workflow** (YAML) and trigger it by ID. The MCP exposes task/workflow run + status tools once the server is up.

## General experience & gotchas (踩坑)
- **Vision = slower and pricier per step** than DOM-based tools. Its edge is resilience to layout change, not speed/cost, don't use it where a stable selector script (playwright) or bulk crawler (crawl4ai) would do.
- **Heaviest to operate** of the domain's frameworks: a server + Docker, not a pip-install lib. Standing it up for a single extraction is over-engineering, reserve for recurring, redesign-prone workflows.
- **AGPL-3.0** is the strictest license in this shard, fine for internal/self-host research, a real constraint if you bundle it into a distributed product.
- Anti-bot: vision doesn't bypass Cloudflare/DataDome challenge walls, a CAPTCHA still blocks it. Pair with stealth (patchright/camoufox) or Bright Data ② if the target is hardened.
- Self-host throughput is bounded by your one browser fleet + LLM rate limits; add proxies for scale (software free, proxies are the hidden cost).

## Failure signals & fallback
Failed = task stuck/timing out, CAPTCHA wall, or wrong fields filled (vision misread). Fallbacks: **playwright MCP / stagehand** for selector-precise control, **browser-use** for lighter NL goals, **crawl4ai** for bulk extraction, **Bright Data ②** when the barrier is anti-bot.

## Last verified: 2026-06
