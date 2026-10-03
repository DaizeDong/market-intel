# Release runbook

## Prepare one release commit

Work on `main`, update the plugin version, top changelog entry and derived README
fields, and commit through the normal hooks. The top changelog entry must match
the requested version and release date. The release script publishes this prepared
commit; it does not edit, stage, commit or automatically fix source files.
If a config-bridge sidecar is required, generate and review it during preparation
before committing the release.

The optional changelog drafter uses installed `llmcall` with current defaults.
Review its draft before committing. Deterministic validation needs no model call.

Resolve the full market-intel checkout and the PRIVATE companion path first.
Run the quoted absolute `tools/release.ps1` path with `-Version`, `-ConfigRepo`
and `-DryRun`. Remove `-DryRun` only when publication is authorized.

## Shared preflight for dry run and publication

1. Verify clean `main`, exact HEAD/main identity and a single matching origin
   fetch/push destination. Remote main must be a known ancestor of the prepared
   commit; fetch explicitly beforehand if its object is unavailable.
2. Require the requested tag to be absent locally and remotely. Check the plugin
   version and the first changelog entry.
3. Run `verify_matrix.py` against the verified remote main commit. Missing or
   invalid baselines and Git failures abort; historical comparisons use a copied index.
4. Require the companion sync checker to exist and exit zero. Its A-G bucket
   output must be complete, unique and free of B-G drift. A nonzero exit is never
   reinterpreted as an A-only pass, including launch errors and tracebacks.
5. Run `check_doc_drift.py --json --no-cache` and strictly validate its canonical
   values, drift rows and native/declared exit codes. Only internally consistent
   clean or warning evidence is accepted. Missing scripts, malformed output and
   unknown exit codes block. No automatic fix or cache write runs here.
6. Recheck branch, commit and clean state. Dry run reports this commit's preflight
   result and exits before any tag or push.

## Publication and recovery

Create a lightweight tag at the verified commit, check its target, then atomically
push that exact commit to `refs/heads/main` and `refs/tags/<tag>`. Hook output and
native failures remain visible. Read back both remote refs and require both to
match the prepared commit before reporting success.

If publication or readback fails, retain the prepared commit and local tag and
inspect both remote refs before deciding how to retry. The script refuses existing
tags; it never deletes tags, rewrites remote history or resets the worktree as an
automatic recovery. A blocked gate must be repaired and rerun, not bypassed.

## Validation boundary

Pure contract tests exercise generated checker/ref evidence, and static tests
check gate placement. They do not execute a release, contact a provider, prove
remote permissions, or establish that a publication succeeded.
