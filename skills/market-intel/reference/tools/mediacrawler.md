# Tool: NanmiCoder/MediaCrawler

- **Domain(s):** browser-automation (also: reddit-community, social-publishing)
- **Barrier route:** ④ · **Source tier:** L4 · **Ready MCP:** no (Python CLI / framework; drive directly, no MCP wrapper)
- **Cost:** free (self-host OSS) — proxies are the only hidden cost at scale [github.com/NanmiCoder/MediaCrawler, fetched 2026-06]
- **Repo / Provider:** github.com/NanmiCoder/MediaCrawler — `NanmiCoder/MediaCrawler (50.9k★, gh-api 2026-06)`; license NOASSERTION (non-commercial source-available, see repo LICENSE), active (pushed 2026-05)
- **Top pick for its domain:** no (specialist — the go-to for Chinese platforms, not a general browser tool)

## What it does / when to pick it
Playwright-based crawler purpose-built for **7 Chinese platforms**: 小红书 (Xiaohongshu), 抖音 (Douyin), 快手 (Kuaishou), B站 (Bilibili), 微博 (Weibo), 贴吧 (Tieba), 知乎 (Zhihu). It logs in via a real browser (QR-scan or cookie), then pulls posts, comments, sub-comments, and creator profiles. **Decision rule:** reach for MediaCrawler when the target is a *Chinese* social platform and you need cross-platform breadth in one codebase — it beats stitching together single-platform repos. For 小红书 specifically where you also need to *post* notes, prefer the sibling **xpzouying/xiaohongshu-mcp** (ready Go MCP, route ④). For non-Chinese platforms use the per-platform repos in their own domain shards (twikit for X, instagrapi for IG, etc.). Plain **playwright MCP** is the fallback if you only need one page from one platform.

## Install
Self-host, Python ≥ 3.9. There is **no MCP** — you run it as a project and the agent shells out to it.
```
git clone https://github.com/NanmiCoder/MediaCrawler
cd MediaCrawler
uv sync            # or: pip install -r requirements.txt
uv run playwright install   # fetch the Chromium binary it drives
uv run main.py --platform xhs --lt qrcode --type search --keywords "关键词"
```
Windows note: stdio/MCP flakiness is irrelevant here (no MCP); just ensure the Playwright Chromium binary installed correctly (`playwright install`). Cross-link install mechanics: `reference/install-guide.md` (route ④ prerequisites: throwaway account + proxy pool). No volatile pricing row — it is free OSS; the L1 line lives under `pricing-install.md` → browser-automation → platform-specific repos.

## Auth / keys
No API key. Auth is a **logged-in session**: launch with `--lt qrcode`, scan the QR with the platform's mobile app, and the cookie is cached to `browser_data/` for reuse. You can also paste a cookie string via `--lt cookie` (config `config/base_config.py` → `COOKIES`). Secret-hygiene: the cached cookie under `browser_data/` is a live session credential — treat it like a key, never commit `browser_data/` or paste the cookie into the transcript; use a throwaway account.

## Usage — call examples
CLI flags (`main.py`): `--platform {xhs|dy|ks|bili|wb|tieba|zhihu}`, `--type {search|detail|creator}`, `--keywords`, `--lt {qrcode|cookie}`, plus `ENABLE_GET_COMMENTS` / `ENABLE_GET_SUB_COMMENTS` in `config/base_config.py`.
Minimal example — search 小红书 for a keyword and pull comment trees:
```
# in config/base_config.py: ENABLE_GET_COMMENTS = True
uv run main.py --platform xhs --lt qrcode --type search --keywords "无人机"
# results land in data/ (json/csv) or a DB if STORAGE configured
```

## General experience & gotchas (踩坑)
- **License is non-commercial / source-available (NOASSERTION),** not a permissive OSS license — for paid client deliverables read the repo LICENSE first; scraping these platforms also violates each platform's ToS (ban risk → throwaway account).
- **Rate / ban signals:** Xiaohongshu and Douyin throttle aggressively; without a residential proxy pool (`config` → `ENABLE_IP_PROXY`, `IP_PROXY_POOL_COUNT`) you get sliding-CAPTCHA walls (滑块验证) and 461/risk-control responses within a few hundred requests. Software is free; **proxies are the real cost at scale.**
- **Cookie rot:** cached `browser_data/` sessions expire silently — symptom is an abrupt empty-result run, not an error. Re-scan the QR.
- **Comment depth costs:** `ENABLE_GET_SUB_COMMENTS` multiplies request volume (each top comment fans out) — the fastest way to trip risk-control. Pull top-level first, sub-comments only when needed.
- **Field quirks:** 抖音/快手 return short-lived signed media URLs; download immediately, don't store the URL. Note volumes (点赞/收藏) are snapshot-at-fetch, not historical.

## Failure signals & fallback
You know it failed when: QR login loops without caching a cookie, runs return empty `data/` with a 461/滑块 in the browser, or the platform serves a risk-control interstitial. **Fallback ladder:** (1) for 小红书 posting *and* reading, switch to **xpzouying/xiaohongshu-mcp** (ready MCP); (2) for 微博 specifically, **dataabc/weibo-crawler**; (3) for a one-off single page, drop to the already-connected **playwright MCP** with a throwaway logged-in session; (4) if fingerprint-blocked, route the browser through **camoufox** / **camofox-browser**.

## Last verified: 2026-06
