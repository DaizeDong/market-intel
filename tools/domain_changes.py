"""Catalog coverage and row-change gates over current and historical domain unions."""
import re
from human_review import review_matches

DOMAIN_DIRECTORY = "skills/market-intel/reference/domains"
DEATH_CODES = ("D-404", "D-STALE", "D-PRICE", "D-TOS", "D-SUPERSEDED")


def count_table_rows(text):
    """Count markdown source-table rows (lines starting with '|' that aren't header/sep)."""
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", s) and "---" not in s:
            # skip header rows that contain the literal column names
            if not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I):
                n += 1
    return n


def historical_domains(comparison, current):
    """A failed historical enumeration propagates as NOT_EXAMINED."""
    prefix = DOMAIN_DIRECTORY + "/"
    names = {path[len(prefix):-3] for path in comparison.files(DOMAIN_DIRECTORY)
             if path.startswith(prefix) and path.endswith(".md")
             and "/" not in path[len(prefix):]}
    return {name: comparison.show(f"{prefix}{name}.md") or ""
            for name in sorted(set(current) | names)}


def check_coverage(current, baseline, count_rows, block, global_drop=0.10, shard_drop=0.30):
    base_total = cur_total = 0
    for domain in sorted(set(current) | set(baseline)):
        cur = count_rows(current.get(domain, ""))
        base = count_rows(baseline.get(domain, ""))
        cur_total += cur
        base_total += base
        if base and (base - cur) / base > shard_drop:
            block("COVER", f"{domain}: source rows dropped {base}->{cur} (>{int(shard_drop*100)}%)")
    if base_total and (base_total - cur_total) / base_total > global_drop:
        block("COVER", f"total source rows dropped {base_total}->{cur_total} (>{int(global_drop*100)}%)")
    return cur_total, base_total


