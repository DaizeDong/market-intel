#!/usr/bin/env python3
"""Generate the console's reproducible synthetic evidence; never inspect a host."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from ledger_schema import schema, synthetic_rows

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "market-intel-maintenance-v3-synthetic"


def fixture():
    return {
        "synthetic_origin": RECIPE,
        "maintenance": {
            "companion_identity": "example/companion",
            "public_identity": "example/public",
            "other_identity": "example/other-private",
            "discovery": {"discovered_at": "2031-01-02", "surface": "E1",
                          "name": "Synthetic source", "url": "https://example.com/source",
                          "signal": "synthetic", "one_line_pitch": "Generated discovery example."},
            "surface": {"surface": "E1", "key": "E1:synthetic", "title": "Synthetic source",
                        "url": "https://example.com/source", "signal": "synthetic", "raw": {}},
            "ledger": synthetic_rows(),
            "release": {
                "version": "1.2.3", "commit": "a" * 40,
                "sync": "\n".join(f"[0] {bucket} - synthetic bucket" for bucket in "ABCDEFG"),
                "doc": {"canonical": {"version": "1.2.3", "domain_count": 1, "tool_count": 2},
                        "drifts": [], "exit_code": 0},
                "warning": {"severity": "warn", "field": "synthetic narrative", "location": "README.md"},
            },
        },
        "tool": {"slug": "synthetic-display", "name": "Synthetic catalog operation",
                 "source_id": "github-mcp", "capability_id": "search", "kind": "repo",
                 "domain": "frontier-research", "authentication_required": True},
        "inventory": {
            "schema_version": 1,
            "generated": "2031-01-02T03:04:05+00:00",
            "host": "fixture-machine",
            "clis": {"gh": "C:/Synthetic Tools/gh.exe"},
            "py_modules": {"ccxt": True},
            "mcp": {"ran": True, "servers": [{"name": "github", "connected": True}]},
            "companion": {"present": True, "tools": {"github-mcp": {"installed": True}}},
        },
        "evidence": {
            "schema_version": 1,
            "host": "codex",
            "session_id": "fixture-session",
            "provenance": {"host": "codex", "session_id": "fixture-session",
                           "observed_at": "2031-01-02T03:04:05+00:00",
                           "observation_method": "current-session-adapter"},
            "capabilities": [{
                "source_id": "github-mcp",
                "capability_id": "search",
                "host": "codex",
                "session_id": "fixture-session",
                "observed_at": "2031-01-02T03:04:05+00:00",
                "exposed": True,
                "supported": True,
                "execution": "success",
                "authentication": "authenticated",
                "response_valid": True,
            }],
        },
    }


def generate(out=None, *, check=False):
    sample = fixture()
    objects = {
        "inventory/availability-cache.json.example": sample["inventory"],
        "inventory/host-capabilities.json.example": sample["evidence"],
        "skills/market-intel/reference/live-run-schema.json": schema(),
    }
    payloads = {name: (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
                for name, value in objects.items()}
    payloads["skills/market-intel/reference/remaining-tools.md.example"] = (
        "# Synthetic setup checklist\n\n"
        "This generated example records no real account or host state.\n\n"
        f"- Source: {sample['tool']['source_id']}\n"
        f"- Selected operation: {sample['tool']['capability_id']}\n"
        "- Readiness: setup\n"
        "- Missing evidence: current-session execution and content validation\n"
        "- Next step: inspect the selected host's callable tools, then run a read-only probe.\n"
    ).encode("utf-8")
    discovery = sample["maintenance"]["discovery"]
    payloads["discovery-state.md.example"] = (
        "# Discovery state (synthetic example)\n\n"
        "## Inbox\n\n"
        f"### {discovery['discovered_at']} sweep\n\n"
        f"**{discovery['surface']}** (1)\n\n"
        f"- [{discovery['discovered_at']}] @{discovery['surface']} "
        f"**{discovery['name']}**: {discovery['one_line_pitch']} "
        f"({discovery['signal']}) {discovery['url']}\n"
    ).encode("utf-8")
    surface = {**sample["maintenance"]["surface"],
               "discovered_at": sample["inventory"]["generated"]}
    payloads["surface-inbox.jsonl.example"] = (
        json.dumps(surface, sort_keys=True) + "\n").encode("utf-8")
    payloads["skills/market-intel/metrics/live-runs.jsonl.example"] = (
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                for row in synthetic_rows()).encode("utf-8"))
    mismatches = []
    for name, payload in payloads.items():
        target = Path(out) / Path(name).name if out else ROOT / name
        if check:
            if not target.is_file() or target.read_bytes() != payload:
                mismatches.append(name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    if check:
        print("examples: differs from generator: " + ", ".join(mismatches)
              if mismatches else "examples: reproducible")
    return 1 if mismatches else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="generate flat comparison files in this directory")
    parser.add_argument("--check", action="store_true", help="verify example bytes without writing")
    args = parser.parse_args()
    raise SystemExit(generate(args.out, check=args.check))

