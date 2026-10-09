# Incident runbook, fixing a broken matrix entry

Use this when a tool in the source matrix is found broken in the wild, either (a) a user
hits a dead/changed/paywalled entry mid-research, or (b) a refresh sweep (monthly / weekly /
opportunistic) discovers an entry that no longer behaves as advertised. The six steps below
are canonical; do them in order, do not skip. The point is to convert a one-off incident
into a permanent matrix improvement plus a feedback-loop record, without silent deletion
(C7 / R3) and without quietly drifting the matrix (P3).

---

## 1. Log to the live-run ledger (`<data>/metrics/live-runs.jsonl`, PRIVATE store, not this repo)

Use the incident helper to append one record through the verified PRIVATE
destination and its locked update transaction. Never append by shell redirection.
The canonical schema is
[`live-run-schema.json`](../skills/market-intel/reference/live-run-schema.json),
and [generated examples](../skills/market-intel/metrics/live-runs.jsonl.example)
cover all supported outcomes. Both are produced by `tools/make_fixtures.py`.

The supported outcomes and their meanings are defined in the
[live-run contract](../skills/market-intel/reference/live-run-contract.json),
including distinct transport, authentication, quota and content failures.
Keep the actual observation; do not relabel a fallback or unverified result as a
confirmed failure. The feedback reader preserves those two outcomes as open
questions without granting verification credit or inventing a barrier. A non-null
user correction remains a priority signal. Failed persistence is a storage error,
not a completed incident record.

## 2. Identify the D-code

Use the evidence thresholds in [`CONSTITUTION.md` C4](../CONSTITUTION.md#c4-deletion-is-a-high-privilege-act-the-burden-of-proof-is-on-removal),
then apply the refresh protocol's retained-tombstone procedure. The five canonical codes:

| code | meaning | trigger |
|---|---|---|
| `D-404` | repo / endpoint gone | confirmed API 404 or archived repository |
| `D-PRICE` | route now paywalled | official price page proves the paywall, with URL and date |
| `D-STALE` | stale route with a replacement | more than 18 months without a push AND a verified replacement added |
| `D-TOS` | official policy killed the route | official-policy evidence that this route is no longer permitted |
| `D-SUPERSEDED` | verified better source replaces it | name the verified replacement and retain supporting evidence |

**Verify:** the code matches the evidence in Step 1's `detail` field. A `D-404` entry should
cite an HTTP 404 / `gh api` error; a `D-PRICE` should quote the new price page; etc.

A temporary challenge, account failure, DNS failure or uncertain diagnosis remains an
observation/setup gap until a C4 predicate is proved. No verified successor does not imply
`D-STALE` or `D-404`; keep the entry and report the unresolved evidence.

## 3. Edit the shard

Only after Step 2 establishes a C4 death code, open
`skills/market-intel/reference/domains/<domain>.md` and mark the existing row as a tombstone:

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

Complete the catalog change before verification: retain and mark the old row in
`skills/market-intel/reference/tools/index.md`, retain the per-tool card with its death banner,
and keep its `tools/registry.json` record with synchronized metadata. A successor needs its
own canonical registry record, index row and per-tool card before it can become a default.
Apply the same synchronization to a rename.

**Verify:** confirm the retained shard/index/card tombstones and registry consistency, including
the optional successor's registration. Run
`python tools/verify_matrix.py --no-cache --base <baseline-ref>` from the full consumer
checkout, using the verified prior commit as the baseline, and confirm STRUCT / REPO / FRESH /
TOOLS / REGISTRY pass. Advance `## Last verified` only after the required scope was rechecked.

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

Resolve the active companion through [the CONFIG discovery contract](../CONFIG.md#discovery-convention-e2),
including its supported aliases and same-companion DATA selection. Invalid, missing or conflicting
explicit selectors are errors; do not fall back or skip them. Skip to Step 6 only when normal
discovery establishes that no companion is configured.

For a resolved companion, run its checker without reading or printing secret values:

```
python "<resolved-companion>/scripts/sync-check.py"
```

A missing checker or failed command is an unresolved synchronization gap.

Step 3 creates the retained tool-card tombstone used by **bucket C** ("Config points to a
skill doc tombstoned `⚠ Avoid (dead, D-xxx)`"). Inspect the actual report and follow the
resolved companion's `runbooks/sync-with-skill.md` §C. Preserve versioned retirement and
replacement metadata. Update configured install state before changing its dependent host
configuration, and handle credentials under the selected storage and rotation policy. A
catalog retirement alone does not authorize deleting credentials or changing a live host.

**Verify:** rerun the resolved checker and confirm the intended retirement/replacement is
recorded and the reported buckets are addressed. Keep any unresolved sync findings explicit.

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

## Synthetic examples

Use the generated ledger linked above to learn the record shape. Real incident
details, target identifiers and user quotations belong only in the PRIVATE
companion. Publication should describe a reviewed tool-level correction without
copying the underlying user's research record.
