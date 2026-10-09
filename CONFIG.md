# market-intel, Config

`market-intel` is **config-bearing**: it reads per-user / per-machine state (API keys, the
installed-tool registry, endpoints) from a **separate, private companion config repo** that you
create and keep out of this repo. Secrets never live here.

This file is the repo-root config contract (config-spec **E1**). The **authoritative, versioned
deep spec** is [`skills/market-intel/reference/companion-config-spec.md`](skills/market-intel/reference/companion-config-spec.md)
(currently **v1.3, STABLE**), when this summary and the spec ever disagree, **the spec wins**.
Overview + tutorial: [`companion-config-repo.md`](skills/market-intel/reference/companion-config-repo.md);
GitHub-side lockdown to run **before** the first secret: [`companion-config-hardening.md`](skills/market-intel/reference/companion-config-hardening.md).

## Discovery convention (E2)

`MARKET_INTEL_CONFIG` selects the companion root; `MARKET_INTEL_CONFIG_DIR` is its lower-priority alias. `MARKET_INTEL_DATA_DIR` may select the supported DATA directory in that same companion. Conflicting CONFIG and DATA selections, empty selectors and explicit missing paths fail before any write. With no explicit selector, the pinned Guards resolver checks a proven sibling companion, `~/.market-intel-config`, then its legacy `~/.market-intel-data` convention. There is no separate XDG search. Settings and DATA share this selection. `--config-dir` on the doctor selects one companion in isolation from inherited selectors; restore normal environment selection before running the product. Runtime writers require an existing `<companion>/data`; DATA_DIR must name it. Root-level inventory or live-ledger writes are unsupported.

### Where real-run output goes: the private companion repo, versioned

`guards/tools/datadir.py` provides the shared DATA path discovery. It is a path
resolver; writers must still establish that the final destination is a PRIVATE
versioned companion before writing. An explicit missing destination is an error,
not permission to create an unmanaged fallback.

```bash
python guards/tools/datadir.py --path market-intel metrics/live-runs.jsonl
```

For inventory, set `MARKET_INTEL_CONFIG` (alias `MARKET_INTEL_CONFIG_DIR`) to the PRIVATE
companion and create its `data/` child during setup. `MARKET_INTEL_DATA_DIR`, if set,
must select that same child. Missing data/ is NOT initialized; writers never use the companion
root as a fallback. `console.py --refresh` validates the final canonical containing
repository, existing history, every physical and effective fetch/push destination,
fresh local PRIVATE visibility receipts and Git ignore status before collecting
inventory or creating directories. It refuses public, unknown, unmanaged, missing
and consumer-tree destinations.

Visibility proof reads the installed guard's `~/.pii-guard/visibility.json` receipt;
the console does not query GitHub or refresh that receipt. The shared guard requires
a valid timestamp, age within its accepted window (currently 30 days), and PRIVATE
entries for every destination. Use the installed guard's authenticated visibility
refresh workflow before first use, after changing destinations or repository
visibility, and whenever the receipt is missing, expired or invalid. Rerun the
console only after that refresh succeeds; never create a PRIVATE receipt by hand.

Inventory snapshots live at `inventory/availability-cache.json` below the resolved
DATA directory. Atomic replacement preserves the earlier valid snapshot on failure;
failed writes return nonzero. The console reports the verified companion identity
and never edits `.gitignore`. Commit the snapshot through the companion's existing
versioning workflow; the console does not commit automatically.

Incident writes use the same verifier for `metrics/live-runs.jsonl` below DATA.
The helper verifies the final containing PRIVATE repository before reading or
creating the ledger, and rechecks it before atomic replacement. It reports the
verified repository identity on success and returns nonzero on persistence failure.

Ordinary catalog reads need no DATA initialization and collect no inventory. For
current operation evidence, set `MARKET_INTEL_HOST`, `MARKET_INTEL_SESSION_ID` and
`MARKET_INTEL_CAPABILITIES` (an explicit JSON file path). The
[host capability contract](skills/market-intel/reference/host-capabilities.md)
defines schema v1, freshness, authentication failures and selected operation proof.
Keep these real observations in the PRIVATE companion. Generated examples in
`inventory/*.example` illustrate the schema without asserting real readiness.

