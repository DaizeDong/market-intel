# Domain: ready-skills

**Triage signals:** "is there a ready-made skill/plugin for marketing/SEO/content/research", don't
want to assemble MCPs from scratch, 现成的营销/调研 skill.

> Ecosystem reality: marketing / SEO / content / research skills are abundant and install-and-go.
> Business-ops深度 and arbitrage/making-money are scarce — still need MCP assembly + custom logic.

| resource | type | use | get |
|---|---|---|---|
| **coreyhaines31/marketingskills** (32.6k★) | skill bundle | ~40 skills: customer-research, competitor-profiling, programmatic-seo, directory-submissions, copy, ads, email | `npx skills add coreyhaines31/marketingskills` |
| **ericosiu/ai-marketing-skills** (2.6k★) | skill bundle | finance-ops / sales-pipeline / revenue-intel / outbound / lead-dossier — fills the "business-ops scarce" gap | `git clone` + pip + cp (NOT npx) |
| **indranilbanerjee/digital-marketing-pro** (133★) | skill bundle | AEO/GEO answer-engine optimization (ChatGPT/Perplexity/Google AI Mode) | GitHub |
| **Anthropic official Marketing plugin** | official plugin | /competitive-brief, /seo-audit, /campaign-plan; connects HubSpot/Ahrefs/Klaviyo | claude.com/plugins/marketing |
| **AgricIDaniel/claude-seo** (8.5k★) | plugin | strongest SEO, 25 sub-skills + 18 agents, offline | `/plugin marketplace add AgricIDaniel/claude-seo` |
| **ishwarjha/claude-marketing-research-skill** | packaged skill | 6-stage market research workflow (competitor→product→persona→positioning) | GitHub |
| alirezarezvani/claude-skills (17.6k★) | mega bundle | 338 skills incl market-research, c-level, finance | `/plugin marketplace add alirezarezvani/claude-skills` |
| ComposioHQ/awesome-claude-skills (63.8k★) | catalog | deep-research, lead-research-assistant; discovery hub | GitHub |

**Default pick:** Marketing/competitor/content → coreyhaines31/marketingskills (装了即用). SEO →
claude-seo. Packaged market-research pipeline → ishwarjha. Discovery → ComposioHQ catalog.

**Judgment:** marketing/SEO/content/research = rich, install直用; business-ops深度 + arbitrage =
scarce, still assemble MCPs. Every skill's ceiling = which data MCPs you connect — the skill is a
shell; the work moved to MCP wiring + auth.

**Install guidance:** these are skills/plugins, not MCPs — install via the get-column commands.
