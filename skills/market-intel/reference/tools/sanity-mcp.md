# Tool: Sanity hosted MCP

- **Domain(s):** content-cms (also: none)
- **Barrier route:** ① · **Source tier:** L1 · **Ready MCP:** yes — hosted HTTP `https://mcp.sanity.io` (OAuth, GA)
- **Cost:** free tier $0 forever (2 datasets, 20 seats); Growth $15/seat/mo [https://www.sanity.io/pricing, fetched 2026-06]
- **Repo / Provider:** https://www.sanity.io (hosted MCP, not a self-host repo)
- **Top pick for its domain:** yes (best headless experience)

## What it does / when to pick it
Sanity's official hosted MCP: **40+ schema-aware tools**; it reads your project's schema and keeps its rules auto-updated, so writes respect your content types. **Decision rule:** pick this when the project is a true **headless / structured-content** CMS (multi-channel, typed content, GROQ queries) — it is the cleanest headless experience in the domain. If the backend is a plain WordPress blog, use WordPress MCP; if you just want a fully owned blog with no platform, use static (Hugo/Astro).

## Install
See `reference/volatile/pricing-install.md` → content-cms. Two paths: the `sanity` CLI auto-configures the MCP, **or** add the remote HTTP MCP `https://mcp.sanity.io` and complete the **OAuth** flow. HTTP transport is Windows-friendly (no local Node process). Restart / `/mcp` reconnect after adding; OAuth servers show `! Needs authentication` until you finish the browser consent.

## Auth / keys
OAuth — no long-lived API key to paste, so there is little to leak. Authorize in the browser, grant the project, done. (No secret-hygiene clipboard dance needed here since it's OAuth, not a bearer key.) See `reference/install-guide.md` for the connect/verify mechanics.

## Usage — call examples
Tools cover document create/patch/publish, schema introspection, GROQ query, and dataset ops. Minimal flow: introspect schema → create a document of the right type → patch fields → publish. Because it's schema-aware, malformed-type writes are rejected up front rather than silently stored wrong.

## General experience & gotchas (踩坑)
- **GA, schema-aware = the domain's strongest fit** for structured content; this is why it's a top pick alongside WordPress MCP.
- Free tier = **public datasets only** (private datasets start at Growth $15/seat/mo) — research/test in a public dataset is fine, but don't assume privacy on $0.
- OAuth scope is per-project/per-org; if you're in the wrong org the tools connect but return empty/permission errors — confirm the active project.
- Drafts vs. published is a real distinction in Sanity (`drafts.` prefix); "I created it but it's not live" usually means you created a draft and never published.
- **SEO命门:** if Sanity feeds a site that also syndicates, set canonical on the rendered front-end.

## Failure signals & fallback
`! Needs authentication` in `claude mcp list` (OAuth not completed) or empty results (wrong org/project). Fallback within domain: **WordPress MCP** for a blog backend, or **Contentful MCP** as the other major headless option (multi-locale).

## Last verified: 2026-06