def check_domain_diff(d, diff, base_text, changelog_added, star_claim_re, block, *, current_text=None,
                      human_review=None, baseline_commit=None):
    """Preserve CHURN, DELETE and ROUTE rules for an individual historical/current domain."""
    base_text = base_text or ""
    genuinely_added_any = []
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    base_lines = len((base_text or "").splitlines()) or 1
    churn = (len(added) + len(removed)) / base_lines
    if churn > 0.40:
        if review_matches(human_review, baseline_commit, d, base_text, current_text):
            print(f"PASS [CHURN-REVIEW] {d}: exact baseline and candidate content match human C7 review")
        else:
            block("CHURN", f"{d}: {int(churn*100)}% of lines changed (>40%) — looks like a rewrite, not an "
                           f"incremental edit (C7); route to human review")
    def _row_name(line):
        # first cell of a markdown table row = the source identity; strip markdown emphasis AND the
        # volatile (NNk★) star annotation. A star-count refresh is an EDIT of an existing source, not
        # a delete+add of a different one, so it must NOT change the row's identity -- otherwise fixing
        # a stale star (required by the STAR check) trips the DELETE check (C4), the two contradicting
        # each other on any star fix living in the identity cell. The STAR check still verifies the
        # number independently; identity is the repo/tool name, never its (volatile) star count.
        cells = [c.strip() for c in line.lstrip("+-").strip().strip("|").split("|")]
        if not cells:
            return ""
        name = re.sub(r"[*`~]", "", cells[0])
        # Strip the star count in EVERY shape, via the same regex the STAR gate matches with. It
        # used to strip only the literal `(NNk★)`, the same narrow assumption STAR itself made, so
        # the moment STAR started catching a stale `(133★)` and the fix landed, DELETE saw the row's
        # identity change and blocked the very edit STAR demanded. Two gates disagreeing about what
        # a star annotation looks like is how a repo ends up unable to satisfy both.
        name = star_claim_re.sub("", name)
        name = re.sub(r"\(\s*[,;]?\s*\)", "", name)
        name = re.sub(r"\s+\)", ")", re.sub(r"\(\s+", "(", name))
        return re.sub(r"\s{2,}", " ", name).strip().lower()
    def _is_src_row(line):
        s = line.lstrip("+-").strip()
        return s.startswith("|") and "---" not in s and not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I)
    added_names = {_row_name(l) for l in added if _is_src_row(l)}
    removed_names = {_row_name(l) for l in removed if _is_src_row(l)}
    # an added table row whose source-name was NOT already present (removed line) = a genuinely NEW
    # source row (mirror of genuinely_removed). Edits show as remove+add of the same name -> excluded.
    genuinely_added_any += [n for n in added_names if n and n not in removed_names]
    # a removed table row whose source-name still appears in an added row = MODIFICATION, not a
    # deletion (git diff shows an edited line as remove+add). Only a name that's GONE is a real delete.
    genuinely_removed = [l for l in removed if _is_src_row(l) and _row_name(l) and _row_name(l) not in added_names]
    def _plain(text):
        return re.sub(r"[*`~]", "", text).strip().lower()

    def _scoped_reason(name, text, markers):
        for line in text.splitlines():
            plain = _plain(line.lstrip("+")).lstrip("- ")
            if _is_src_row(line):
                if _row_name(line) == name and any(marker.lower() in plain for marker in markers):
                    return True
            else:
                match = re.match(re.escape(name) + r"\s*:\s*(.*)", plain)
                if match and any(marker.lower() in match.group(1) for marker in markers):
                    return True
        return False

    def _rendered_lines(text):
        """Exclude fenced and indented code from rendered catalog declarations."""
        fence = None
        for line in text.splitlines():
            if fence:
                if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                    fence = None
                yield ""
                continue
            opening = re.match(r" {0,3}(`{3,}|~{3,})", line)
            if opening:
                fence = (opening.group(1)[0], len(opening.group(1)))
                yield ""
            elif line.startswith(("    ", "\t")):
                yield ""
            else:
                yield line

    def _paid_reason(name, text):
        bodies = []
        marker = r"(?:paid because|why paid|free route|no free route)\b"
        for line in _rendered_lines(text):
            plain = _plain(line.lstrip("+")).lstrip("- ")
            if _is_src_row(line) and _row_name(line) == name:
                # Other table cells are capabilities, not scoped reason declarations.
                bodies.extend(_plain(cell) for cell in line.strip().strip("|").split("|")[1:]
                              if re.match(marker, _plain(cell)))
            else:
                match = re.match(re.escape(name) + r"\s*:\s*(.*)", plain)
                if match:
                    # Retain every scoped statement. An unsupported or contradictory
                    # second statement cannot disappear behind one supported declaration.
                    bodies.append(match.group(1))
        if not bodies:
            return False
        for body in bodies:
            match = re.fullmatch(
                r"(?:paid because\s+|why paid\s*:\s*|free route (?:unavailable|blocked|gone)\s*:\s*|"
                r"no free route\s*:\s*)(.+)", body)
            if not match:
                return False
            support = match.group(1).rstrip(".").strip()
            # Consume the complete supported limitation sentence. Merely mentioning
            # a limitation word, quoting it, or negating it supplies no C2 evidence.
            words = r"[a-z0-9_/.-]+(?: [a-z0-9_/.-]+)*"
            limitation = (
                r"(?:no free route exists|"
                + words + r" (?:is|are) (?:unavailable|blocked|gone|restricted)|"
                r"(?:[a-z0-9_/-]+ ){0,3}restrictions?)"
                r"(?: (?:for|through|on) " + words + r")?"
                r"(?:, as verified in " + words + r")?"
            )
            if not re.fullmatch(limitation, support):
                return False
            # These tokens cannot be part of the supported noun-phrase restriction form
            # or its qualifiers. The affirmative 'no free route exists' is explicit above.
            if re.search(r"\b(?:not|never|false|untrue|incorrect|wrong|maybe|perhaps|uncertain|"
                         r"unverified|hypothetical|refuted|quoted|word|term|claim|available|"
                         r"supports|works)\b", support):
                return False
            if re.search(r"\bno\b", support) and not support.startswith("no free route exists"):
                return False
        return True

    added_text = "\n".join(added)
    for name in sorted({_row_name(line) for line in genuinely_removed}):
        if not _scoped_reason(name, changelog_added + "\n" + added_text, DEATH_CODES):
            block("DELETE", f"{d}: '{name}' removed without its own death-code/evidence record "
                            f"(C4); add '<source>: D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED' "
                            f"with evidence in CHANGELOG or a matching Avoid(dead) tombstone")

    if current_text is None:
        # Compatibility for callers with only a diff. The matrix supplies its current text directly.
        original, patched, cursor, in_hunk = base_text.splitlines(), [], 0, False
        for line in diff.splitlines():
            hunk = re.match(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", line)
            if hunk:
                start = max(0, int(hunk.group(1)) - 1)
                patched.extend(original[cursor:start])
                cursor, in_hunk = start, True
            elif in_hunk and line.startswith(" "):
                patched.append(line[1:])
                cursor += 1
            elif in_hunk and line.startswith("-"):
                cursor += 1
            elif in_hunk and line.startswith("+"):
                patched.append(line[1:])
        if in_hunk:
            patched.extend(original[cursor:])
        else:
            removed_text = {line[1:] for line in removed}
            patched = [line for line in original if line not in removed_text] + [line[1:] for line in added]
        current_text = "\n".join(patched)

    # ---- ROUTE (C2: a Default pick may not silently downgrade free/④③ -> paid ①②) ----
    # Compare effective route cells for surviving identities, including header-only edits.
    # A route cell can list several barriers; its best declared route governs C2.
    # Capability/notes cells cannot establish a source's route.
    GLYPH_RANK = {"④": 4, "③": 3, "②": 2, "①": 1}
    def _route_ranks(route):
        route = " ".join(route.lower().split())
        # C2 protects free sources as well as browser/self-host routes. The legend calls
        # official APIs "often paid", not always paid; local builds are not browser route ④.
        if route == "free/local":
            return [4]
        descriptors = (r"free(?: oss| tier)?|official(?: \(local stdio\) \+ lib)?|resale|self-host|"
                       r"oauth, non-custodial|bot-token|l2(?: wrapper)?|core|watch|archive|scrape|"
                       r"rss|browser(?:/rss)?|stealth tier")
        ranks = []
        # Consume every affirmative atom. Unknown, negated or questioned remainders make
        # the entire cell unresolved; an embedded glyph cannot salvage such a claim.
        for part in re.split(r"\s*/\s*(?=[①②③④])", route):
            annotated = re.fullmatch(r"(.+?) \(([①②③④].*)\)", part)
            atoms = annotated.groups() if annotated else (part,)
            for atom in atoms:
                match = re.fullmatch(r"([①②③④])(?: (" + descriptors + r"))?", atom)
                if not match:
                    return []
                glyph, descriptor = match.groups()
                ranks.append(GLYPH_RANK[glyph])
                if glyph in "①②" and descriptor in {"free", "free oss", "free tier"}:
                    ranks.append(4)
        return ranks

    def _source_rows(text):
        rows, duplicates, routes, route_cells = {}, set(), {}, {}
        route_column = None
        lines = list(_rendered_lines(text))
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("|"):
                route_column = None
                continue
            if re.fullmatch(r"[\s:|-]+", stripped):
                continue
            cells = stripped.strip("|").split("|")
            if not _is_src_row(line):
                separator = lines[index + 1].strip().strip("|").split("|") if index + 1 < len(lines) else []
                valid = len(separator) == len(cells) and all(
                    re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in separator)
                columns = [offset for offset, cell in enumerate(cells) if _plain(cell) == "route"]
                route_column = columns[0] if valid and len(columns) == 1 else None
                continue
            name = _row_name(line)
            if name in rows:
                duplicates.add(name)
            rows[name] = line
            route = cells[route_column] if route_column is not None and route_column < len(cells) else None
            route_cells[name] = " ".join(route.lower().split()) if route is not None else None
            routes[name] = _route_ranks(route or "")
        return rows, duplicates, routes, route_cells

    old_rows, old_duplicates, old_source_routes, old_route_cells = _source_rows(base_text)
    new_rows, new_duplicates, new_source_routes, new_route_cells = _source_rows(current_text)
    edited_names = added_names & removed_names
    for name in sorted(old_rows.keys() & new_rows.keys()):
        if old_route_cells[name] == new_route_cells[name]:
            # A headerless edited row carrying route notation cannot be compared safely.
            # This is an unresolved comparison, not route inference from another cell.
            if name in edited_names and new_route_cells[name] is None and re.search(
                    r"[①②③④]|(?<!\w)free/local(?!\w)", old_rows[name] + new_rows[name], re.I):
                block("ROUTE", f"{d}: '{name}' modified row has an unresolved declared route")
            continue
        if name in old_duplicates or name in new_duplicates:
            block("ROUTE", f"{d}: '{name}' changed route has an ambiguous source identity")
            continue
        rem_routes, add_routes = old_source_routes[name], new_source_routes[name]
        if not add_routes:
            block("ROUTE", f"{d}: '{name}' modified row has an unresolved declared route")
            continue
        if not rem_routes:
            rem_routes = [4]  # An unresolved old route cannot establish a paid baseline.
        if max(rem_routes) >= 3 and max(add_routes) <= 2:   # ④/③ -> ①/② downgrade
            if not _paid_reason(name, changelog_added + "\n" + new_rows[name]):
                block("ROUTE", f"{d}: '{name}' route downgraded free/④③ -> paid ①② without a "
                               f"CHANGELOG reason (C2) — add why (route/why paid) or revert")

    def _default_pick(text):
        selected = None
        for line in _rendered_lines(text):
            match = re.match(r"default\s+pick:\s*(.*)", _plain(line))
            if match:
                selected = [match.group(1)]
            elif selected is not None:
                if not line.strip() or line.lstrip().startswith(("#", "|", "---")):
                    break
                selected.append(_plain(line))
        return "\n".join(" ".join(line.split()) for line in selected).strip() if selected is not None else None

    def _source_matches(pick, names):
        found = []
        for name in names:
            for match in re.finditer(r"(?<![\w/.-])" + re.escape(name) + r"(?![\w/-]|\.[\w])", pick or ""):
                found.append((match.start(), -len(name), name))
        return sorted(found)

    def _ambiguous_legacy_identity(pick, rows):
        # Legacy picks often omit parenthetical metadata or an API/MCP suffix.
        # Aliases can expose ambiguity, but never establish that an old route was paid.
        aliases = {}
        for name in rows:
            label = name.split("(", 1)[0].strip()
            for alias in {label, re.sub(r"\s+(?:api|mcp)$", "", label)}:
                if alias:
                    aliases.setdefault(alias, set()).add(name)
        exact_spans = [(start, start + len(name)) for start, _, name in _source_matches(pick, rows)]
        for start, _, alias in _source_matches(pick, aliases):
            if len(aliases[alias]) > 1 and not any(
                    left <= start and start + len(alias) <= right for left, right in exact_spans):
                return True
        return False

    def _default_choices(pick, rows):
        """Resolve explicit operands, preserving workflow roles and unresolved choices."""
        choices, unresolved, role_counts = [], [], {}
        if pick is None:
            return choices, unresolved
        # Wrapped operands remain part of their preceding explicit operator.
        text = re.sub(r"(→|->|\+|/|\bor)\s*\n\s*", r"\1 ", pick)
        text = re.sub(r"\s*\n\s*(→|->)", r" \1", text)
        clauses = re.split(r"[;；]|(?<=[.!。])\s+|\n", text)
        for clause in clauses:
            clause = clause.strip().lstrip("- ")
            if not clause:
                continue
            if re.search(r"→|->", clause):
                role, operand = re.split(r"→|->", clause, maxsplit=1)
                role = role.strip()
                if any(start == 0 for start, _, _ in _source_matches(role, rows)):
                    role, operand = "default", clause
                if not role:
                    unresolved.append(clause)
                    continue
            else:
                role, operand = "default", clause
                operand = re.sub(r"^(?:start with|use|add|choose|select|escalate to)\s+", "", operand)
            while operand.strip():
                operand = operand.strip().lstrip("(").strip()
                matches = [(start, length, name) for start, length, name in _source_matches(operand, rows)
                           if start == 0]
                if not matches:
                    unresolved.append(operand)
                    break
                name = matches[0][2]
                position = role_counts.get(role, 0)
                choices.append(((role, position), name))
                role_counts[role] = position + 1
                tail = operand[len(name):].strip()
                if not tail or re.fullmatch(r"[.)。]*", tail):
                    break
                if tail.startswith(":"):
                    # Source-scoped causal prose is evaluated as a reason, not a choice list.
                    if not _paid_reason(name, name + tail):
                        unresolved.append(name + tail)
                    break
                connector = re.match(r"^(?:\(?\+|/|or\b|and\b|followed by\b|→|->)\s*", tail)
                if connector:
                    operand = tail[connector.end():]
                    if not operand:
                        unresolved.append(tail)
                    continue
                if re.match(r"^(?:\(optional\)|for\b|after\b|when\b|if\b|with\b|is unavailable\b)", tail):
                    if re.search(r"[,，]|\+|→|->|\bfollowed by\b|\bor\b|\band\b", tail):
                        unresolved.append(tail)
                    break
                unresolved.append(tail)
                break
        return choices, unresolved

    old_pick = _default_pick(base_text)
    new_pick = _default_pick(current_text)
    old_choices, unresolved_old = _default_choices(old_pick, old_rows)
    new_choices, unresolved_new = _default_choices(new_pick, new_rows)
    old_names = [name for _, name in old_choices]
    new_names = [name for _, name in new_choices]
    selected_route_changed = any(old_route_cells.get(name) != new_route_cells.get(name)
                                 for name in set(old_names) | set(new_names))
    if new_pick != old_pick or selected_route_changed:
        ambiguous_old = bool(old_duplicates.intersection(old_names)) or (
            _ambiguous_legacy_identity(old_pick, old_rows))
        ambiguous_new = bool(new_duplicates.intersection(new_names)) or (
            _ambiguous_legacy_identity("\n".join(unresolved_new), new_rows))
        if ambiguous_old or ambiguous_new:
            block("ROUTE", f"{d}: changed Default pick has an ambiguous "
                           f"{'historical' if ambiguous_old else 'current'} source identity")
        elif unresolved_new or not new_choices:
            detail = "; ".join(unresolved_new) if unresolved_new else "(no selected source)"
            block("ROUTE", f"{d}: changed Default pick has an unresolved explicit choice: {detail}; "
                            "use full table identities and supported choice syntax")
        else:
            historical = dict(old_choices)
            historical_routes = [rank for name in old_names for rank in old_source_routes[name]]
            historical_complete = not unresolved_old and bool(old_choices) and all(
                old_source_routes[name] for name in old_names)
            warned = False
            for role, name in new_choices:
                routes = new_source_routes[name]
                if not routes:
                    block("ROUTE", f"{d}: Default pick '{name}' has no explicit source route")
                    continue
                previous = historical.get(role)
                baseline = old_source_routes.get(previous, [])
                if not baseline:
                    # A new or unresolved workflow cannot inherit a paid primary's cost.
                    baseline = historical_routes if historical_complete else []
                if not baseline:
                    if not warned:
                        print(f"WARN [ROUTE-BASELINE] {d}: historical Default route unresolved; "
                              "applying conservative free-route comparison, not historical verification")
                        warned = True
                    baseline = [4]
                if max(baseline) >= 3 and max(routes) <= 2 and not _paid_reason(
                        name, changelog_added + "\n" + new_pick):
                    block("ROUTE", f"{d}: Default pick '{name}' replaces free/③④ with paid ①② "
                                   "without its own supported paid-route explanation (C2)")

    return genuinely_added_any
