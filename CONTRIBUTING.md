# Contributing to market-intel

Thanks for considering a contribution. Most contributions fall into one of three patterns;
each has a slightly different path.

## Pattern 1, Add a new tool to the source matrix

The matrix lives in `skills/market-intel/reference/`. Adding a tool means writing
**four** synchronized catalog changes, plus navigation when the top pick changes:

1. **`reference/domains/<domain>.md`**, add a row to the source table. Include barrier route
   (① official / ② resale / ③ self-host scrape / ④ browser-automation / ⑤ agent-native),
   capability, detect/install hint, and a one-line risk/cost note.
2. **`reference/tools/<slug>.md`**, full per-tool how-to. Follow the structure of any existing
   tool doc (`reference/tools/polygon.md` is a canonical example). Required sections: Domain(s) /
   Barrier route / Source tier / What it does / Install / Auth / Usage / Gotchas / Last verified.
3. **`reference/tools/index.md`**, add a row pointing at your new tool doc, under the right
   domain section.
4. **`reference/tools/registry.json`**, add its canonical source record and operation metadata.

Update `reference/sources-index.md` only if the domain's top pick changes. Replacements and
renames require the same catalog synchronization; retained tombstones keep their index row,
tool card and registry record.

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

This runs the layered checks: STRUCT / TOOLS / REPO / STAR / **GHACTIVE** / FRESH / DOCCOVER /
REGISTRY / METH / COVER / CHURN+DELETE / CONST. Any BLOCK = fix it; WARN = explain it in the PR.

C7 rewrites require an operator's review of the exact diff. After approval, the operator may
provide `MARKET_INTEL_C7_REVIEW` as local environment configuration and as a trusted repository
variable for CI. Its version-1 JSON contains `baseline` and `replaced_baseline` commit IDs plus
`domains`, keyed by domain name with `before` and `after` SHA-256 hashes of UTF-8 content after
universal-newline normalization. Keep review conversations and other private evidence outside
the public repository. The gate accepts C7 only for the matching baseline, domain and both
content hashes; missing or changed content still blocks, and every other gate retains its veto.
For normal history, use the same commit for both baseline fields. A history rewrite may name
the replaced commit separately; CI uses that mapping only when the candidate has exactly one
parent and it is the configured sanitized baseline. Missing history without this exact mapping
remains `NOT_EXAMINED`.

Of particular note: **GHACTIVE** is the deterministic activity gate. Full spec lives in
`tools/verify_matrix.py` module docstring (canonical). Short version: every github.com URL
in any shard gets a real `gh api` check; 404 / archived / >12mo stale all gate the PR. If
an activity check reports staleness, review the evidence against `CONSTITUTION.md` C4.
`D-STALE` requires more than 18 months without a push and a verified replacement added.
Do not invent a death code to clear a gate; report an unresolved conflict for review.

### Companion-config side (only if you're also installing the tool)

If you're personally using the new tool with the companion-config repo pattern, also follow
`runbooks/add-new-tool.md` in the companion repo to scaffold `tools/<slug>/` template files
and `secrets/<slug>.env`. That's separate from the matrix-side contribution, the matrix
documents the tool; the companion-config tracks YOUR install state.

## Pattern 2, Update or remove an existing tool

- **Update**: keep the shard, tool card, index and registry metadata synchronized. Bump
  `## Last verified: YYYY-MM` only after the documented scope was actually reverified. Note
  in the PR what changed (capability, pricing, repo URL).
- **Remove**: do **NOT** silently delete. Mark the doc `⚠ Avoid (dead, D-<code>)`. The
  5 death codes (D-404 / D-PRICE / D-STALE / D-TOS / D-SUPERSEDED) and per-code action
  are defined in `CONSTITUTION.md` C4 and applied by the refresh protocol.
  Preserve and mark the shard row, index row and tool card, and retain the registry record
  with synchronized metadata so the next sweep and companion check retain the retirement signal. Silent
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
