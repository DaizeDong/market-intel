# Tool: eBay Browse/Finding API

- **Domain(s):** ecommerce-arbitrage (also: none)
- **Barrier route:** ① official · **Source tier:** L1 · **Ready MCP:** no (official REST + AppID; wrap it yourself)
- **Cost:** **free** (official API, generous call quota; standard app limit ~5,000 calls/day on Browse) [https://developer.ebay.com]
- **Repo / Provider:** https://developer.ebay.com (official eBay Developers Program; no GitHub repo)
- **Top pick for its domain:** no (but the free, official, no-ToS-risk eBay leg)

## What it does / when to pick it
Official eBay item data: **current listing price, discounts, lowest-price compare** across live listings (Browse API; the legacy Finding API is sunset → use **Browse** / Marketplace Insights). Pick it whenever the cross-platform compare includes eBay — it's free, official, zero ban risk, so always prefer it over scraping eBay. For a multi-source compare (Amazon + Google Shopping + eBay in one call) PriceAPI is more convenient but paid; eBay's own API is the free, authoritative leg.

## Install
No MCP. Register an app at `developer.ebay.com` → get the **AppID** (client id/secret) → OAuth client-credentials token → REST. HTTP/REST only. The volatile one-liner note lives in `pricing-install.md` → `ecommerce-arbitrage` (eBay: developer.ebay.com AppID, free). Wrap the REST behind a thin tool; there's no `claude mcp add` for it.

## Auth / keys
Create a developer account → an app keyset (Production + Sandbox). Browse API uses an **OAuth application token** minted from client id/secret (client-credentials grant) — no user login needed for public item data. Key-bearing → hygiene one-liner: keep client-secret out of the transcript/git; env or direct `~/.claude.json`. See `reference/install-guide.md` (Secret-handling hygiene).

## Usage — call examples
Mint token: `POST https://api.ebay.com/identity/v1/oauth2/token` (client-credentials, scope `…/scope`). Then search: `GET https://api.ebay.com/buy/browse/v1/item_summary/search?q=KEYWORD&filter=price:[..]&sort=price` → lowest-price compare. `GET /buy/browse/v1/item/{itemId}` for one item. Sold/median data needs **Marketplace Insights API** (gated approval).

## General experience & gotchas (踩坑)
- **Finding API is legacy/being retired** — code against **Browse**; old tutorials pointing at `findItemsByKeywords` will rot.
- **Sold/completed prices (the real arbitrage signal) are gated:** Browse shows *active* listings only. Median/sold comps require Marketplace Insights API, which needs a separate business-justification approval — plan for it, don't assume sold data is one call away.
- Sandbox returns fake inventory — always confirm you're hitting the **Production** host before trusting prices.
- Application token expires (~2h) and must be refreshed; a 401 mid-run is usually an expired token, not a bad key.
- Marketplace is per-site (`EBAY_US`, `EBAY_GB`…) via the `X-EBAY-C-MARKETPLACE-ID` header — omitting it defaults to US and silently skews a non-US compare.

## Failure signals & fallback
Failure: HTTP 401 (expired/invalid token), 403 (scope not granted — common for Insights), or empty `itemSummaries`. **Fallback:** PriceAPI ② (paid, includes eBay + Amazon + Google Shopping in one) for convenience, or playwright ④ to read a sold-listings page if Insights access is denied. Flag the gap when sold data is unavailable.

## Last verified: 2026-06
