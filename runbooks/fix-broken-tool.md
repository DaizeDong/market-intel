# Incident runbook, fixing a broken matrix entry

Use this when a tool in the source matrix is found broken in the wild, either (a) a user
hits a dead/changed/paywalled entry mid-research, or (b) a refresh sweep (monthly / weekly /
opportunistic) discovers an entry that no longer behaves as advertised. The six steps below
are canonical; do them in order, do not skip. The point is to convert a one-off incident
into a permanent matrix improvement plus a feedback-loop record, without silent deletion
(C7 / R3) and without quietly drifting the matrix (P3).

---

## 1. Log to the live-run ledger (`<data>/metrics/live-runs.jsonl`, PRIVATE store, not this repo)

Append one JSON line. Schema:

```
{"ts":"YYYY-MM-DDTHH:MM:SSZ","domain":"<shard>","source":"<slug>","route":"①②③④","outcome":"<one of 6>","detail":"<≤200 chars, evidence>","user_correction":null|"<user verbatim>"}
```

`outcome` MUST be one of these six (any other string fails Step -1 bucket parsing in
`refresh-protocol.md`):

| outcome | when to use | example detail |
|---|---|---|
| `dead` | repo 404 / archived / endpoint gone | `gh api repos/kukapay/funding-rates-mcp → 404 since 2025-04` |
| `barrier_found` | new paywall / captcha / TOS hostility | `Etherscan free-tier dropped chain X; needs paid Pro $99/mo` |
| `coverage_gap` | user question the matrix can't answer | `no shard covers Telegram channel scraping for SEA markets` |
| `price_mismatch` | shard price / rank / capability blurb wrong vs official site | `shard says €19 Keepa Basic, official page says €24 as of 2026-06` |
| `verified` | tool was actually used and worked | `pulled live Amazon LP6 Pro price via brightdata scrape_as_markdown OK` |
| `user_correction` | user manually overrode our inference | (set `user_correction` field to the quoted user text) |

Append with redirection, do not pretty-print, do not reorder existing lines, one line per entry.

**Verify:** `tail -1 "$(python tools/datadir.py --path market-intel metrics/live-runs.jsonl)" | python -c "import json,sys; json.loads(sys.stdin.read())"` exits 0.

**Common mistake:** logging the outcome as `fallback_used` or `unverifiable` (legacy free-form
strings present in older entries). Step -1's bucket table only knows the six above; anything
else is silently dropped and the incident loses its feedback-loop weight. Use the closest of
the six. If a tool fell back, it's usually `coverage_gap` (matrix couldn't cover the need) or
`barrier_found` (a barrier blocked the route).

## 2. Identify the D-code

Pick the death code per `skills/market-intel/reference/refresh-protocol.md` §防退化协议 step 3
and §R3. The five canonical codes:

| code | meaning | trigger |
|---|---|---|
| `D-404` | repo / endpoint gone | `gh api` returns 404, DNS NXDOMAIN, dead URL |
| `D-PRICE` | priced out of usefulness | free tier killed, paywall added, price jumped past the domain's affordability threshold |
| `D-STALE` | abandoned but technically reachable | last commit >12mo, no releases, issues piling up unanswered |
| `D-TOS` | TOS / legal hostility | platform actively bans scraping, captcha walls, account bans on usage |
| `D-SUPERSEDED` | replaced by a clearly better thing | newer official MCP exists, upstream moved, fork took over |

**Verify:** the code matches the evidence in Step 1's `detail` field. A `D-404` entry should
cite an HTTP 404 / `gh api` error; a `D-PRICE` should quote the new price page; etc.

**Common mistake:** using `D-SUPERSEDED` when there is no documented successor yet, that's
`D-STALE` or `D-404`. Reserve `D-SUPERSEDED` for cases where you can name the replacement.

## 3. Edit the shard

Open `skills/market-intel/reference/domains/<domain>.md`. Find the row for the broken tool.
Replace it with a tombstone row:

```
| ~~<original name>~~ | ~~<route>~~ | ⚠ Avoid (dead, D-<code>) — <one-line reason + URL/evidence> | — | — |
```

