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

## ④ Browser/OSS route (free, self-host)
| repo | route | note |
|---|---|---|
| **gosom/google-maps-scraper** (4.2k★) | ④ self-host | local B2B leads: name/phone/site/**email**, **far lower risk than LinkedIn** |
| omkarcloud/google-maps-scraper (2.7k★) | ④ | 50+ fields incl email/socials + enrichment |
| joeyism/linkedin_scraper (4.2k★) | ④ | Selenium + your login session; ⚠ highest ban risk, small batch only |
| cullenwatson/StaffSpy (254★) | ④ | scrape company staff lists; ⚠ ToS/ban risk |

**Default (free route):** for local-business B2B leads use **gosom/google-maps-scraper** (emails +
phones, low legal risk). Avoid LinkedIn scraping when possible — if unavoidable use a throwaway acct.

**Compliance red line:** LinkedIn cookie-scraping (PhantomBuster / joeyism) = 25–35% ban rate — use
Bright Data instead (採集 off your account, legally defended) or pivot to Google Maps leads. Any
personal-data workflow needs GDPR/CCPA delete-request handling.

**Install guidance:** `reference/volatile/pricing-install.md` → leadgen-crm.
