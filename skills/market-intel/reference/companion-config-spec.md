# Companion config repo — formal specification

**Status**: STABLE. Spec version: `1`.

This is the **formal contract** between the market-intel skill (and sister skills following the
same pattern) and any companion config repo the user maintains. Conforming repos can be
mechanically read by SKILL.md's Step 3 detection logic, by future automation, and by an agent
that needs to know what the user installed without reading 15 free-form READMEs.

The companion repo concept + rationale is in [`companion-config-repo.md`](companion-config-repo.md);
this file is the spec.

> ⚠️ **Conformance**: Any companion config repo claiming to be "market-intel spec v1" MUST
> satisfy every MUST clause below. Skills consuming such repos SHOULD ignore unknown fields
> (forward compatibility) and SHOULD degrade gracefully when optional fields are absent.

---

## 1. Discovery

The skill MUST probe these paths in order; the first that exists is the active companion repo:

1. **`$MARKET_INTEL_CONFIG`** env var (highest priority, location-independent).
2. **`~/.market-intel-config/`** (dotfile-in-home, universal fallback).
3. **`~/.config/market-intel-config/`** (XDG-style, Linux/macOS).

If none exists, skills MUST degrade to matrix-only mode and continue functioning. Companion
repo is **never required**, only optional and recommended.

---

## 2. Required directory structure

```
<companion-config-repo>/
├── registry.json                              # REQUIRED
├── tools/                                     # REQUIRED (may be empty)
│   └── <slug>/                                # OPTIONAL (zero or more)
│       ├── claude.json.template               # REQUIRED if <slug>/ exists
│       └── env.template                       # REQUIRED if <slug>/ exists
└── secrets/                                   # REQUIRED (gitignored by .gitignore)
    └── <slug>.env                             # OPTIONAL (only when tool has env vars)
```

All other paths (`scripts/`, `runbooks/`, `.github/`, top-level docs) are CONVENTIONAL but not
part of the spec — they're tooling concerns specific to the user's workflow.

### 2.1 Required files at the repo root

| Path | Status | Purpose |
|---|---|---|
| `registry.json` | REQUIRED | Machine-readable index. See §3. |
| `tools/` | REQUIRED | Directory containing per-tool subdirs. May be empty when no tools installed. |
| `secrets/` | REQUIRED | Gitignored directory holding secret env files. May be empty. |

### 2.2 Required gitignore patterns

A conforming repo's `.gitignore` MUST exclude:

```
secrets/*
!secrets/README.md
!secrets/.gitkeep
*.env
!*.env.template
!env.template
claude.json
.claude.json
```

The intent: real `.env` files and any live `~/.claude.json` MUST never enter git. Defense in
depth via additional patterns (`*.key`, `*_token`, etc.) is RECOMMENDED.

---

## 3. `registry.json` schema

Top-level shape:

```json
{
  "schema_version": 1,            // REQUIRED — integer, this spec is version 1
  "generated": "YYYY-MM-DD",      // OPTIONAL — informational, free-text date
  "machine": "string",            // OPTIONAL — informational, free-text host/profile id
  "comment": "string",            // OPTIONAL — informational
  "summary": { ... },             // OPTIONAL — informational (see §3.2)
  "tools": [ ... ]                // REQUIRED — array of tool entries (see §3.1)
}
```

Skills MUST:
- Check `schema_version` and refuse to consume unknown major versions.
- Tolerate any number of unknown top-level fields (forward compatibility).

Skills SHOULD:
- Use `tools[]` as the primary source; `summary` is for humans.

### 3.1 Per-tool entry schema (`tools[]`)

