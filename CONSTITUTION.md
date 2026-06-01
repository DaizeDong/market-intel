# CONSTITUTION — immutable rules for every automated update

These are the accumulated lessons that **every automated refresh MUST honor**. They are injected as
hard constraints into each headless run. An automated run may NOT edit this file — it is changed
only by a human, in its own PR. The verify gate refuses any run that fails a constitution clause.

The point: the source matrix must **monotonically improve** — each update may make it better or keep
it equal, never worse. Guardrails only accumulate; they are never relaxed by automation.

## C1 — GitHub facts are API-verified, never recalled
Any repo/MCP entered or modified must be confirmed via the GitHub API (`gh api repos/<owner>/<repo>`):
it must exist (not 404), and its star count / last-push must be the **real** value the API returns.
Never write a repo name, star count, or date from memory. Can't verify → don't include it.

## C2 — Free / browser (route ④③) is first-class
Route ④ (browser / act-like-human) and free sources are preferred over paid when equivalent. A
Default pick must NOT silently move from a free/④ source to a paid ①/② one. Reach for paid only for
data the free route can't get (e.g. Keepa price history), scale reliability, or compliance — and say
why in the changelog.

## C3 — Source tiers (L1–L5) and barrier routes (①②③④) are mandatory annotations
Every source keeps its tier and route. Vendor self-claims (L3) cannot be the sole support for a
capability/price claim.

## C4 — Deletion is a high-privilege act; the burden of proof is on removal
Removing or demoting an existing source requires a machine-verifiable death code with evidence:
D-404 (api 404/archived) · D-STALE (>18mo no push AND a replacement added) · D-PRICE (official page
proves it's now paywalled, with URL+date) · D-TOS (official policy killed the route) · D-SUPERSEDED
(a verified better source named). A machine-alive source is NOT deletable on vibes. Dead entries move
to an "Avoid (dead)" tombstone, not silent deletion (so they aren't re-hallucinated back in).

## C5 — Citations / prices are re-verified against the official source
Price/policy changes carry an official URL + fetch date. Unverifiable numbers are marked "unverified"
and do not enter the matrix as fact.

## C6 — When in doubt, leave it out (宁缺毋编)
Missing info stays blank / marked stale-or-unknown. Never fabricate plausible-sounding entries to
fill a gap.

## C7 — Incremental edits, never rewrite
A refresh is a diff against the existing matrix, not a from-scratch rebuild. Large rewrites
(>40% of a shard changed, or a whole table replaced) must go to human review, not auto-commit.

## C8 — Time only moves forward
`last_verified` for any section may only advance, never go backward; never a future date.

## C9 — Discovery must run, not just re-verification
Every sweep actively looks for newer/better tools (Discovery phase), not just re-checks existing
entries — otherwise the matrix stagnates. New-but-unproven (adoption=0) goes to a watchlist, not
into the matrix. New ≠ good; high stars ≠ applicable.

## C10 — Bad updates never reach main
Automated runs work on a branch and open a PR; they never push main directly. The deterministic
verify gate (`tools/verify_matrix.py`) has final veto over landing — an LLM reviewer may only make
the verdict more conservative, never override a gate failure.
