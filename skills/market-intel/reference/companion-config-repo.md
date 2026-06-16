# Companion config repo (optional ops-state backing)

market-intel is the **matrix** (which tools exist, where they live, how to install them). The
matrix is **public** and **shared**. But once a user actually starts installing tools and
acquiring API keys, they accumulate per-machine **operational state**:

- Which tools did *I* install? When? On which machine?
- Which tier did I sign up for? With which email?
- Where are my credentials? When were they last rotated?
- Is my MCP currently healthy?

That ops state is **private** to one user (or one organization). It does not belong in
market-intel's public source tree.

The **companion config repo pattern** is the recommended way to manage it.

## The pattern

```
~/CodesSelf/
├── market-intel/           # PUBLIC — the matrix (this repo)
└── market-intel-config/    # PRIVATE — ops state + secrets
```

The private companion repo:
- Mirrors the matrix's per-tool granularity (`tools/<slug>/`).
- For each installed tool, holds:
  - `claude.json.template` (with `<YOUR_TOKEN>` placeholder, committed).
  - `env.template` (skeleton, committed).
  - `<slug>.env` (real key, gitignored, OneDrive-backed up).
  - `README.md` (register URL, tier, last-rotated date, registered-with email).
- Holds `scripts/apply.py` that merges templates + secrets → `~/.claude.json` idempotently.
- Holds `scripts/verify.sh` that snapshots `claude mcp list` health into a registry file.
- Ships a CI gate (`.github/workflows/no-secret-leak.yml`) that fails on common key patterns.

Reference implementation: [DaizeDong/market-intel-config](https://github.com/DaizeDong/market-intel-config) (private — author's
own ops state; structure replicable, content per-user).

## Why this split

**P5 (delegate, don't reinvent)** from `PHILOSOPHY.md`: market-intel is a thin layer. Mixing
operational state into the matrix repo would:
- Bloat clones for users who just want to read the matrix.
- Create awkward decisions about "which tools should be visible in the index" — your installed
  set ≠ everyone else's.
- Tempt users to commit secrets to the matrix repo by mistake.
- Force a coupling between matrix updates and your personal install state.

Splitting them keeps each repo focused: matrix = knowledge asset; companion = ops state.

## How to bootstrap your own

```bash
# 1. Fork the directory layout from market-intel-config
mkdir -p ~/CodesSelf/<your-org>-market-intel-config/{tools,secrets,scripts,runbooks,.github/workflows}
cd ~/CodesSelf/<your-org>-market-intel-config

# 2. Copy the canonical .gitignore + CI gate + apply.py + verify.sh from the reference impl
# (or fork DaizeDong/market-intel-config private and rewrite README.md)

# 3. For each tool in market-intel you want to install, create tools/<slug>/:
#    - claude.json.template (the MCP snippet with placeholders)
#    - env.template (skeleton)
#    - README.md (you'll fill in tier/email/rotation as you go)

# 4. Sign up for the service, get the key, paste into secrets/<slug>.env via clipboard
#    (NEVER paste keys into the Claude chat input)

# 5. Run: python3 scripts/apply.py

# 6. Restart Claude session

# 7. Verify: bash scripts/verify.sh
```

## Why "private" matters

A leaked API key in a public repo is harvested by bots within seconds — GitHub's public
surface is continuously scanned. Even **private repos can leak** through forks, OAuth-token
compromises, accidental visibility flips, and cached mirrors. So:

- **`secrets/` is gitignored** (primary defense).
- **CI gate scans for typical key patterns** (defense in depth).
- The repo itself is **private** (third layer).
- Real secrets actually live on **filesystem + OneDrive** (Microsoft's encryption boundary),
  never on GitHub.

See the reference implementation's `PHILOSOPHY.md` for the full rationale.

## Cross-skill applicability

The same companion-repo pattern fits any market-intel-style "matrix" skill:
- `shopping-aggregator` users can stand up a `shopping-aggregator-config` companion repo
  for their Keepa subscription, Camelcamelcamel email, Apify token, etc.
- Future matrix-shaped skills (e.g. an academic-research-tools matrix) would follow the
  same split.

In all cases the matrix is shared knowledge; the companion is private ops state.
