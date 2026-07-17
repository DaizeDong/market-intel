# Tool: dataabc/weibo-crawler

- **Domain(s):** browser-automation (also: social-publishing)
- **Barrier route:** ④ · **Source tier:** L4 · **Ready MCP:** no (Python script / config-driven; the agent runs it directly)
- **Cost:** free (open source). ⚠ **No LICENSE file** in the repo (gh-api 2026-06), no explicit grant; treat as research-only and don't assume reuse rights. Proxies/cookies are the hidden cost.
- **Repo / Provider:** github.com/dataabc/weibo-crawler, `dataabc/weibo-crawler (4.5k★, gh-api 2026-06)`, no license, pushed 2026-05
- **Top pick for its domain:** no

## What it does / when to pick it
A focused crawler for **微博 (Weibo)**: pull a given user's posts (text, images, video links, reposts), post metadata (likes/comments/reposts counts, timestamps), and basic profile info, exporting to CSV/JSON/MySQL/MongoDB/SQLite. **Pick it when the target is specific Weibo users/accounts** and you want a ready config-driven pull. For multi-platform Chinese coverage (also 抖音/小红书/B站/快手/知乎/贴吧) prefer **NanmiCoder/MediaCrawler** (50k★); use weibo-crawler when Weibo is the whole job and you want the lighter single-purpose tool.

## Install
`git clone https://github.com/dataabc/weibo-crawler && pip install -r requirements.txt`, then edit `config.json` (target user IDs, fields, date range, output format). Run `python weibo.py`. Python ≥3.x. Not an MCP, driven by config + script. L1 line: `reference/volatile/pricing-install.md#browser-automation`. Works on native Windows (pure-Python requests, no Playwright). README/config are in Chinese.

## Auth / keys
No service key. It reads Weibo's m.weibo.cn endpoints; for anything beyond public/limited data you must supply a **logged-in cookie** in `config.json` (`cookie` field). The cookie is a session secret, treat like a key: user supplies it themselves, don't echo/commit it (see `install-guide.md` secret hygiene). **Use a throwaway Weibo account**, this is route ④, ToS-violating, ban risk on the account whose cookie you use.

## Usage, call examples
```jsonc
// config.json (excerpt)
{ "user_id_list": ["1234567890"],   // target Weibo UID(s)
  "since_date": "2026-01-01",
  "write_mode": ["csv", "json"],
  "cookie": "<your logged-in cookie>" }
```
```bash
python weibo.py        # crawls per config.json, writes to ./weibo/<uid>/
```
Drop a `user_id_list.txt` for batch targets; output lands per-user under `./weibo/`.

## General experience & gotchas (踩坑)
- **Cookie is mandatory for real coverage.** Without a logged-in cookie you get a thin/empty pull; with one you risk that account, always a throwaway, never a primary.
- **Weibo throttles aggressively.** Rapid pulls trigger rate limits / empty pages / the account getting challenged. Slow the crawl, cap UIDs per run, rotate cookies+proxies for volume. Proxies are the real cost at scale (software is free).
- **Brittle to Weibo's changes.** It depends on m.weibo.cn response shapes; when Weibo tweaks them fields go null or the crawl stalls silently, check for empty output, don't trust exit code. Last push 2026-05 (active), but verify it still works before a big run.
- **No license** is the sharpest catch vs. siblings, research use only; don't bundle/redistribute.
- **Chinese-language config & docs**, field names and README are 中文; budget time to map config keys.

## Failure signals & fallback
Failed = empty/partial CSV, null engagement counts, the crawl stalling, or a challenge/login redirect (cookie expired or account flagged). Fallbacks: refresh the cookie / swap to another throwaway, add proxies + throttle; for broader Chinese-platform coverage switch to **NanmiCoder/MediaCrawler**; or drive **playwright MCP** against the rendered m.weibo.cn page for a small manual pull.

## Last verified: 2026-06
