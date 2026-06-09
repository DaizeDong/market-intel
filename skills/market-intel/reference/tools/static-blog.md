# Tool: Static blog (Hugo/Astro + claude-blog skill)

- **Domain(s):** content-cms (also: none)
- **Barrier route:** — (no barrier; you own the target) · **Source tier:** L1 · **Ready MCP:** no — workflow via the `claude-blog` skill + git + `/vercel:deploy`
- **Cost:** **free** — zero platform fee. Hugo is FOSS (Apache-2.0, gohugo.io, fetched 2026-06); Astro is MIT. Only possible cost is hosting, and Vercel/Netlify/GitHub Pages have free tiers.
- **Repo / Provider:** Hugo — https://gohugo.io (Apache-2.0, active, frequent releases per official site 2026-06). Astro alternative — https://astro.build (MIT). Not a single GitHub repo; it's a generator + your own content repo.
- **Top pick for its domain:** yes (the default when you control the publishing target)

## What it does / when to pick it
Write `.md` files with YAML/TOML front matter → a static site generator (Hugo or Astro) builds plain HTML → `git push` → host auto-deploys. **Decision rule (shard default-pick):** this is THE pick when you want your **own controllable blog** — no platform lock-in, no per-call fee, no API tokens to rotate, fully versioned in git. Choose a hosted CMS backend (**WordPress MCP / Sanity hosted MCP**) only when a non-technical team needs a web editor or the content is already in a CMS. For blasting one post across many platforms after publishing, layer **Pipepost** on top (canonical = this blog).

## Install
No MCP / no `claude mcp add` — it's a build-and-push workflow. Install Hugo (`winget install Hugo.Hugo.Extended` on Windows, or `brew install hugo`) or scaffold Astro (`npm create astro@latest`). The `claude-blog` skill (if present in your skill set) drives "write MD/front-matter → commit → deploy"; deploy is handled by `/vercel:deploy` (the Vercel deploy command is available in this environment). See `reference/volatile/pricing-install.md` → content-cms and `reference/install-guide.md` (L0). ⚠ The `claude-blog` skill is referenced by the shard but was **not found in this repo's skill set (2026-06)** — if it's missing, the workflow still works via Hugo/Astro + git + `/vercel:deploy` directly.

## Auth / keys
**None for the content itself** — there are no API keys; the blog is just files in a git repo. The only credential is your git/host login (GitHub + Vercel), which you authenticate once in the browser. Nothing secret enters the transcript, so the usual key-leak hazard does not apply here. (If you wire a deploy token for CI, treat it per `reference/install-guide.md` → Secret-handling hygiene.)

## Usage — call examples
1. Create a post: `content/posts/my-post.md` with front matter (`title`, `date`, `draft: false`, `canonicalURL`, tags).
2. Preview: `hugo server -D` (or `npm run dev` for Astro).
3. Build + ship: `git add . && git commit -m "post: ..." && git push` → host rebuilds, or run `/vercel:deploy`.
The deliverable is a live URL on your own domain — this URL is the **canonical original** that all syndication (Pipepost, Dev.to, Medium) should point back to.

## General experience & gotchas (踩坑)
- **This is the canonical source of truth (SEO命门):** because you own it, set every syndicated copy's `rel=canonical` to *this* post's URL. The static blog should be published *first*, then syndicated — never the other way around, or you eat a dedup penalty.
- **Zero ongoing cost / zero ban risk** — no platform account to get throttled or banned, no token to rotate. This is exactly why the shard makes it the default (CONSTITUTION C2: prefer free/own-controllable).
- **Build-time, not write-time:** content only goes live after a successful build + deploy. A broken front-matter field or a bad shortcode fails the *build* (the post silently never appears) rather than erroring on save — check the deploy log, not just the commit.
- **Hugo "Extended" matters:** the non-extended build can't process SCSS/asset pipelines; symptom is a cryptic build failure on themes that use them. Install the Extended edition.
- **Draft trap:** `draft: true` (or a future `date`) makes Hugo skip the page in a production build — the post is committed but invisible. Verify with the live URL, not the repo.
- **No backend = no comments/forms/members** out of the box (use a third-party widget or Ghost if you need members/newsletter).

## Failure signals & fallback
Failure = the deploy log shows a build error (front matter / template / missing Extended build), or the page 404s because of `draft`/future-date. Fix the source and re-push — there's no live-edit safety net. If the team genuinely needs a web editor or members/newsletter, fall back to a CMS backend: **WordPress MCP** or **Sanity hosted MCP** (per shard default-pick); for multi-platform reach keep this blog as canonical and add **Pipepost**.

## Last verified: 2026-06
