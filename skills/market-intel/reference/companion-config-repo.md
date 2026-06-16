# Companion config repo (recommended ops-state backing)

market-intel is the **matrix** — which tools exist, where they live, how to install them. The
matrix is **public** and **shared**. But once a user actually starts installing tools and
acquiring API keys, they accumulate per-machine **operational state**:

- Which tools did *I* install? When? On which machine?
- Which tier did I sign up for? With which email?
- Where are my credentials? When were they last rotated?
- Is my MCP currently healthy?

That ops state is **private** to one user (or one organization). It does not belong in this
matrix repo.

The **companion config repo pattern** is the recommended way to manage it. SKILL.md's Step 3
detects whether the current user has one mounted and treats it as the authoritative source of
"what is installed" (in addition to `claude mcp list`).

> 📐 **Formal contract**: For the precise schema (required vs optional fields, forward
> compatibility rules, conformance checklist), see
> [`companion-config-spec.md`](companion-config-spec.md). This file is the **overview +
> rationale + tutorial**; the spec file is what skills and tooling actually consume.

## The split

The user keeps two repos (locations are entirely up to them):

- **The matrix** (this public repo, cloned wherever).
- **The companion config repo** (a separate, **private** repo that holds the user's per-machine
  ops state — installed-tools registry, JSON templates, gitignored secrets, scripts).

The companion config repo is **per-user / per-organization**: each user creates their own
private repo on their own Git host (GitHub, GitLab, Codeberg, self-hosted, or no remote at
all). There is no shared canonical companion repo — by design — because the contents are by
nature personal.

## Discovery convention (used by SKILL.md Step 3)

The skill probes for a companion repo in this order; the first that resolves is used:

1. **`$MARKET_INTEL_CONFIG`** env var (set in the user's shell rc / profile / OS-level env).
   This is the **recommended** way — explicit, location-independent.
2. **`~/.market-intel-config/`** — dotfile-in-home fallback (works on all OSes uniformly).
3. **`~/.config/market-intel-config/`** — XDG-style fallback (Linux/macOS).

The user picks. There is no required filesystem location.

If no companion repo is found, the skill degrades to "matrix-only" mode and just uses
`claude mcp list` to see what's available, with no awareness of per-tool tier / quota /
rotation info.

## Repo structure (memorize the shape — it's identical across users)

```
<companion-config-repo>/
├── README.md
├── PHILOSOPHY.md                # secret-by-design principles
├── CHANGELOG.md
├── LICENSE                      # typically MIT (or whatever the user prefers)
├── .gitignore                   # *** THE PRIMARY SECRET GATE ***
├── .github/workflows/
│   └── no-secret-leak.yml       # CI scans every push for key patterns (defense in depth)
│
├── registry.json                # 🟢 machine-readable installed-tools state (committed)
│
├── tools/                       # 🟢 per-tool ops record (committed)
│   └── <slug>/
│       ├── README.md            # tier + register URL + rotation history + dashboard URL
│       ├── claude.json.template # JSON snippet for ~/.claude.json mcpServers section
│       └── env.template         # KEY=VALUE skeleton (no values)
│
├── secrets/                     # 🚨 gitignored — real keys live here
│   ├── README.md                # explains what this dir is (the only committed file)
│   ├── .gitkeep                 # ensures the dir exists after fresh clone
│   └── <slug>.env               # real KEY=VALUE per tool (gitignored)
│
├── scripts/                     # 🟢 automation (committed)
│   ├── apply.py                 # merges templates + secrets → ~/.claude.json idempotently
│   ├── verify.sh                # parses `claude mcp list` → updates registry.json
│   ├── capture-key.ps1          # clipboard-only key capture (Windows; no echo, length-verified)
│   ├── backup-secrets.sh        # syncs secrets/ to an out-of-band backup location
│   └── restore-from-onedrive.sh # restores secrets/ from backup on a new machine
│
└── runbooks/                    # 🟢 human ops docs (committed)
    ├── new-machine.md           # bootstrap on a fresh machine
    ├── secret-rotation.md       # when a key leaks or rotates
    ├── add-new-tool.md          # how to onboard a new tool into the companion repo
    └── uv-path.md               # Windows uvx PATH gotcha
```

## Detailed file formats

### `tools/<slug>/claude.json.template`

A complete JSON snippet that will be merged into `~/.claude.json` under `mcpServers`. Use
`<UPPER_SNAKE_CASE>` placeholders for any secret value — they get substituted at apply time
from `secrets/<slug>.env`. Examples:

**stdio MCP with one key:**
```json
{
  "mcpServers": {
    "finnhub": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-finnhub"],
      "env": {
        "FINNHUB_API_KEY": "<FINNHUB_API_KEY>",
        "FINNHUB_STORAGE_DIR": "<FINNHUB_STORAGE_DIR>"
      }
    }
  }
}
```

**HTTP MCP with bearer token:**
```json
{
  "mcpServers": {
    "apify": {
      "type": "http",
      "url": "https://mcp.apify.com",
      "headers": {"Authorization": "Bearer <APIFY_API_TOKEN>"}
    }
  }
}
```

**Token-in-URL HTTP MCP:**
```json
{
  "mcpServers": {
    "brightdata": {
      "type": "http",
      "url": "https://mcp.brightdata.com/mcp?token=<BRIGHTDATA_TOKEN>"
    }
  }
}
```

**SSE MCP (no key, public endpoint):**
```json
{
  "mcpServers": {
    "coingecko": {
      "type": "sse",
      "url": "https://mcp.api.coingecko.com/sse"
    }
  }
}
```

**Key-free stdio MCP:**
```json
{
  "mcpServers": {
    "mcp-hn": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-hn"],
      "env": {}
    }
  }
}
```

### `tools/<slug>/env.template`

KEY=VALUE skeleton with empty values + a registration URL comment. Real values go in
`secrets/<slug>.env`, never here. Example:

```bash
# Finnhub — register at https://finnhub.io/register (instant key in dashboard)
# Storage dir is local-only, no network value — pick any writable folder

FINNHUB_API_KEY=
FINNHUB_STORAGE_DIR=
```

### `tools/<slug>/README.md`

Recommended fields (skip what doesn't apply):

```markdown
# <slug>

- **Domain**: <which market-intel domain shard this tool belongs to>
- **Provider**: [<name>](<registration URL>)
- **Tier**: <free / freemium / paid — describe quota briefly>
- **Transport**: <stdio (uvx) | stdio (npx) | HTTP (hosted) | SSE>
- **Status**: <Connected / Needs auth / Failed> (verified <YYYY-MM-DD>)
- **Installed**: <YYYY-MM-DD>
- **Dashboard**: <URL>
- **Last rotated**: <YYYY-MM-DD>

## What it provides

<2-5 bullets on capabilities>

## Reinstall on a new machine

\`\`\`bash
python3 scripts/apply.py --tool <slug>
# Restart Claude session
\`\`\`
```

> ⚠️ Do **not** include per-account identifying info (email, username, phone, account IDs)
> here. Those go in `secrets/_account-info.env` (gitignored), not in this README which a
> future maintainer or collaborator might see.

### `secrets/<slug>.env`

Plain `.env`, UTF-8 **without BOM** (PowerShell 5's `Set-Content -Encoding UTF8` writes BOM —
`scripts/capture-key.ps1` and the canonical `apply.py` both handle the no-BOM convention
correctly). Example:

```bash
FINNHUB_API_KEY=<real key value>
FINNHUB_STORAGE_DIR=<local path>
```

### `secrets/_account-info.env` (optional, gitignored)

Per-service registration log: which email used, which username, registered date, dashboard
URL, last-rotation date, phone (if required). Useful for survival across machine wipes and for
your own audit. **Never committed.**

### `registry.json`

Machine-readable index updated by `scripts/verify.sh`:

```json
{
  "schema_version": 1,
  "generated": "<YYYY-MM-DD>",
  "summary": {
    "connected_count": <N>,
    "needs_auth_count": <N>,
    "failed_count": <N>,
    "total_in_repo": <N>
  },
  "tools": [
    {"slug": "<slug>", "installed": true, "health_last": "connected"}
  ]
}
```

## Why this split

**P5 (delegate, don't reinvent)** from `PHILOSOPHY.md`: market-intel is a thin layer. Mixing
operational state into the matrix would:

- Bloat clones for users who just want to read the matrix.
- Create awkward decisions about "which tools should be visible in the index" — your installed
  set ≠ everyone else's.
- Tempt users to commit secrets to the matrix repo by mistake.
- Force a coupling between matrix updates and personal install state.

Splitting them keeps each repo focused: matrix = knowledge asset; companion = ops state.

## How to bootstrap your own companion repo

Pick any path that works for you (set `$MARKET_INTEL_CONFIG` to point at it, or use one of the
discovery fallbacks above):

```bash
# 1. Create the directory layout (substitute YOUR chosen path for $CFG)
CFG=~/.market-intel-config   # or wherever you want; or `mkdir -p "$MARKET_INTEL_CONFIG"`
mkdir -p "$CFG"/{tools,secrets,scripts,runbooks,.github/workflows}
cd "$CFG"

# 2. Author the canonical files (.gitignore, README.md, PHILOSOPHY.md, scripts/apply.py,
#    scripts/verify.sh, scripts/capture-key.ps1, .github/workflows/no-secret-leak.yml).
#    Use the structure section above as the spec. The canonical .gitignore must include:
#
#    secrets/*
#    !secrets/README.md
#    !secrets/.gitkeep
#    *.env
#    !*.env.template
#    !env.template
#    claude.json
#    .claude.json
#    *credentials*.json
#    *.key
#    *.pem
#    !*.key.template
#    !*.pem.template
#
#    plus defense-in-depth patterns for *_token / *api_key* / etc.

# 3. git init, then sanity-check before any commit:
git add .
git diff --cached --name-only | grep -E "\.env$" | grep -v "\.template$" \
  && echo "🚨 ABORT: real .env staged" || echo "✓ clean"

# 4. Create a PRIVATE repo on GitHub (or your Git host), point origin at it, push.

# 5. For each tool in market-intel you want to install, create tools/<slug>/ with the
#    three files above. Acquire the key via the provider's dashboard.

# 6. Capture the key via clipboard (PowerShell on Windows):
.\scripts\capture-key.ps1 -Slug <slug> -Var <KEY_VAR_NAME>

# 7. Apply: python3 scripts/apply.py --tool <slug>
# 8. Restart Claude session.
# 9. Verify: bash scripts/verify.sh
# 10. git add tools/<slug>/ ; git commit ; git push   (secrets/ is auto-excluded)
```

## Two storage modes (Mode A vs Mode B)

The spec recognizes two valid ways to store the actual secret values:

- **Mode A** — secrets `*.env` files **committed** alongside templates in the (private)
  repo. Single source of truth, `git clone` is the full backup + bootstrap. Appropriate
  when the repo is genuinely private and all keys are data-API tier from providers NOT in
  GitHub's Secret Scanning Partnership (most read-only data APIs qualify: Tavily, Etherscan,
  FRED, Finnhub, CoinGecko, etc.).
- **Mode B** — secrets `*.env` files **gitignored**; real values backed up via cloud-storage
  sync, encrypted USB, or a dedicated secret-management tool. Appropriate when keys come
  from partnership providers (OpenAI `sk-`, Anthropic `sk-ant-`, AWS `AKIA`, Stripe
  `sk_live_`, GitHub `ghp_`, Slack `xox`, etc.) — those WILL be auto-revoked by GitHub
  Secret Scanning even in private repos.

Either mode is conformant; see [`companion-config-spec.md`](companion-config-spec.md) §5.3
for the full trade-off analysis.

### Defense-in-depth posture under Mode A

A leaked API key in a **public** repo is harvested by bots within seconds. Even **private
repos can leak** through forks, OAuth-token compromises, accidental visibility flips, and
cached mirrors — but for low-stakes data-API keys the residual risk is acceptable in
exchange for the simpler workflow. Mitigations:

- The repo is **private**.
- The repo's `secrets/README.md` declares Mode A explicitly so future maintainers / agents
  know what to expect.
- If you ever need to add a partnership-provider key, switch that key (and only that key,
  or the whole repo) to Mode B before committing.

### Defense-in-depth posture under Mode B

- **`secrets/` is gitignored** (primary defense).
- Optional **CI gate** scans for typical key patterns on every push (defense in depth) —
  recommended when the repo has multiple contributors.
- The repo itself is **private** (third layer).
- Real secrets live on **local filesystem + an out-of-band backup** (cloud sync, encrypted
  drive, etc.), never on GitHub.

## Cross-skill applicability

The same companion-repo pattern fits any market-intel-style "matrix" skill:

- `shopping-aggregator` users can stand up a `shopping-aggregator-config` companion repo for
  their Keepa subscription, Camelcamelcamel email, Apify token, etc.
- Future matrix-shaped skills (e.g. an academic-research-tools matrix) would follow the same
  split.

In all cases the matrix is shared knowledge; the companion is private ops state.