If a successor exists, ADD a new row ABOVE the tombstone (do not collapse them into one
row, keep both visible so the dead entry isn't re-hallucinated next sweep, per R3):

```
| **<successor name>** (<repo> <N>★) | ① | <capability> | <detect> | replaces `<old slug>` (D-<code> since YYYY-MM); <why successor wins> |
```

If the broken tool was the **default pick** at the bottom of the shard, update the
"Default pick:" line to name the successor (or a fallback if there is none).

**Verify:** open the file, confirm the old name is struck through, the D-code appears, and
the row count matches (tombstone + optional successor). Run
`python skills/market-intel/tools/verify_matrix.py` and confirm STRUCT / REPO / FRESH all
pass; STALE may WARN until §R2 re-verify advances `## Last verified`.

**Common mistake:** deleting the row instead of tombstoning. Silent deletion lets the next
Discovery sweep re-find the dead tool and "rediscover" it as new (R3). Always leave the
tombstone in place. Also: per R3, a `rebrand` (Polygon → Massive) is not a death, keep it
live and tag REBRAND in the note column instead of using a D-code.

## 4. Update `sources-index.md`, only if the top pick changed

Most fixes (a single non-default entry going dead) do NOT touch `sources-index.md`. Edit it
**only** when the shard's `**Default pick:**` line has been updated and the index's one-line
summary of that domain now points at a different top tool.

When you do edit it: change exactly the one cell that names the changed top pick, leave the
domain row's other cells alone. The index is a navigation aid, not a duplicate matrix.

**Verify:** `grep "<old top pick name>" skills/market-intel/reference/sources-index.md` returns
nothing for that domain's row. `verify_matrix.py` STRUCT check passes (index↔shard consistency).

**Common mistake:** updating the index "just in case" when the default pick is unchanged.
That introduces noisy diffs and triggers spurious STRUCT mismatches if the index drifts
ahead of the shard. Touch it only when the shard's default actually moved.

## 5. (If companion-config installed) update config side

Skip this step entirely if there is no companion `market-intel-config` repo on this machine
(check with `ls C:\Users\<username>\CodesClaude\market-intel-config`, if absent, jump to Step 6).

When present, run the drift checker from the config repo:

```
python C:\Users\<username>\CodesClaude\market-intel-config\scripts\sync-check.py
```

The tombstone you just added in Step 3 will surface in **bucket C** ("Config points to a
skill doc tombstoned `⚠ Avoid (dead, D-xxx)`"). Follow the per-D-code action per
`market-intel-config/runbooks/sync-with-skill.md` §C, typically: remove the tool's row from
`registry.json`, delete its `secrets/<slug>.env`, and (if there's a successor) point
`replacement_for: "<successor-slug>"` from the old entry to the new one. Buckets D / E
(orphan secret / orphan MCP) may follow once the registry row is gone, clear those too.

**Verify:** re-run `python scripts/sync-check.py`; the C bucket count for this slug is now 0.

**Common mistake:** clearing bucket C by deleting the secret first and the registry row
second, leaves the registry pointing at a non-existent secret file for a window. Do
registry first, then secrets, then re-run the check.

## 6. Commit with prefix `incident: <slug> D-<code>`

One commit per incident. Message format:

```
incident: <slug> D-<code> — <≤60 char summary>

<2-4 line body: what broke, evidence URL, successor if any, downstream config touched yes/no>
```

The `incident:` prefix is load-bearing: `git log --grep="^incident:"` is the canonical
incident audit list across the matrix's lifetime, and CHANGELOG cleanup passes use it to
batch incidents into the next monthly entry.

**Verify:** `git log --grep="^incident:" -1 --oneline` shows your commit at HEAD.

**Common mistake:** lumping the incident fix into a multi-purpose commit ("monthly sweep
+ this dead tool"). The grep-prefix loses signal, keep incidents in their own commits even
during a sweep.

---

## Worked example, `kukapay/funding-rates-mcp` stale in a crypto-defi sweep

Suppose a `crypto-defi` weekly Discovery sweep flags `kukapay/funding-rates-mcp` as
unreachable: `gh api repos/kukapay/funding-rates-mcp` returns 404, last release Apr 2025.

**Step 1, log:**

```
{"ts":"2026-06-17T14:22:00Z","domain":"crypto-defi","source":"kukapay/funding-rates-mcp","route":"①","outcome":"dead","detail":"gh api 404; repo last seen 2025-04; vooi-app/mcp confirmed as live replacement","user_correction":null}
```

**Step 2, D-code:** repo is gone (404) AND a successor is named, pick `D-SUPERSEDED`
(not `D-404`, because the supersession story is the cleaner record; if `vooi-app/mcp`
didn't exist we'd use `D-404`).

**Step 3, shard edit** at `skills/market-intel/reference/domains/crypto-defi.md`:

```
| **vooi-app/mcp** (active 2026-06) | ① | perp/DEX-aggregator MCP — funding-rate divergence + cross-venue spreads | hosted MCP, MIT | (already present, no change)
| ~~kukapay/funding-rates-mcp~~ | ~~①~~ | ⚠ Avoid (dead, D-SUPERSEDED) — repo gone 2025-04, replaced by vooi-app/mcp | — | — |
```

(The `vooi-app/mcp` row was already present from an earlier sweep, only the kukapay row
gets the tombstone treatment.)

**Step 4, sources-index.md:** the `crypto-defi` top pick line already names vooi-app for
funding rates, so **no edit**. Skip.

**Step 5, companion-config:**

```
$ python C:\Users\<username>\CodesClaude\market-intel-config\scripts\sync-check.py
Bucket C: 1 entry
  - kukapay-funding-rates-mcp → D-SUPERSEDED (successor: vooi-app-mcp)
```

Per `sync-with-skill.md §C`: drop kukapay row from `registry.json`, delete
`secrets/kukapay-funding-rates-mcp.env` if present, set `replacement_for: "vooi-app-mcp"`
in any lingering references. Re-run, bucket C clears.

**Step 6, commit:**

```
incident: kukapay-funding-rates-mcp D-SUPERSEDED — repo gone 2025-04, vooi-app/mcp live

Found dead in crypto-defi weekly Discovery; gh api 404, last seen 2025-04.
Successor vooi-app/mcp (already in shard since 2026-06) confirmed working.
Tombstoned shard row, cleared config bucket C (1 entry).
```

Push. Done, the next monthly sweep will see this entry in `live-runs.jsonl` under
`outcome:dead`, the `crypto-defi` domain will get hot-mode Discovery budget ×2, and
`git log --grep="^incident:"` now lists this incident for posterity.