```json
{
  "slug": "string",               // REQUIRED — kebab-case identifier; MUST match tools/<slug>/ dir
  "installed": true,              // REQUIRED — boolean; true if this tool is currently in use
  "matrix_slug": "string | null", // OPTIONAL — slug in the public matrix (market-intel by default)
                                  //            null if this tool isn't in any matrix yet
  "matrix_origin": "string",      // OPTIONAL — name of the matrix when not market-intel
                                  //            (e.g. "shopping-aggregator" for biggo-mcp)
  "domain": "string",             // OPTIONAL — fast-path routing hint (e.g. "finance-markets")
  "tier": "string",               // OPTIONAL — short summary: "free" | "freemium" | "paid"
  "transport": "string",          // OPTIONAL — "stdio" | "http" | "sse"
  "health_last": "string",        // OPTIONAL — "connected" | "needs_auth" | "failed" | "unknown"
  "health_checked": "ISO8601",    // OPTIONAL — when health_last was last verified
  "notes": "string"               // OPTIONAL — free text
}
```

**MUST**: `slug` and `installed` are the only strictly required fields. Everything else is
OPTIONAL but RECOMMENDED.

**MUST**: `slug` MUST be valid as a filesystem directory name on all major OSes (no `/`, `\`,
`:`, `?`, `*`, `"`, `<`, `>`, `|`, no leading dot, no trailing whitespace). Convention:
kebab-case ASCII.

**MUST**: `matrix_slug` (when present and non-null) MUST exactly match a `reference/tools/<slug>.md`
in the corresponding public matrix repo. This is how skill detection reverse-looks up
tier/domain info from the matrix.

**SHOULD**: When the matrix has a tool with a `-mcp` suffix, the companion repo's `slug` SHOULD
also use that suffix for symmetry (e.g. `fred-mcp`, not `fred`).

### 3.2 `summary` shape (optional)

When `summary` is present, it MUST follow this shape:

```json
{
  "config_tools_total": <int>,
  "config_tools_with_keys": <int>,
  "config_tools_key_free": <int>,
  "comment": "string"
}
```

`summary` counts MUST be scoped to **this companion repo's tracked tools only** — NOT
session-wide MCP counts (which would conflate with plugin-managed and claude.ai-managed MCPs).

---

## 4. Per-tool directory: `tools/<slug>/`

When `tools/<slug>/` exists, it MUST contain at minimum:

| File | Status | Purpose |
|---|---|---|
| `claude.json.template` | REQUIRED | JSON snippet to merge into `~/.claude.json` mcpServers section. See §4.1. |
| `env.template` | REQUIRED | KEY=VALUE skeleton documenting required env vars. See §4.2. |
| `README.md` | RECOMMENDED | Human-readable doc with tier, register URL, rotation history. Free-form. |
| `manifest.json` | OPTIONAL (future) | Structured per-tool metadata. Spec reserved for v2; not yet defined. |

### 4.1 `claude.json.template` format

A standalone JSON document containing an `mcpServers` partial. Two valid shapes:

**Shape A (preferred): top-level `mcpServers` wrapper.**
```json
{
  "mcpServers": {
    "<server-name>": {
      "type": "stdio",
      "command": "uvx",
      "args": ["<pypi-package>"],
      "env": {
        "<UPPER_SNAKE_NAME>": "<UPPER_SNAKE_NAME>"   // placeholder, see below
      }
    }
  }
}
```

**Shape B (compact): top-level keys are MCP server names.**
```json
{
  "<server-name>": { "type": "stdio", "command": "uvx", "args": ["..."] }
}
```

Skills implementing apply-like behavior MUST accept both shapes; tooling SHOULD emit Shape A.

**Placeholder syntax**: a token of the form `<NAME>` where `NAME` matches `[A-Z][A-Z0-9_]*`
(UPPER_SNAKE_CASE) is a placeholder for substitution from `secrets/<slug>.env`. A placeholder
MUST resolve to a value at apply time; if any placeholder is missing its value, apply MUST
fail loudly and refuse to write the resulting JSON.

**Transport-specific shapes:**

| transport | required keys | example |
|---|---|---|
| stdio | `type: "stdio"`, `command`, `args[]`, optional `env` | `{"type":"stdio","command":"uvx","args":["mcp-hn"]}` |
| http | `type: "http"`, `url`, optional `headers` | `{"type":"http","url":"https://mcp.apify.com","headers":{"Authorization":"Bearer <APIFY_API_TOKEN>"}}` |
| sse | `type: "sse"`, `url` | `{"type":"sse","url":"https://mcp.api.coingecko.com/sse"}` |
| http (token-in-URL) | `type: "http"`, `url` (with `<TOKEN>` placeholder in querystring) | `{"type":"http","url":"https://mcp.brightdata.com/mcp?token=<BRIGHTDATA_TOKEN>"}` |

### 4.2 `env.template` format

Plain `KEY=VALUE` lines, one per env var the tool needs. Values MUST be empty (the template
documents the variable names; real values go in `secrets/<slug>.env`).

```bash
# <tool name> — register at <provider URL>
# Brief notes about each variable, optional

REQUIRED_VAR_1=
REQUIRED_VAR_2=
```

**MUST**: UTF-8 **without BOM**. PowerShell 5's `Set-Content -Encoding UTF8` writes BOM and
breaks parsers; tooling that writes env files MUST use BOM-less UTF-8.

**MUST**: keys MUST match the UPPER_SNAKE_CASE placeholder names used in
`claude.json.template`.

For tools with no env vars, `env.template` SHOULD still exist as a one-line marker:

```bash
# <slug> — no env vars required (free, no key)
```

### 4.3 `README.md` format (recommended)

Free-form markdown. RECOMMENDED sections (skills may scan for these but MUST handle their
absence):

- `## What it provides` — 2-5 bullets on capabilities.
- `## Tier` — pricing tier + rate limits.
- `## Register` — provider's signup URL.
- `## Reinstall on a new machine` — typically just `python3 scripts/apply.py --tool <slug>`.

Per-account identifying info (email, username, phone, account IDs) MUST NOT appear in this
README — that information belongs in `secrets/_account-info.env` (gitignored, see §5.1).

---

## 5. `secrets/` directory

### 5.1 File naming

| File | Status | Purpose |
|---|---|---|
| `secrets/<slug>.env` | OPTIONAL per slug | Real env values for `tools/<slug>/`. Gitignored. |
| `secrets/_account-info.env` | OPTIONAL | Cross-service metadata (default email/username/auth-method preference, per-service registration log). Leading underscore = "not-a-tool". |
| `secrets/README.md` | RECOMMENDED | Human-readable note explaining the directory. |
| `secrets/.gitkeep` | RECOMMENDED | Ensures the dir exists after fresh clone. |

### 5.2 File format

UTF-8 **without BOM**. Plain `KEY=VALUE` lines. Values:
- MAY contain any characters except newline (use `\n` if needed, though tooling typically
  doesn't support that).
- SHOULD NOT be quoted (consumers expecting plain bash `.env` semantics).
- MAY use forward slashes for filesystem paths on Windows (avoid backslash JSON escape
  issues when values are substituted into `claude.json.template`).

### 5.3 Storage modes (Mode A vs Mode B)

The spec recognizes **two valid storage modes**. Either is conformant; pick based on
threat model.

#### Mode A — committed to the (private) repo

- `secrets/*.env` is **committed** alongside templates.
- **Pros**: single source of truth; `git clone` + `apply.py` is the full new-machine
  bootstrap; git history is the backup.
- **Cons**: GitHub data-breach / OAuth-token compromise / accidental-public-flip / forking
  by a collaborator all expose the keys. GitHub Secret Scanning Partnership scans private
  repos too — partner providers (OpenAI `sk-`, Anthropic `sk-ant-`, AWS `AKIA`, Stripe
  `sk_live_`, GitHub `ghp_`, Slack `xox`, etc.) are notified on detection and may
  **auto-revoke** the key.
- **When appropriate**: the repo is genuinely private (no collaborators), all keys are
  data-API tier from non-partnership providers (Tavily, Etherscan, FRED, Finnhub,
  CoinGecko, etc.), and the user accepts the residual risk for the simpler workflow.
- **When NOT appropriate**: any partnership-provider key. Those WILL auto-revoke.

#### Mode B — gitignored + out-of-band backup

- `secrets/*.env` is **gitignored**; real values backed up via cloud-storage sync, encrypted
  USB, or a dedicated secret-management tool.
- **Pros**: keys never enter git; no GitHub exposure surface; safe to add collaborators.
- **Cons**: bootstrap is two-step (`git clone` + restore).
- **Required `.gitignore` patterns under Mode B**:
  ```
  secrets/*
  !secrets/README.md
  !secrets/.gitkeep
  *.env
  !*.env.template
  !env.template
  claude.json
  .claude.json
  ```

#### Declaring the mode

A conforming repo's `secrets/README.md` SHOULD state which mode it uses at the top so future
maintainers / agent consumers know whether to expect `*.env` files in git or not.

### 5.4 Backup

- **Mode A**: git is the backup (pushing to a private remote covers durability).
- **Mode B**: backup mechanism is the user's choice. `scripts/backup-secrets.sh` +
  `scripts/restore-from-onedrive.sh` are conventional helpers but not required.

---

## 6. The "apply" contract

A conforming companion repo SHOULD ship a script (canonically `scripts/apply.py`) that:

| MUST | The script |
|---|---|
| **Idempotency** | be idempotent: re-runs produce the same `~/.claude.json` content. |
| **No-echo** | NEVER print secret values to stdout/stderr. Log length-only summaries. |
| **Fail-loud** | refuse to write when a `claude.json.template` placeholder has no matching `secrets/<slug>.env` value. |
| **Backup** | back up the existing `~/.claude.json` before writing. |
| **Merge semantics** | merge each tool's rendered snippet into `~/.claude.json`'s `mcpServers` section without touching other top-level fields. |
| **Atomic write** | write via a temp file + atomic rename. |

The reference `apply.py` in DaizeDong/market-intel-config satisfies all of these.

---

## 7. The "verify" contract

A conforming companion repo SHOULD ship a script (canonically `scripts/verify.sh`) that:

- Runs `claude mcp list` and masks tokens before any display.
- Updates `registry.json` `tools[].health_last` from the live output.
- Updates `registry.json` `tools[].health_checked` with an ISO8601 timestamp.
- Tolerates MCPs in `claude mcp list` that aren't in `registry.json` (they're session-wide
  context, not config-tracked).

---

## 8. Versioning policy

- `schema_version` is a single integer.
- **Minor changes** (new optional fields, new optional files) MUST NOT bump the version.
  Skills that don't understand new optional fields MUST continue working.
- **Breaking changes** (removing fields, repurposing fields, restructuring the directory)
  MUST bump the major integer.
- Skills consuming companion repos MUST refuse to operate on a `schema_version` newer than
  they understand, but MAY operate on older versions if they remain backward-compatible.

Migration from version N to N+1 SHOULD ship with a documented mechanical migration in the
spec itself.

---

## 9. Conformance checklist

A repo conforms to this spec when:

- [ ] `.gitignore` contains the patterns in §2.2 (real `.env` files cannot be committed).
- [ ] `registry.json` exists at the repo root and has `schema_version: 1` (or higher that's
      backward-compat with v1).
- [ ] Every entry in `registry.json` `tools[]` has REQUIRED fields `slug` and `installed`.
- [ ] For every `slug` in `tools[]`, `tools/<slug>/` exists and contains
      `claude.json.template` + `env.template`.
- [ ] Every `claude.json.template` parses as valid JSON after placeholder substitution from
      the corresponding `secrets/<slug>.env`.
- [ ] All `.env` files (real and template) are UTF-8 without BOM.
- [ ] No per-account identifying info in committed READMEs (audit by grepping for emails
      / phone / personal usernames).

Tooling (apply.py, verify.sh, capture-key) is RECOMMENDED but not part of conformance.

---

## 10. Future extensions (reserved)

- **`tools/<slug>/manifest.json`** — structured per-tool metadata (tier, transport, env_vars
  with descriptions, registration URLs). Currently OPTIONAL; v2 of this spec may make it
  REQUIRED for full machine consumption.
- **`schemas/`** — JSON Schema files for programmatic validation. Currently not shipped;
  may be added later.
- **`apply` as a callable** — currently apply.py is per-repo; a shared library could be
  factored out.

Until v2 of this spec, these are NOT part of the contract.
