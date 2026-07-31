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

### Config and data are two different directories

`tools/datadir.py` resolves real-run **output** to `~/.market-intel-config/data/`, which is the
same dotfile path as discovery fallback 2. Those two roles must not land in one directory: the
companion config is a **git repo** (the setup walkthrough has you `git init` it), so letting the
data home sit inside it puts real-run output inside a git worktree, which is exactly the leak
class the data boundary exists to stop. `.gitignore` does not settle it, it is advisory and
`git add -f` walks straight through.

Keep them apart, in either direction:

* put the companion repo somewhere else and pin it with `$MARKET_INTEL_CONFIG` (leaving the
  dotfile path free to be the plain, non-repo data home), or
* leave the companion repo at the dotfile path and move the data home with
  `$MARKET_INTEL_DATA_DIR`.

`fleet_check`'s `databoundary` row fails for as long as the resolved data dir is inside any git
worktree, so it will tell you if these ever collapse back together.

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
