# Contributing to market-intel

Thanks for considering a contribution. Most contributions fall into one of three patterns;
each has a slightly different path.

## Pattern 1, Add a new tool to the source matrix

The matrix lives in `skills/market-intel/reference/`. Adding a tool means writing
**four** synchronized changes:

1. **`reference/sources-index.md`**, only if the tool changes a domain's *top pick*. Most adds don't.
2. **`reference/domains/<domain>.md`**, add a row to the source table. Include barrier route
   (① official / ② resale / ③ self-host scrape / ④ browser-automation / ⑤ agent-native),
   capability, detect/install hint, and a one-line risk/cost note.
3. **`reference/tools/<slug>.md`**, full per-tool how-to. Follow the structure of any existing
   tool doc (`reference/tools/polygon.md` is a canonical example). Required sections: Domain(s) /
   Barrier route / Source tier / What it does / Install / Auth / Usage / Gotchas / Last verified.
4. **`reference/tools/index.md`**, add a row pointing at your new tool doc, under the right
   domain section.

### Naming convention (companion-config-spec §3.1 SHOULD)

- `<slug>.md` is the **pure tool name** (kebab-case, no owner prefix) when unambiguous.
- Add owner prefix ONLY when a same-name tool already exists from a different owner:
  - ✅ `arctic_shift.md` (unique brand)
  - ✅ `saseq-discord-mcp.md` (because `discord-mcp.md` already exists for elyxlz)
  - ✅ `antigravity-awesome-skills.md` (unique brand, sickn33's fork)

### Verify before PR

Run the deterministic gate:

```bash
python tools/verify_matrix.py
```

This runs 7 layered checks: STRUCT / TOOLS / REPO / STAR / **GHACTIVE** / FRESH / DOCCOVER /
REGISTRY / METH / COVER / CHURN+DELETE / CONST. Any BLOCK = fix it; WARN = explain it in the PR.

Of particular note: **GHACTIVE** is the deterministic activity gate. Full spec lives in
`tools/verify_matrix.py` module docstring (canonical). Short version: every github.com URL
in any shard gets a real `gh api` check; 404 / archived / >12mo stale all gate the PR. If
you're knowingly citing a stale repo, mark it `D-STALE` in its row.

### Companion-config side (only if you're also installing the tool)

If you're personally using the new tool with the companion-config repo pattern, also follow
`runbooks/add-new-tool.md` in the companion repo to scaffold `tools/<slug>/` template files
and `secrets/<slug>.env`. That's separate from the matrix-side contribution, the matrix
documents the tool; the companion-config tracks YOUR install state.

## Pattern 2, Update or remove an existing tool

- **Update**: edit the row + the tool doc. Bump `## Last verified: YYYY-MM`. Note in PR what
  changed (capability, pricing, repo URL).
- **Remove**: do **NOT** silently delete. Mark the doc `⚠ Avoid (dead, D-<code>)`. The
  5 death codes (D-404 / D-PRICE / D-STALE / D-TOS / D-SUPERSEDED) and per-code action
  are documented canonically in `skills/market-intel/reference/refresh-protocol.md` §C4.
  Tombstoning preserves the row + a downstream signal for the next refresh sweep. Silent
  deletion breaks the monotonic-evolution guarantee (P3 in `PHILOSOPHY.md`).

## Pattern 3, Propose a new domain or framework change

Larger contributions (new domain, new gate, new doctrine) start with an issue + a brief
prose proposal. Read `PHILOSOPHY.md` first, every change must pass the generative test:

> "Does this fix the framing, or just patch a symptom?"

If it's a framing change, it lands in `PHILOSOPHY.md` first and trickles into the rest. If it's
a tactic, it lands as a normal tool/row change without invoking `PHILOSOPHY.md`.

New domain proposals: see `reference/sources-index.md` "Reserved placeholders" for the
already-identified next-domain candidates with their maturity triggers.

## Style

- No emoji unless the file already uses them (most don't).
- Tables and one-liners over paragraphs where it conveys the same info.
- Lead with "what it does + when to pick it"; mechanical install/auth/usage details are
  refreshable, judgment isn't.
- Cite repo stars and pricing as `[fetched YYYY-MM]`, explicit date is the only honest stamp.

## Where to start reading

If you're new to the codebase, recommended order:

1. `README.md`, what the skill is, who it's for, install
2. `PHILOSOPHY.md`, the 6 principles that govern every change
3. `skills/market-intel/SKILL.md`, the user-facing workflow
4. `skills/market-intel/reference/sources-index.md`, domain map (one-line index)
5. `skills/market-intel/reference/refresh-protocol.md`, how the matrix gets updated
6. `skills/market-intel/reference/companion-config-spec.md`, only if you'll use the per-machine config pattern
7. ONE specific `reference/domains/<domain>.md` shard relevant to your contribution
8. The CONTRIBUTING.md you're reading now

Skip levels 6-7 unless you need them. Level 1-3 + 5 + this file is enough to land a PR.

## License

MIT. Contributions inherit the project license.
