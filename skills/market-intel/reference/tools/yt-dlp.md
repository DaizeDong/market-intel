# Tool: yt-dlp/yt-dlp

- **Domain(s):** browser-automation (also: reddit-community)
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** no (CLI / Python lib; the agent shells out or imports it)
- **Cost:** free (open source, Unlicense / public domain). No API cost; proxies/cookies only when a target rate-limits or geo-blocks.
- **Repo / Provider:** github.com/yt-dlp/yt-dlp, `yt-dlp/yt-dlp (169.4k★, gh-api 2026-06)`, Unlicense, pushed 2026-06
- **Top pick for its domain:** no (but the de-facto standard for media + media-metadata extraction)

## What it does / when to pick it
The standard **media downloader + metadata extractor** for YouTube and 1000+ sites (TikTok, Twitter/X video, Reddit video, Instagram, Bilibili, etc.). For market-intel its **metadata** mode is the real value: view counts, upload dates, titles, descriptions, channel stats, and full subtitle/transcript pulls, without downloading bytes. **Pick it** whenever the signal lives in a video platform (creator reach, view velocity, transcript text for sentiment) rather than writing a bespoke scraper. Cross-domain: pull Reddit/X video metadata where the platform API is thin.

## Install
`pip install yt-dlp` (or `pip install -U yt-dlp` to update, it updates constantly) or a standalone binary. Not an MCP, shell out to the CLI or `import yt_dlp`. L1 line: `reference/volatile/pricing-install.md#browser-automation`. Works fine on native Windows (single binary / pip), no Playwright path quirks. Pair with `ffmpeg` only if you actually need to merge/convert media (metadata pulls don't).

## Auth / keys
No service key. For age-gated / login-walled / rate-limited content, supply **browser cookies**: `--cookies-from-browser chrome` or a `--cookies cookies.txt` file. Cookies are session secrets, treat like keys: don't echo or commit them; the user exports them themselves (see `install-guide.md` secret hygiene). For scrape-heavy pulls use a throwaway account's cookies.

## Usage, call examples
```bash
# metadata only, no download — the market-intel workhorse:
yt-dlp --skip-download --print "%(title)s | %(view_count)s | %(upload_date)s" <url>
yt-dlp -J <url>                       # full JSON metadata to stdout
yt-dlp --write-auto-subs --sub-lang en --skip-download <url>   # transcript
```
```python
import yt_dlp
with yt_dlp.YoutubeDL({"skip_download": True}) as y:
    info = y.extract_info(url, download=False)   # dict: view_count, etc.
```
Use `-J` / `extract_info(download=False)` to get structured stats without pulling bytes.

## General experience & gotchas (踩坑)
- **Update constantly.** Platforms change extractors weekly; a stale yt-dlp silently breaks (`Unable to extract`, signature errors). `pip install -U yt-dlp` is step 0 of any debugging, most "it stopped working" is just an old version.
- **Use `--skip-download`/`-J` for intel**, you almost never need the media file; metadata + subtitles are the signal and are far faster/lighter.
- **Rate limits & throttling:** bulk pulls trigger 429 / "Sign in to confirm you're not a bot." Add cookies, slow down (`--sleep-requests`), or proxy. YouTube has tightened bot checks, cookies fix most of it.
- **Geo/age/login walls** need cookies; without them some fields come back null silently, check for empty `view_count`/`uploader` rather than trusting success.
- **ToS:** downloading violates most platforms' terms even though the tool is legal; for market-intel prefer metadata-only and respect robots/rate limits.

## Failure signals & fallback
Failed = `Unable to extract ...` / `Sign in to confirm you're not a bot` / 429 / null metadata fields. Fixes-then-fallbacks: update yt-dlp, add cookies, throttle/proxy. If a platform fully blocks it, fall back to that platform's own route, e.g. **twitterapi.io ②** for X, the **reddit** MCPs for Reddit, **TikTok-Api** for TikTok, or **playwright MCP** to read the rendered page directly.

## Last verified: 2026-06
