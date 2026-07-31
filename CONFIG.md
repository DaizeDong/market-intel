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

`tools/datadir.py` resolves real-run **output** to `data/` inside your companion config repo. It
follows the same pointer this page already describes:

1. `$MARKET_INTEL_DATA_DIR`, an explicit override.
2. `$MARKET_INTEL_CONFIG` (or `$MARKET_INTEL_CONFIG_DIR`), the companion repo: `data/` under it
   when that exists, the repo root otherwise.
3. `~/.market-intel-config/data/`, the companion repo at its default dotfile path.
4. `~/.market-intel-data/`, standalone.
5. None, meaning the tool is **uninitialized**, which is the correct state for a fresh clone.

Print it rather than retyping it:

```bash
python tools/datadir.py --path market-intel metrics/live-runs.jsonl
```

**This is a deliberate policy, decided 2026-07-31. Do not "fix" it back.** The rule the data
boundary enforces is *real-run output must never reach a **public** repo, and a public repo never
has an in-repo fallback*. It was never *data must not be in git*. Those are different predicates,
and the second one condemns the correct answer: a **private** repo is exactly where a person's real
data legitimately lives, and it is the only place it gets history, diffs and a backup. The
alternative, a loose directory in `$HOME`, leaves the one artifact that records your real research
runs as the one artifact with no version control at all.

This is also the fleet shape, not a market-intel special case: `daily-hotspots` keeps its
opportunity ledger tracked in its own private companion repo the same way.

An earlier revision of this section said the opposite, and it cost something real: a check written
to the git-vs-not-git predicate failed this skill for keeping its ledger where the doctrine says it
belongs, and the ledger was moved out to an unversioned directory to satisfy it.

`fleet_check`'s `databoundary` row now asserts the predicate that matches the harm: it **FAILS** if
the resolved data dir is inside a repo whose remote is **PUBLIC**, and fails closed if the
visibility cannot be established at all. Inside a **PRIVATE** repo it **PASSES**, and the row names
the repo, so you can tell "the control looked at this and approved it" from "the control skipped
it". Real-run output is still physically absent from **this** repo; the public repo ships only
`skills/market-intel/metrics/live-runs.jsonl.example`.

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
