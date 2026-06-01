# Domain: ecommerce-arbitrage

**Triage signals:** Amazon/eBay/Walmart price, price history, BSR/sales rank, retail/online
arbitrage, cross-platform price compare, 选品/比价/套利.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **Keepa** (+ Keepa MCP cosjef/BWB03) | ① official | **price history curve + BSR/sales history + Buy Box/stock** — irreplaceable | connected + KEEPA_API_KEY | low; €49/mo+ scales with tokens |
| Amazon SP-API (private app) | ① official | your own cost/fees → profit calc | OAuth | private self-use = no dev fee |
| Rainforest API | ② resale | real-time ASIN, Buy Box detection | connected | history weaker than Keepa |
| eBay Browse/Finding API | ① official | item price, discounts, lowest-price compare | AppID | free, official |
| PriceAPI | ② resale | Amazon + Google Shopping + eBay multi-source compare | connected | €499/mo start |
| Oxylabs / Bright Data | ② resale | anti-bot ecom scrape, datasets | mcp connected | absorbs ToS risk |

**Default pick:** Amazon arbitrage → Keepa (the unique foundation) + SP-API private for profit.
Cross-platform compare → PriceAPI, plus free official eBay/Shopify Storefront MCP.

**No usable API (human-only, can't automate):** Helium 10, CamelCamelCamel. Sales numbers from
any tool are *estimates* — cross-check, differences can be multiples.

**Install guidance:** `reference/volatile/pricing-install.md` → ecommerce-arbitrage.