## Model adapter

Core Python commands install with `python -m pip install -r requirements.txt`.
The development requirements add pytest and run without a model adapter.
`incident_helper.py` and `changelog_draft.py` require the operator's separately
configured `llmcall` Python package. The public requirements intentionally do not
depend on a private repository or select a provider.

Use the same Python environment for setup and execution. Install the configured
package from a trusted wheel or checkout supplied by the operator, then check its
interface:

```bash
python -m pip install /absolute/path/to/configured-llmcall-package
python tools/model_adapter.py --check
```

The path is a placeholder for that existing package, not a package name to fetch
from a public index. Follow its own installation and private configuration guide
for provider access. Market-intel forwards the prompt and requested response
schema and inherits that package's routing, model, timeout and fallback policy.

The doctor checks that `llmcall.call` is importable and callable. It performs no
model request and does not establish provider authentication or execution. A
missing or incompatible import reports `UNINITIALIZED` and exits 3; model draft
commands also stop with that status before reading input or writing output.
Provider execution failures remain separate failures with private diagnostics.
The changelog helper prints its draft by default. Optional `--out` paths must be
inside a verified PRIVATE versioned companion; destination or write failures exit
nonzero and preserve the previous file.

## Schema, `registry.json` (E1)

Machine-readable index at the companion-repo root. Full field reference: spec §3. Top-level shape:

```json
{
  "schema_version": 1,            // REQUIRED — integer (this spec major == 1)
  "generated": "YYYY-MM-DD",      // OPTIONAL — informational
  "machine": "string",            // OPTIONAL — informational host/profile id
  "comment": "string",            // OPTIONAL — informational
  "summary": { },                 // OPTIONAL — human-facing rollup (spec §3.2)
  "tools": [                      // REQUIRED — array (may be empty)
    {
      "slug": "example-tool",     // REQUIRED — kebab-case; matches tools/<slug>/
      "installed": true,          // REQUIRED — boolean
      "tier": "freemium",         // OPTIONAL — free | freemium | paid
      "transport": "stdio",       // OPTIONAL — stdio | http | sse | rest | python-lib | brokerage
      "health_last": "connected", // OPTIONAL — connected | needs_auth | failed | unknown | ...
      "health_checked": "ISO8601",// OPTIONAL
      "notes": "free text"        // OPTIONAL
      // + OPTIONAL judgment fields (spec §3.1 v1.2/v1.3): mcp_server_name, deprecation_code,
      //   ban_risk, evidence_url, supersedes, replacement_for, model_tier, route_agent_native
    }
  ]
}
```

Consumers MUST tolerate unknown top-level/entry fields (forward-compat) and degrade when optional
fields are absent. Per tool that needs credentials, add
`tools/<slug>/{claude.json.template, env.template}` (`<UPPER_SNAKE>` placeholders, **UTF-8 without
BOM**, fail-loud on a missing value) and put real values in `secrets/<slug>.env` under the
companion's declared storage mode (versioned in PRIVATE Git for Mode A, gitignored for Mode B).
Apply/verify contracts: spec §6 / §7.

## Companion-repo layout (spec §2)

```
<companion-config-repo>/
├── registry.json                 # REQUIRED
├── tools/                        # REQUIRED (may be empty)
│   └── <slug>/                   # OPTIONAL
│       ├── claude.json.template  # REQUIRED if <slug>/ exists
│       └── env.template          # REQUIRED if <slug>/ exists
└── secrets/                      # REQUIRED; declared Mode A or Mode B policy
    └── <slug>.env                # OPTIONAL; private Git in A, gitignored in B
```

## Secrets and storage modes (E6)

