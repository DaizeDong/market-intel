# Private runtime data

[CONFIG.md](CONFIG.md) defines companion selection and configured readiness.
[storage.contract.json](storage.contract.json) declares every supported artifact,
producer, consumer and retention rule. Real observations and credentials live in
the separate PRIVATE companion, never in this public source.

Runtime producers require an existing companion `data/` directory. Inventory is
`data/inventory/availability-cache.json`; feedback is `data/metrics/live-runs.jsonl`;
surface polling writes `data/surface-inbox.jsonl`. The root `metrics/**` namespace
contains retired history and refuses new runtime writes.

The pinned Guards `authorize_artifact_write` API checks each file's unique owner,
current PRIVATE destination and Git ignore policy. Undeclared, retired and ignored
versioned destinations fail before writing. Structural directories do not authorize
arbitrary children. Atomic staging and update locks use the exact transient
`.staging/` patterns in the contract; successful publication removes them. Inspect
an interrupted operation before removing residual staging.

The companion's selected credential policy remains authoritative. Mode A versions
credentials in verified PRIVATE Git; Mode B ignores them and requires a separate
protected backup. Restore the chosen dependency before treating recovery as ready.

The 64 MiB working-data budget remains enforced. Over-budget snapshots need exact
selected recovery references and digest checks before retirement. A schema check,
path inventory or template-valid result does not establish provider connectivity,
restore success or permission to delete retained data.

## External-tool storage

`resolve_directory` proves an existing directory's PRIVATE boundary only. It does
not authorize arbitrary child files. External-library recipes must select declared
file destinations and revalidate them before persistence. A new dynamic output
namespace needs its own producer, consumer and retention declaration before use;
the source does not grant a general `runtime/**` or `profiles/**` write exemption.

Recipes marked **setup only** have no shipped adapter admitting their complete file
output. Do not launch collection, login or persistence until an adapter declares
its exact namespaces in `storage.contract.json` and calls `resolve_destination`
for every file immediately before writing. Setup examples do not establish runtime
readiness or grant child-file write permission.

Review the installed version's supported storage settings, including implicit
databases, sessions, cookie files, caches, logs, downloads, transcripts, datasets,
request queues and exports. Redirect every output through supported options to an
admitted PRIVATE file destination. If an output cannot be located and redirected,
retain setup status. Capture metadata stdout only in a verified PRIVATE file,
never in the consumer checkout. Keep credentials in the companion's designated
store and backup under its selected policy.
