# Domain: browser-automation (route ④, first-class)

**Triage signals:** any domain where the official/resale API is paid, rate-limited, field-stripped,
or login-walled, and you'd rather have a real browser act like a human. Often gives **better data**
(full rendered page, logged-in view, fields APIs don't return) at **zero API cost**.

**This is not a last resort.** Prefer this route when: (a) the API is expensive/quota-capped,
(b) you need the real logged-in/rendered view, (c) a free open-source repo already covers the target.
Trade-offs: needs a logged-in session/cookies, usually a **proxy pool at scale** (software is free,
proxies are the hidden cost), and most platform-specific scraping **violates that platform's ToS**
(ban risk, use throwaway accounts for write/scrape-heavy work). Verified stars/activity 2026-06-01.

## You already have: playwright MCP
`claude mcp list` → playwright connected. It drives a real Chromium with your session, navigate,
click, fill, screenshot, read rendered DOM. **Default first tool** for any bespoke "act like a
human" task before reaching for a paid API. Add specialized repos below when playwright alone is
too low-level or gets fingerprint-blocked.

## General AI/LLM browser frameworks
| repo | what | Claude fit | note |
|---|---|---|---|
| **browser-use/browser-use** (97.9k★) | LLM drives the browser via natural-language goals | Python lib; agent calls it | most popular; great for "log in and extract X" |
| **vercel-labs/agent-browser** (35.6k★) | native Rust CLI, token-efficient snapshot+@ref for LLM context | CLI; ships `.claude-plugin` | fast peer to playwright MCP (not MCP-native); bundled Chrome |
| **browserbase/stagehand** (23k★) | act/extract/observe primitives over Playwright | TS lib | precise, scriptable AI browser control |
| **Skyvern-AI/skyvern** (22k★) | LLM + vision runs browser workflows, beats layout changes | self-host + API | robust to UI changes via vision |
| **unclecode/crawl4ai** (68.1k★) | LLM-friendly crawler, auto anti-bot (Cloudflare/Akamai) | docker MCP / lib | zero-cost self-host crawl首选 |
| **apify/crawlee** (24k★) | Playwright/Puppeteer/Cheerio + proxy rotation framework | Node lib | base for building bespoke scrapers |
| **ScrapeGraphAI/Scrapegraph-ai** (27k★) | NL-defined graph extraction | Python lib | describe what to extract in words |

## Anti-detection / anti-fingerprint (when plain playwright gets blocked)
| repo | what | note |
|---|---|---|
| **ultrafunkamsterdam/nodriver** (4.3k★) | undetected Chrome automation successor | evades bot detection |
| **daijro/camoufox** (9.1k★) | anti-fingerprint Firefox build | strongest fingerprint spoofing |
| **steel-dev/steel-browser** (7.1k★) | open-source browser infra for AI agents, self-host | hosted-browser alternative |
| **jo-inc/camofox-browser** (9.1k★) | C++-level fingerprint spoofing on Camoufox base, REST API + plugin | free MIT (key only gates cookie-import) |
| **Kaliiiiiiiiii-Vinyzu/patchright** (3.9k★) | undetected-Playwright patch, passes Cloudflare/DataDome/Akamai/Kasada/F5 | free Apache-2.0, keeps full Playwright API; `reference/tools/patchright.md` |

**Default pick:** start with the already-connected **playwright MCP**; for AI-goal-driven extraction
add **browser-use** or **crawl4ai**; if fingerprint-blocked escalate to **camoufox/nodriver**;
for vision-robust workflows use **skyvern**. Platform-specific repos live in each domain shard.

**Install guidance:** `reference/volatile/pricing-install.md` → browser-automation.
