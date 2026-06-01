# Domain: content-cms

**Triage signals:** write blog/long-form then publish to CMS, manage WordPress/Ghost/Notion,
headless CMS, 发博客/内容发布.

| source | route | capability | detect | auth |
|---|---|---|---|---|
| **WordPress MCP** (gaupoit / official adapter) | ① | post CRUD + publish, media, categories | connected | Application Password |
| **Ghost MCP** (@ryukimin/ghost-mcp) | ① | 46 tools incl members/newsletter/tiers, OAuth 2.1 | connected | Admin API Key |
| **Sanity hosted MCP** (mcp.sanity.io) | ① | 40+ tools, schema-aware, rules auto-update | connected (OAuth) | best headless experience, GA |
| Contentful MCP (official) | ① | create/edit/publish, multi-locale | connected | CMA token |
| Strapi 5 native MCP | ① | baked-in, token-scoped per content type | self-host | admin token (no new media upload) |
| Notion hosted MCP (mcp.notion.com) | ① | Notion-flavored markdown, token-efficient | connected (OAuth) | as CMS via status property |
| **Pipepost** (multi-platform) | ① | Dev.to+Hashnode+Ghost+WP+Medium + social broadcast | connected | handles canonical + SEO |
| Static blog (Hugo/Astro) + claude-blog skill | — | write MD/frontmatter → git push → Vercel deploy | skill present | zero platform fee |

**Default pick:** Own controllable blog → static (Hugo/Astro + claude-blog skill + git + `/vercel:deploy`,
zero fee). CMS backend → WordPress MCP / Sanity hosted MCP. Cross-platform syndication → Pipepost.

**SEO命门:** any cross-platform syndication MUST set canonical URL to your own original, or get
dedup-penalized. Rate limits: Webflow publish 1/min, Notion ~3 req/s.

**Install guidance:** `reference/volatile/pricing-install.md` → content-cms.