The companion is separate and PRIVATE. Its declared storage mode governs credentials:
Mode A versions them in verified PRIVATE Git; Mode B ignores them and requires a
separate backup. Both keep secrets out of the public tool and command output.
The bundled initializer supports Mode B only and refuses Mode A. That initializer
default does not describe every existing deployment. Follow the declaration and
recovery instructions in the selected companion; do not reinitialize it to change modes.
See [the storage-mode specification](skills/market-intel/reference/companion-config-spec.md#53-storage-modes-mode-a-vs-mode-b)
for declarations, checks and backup responsibilities.

## First-time setup (E3)

The generated empty registry is a valid template and remains NOT READY. Populate at least one
selected `tools[]` entry with a unique kebab-case `slug` and boolean `installed: true`, plus
`tools/<slug>/claude.json.template` containing an `mcpServers` object and `env.template`.
The doctor validates these configured fields without testing provider connectivity. Prepare a
versioned PRIVATE companion and its data/ directory before invoking runtime writers.

```bash
# 1. Stamp a conformant, empty config skeleton (deterministic — E4):
python scripts/init_config.py            # -> ~/.market-intel-config/  (or pass --out <dir>)

# 2. Point the skill at it (skip if you used the default path):
export MARKET_INTEL_CONFIG=~/.market-intel-config

# 3. Add your tools + secrets, then confirm it is ready:
python scripts/verify_config.py          # doctor: PASS/FAIL per check, names what is missing
```

## Switching between two configs (hot-swap), E5

Select a self-contained config directory with the environment variable. Clear or
update `MARKET_INTEL_DATA_DIR` so it selects the same companion’s `data/` child:

```bash
export MARKET_INTEL_CONFIG=~/configs/work       # config A
export MARKET_INTEL_CONFIG=~/configs/personal   # config B — same skill, different state
```

Verify the swap: `python scripts/init_config.py --out ~/configs/work` and `--out ~/configs/personal`,
run `verify_config.py` against each, then flip `$MARKET_INTEL_CONFIG` between them, both must
verify READY.

## Companion storage and retention

[storage.contract.json](storage.contract.json) declares companion-relative paths, their producers, consumers, recovery requirements and retirement conditions. Existing domain schemas above remain authoritative for field validation. Privacy classification in `.dataclass.json` does not establish retention.

The 64 MiB worktree budget is a review threshold, excluding Git metadata. Exceeding it requires examining dependencies, not discarding core data. Use the shared `skill-smith` storage-contract checker with this source checkout and its PRIVATE companion; no copy of the checker is vendored here. It inventories structure and retention declarations, not live provider readiness or recovery.

Keep current configuration, pending discovery decisions, feedback records, selected final deliverables and referenced recovery evidence. Consolidate exact duplicate ledger copies without changing outcomes. Retain active launcher dependencies even when reproducible. Superseded credential snapshots require a verified retained reference and digest before retirement. Completed probe and research working trees may be retired after their final conclusions and required evidence are retained.

### Exact retention closure before retirement

Record exact selected deliverable, cited-evidence and current account-recovery
references in the existing PRIVATE maintenance receipt. A broad core path is
protective while that review is incomplete; it is not permission to retain
every old probe or capture forever. Releasing files under a broad core pattern
requires owner-reviewed splitting of the broad declaration into disjoint
ownership after dependency review. Every path must match exactly one artifact;
an exact non-core pattern overlaid on an existing core glob does not override
it. The generic storage planner continues to refuse such overlaps and core paths.

Credential recovery retains the snapshot selected by `latest.json` and each
separately justified obligation. Verify the selected reference and digest,
then review superseded snapshot paths and their other recovery duties before
reclassification. The DPAPI snapshot requires its original Windows user and
machine; it is not a portable recovery proof. Existing timestamped snapshots
must not trigger more historical copies or a larger budget. Active launcher
dependencies remain protected even when a lockfile can reproduce them.

Completed migration or research work needs exact integrated revision, selected
conclusion and cited-reference closure before retirement. Do not replace that
closure with a whole-tree archive. This contract change performs no rotation,
cleanup, restore or provider check. If working storage exceeds the 64 MiB
budget, the check remains failed until storage meets its reviewed bound.
