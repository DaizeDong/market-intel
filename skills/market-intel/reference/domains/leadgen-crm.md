# Domain: leadgen-crm

**Triage signals:** B2B leads, prospecting, email find/verify, company intel, CRM sync, outreach,
获客/销售情报/潜客.

| source | route | capability | detect | note |
|---|---|---|---|---|
| **Apollo.io** (native connector + CC plugin) | ① | find+enrich contacts, ICP prospecting, sequences | connected (OAuth) | ⚠ turn OFF Claude model training before connecting |
| Clay (+ MCP) | ② | waterfall enrichment, 150+ providers | connected + key | best for existing Clay teams |
| Hunter.io (official MCP) | ① | email finder + verifier + enrichment | connected + X-API-KEY | precise email work |
| ZoomInfo / Lusha | ① | enterprise database / mid-tier (free tier) | connected | ZoomInfo $15k+/yr; Lusha 40 free/mo |
| People Data Labs | ① | $0.01/record, cheapest at volume | self-wrap (no MCP) | dev API-first |
| **HubSpot / Salesforce / Attio** (official MCP) | ① | CRM read/write, log activity | connected | use whichever CRM you run |
| Smartlead MCP (LeadMagic) | ① | 113+ tools, deliverability + warmup | connected + key | outreach send/sequence |
| ZeroBounce (official MCP) | ① | email verification, batch | connected + key | only mature verify MCP |
| Bright Data Crunchbase MCP | ② | company intel, real-time public data | connected | free 5k/mo, legally tested |

**Default pick:** Find+enrich → Apollo.io native MCP (turn off training first). Verify → Hunter or
ZeroBounce. Outreach → Smartlead. CRM → your CRM's official MCP. Min combo: Apollo → Hunter/ZeroBounce
→ Smartlead → CRM MCP.

**Compliance red line:** LinkedIn cookie-scraping (PhantomBuster) = 25–35% ban rate — use Bright Data
instead (採集 off your account, legally defended). Any personal-data workflow needs GDPR/CCPA
delete-request handling.

**Install guidance:** `reference/volatile/pricing-install.md` → leadgen-crm.
