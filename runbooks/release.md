# Release runbook

## Purpose

Every release between v0.17 and v0.22 missed the companion-config `sync-check` at least
once — twice it shipped silently, and once the tag landed before `verify_matrix.py` was
re-run after a last-minute CHANGELOG edit. The release ritual was held together by memory,
and memory decayed. This runbook (and the script it documents, `tools/release.ps1`) makes
the ritual mechanical: validations are fail-closed, the order is fixed, and the operator
cannot skip a step by forgetting. This implements **PHILOSOPHY.md P2 — 机制不靠意图**:
correct behavior must be structural, not voluntary.

## Pre-requisites

Before running the release script, ensure all of these are true:

- **Working tree clean**: `git status` shows no staged or unstaged changes.
- **CHANGELOG entry pre-authored**: the top entry under `# Changelog` must be
  `## [<version>] - <today YYYY-MM-DD>` (ASCII `-` or em-dash both accepted).
- **`tools/verify_matrix.py` passes locally**: the deterministic matrix gate is green.
- **`market-intel-config/scripts/sync-check.py` has no B-G drift**: bucket A
  (matrix-has-it, config-doesn't) is intentional skips and tolerated; B through G must
  all be zero.
- **You can push to `origin/main`** (credentials warm, branch up to date with remote).

## Steps (mirroring `tools/release.ps1`)

1. **Working tree clean** — `git status --porcelain` must be empty. If it's not,
   commit or stash before continuing; the release commit must contain *only* the version
   bump.
2. **CHANGELOG top entry** — the script scans the first five non-empty lines after
   `# Changelog` for `## [<version>] - <today>`. If step 2 fails, open `CHANGELOG.md`
   and fix the header to match today's date and the requested version.
3. **Bump `.claude-plugin/plugin.json`** — regex replace on `"version": "..."`, not a
   JSON re-serialize. This keeps the file's existing formatting/order/keywords intact.
4. **`python tools/verify_matrix.py`** — the deterministic anti-regression gate. If
   step 4 fails, look at the last 20 lines of its output (printed by the script): the
   gate names which check tripped (STRUCT / REPO / GHACTIVE / STAR / FRESH / COVER /
   CONST). Fix the underlying shard or registry, re-run, then retry the release.
5. **Companion-config `sync-check`** — runs from `market-intel-config/`. Bucket A is
   "matrix has it, config doesn't" and is fine to skip (those are intentional). Any
   count in buckets B-G aborts the release. If step 5 fails, follow
   `market-intel-config/runbooks/sync-with-skill.md` to reconcile, then retry.
6. **`git add CHANGELOG.md .claude-plugin/plugin.json`** — only the two touched files,
   never `git add -A`.
7. **`git commit -m "release: v<version>"`** — message format is load-bearing for the
   release-history scan.
8. **`git tag v<version>`** — annotated tag not required; lightweight is fine.
9. **`git push origin main`** — commit goes up first so the tag has a target on the
   remote.
10. **`git push origin v<version>`** — tag push last; if this fails, main is already
    public but the release isn't tagged — retry the tag push or unwind (see recovery).
11. **Success summary** — script prints version, commit SHA, tag.

## Recovery (per step)

- **After step 6 fails** (add): `git restore --staged .`
- **After step 7 fails** (commit): `git restore --staged .` — also check pre-commit
  hooks; the commit may have been rejected by a lint gate, in which case fix the cause
  and re-run from step 6.
- **After step 8 fails** (tag, commit already landed locally): `git reset --soft HEAD~1`
  to undo the release commit; keep your edits staged for a retry.
- **After step 9 fails** (push main, tag exists locally): retry the push, or
  `git reset --hard HEAD~1; git tag -d v<version>` to fully unwind locally.
- **After step 10 fails** (push tag, main is public): retry `git push origin v<version>`;
  if you want to fully unwind a botched release, you'll need to delete the tag locally
  (`git tag -d v<version>`) AND remotely (`git push origin :refs/tags/v<version>`), and
  optionally revert the release commit on main (`git revert HEAD; git push`).

## When NOT to use this runbook

- **Doc-only commits** (typo fixes in README, runbook edits): just commit and push, no
  tag, no version bump.
- **In-progress sweeps** (mid-refresh, mid-shard edit): land the sweep first; release
  only from a clean main.
- **Hotfix path**: bump the patch number (e.g. 0.23.0 → 0.23.1) and run the same script;
  the gates are the same and the ritual stays mechanical. If you genuinely cannot get
  `verify_matrix.py` green (e.g. GitHub API outage during a urgent fix), do *not* bypass
  — wait for the gate to be runnable. The whole point is fail-closed.

## Principle

This runbook exists because PHILOSOPHY.md P2 — **机制不靠意图** — says we encode the
correct behavior as an enforced mechanism rather than asking the operator to "remember
to run sync-check." The script is the mechanism; this document is the human-readable
mirror of it. If they ever drift, the script is the source of truth.
