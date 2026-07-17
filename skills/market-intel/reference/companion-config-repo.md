# Companion config repo (recommended ops-state backing)

market-intel is the **matrix**, which tools exist, where they live, how to install them. The
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
>
> 🔒 **Harden GitHub-side BEFORE first commit**: a freshly-created GitHub repo is
> dangerously permissive for a place that may hold API keys. See
> [`companion-config-hardening.md`](companion-config-hardening.md) for the 12-step lockdown
> runbook (visibility verification, Features off, Actions disabled, AI-tool GitHub Apps
> uninstalled / scoped, Copilot training opt-out). ~15 min the first time. **Do this before
> Step 4 in the bootstrap below.**

## Minimum viable conformant repo (3 files)

If you want the absolute smallest companion repo that the spec accepts:

```
<your-companion-repo>/
├── .gitignore             # at minimum block real .env files & live ~/.claude.json
├── registry.json          # {"schema_version": 1, "tools": []}
└── tools/                 # empty dir (may have sub-dirs as tools are added)
    └── .gitkeep
```

That's it, empty `tools[]` plus empty `tools/` dir is a valid v1-conformant companion
repo. Spec §2 only requires `registry.json` + `tools/` to exist; `secrets/` becomes
required when you add your first tool. Skills consuming this repo will detect it via the
discovery convention (§1) and treat it as "no tools installed yet".

Add your first tool by creating `tools/<slug>/{claude.json.template, env.template}` plus
`secrets/<slug>.env` (Mode A) or filling templates and gitignoring the env (Mode B).

Use this minimal shape to validate your tooling (apply.py / verify.sh) before adding real
secrets.


## The split

The user keeps two repos (locations are entirely up to them):

- **The matrix** (this public repo, cloned wherever).
- **The companion config repo** (a separate, **private** repo that holds the user's per-machine
  ops state, installed-tools registry, JSON templates, gitignored secrets, scripts).

The companion config repo is **per-user / per-organization**: each user creates their own
private repo on their own Git host (GitHub, GitLab, Codeberg, self-hosted, or no remote at
all). There is no shared canonical companion repo, by design, because the contents are by
nature personal.

## Discovery convention (used by SKILL.md Step 3)

The skill probes for a companion repo in this order; the first that resolves is used:

1. **`$MARKET_INTEL_CONFIG`** env var (set in the user's shell rc / profile / OS-level env).
   This is the **recommended** way, explicit, location-independent.
2. **`~/.market-intel-config/`**, dotfile-in-home fallback (works on all OSes uniformly).
3. **`~/.config/market-intel-config/`**, XDG-style fallback (Linux/macOS).

The user picks. There is no required filesystem location.

If no companion repo is found, the skill degrades to "matrix-only" mode and just uses
`claude mcp list` to see what's available, with no awareness of per-tool tier / quota /
rotation info.

## Repo structure (memorize the shape, it's identical across users)

```
<companion-config-repo>/
├── README.md
├── PHILOSOPHY.md                # secret-by-design principles
├── CHANGELOG.md
├── LICENSE                      # typically MIT (or whatever the user prefers)
├── .gitignore                   # *** THE PRIMARY SECRET GATE *** (patterns differ Mode A vs B)
├── .github/workflows/
│   └── no-secret-leak.yml       # Mode B ONLY — CI scans every push for key patterns.
│                                # Under Mode A this fights intentional commits; delete or
│                                # narrow to non-secret patterns. GitHub-side Push Protection
│                                # similarly should be OFF under Mode A.
│
├── registry.json                # 🟢 machine-readable installed-tools state (committed)
│
├── tools/                       # 🟢 per-tool ops record (committed)
│   └── <slug>/
│       ├── README.md            # tier + register URL + rotation history + dashboard URL
│       │                        # NO per-account PII (see spec §4.3)
│       ├── claude.json.template # JSON snippet for ~/.claude.json mcpServers section
│       └── env.template         # KEY=VALUE skeleton (no values)
│
├── secrets/                     # 🟢 committed under Mode A · 🚨 gitignored under Mode B
│   ├── README.md                # ⚠️ declares ACTIVE storage mode (Mode A vs B)
│   ├── .gitkeep                 # ensures the dir exists after fresh clone
│   ├── _account-info.env        # per-account PII (email/username/phone) — namespace marker
│   └── <slug>.env               # real KEY=VALUE per tool
│
├── scripts/                     # 🟢 automation (committed)
│   ├── apply.py                 # merges templates + secrets → ~/.claude.json idempotently
│   ├── capture-key.ps1          # clipboard-only key capture (Windows; no echo, length-verified)
│   ├── verify.sh                # parses `claude mcp list` → updates registry.json
│   ├── functional-test.py       # JSON-RPC pings each MCP transport (real-call test)
│   ├── backup-secrets.sh        # Mode B ONLY — copy secrets/ → out-of-band store
│   └── restore-from-onedrive.sh # Mode B ONLY — restore secrets/ from backup on new machine
│
└── runbooks/                    # 🟢 human ops docs (committed)
    ├── new-machine.md           # bootstrap on a fresh machine
    ├── secret-rotation.md       # when a key leaks or rotates
    ├── add-new-tool.md          # how to onboard a new tool into the companion repo
    └── uv-path.md               # Windows uvx PATH gotcha
```

## File formats, one worked example, full spec elsewhere

The normative shape of every file (template syntax, JSON schema, gitignore patterns, BOM
requirement) is in [`companion-config-spec.md`](companion-config-spec.md) §4. Don't
paraphrase it here. One worked example to ground the idea:

**`tools/finnhub/claude.json.template`**, stdio MCP with `<UPPER_SNAKE_CASE>` placeholders
that get substituted from `secrets/finnhub.env` at apply time:

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

**`tools/finnhub/env.template`**, KEY=VALUE skeleton with empty values; real values in
`secrets/finnhub.env`:

```bash
# Finnhub — register at https://finnhub.io/register (instant key in dashboard)
FINNHUB_API_KEY=
FINNHUB_STORAGE_DIR=
```

For HTTP-bearer, token-in-URL, SSE, and key-free shapes, see spec §4.1 table.

> ⚠️ **Per-tool README content rule** (spec §4.3, applies under BOTH Mode A and Mode B):
> a committed `tools/<slug>/README.md` MUST NOT contain per-account PII (email, username,
> phone, account IDs). PII goes in `secrets/_account-info.env`, which under Mode A is
> committed but lives in the `secrets/` namespace, and under Mode B is gitignored.

## Why this split

**P5 (delegate, don't reinvent)** from `PHILOSOPHY.md`: market-intel is a thin layer. Mixing
operational state into the matrix would:

- Bloat clones for users who just want to read the matrix.
- Create awkward decisions about "which tools should be visible in the index", your installed
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

# 4. Create a PRIVATE repo on GitHub (or your Git host), point origin at it.
#    ⚠️ BEFORE pushing: run the GitHub-side hardening checklist in
#    reference/companion-config-hardening.md — visibility, Features off, Actions disabled,
#    Pages off, GitHub Apps audit (uninstall AI tools like Codex/Devin or restrict scope),
#    account-level Copilot data-sharing opt-out. ~15 min the first time.
#    Then push.

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

- **Mode A**, secrets `*.env` files **committed** alongside templates in the (private)
  repo. Single source of truth, `git clone` is the full backup + bootstrap. Appropriate
  when the repo is genuinely private and all keys are data-API tier from providers NOT in
  GitHub's Secret Scanning Partnership (most read-only data APIs qualify: Tavily, Etherscan,
  FRED, Finnhub, CoinGecko, etc.).
- **Mode B**, secrets `*.env` files **gitignored**; real values backed up via cloud-storage
  sync, encrypted USB, or a dedicated secret-management tool. Appropriate when keys come
  from partnership providers (OpenAI `sk-`, Anthropic `sk-ant-`, AWS `AKIA`, Stripe
  `sk_live_`, GitHub `ghp_`, Slack `xox`, etc.), those WILL be auto-revoked by GitHub
  Secret Scanning even in private repos.

Either mode is conformant; see [`companion-config-spec.md`](companion-config-spec.md) §5.3
for the full trade-off analysis.

### Defense-in-depth posture under Mode A

A leaked API key in a **public** repo is harvested by bots within seconds. Even **private
repos can leak** through forks, OAuth-token compromises, accidental visibility flips, and
cached mirrors, but for low-stakes data-API keys the residual risk is acceptable in
exchange for the simpler workflow. Mitigations:

- The repo is **private**.
- The repo's `secrets/README.md` declares Mode A explicitly so future maintainers / agents
  know what to expect.
- If you ever need to add a partnership-provider key, switch that key (and only that key,
  or the whole repo) to Mode B before committing.

### Defense-in-depth posture under Mode B

- **`secrets/` is gitignored** (primary defense).
- Optional **CI gate** scans for typical key patterns on every push (defense in depth) ,
  recommended when the repo has multiple contributors.
- The repo itself is **private** (third layer).
- Real secrets live on **local filesystem + an out-of-band backup** (cloud sync, encrypted
  drive, etc.), never on GitHub.

## Cross-skill applicability

The same companion-repo pattern fits any market-intel-style "matrix" skill:

- `shopping-aggregator` users can stand up a `<skill>-config` companion repo for
  their Keepa subscription, Camelcamelcamel email, Apify token, etc.
- Future matrix-shaped skills (e.g. an academic-research-tools matrix) would follow the same
  split.

In all cases the matrix is shared knowledge; the companion is private ops state.
