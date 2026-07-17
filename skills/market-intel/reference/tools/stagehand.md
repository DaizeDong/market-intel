# Tool: browserbase/stagehand

- **Domain(s):** browser-automation (also: none)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** no (TypeScript lib over Playwright; wrap it yourself)
- **Cost:** free (open source). LLM tokens for `act`/`extract`/`observe` calls + optional Browserbase hosting fee if you run on their cloud (self-host on your own Chromium is free).
- **Repo / Provider:** github.com/browserbase/stagehand, `browserbase/stagehand (23.0k★, gh-api 2026-06)`, MIT, pushed 2026-06
- **Top pick for its domain:** no

## What it does / when to pick it
Adds three AI primitives, `act` (do this), `extract` (pull structured data with a schema), `observe` (find candidate actions), on top of Playwright in **TypeScript**. **Pick it over browser-use** when you want *precise, scriptable* AI control: deterministic Playwright code for the stable parts, AI only at the brittle steps, with Zod-typed extraction. Pick browser-use instead for fully autonomous NL goals; pick plain playwright MCP if you don't need any AI step. TS-only, skip it if your harness is Python (use browser-use/crawl4ai).

## Install
`npm i @browserbasehq/stagehand` (Node ≥18; runs on local Playwright Chromium by default, or set Browserbase env to use their hosted browser). Not an MCP, call from a TS script. See L1 line in `reference/volatile/pricing-install.md#browser-automation`. On Windows prefer running the Node script in a clean shell; HTTP-first guidance in `install-guide.md` doesn't apply (this is a lib, not a server).

## Auth / keys
No Stagehand service key for local mode. Needs an **LLM API key** (`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`) for the AI primitives; optionally a **Browserbase API key + project ID** if running on Browserbase cloud. Target-site auth = supplied session/cookies. Key-bearing: set keys via env yourself, keep them out of the transcript (see `install-guide.md` secret hygiene).

## Usage, call examples
```ts
import { Stagehand } from "@browserbasehq/stagehand";
const sh = new Stagehand({ env: "LOCAL" });           // or "BROWSERBASE"
await sh.init();
await sh.page.goto("https://site");
await sh.page.act("click the login button");
const data = await sh.page.extract({ instruction: "list product names+prices",
  schema: z.object({ items: z.array(z.object({ name: z.string(), price: z.string() })) }) });
```

## General experience & gotchas (踩坑)
- **TypeScript-first.** The Python port lags the TS one, for Python pipelines prefer browser-use/crawl4ai rather than fighting the less-maintained Python path.
- **`extract` with a Zod schema is the strong point**, typed output beats free-text scraping. But every `act`/`extract`/`observe` is an LLM call; cost scales with how many AI steps you keep. Script the deterministic steps in raw Playwright and reserve AI for the brittle ones.
- **Browserbase cloud ≠ free.** Default LOCAL mode is free on your own Chromium; only opt into Browserbase when you need their managed/stealth browser fleet (separate billing).
- **Same anti-bot ceiling** as Playwright underneath, hardened Cloudflare/DataDome still blocks LOCAL mode (Browserbase adds some stealth). Signal: CAPTCHA/403/empty extract. Escalate to patchright/nodriver/camoufox or Bright Data ②.
- Pin the version (23k★, near-daily pushes); the `act/extract/observe` API and config keys have shifted across releases.

## Failure signals & fallback
Failed = `extract` returns empty/garbage against the schema, `act` can't locate the element, CAPTCHA/403. Fallbacks: **browser-use** (autonomous goal), **playwright MCP** (deterministic script), **crawl4ai** (bulk + anti-bot), or **Bright Data ②** for the hard barrier.

## Last verified: 2026-06
