# Tool: towfiqi/serpbear

- **Domain(s):** seo-keywords (also: none)
- **Barrier route:** ④ self-host · **Source tier:** L4 · **Ready MCP:** no, self-hosted web app + REST API; drive via its API or UI
- **Cost:** free (self-host; optional paid scraper add-on) [github.com/towfiqi/serpbear, gh-api 2026-06]
- **Repo / Provider:** github.com/towfiqi/serpbear, towfiqi/serpbear (2.0k★, gh-api 2026-06; MIT, last push 2026-05-14, active)
- **Top pick for its domain:** yes, the free-route default *pairing* for rank tracking alongside SearXNG (★ in index)

## What it does / when to pick it
SerpBear is a self-hosted **keyword rank tracker**: add domains + keywords, and it records daily SERP position over time with email/Slack/webhook alerts and a small REST API. It **replaces paid rank-monitoring** (the rank-tracking slice of Semrush/SE Ranking/Ahrefs) at zero subscription cost. Pick it when the deliverable is "track where my/competitor keywords rank over days/weeks", not one-off SERP pulls. For ad-hoc SERP scraping use SearXNG; for search *volume*/difficulty/backlinks use DataForSEO/SE Ranking/Ahrefs (SerpBear tracks position only). It pairs naturally with SearXNG, which can act as its scraping backend.

## Install
Self-host via Docker (no MCP package):
```
docker run --rm -d -p 3000:3000 -e USER=admin -e PASSWORD=<pw> -e SECRET=<rand> -e APIKEY=<rand> -v "${PWD}/serpbear_data:/app/data" towfiqi/serpbear
```
Then open `http://localhost:3000`, add a domain + keywords, and configure a scraper (see Auth). No MCP transport, read data via its REST API. See `reference/install-guide.md` for route-④ Docker prerequisites + Windows notes; confirm the current command in `reference/volatile/pricing-install.md` → seo-keywords.

## Auth / keys
App login is `USER`/`PASSWORD`; the REST API uses the self-generated `APIKEY` header (you set it at deploy time). The **SERP scraping backend** is separate: SerpBear needs a source to read Google positions, either a paid scraper (ScrapingRobot/SerpApi/SpaceSerp key) or **point it at your self-hosted SearXNG** to stay fully free. Since all keys here are *your own* self-generated secrets in your container env, the only hygiene rule is the standard one, keys live plaintext in env/`~/.claude.json`; never commit or screenshot. One-line pointer: `reference/install-guide.md` § secret hygiene.

## Usage, call examples
Read tracked keywords for a domain via REST:
```
curl -H "Authorization: <APIKEY>" "http://localhost:3000/api/keywords?domain=example.com"
```
Returns each keyword's current `position`, `history` (dated positions), `url`, and `lastUpdated`. Add keywords via `POST /api/keywords`.

## General experience & gotchas (踩坑)
- **No scraper = no data.** SerpBear itself does NOT scrape; out of the box positions stay blank until you wire a scraping source. The free path is to set SearXNG/your scraper as the backend, otherwise you're back to a paid SERP key, defeating the free-route purpose.
- **Google throttling hits the backend, not SerpBear.** If positions stop refreshing, the failure is in the scraper/proxy layer (CAPTCHA, IP block), not the app. Add proxies at volume.
- **Daily cadence only**, it's a tracker, not a real-time SERP API. Don't use it for one-shot lookups (use SearXNG/playwright for those).
- Self-generated `SECRET`/`APIKEY` must be set or auth/sessions misbehave; keep them stable across restarts or you lock yourself out.
- Mobile vs desktop and country/locale must be set per keyword; mismatched locale silently tracks the wrong SERP.

## Failure signals & fallback
Blank/stale positions, or alerts never firing = scraper backend down or unconfigured (check the scraper key/SearXNG endpoint). If rank history is the goal and self-host is too much upkeep, fall back to a paid rank tracker (**SE Ranking** 14-day trial, or **Semrush** Pro). For one-off SERP pulls instead of tracking, use **SearXNG** (④) or **playwright MCP**.

## Last verified: 2026-06
