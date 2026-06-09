# Tool: instaloader/instaloader

- **Domain(s):** social-publishing (also: browser-automation)
- **Barrier route:** ③ · **Source tier:** L4 · **Ready MCP:** no (Python lib + CLI; wrap it yourself)
- **Cost:** free (OSS) — proxies/accounts only at scale
- **Repo / Provider:** github.com/instaloader/instaloader — `instaloader/instaloader (12.5k★, gh-api 2026-06)` (MIT; actively maintained, last push 2026-04)
- **Top pick for its domain:** no (but the safest IG choice when you only need to READ)

## What it does / when to pick it
**Read-only** Instagram downloader: posts, profiles, stories, highlights, followers/followees,
captions, comments, geotags, hashtag feeds. Pick it whenever the IG task is *data collection*, not
posting — it's lower ban-risk than write tools because it only reads. If you need to **post / comment /
DM**, this can't do it → use **instagrapi** ③ instead.

## Install
`pip install instaloader` (Python ≥ 3.10). Ships a CLI (`instaloader profile <name>`) and a Python
API. No ready MCP. Volatile line: `reference/volatile/pricing-install.md` → social-publishing /
browser-automation.

## Auth / keys
Anonymous works for public profiles (very rate-limited). For private/followed content or higher
limits, log in: `instaloader --login=USER` (it stores a session file you reuse). No API key. The IG
password is a secret — user supplies it; never echo it (see `reference/install-guide.md`).

## Usage — call examples
```python
import instaloader
L = instaloader.Instaloader()
L.download_profile("nasa", profile_pic_only=False)   # CLI: instaloader nasa
```
Iterate `Profile.from_username(L.context, "nasa").get_posts()` for metadata without downloading media.

## General experience & gotchas (踩坑)
- Read-only ≠ ban-proof — **anonymous scraping is aggressively rate-limited** and IG throws 401/429
  fast. Authenticated + a saved session + slow pacing is far more reliable; still use a throwaway
  account, not your main.
- IG periodically breaks the unofficial endpoints; keep the lib current (it's actively maintained).
- Stories/highlights and private profiles **require login**; public posts may work anonymously but
  flakily.
- Don't hammer it in a loop — add delays; bursts trip "Please wait a few minutes" and can checkpoint
  the account.

## Failure signals & fallback
`401 Unauthorized` / `429` / `Please wait a few minutes` / `QueryReturnedBadRequestException` =
throttled or endpoint changed → log in, slow down, rotate proxy. If still blocked, fall back to
**playwright MCP** ④ (logged-in browser) or **brightdata** ② (provider absorbs the IG anti-bot wall)
for IG data at scale.

## Last verified: 2026-06
