# market-intel, Config

`market-intel` is **config-bearing**: it reads per-user / per-machine state (API keys, the
installed-tool registry, endpoints) from a **separate, private companion config repo** that you
create and keep out of this repo. Secrets never live here.

This file is the repo-root config contract (config-spec **E1**). The **authoritative, versioned
deep spec** is [`skills/market-intel/reference/companion-config-spec.md`](skills/market-intel/reference/companion-config-spec.md)
(currently **v1.3, STABLE**), when this summary and the spec ever disagree, **the spec wins**.
Overview + tutorial: [`companion-config-repo.md`](skills/market-intel/reference/companion-config-repo.md);
GitHub-side lockdown to run **before** the first secret: [`companion-config-hardening.md`](skills/market-intel/reference/companion-config-hardening.md).

## Discovery convention (how the skill finds your config), E2

The skill probes these paths in order; the first that exists is the active companion repo
(spec §1):

1. `$MARKET_INTEL_CONFIG`, environment variable (highest priority, location-independent).
2. `~/.market-intel-config/`, dotfile-in-home, universal fallback.
3. `~/.config/market-intel-config/`, XDG-style fallback (Linux/macOS).

If none resolves, the skill **degrades to matrix-only mode and keeps working**, the companion
repo is always optional, never a hard crash. (The bundled `scripts/` also accept
`$MARKET_INTEL_CONFIG_DIR` as a convenience alias for path 1.)

### Where real-run output goes: the private companion repo, versioned

`guards/tools/datadir.py` provides the shared DATA path discovery. It is a path
resolver; writers must still establish that the final destination is a PRIVATE
versioned companion before writing. An explicit missing destination is an error,
not permission to create an unmanaged fallback.

```bash
python guards/tools/datadir.py --path market-intel metrics/live-runs.jsonl
```

For inventory, set `MARKET_INTEL_DATA_DIR` to an existing directory in a private
companion, or set `MARKET_INTEL_CONFIG` (alias `MARKET_INTEL_CONFIG_DIR`) to that
companion. The shared convention uses `data/` when present and otherwise the
companion root. `console.py --refresh` validates the final canonical containing
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
BOM**, fail-loud on a missing value) and put real values in `secrets/<slug>.env` (gitignored).
Apply/verify contracts: spec §6 / §7.

## Companion-repo layout (spec §2)

```
<companion-config-repo>/
├── registry.json                 # REQUIRED
├── tools/                        # REQUIRED (may be empty)
│   └── <slug>/                   # OPTIONAL
│       ├── claude.json.template  # REQUIRED if <slug>/ exists
│       └── env.template          # REQUIRED if <slug>/ exists
└── secrets/                      # REQUIRED, gitignored
    └── <slug>.env                # OPTIONAL (real values, never committed)
```

## Secrets, Mode B (E6)

The companion config repo is **separate and private** (reference deployment:
`DaizeDong/market-intel-config`). `secrets/*` is **gitignored**, real values never enter git;
back them up out-of-band. Neither this skill repo nor the config repo ever echoes secret values.

## First-time setup (E3), succeeds on the first try

```bash
# 1. Stamp a conformant, empty config skeleton (deterministic — E4):
python scripts/init_config.py            # -> ~/.market-intel-config/  (or pass --out <dir>)

# 2. Point the skill at it (skip if you used the default path):
export MARKET_INTEL_CONFIG=~/.market-intel-config

# 3. Add your tools + secrets, then confirm it is ready:
python scripts/verify_config.py          # doctor: PASS/FAIL per check, names what is missing
```

## Switching between two configs (hot-swap), E5

A config dir is self-contained (no hardcoded paths). Keep as many as you like and switch by
repointing the env var, no other change:

```bash
export MARKET_INTEL_CONFIG=~/configs/work       # config A
export MARKET_INTEL_CONFIG=~/configs/personal   # config B — same skill, different state
```

Verify the swap: `python scripts/init_config.py --out ~/configs/work` and `--out ~/configs/personal`,
run `verify_config.py` against each, then flip `$MARKET_INTEL_CONFIG` between them, both must
verify READY.
