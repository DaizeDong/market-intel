# Tool: langchain-ai/social-media-agent

- **Domain(s):** social-publishing (also: none)
- **Barrier route:** ③ self-host · **Source tier:** L2 · **Ready MCP:** no, it is a LangGraph agent app (clone + run + supply keys), not an MCP server or skill
- **Cost:** free (OSS, MIT), self-host; you pay the underlying LLM + any post-API/ingest-API keys it calls
- **Repo / Provider:** github.com/langchain-ai/social-media-agent, `langchain-ai/social-media-agent (2.6k★, gh-api 2026-06)`; active (pushed 2026-06-09, not archived, MIT)
- **Top pick for its domain:** no (a content-pipeline layer, not a posting endpoint)

## What it does / when to pick it
A LangGraph **agent for sourcing, curating, and scheduling** social posts with **human-in-the-loop** review, it ingests content (URLs/feeds), drafts posts, pauses for human approval, then schedules. **Decision rule:** pick it when the job is the *whole content pipeline* (find → write → approve → schedule), not just "post this string." It sits **a tier above the post APIs**: it does not replace them, it *drives* them, pair it with **Buffer** / **Postiz** (or Arcade/Twitter integrations) as the actual publishing backend. If you only need to push a known post to platforms, skip this and call **Buffer** (① free) / **Blotato** / **Postiz** directly. If you want a packaged Postiz-only front-end instead of a full pipeline, see `postiz-agent`.

## Install
Clone and run the LangGraph app (Node/TS, plus a LangGraph runtime); supply the keys it needs (LLM + content-ingest + a posting backend). Exact, time-stamped line: `reference/volatile/pricing-install.md → social-publishing` ("langchain-ai/social-media-agent (2.6k★): clone + keys (content pipeline)"). It is **not** an MCP, there is no `claude mcp add` one-liner; it runs as its own service and you interact via its UI/LangGraph endpoints. Windows: it expects a Node + LangGraph dev environment; prefer running it under WSL/Docker if stdio/path issues bite. L0 mechanics (secret hygiene, transports): `reference/install-guide.md`.

## Auth / keys
Multiple keys depending on wiring: an **LLM key** (Anthropic/OpenAI), **content-ingest keys** (e.g. FireCrawl/Arcade for URL→post), and a **posting backend** (Twitter/LinkedIn via Arcade, or Buffer/Postiz). Secret-hygiene (one line): never echo or paste the user's keys into the transcript, have the user place them in the app's own `.env`, and never `browser_snapshot` a key page; full procedure in `reference/install-guide.md`.

## Usage, call examples
Not a tool you call per-MCP, you run the graph. Typical loop: drop a source URL → agent generates a draft → **human approves/edits in the loop** → agent schedules to the configured backend. Conceptual entry:
```
# from the cloned repo
yarn install && yarn dev   # starts the LangGraph agent + studio
# then submit a content URL via the studio / API; review the drafted post; approve to schedule
```
The actual publish step is delegated to whatever posting integration you configured (Arcade-Twitter/LinkedIn, or Buffer/Postiz).

## General experience & gotchas (踩坑)
- **It does not post by itself**, it needs a posting backend wired in; treating it as a one-stop publisher is the main misread. Budget for Buffer/Postiz **plus** this.
- **Human-in-the-loop is a feature, not optional**, it intentionally pauses for approval; an unattended/auto-run setup defeats its purpose and can be brittle.
- **Heaviest setup in this domain**, LangGraph runtime + LLM key + ingest key + post backend; far more moving parts than a single post-MCP. Only worth it when curation/quality gating is the actual goal.
- LLM + ingest API costs are **per-run and yours**, the OSS is free, the pipeline calls are not; watch token/ingest spend on large feeds.
- X link-posts still cost **$0.20 each** at the platform level (shard cost trap) when X is the chosen backend, the agent doesn't remove platform write costs.
- Maintained by LangChain and active (pushed 2026-06-09, 2.6k★), but it tracks the fast-moving LangGraph/integration surface, pin versions and re-check the README's required integrations before a run.

## Failure signals & fallback
Failure looks like: the graph stalling at the human-approval node (no reviewer), an ingest/LLM key error during drafting, or the scheduling step failing because the posting backend (Buffer/Postiz/Arcade) isn't connected. **Fallbacks:** for plain posting, drop the pipeline and use **Buffer** (① free tier) / **Postiz** (OSS self-host) / **Blotato** (Claude Code native MCP) directly; for a single free platform, atproto (Bluesky) / Mastodon.py with no agent at all. Use `postiz-agent` if you want a lighter Postiz-only front-end instead of a full curation pipeline.

## Last verified: 2026-06
