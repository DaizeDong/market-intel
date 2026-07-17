# Domain: content-cms

**Triage signals:** write blog/long-form then publish to CMS, manage WordPress/Ghost/Notion,
headless CMS, 发博客/内容发布.

| source | route | capability | detect | auth |
|---|---|---|---|---|
| **WordPress MCP** (WordPress/mcp-adapter, 1236★ official) | ① | post CRUD + publish, media, categories via Abilities API | connected | App Password; **D-SUPERSEDED** old gaupoit (0★) / archived Automattic/wordpress-mcp |
| **Ghost MCP** (MFYDev/ghost-mcp, 199★) | ① | ~45 tools incl members/newsletter/tiers | connected | Admin API Key; old @ryukimin/ghost-mcp **D-404** (community repo, not official Ghost org) |
| **Sanity hosted MCP** (mcp.sanity.io) | ① | 40+ tools, schema-aware, rules auto-update | connected (OAuth) | best headless experience, GA |
| Contentful MCP (contentful/contentful-mcp-server 58★) | ① | create/edit/publish, multi-locale | connected | CMA token; free 100k API calls/mo |
| Strapi 5 native MCP | ① | baked-in, token-scoped per content type | self-host | admin token (no new media upload) |
| Notion hosted MCP (mcp.notion.com) | ① | Notion-flavored markdown, token-efficient | connected (OAuth) | as CMS via status property |
| **directus/mcp** (79★ official) | ① | official MCP for Directus (SQL-backed headless CMS, 36k★) | connected | for SQL-backed headless stacks |
| **webflow/mcp-server** (132★ official) | ① | Webflow CMS collections/items/publish | connected (OAuth) | fills the Webflow gap (was a rate-limit footnote only) |
| **Pipepost** (multi-platform) | ① | Dev.to+Hashnode+Ghost+WP+Medium + social broadcast | connected | handles canonical + SEO |
| Static blog (Hugo/Astro) + claude-blog skill |, | write MD/frontmatter → git push → Vercel deploy | skill present | zero platform fee |

**Default pick:** Own controllable blog → static (Hugo/Astro + claude-blog skill + git + `/vercel:deploy`,
zero fee). CMS backend → WordPress MCP / Sanity hosted MCP. Cross-platform syndication → Pipepost.

**SEO命门:** any cross-platform syndication MUST set canonical URL to your own original, or get
dedup-penalized. Rate limits: Webflow publish 1/min, Notion ~3 req/s.

**Install guidance:** `reference/volatile/pricing-install.md` → content-cms.

**Saturation flag (set 2026-06-17 sweep):** 10+ sources cover headless/visual/syndication routes;
5 fresh candidates from the 2026-06-17 sweep all demoted to watch as not needle-moving. Next sweep:
**skip full Discovery for this domain** unless a real-run `live-runs.jsonl` entry surfaces a gap
(P6 honest boundary, don't burn Discovery budget on a saturated domain).
