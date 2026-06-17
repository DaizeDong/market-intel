# Doc sync runbook — keeping the narrative honest as the code evolves

## Why this exists

Between v0.17 and v0.24 the top-level docs drifted hard. The README version badge sat at 0.16.0 while `plugin.json` had moved to 0.24.0 — eight releases of silent staleness. PHILOSOPHY.md was untouched while the system roughly doubled in scope. ROADMAP.md still listed trigger items as pending after they had shipped. README_CN mirrored none of the structural changes its English sibling had absorbed. The proximate cause was that `release.ps1` only touches `plugin.json` and `CHANGELOG.md`; nothing else in the doc tree is on the release path. The deeper cause is that "remember to update the README" is an honor-system rule, and honor-system rules decay. PHILOSOPHY P6 (honest boundaries) requires the README narrative match what the system actually does — when the narrative lags reality, users and future-us are quietly misled. **Doc drift is therefore a P6 violation, not a cosmetic issue.** This runbook is the doctrine for preventing it; `tools/check_doc_drift.py` is the mechanism that enforces the parts a machine can enforce.

## Canonical sources vs derived fields

Every machine-checkable fact has exactly one canonical home. Derived fields are validated against it, never hand-edited as truth.

| Canonical | Derived | Check command |
|---|---|---|
| `.claude-plugin/plugin.json` `version` field | README version badge, README_CN version badge, CHANGELOG top entry version | `python tools/check_doc_drift.py` |
| `domains/*.md` file count (excluding `mcp-ecosystem.md` meta-doc) | README "Source Matrix-N domains" badge, README "## The source matrix (N domains)" heading, README_CN equivalents | same |
| `tools/*.md` file count (excluding `*.auto.md`) | Tool-count mentions in README / SKILL.md if present | same |
| Top-level docs section list in README | README_CN parallel structure | same |

**Principle: only ONE canonical source per fact.** If a number lives in two places, one of them is wrong and we don't yet know which. The rule for adding any future "number in the docs" is: pick the canonical home, generate or validate the rest.

## Narrative-vs-derived distinction

Some doc content cannot be auto-synced because it requires human judgment:

- README "What is this" prose narrative
- PHILOSOPHY.md principles (rarely change, but when they do, it's deliberate)
- ROADMAP trigger items — the *what* is canonical text, but *shipped-vs-pending* status is a human call
- Sister-skill list and usage examples
- README "Why this exists" / motivating examples

These get **warning-level** flags from `check_doc_drift.py` when heuristics suggest staleness (e.g. file untouched for 6+ months while CHANGELOG keeps growing). Warnings do not fail the release — they prompt a human to look. Fail-level gates apply only to fields with a single canonical source.

## Per-release workflow (auto + manual gates)

`release.ps1` will gain two new steps after the existing version-bump logic:

1. Bump `plugin.json` version (canonical, existing step).
2. Validate CHANGELOG entry — human-written, date-format checked (existing step 2).
3. **NEW step 5c**: run `check_doc_drift.py`. Any **fail-level** drift aborts the release. The author fixes and re-runs.
4. **NEW step 5d (optional)**: run `check_doc_drift.py --fix` to auto-bump README badges and counts. Re-check after; if clean, proceed to tag.

Steps the release author MUST eyeball before tagging — these are the things the checker can't decide:

- Does the README "What is this" paragraph still describe what the system does?
- Any ROADMAP "Triggered work" items shipped this release? Check them off explicitly in the same commit.
- PHILOSOPHY — was a principle added, revised, or invalidated? If yes, confirm README's links into PHILOSOPHY still resolve and still say what they used to say.
- README_CN — does the structural shape still match README? (Auto-checker catches counts; humans catch reorderings.)

## Per-refresh-sweep workflow (cleanup pass extension)

`runbooks/refresh-protocol.md` already covers domain shards and per-tool doc decay. Extend its cleanup pass with three new checks:

- **Top-level doc freshness sweep**: read mtime of PHILOSOPHY.md, ROADMAP.md, EVOLUTION.md, CONSTITUTION.md. If any has been untouched for >12 months AND CHANGELOG has accumulated ≥5 entries in that window, surface as "stale narrative — needs human review".
- **README narrative vs reality**: spawn a fork agent to read README + SKILL.md + `sources-index.md`, then judge whether the README still describes the system honestly. Output is binary: "PASS" or "drift between README and reality at section X — concrete description". This is the catch-all for the things the checker can't enforce.
- **ROADMAP demotion**: any "Triggered work" item with no commit activity touching its scope in 12 months → propose demoting to "deferred" with a written reason. Better to admit a thing isn't happening than to leave it as silent debt.

## Entropy controls (the long-term play)

Five mechanisms, working together, prevent unbounded entropy growth:

1. **Single canonical source per fact** (table above). No fact lives in two places.
2. **Fail-closed drift gate** (`check_doc_drift.py` in `release.ps1` step 5c). Drift can't ship.
3. **Time-decay alerts** (refresh-protocol cleanup pass). Monthly sweep surfaces stale narrative; quarterly fork audit checks README-vs-reality.
4. **PHILOSOPHY P3 (monotonic evolution)**. Guardrails accumulate, never relax. Coverage thresholds, gate counts, drift checks — these only ratchet up. A future release that wants to remove a check has to justify it in writing.
5. **PHILOSOPHY P5 (refresh/runtime separation)**. Refresh-side infrastructure stays in `tools/`; nothing crosses into the user-query path. LOC growth on the user path is bounded by SKILL.md size, which is itself a P5 budget. The checker, this runbook, and the cleanup sweeps all live on the refresh side and impose zero cost on user queries.

Together: derived fields stay correct (mechanism, gate 2); narrative drift is surfaced fast (alerts, gate 3); LOC on the hot path is bounded (P5, gate 5); guardrails only ratchet forward (P3, gate 4); facts have a single home (gate 1).

## How to add a new derived field

When a future release introduces a new machine-checkable derived field (e.g. "transport types supported" badge, "N MCP integrations" count, "supported model providers"):

1. Define the canonical source — which file, which line/key. Write it down in the table above.
2. Add a check function in `tools/check_doc_drift.py`. Fail-level if it's purely numerical; warn-level if it requires interpretation.
3. Append a row to this runbook's canonical/derived table.
4. If `--fix` should auto-correct the derived field, extend the fixer too.

**Never add an "honor system" rule** like "remember to update X when you do Y". If it isn't machine-checked, it isn't in scope and it will drift. If a field can't be machine-checked, route it through the narrative-warning path (mtime heuristics, fork audit) instead.

## When NOT to check drift

Some files are exempt by design and the checker should skip them:

- Files known to be human-authored narrative: PHILOSOPHY.md core principles, design-note paragraphs in README. The fork audit catches major drift here; pattern-matching does not.
- Files that are intentionally time-bound logs: CHANGELOG.md entries (they describe a past state and should not be rewritten), release notes.
- Archive directories: `runbooks/archive/`, `scripts/legacy/`, anything under a path component named `archive` or `legacy`. These are preserved for forensic value, not for current correctness.

## What ALSO contributes to entropy and is mitigated elsewhere

Doc drift is one entropy source among several. For completeness, the other vectors and where they're handled:

- **Test-stub files left in `metrics/` from fork sessions** — caught by `tools/sync-check.py` bucket E (orphans) and `scripts/cleanup-workflows.ps1`.
- **TODO / FIXME comments accumulating** — flagged by an annual sweep (currently TODO; see EVOLUTION.md backlog).
- **Dead per-tool docs after a tool is removed** — caught by `tools/verify_matrix.py` STALE/DEAD gates and the shard's C4 tombstoning rule.
- **Stale domain shards** — caught by the refresh-protocol cleanup pass, which already has shard-decay heuristics.

This runbook owns only top-level doc drift. The other vectors have their own owners; don't duplicate logic here.

## Trigger summary

- **Manual**: `python tools/check_doc_drift.py` (any time the author wants to spot-check)
- **Automatic, per-release**: `release.ps1` step 5c runs the checker before tagging; fail aborts the release
- **Automatic, monthly**: refresh-protocol cleanup pass invokes the checker at warn level + runs the mtime heuristics
- **Automatic, annual**: a fork agent does a full README-vs-reality narrative audit and posts findings to the refresh report

The combination — machine gates for facts, narrative audits for prose, monotonic guardrails for the whole system — is what keeps entropy from monotonically increasing as the repo self-evolves.
