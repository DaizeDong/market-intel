#!/usr/bin/env python3
"""Generate the console's reproducible synthetic evidence; never inspect a host."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from ledger_schema import schema, synthetic_rows

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "market-intel-maintenance-v3-synthetic"


def runtime_transport_cases():
    """Generate transport negatives independently of a live companion or account."""
    identity = fixture()["maintenance"]["companion_identity"]
    return [
        ("https", f"https://github.com/{identity}.git", {}, {}, True),
        ("http", f"http://github.com/{identity}.git", {}, {}, False),
        ("https-port", f"https://github.com:8443/{identity}.git", {}, {}, False),
        ("ssh-port", f"ssh://git@github.com:2222/{identity}.git", {}, {}, False),
        ("ssh-command", f"git@github.com:{identity}.git", {},
         {"GIT_SSH_COMMAND": "synthetic-must-not-run"}, False),
        ("ssh-config", f"git@github.com:{identity}.git",
         {"core.sshCommand": "synthetic-must-not-run"}, {}, False),
        ("https-proxy", f"https://github.com/{identity}.git",
         {"http.proxy": "https://example.com/synthetic-proxy"}, {}, False),
        ("tls-override", f"https://github.com/{identity}.git", {},
         {"GIT_SSL_NO_VERIFY": "true"}, False),
        ("missing-push-remote", f"https://github.com/{identity}.git",
         {"remote.pushDefault": "absent-remote"}, {}, False),
        ("local-push-remote", f"https://github.com/{identity}.git",
         {"branch.main.pushRemote": "."}, {}, False),
    ]


def runtime_visibility_cases():
    """Generate invalid receipts for native consumer failure-path checks."""
    identity = fixture()["maintenance"]["companion_identity"]
    now = datetime.now(timezone.utc).isoformat()
    return [
        ("malformed-json", "not json"),
        ("array", "[]"),
        ("null-state", json.dumps({"_refreshed": now, identity: None})),
        ("wrong-identity", json.dumps({"_refreshed": now, "example/wrong": "PRIVATE"})),
        ("stale", json.dumps({"_refreshed": "2020-01-01T00:00:00+00:00", identity: "PRIVATE"})),
        ("future", json.dumps({"_refreshed": "2099-01-01T00:00:00+00:00", identity: "PRIVATE"})),
    ]


def make_runtime_repository(repository, environment, identity=None, *, versioned=True):
    """Build only generated Git objects; no hooks, network, or existing DATA are read."""
    repository = Path(repository)
    repository.mkdir(parents=True)

    def git(*arguments, input=None):
        result = subprocess.run(["git", "-C", str(repository), *arguments],
                                env=environment, input=input, capture_output=True,
                                text=True, encoding="utf-8", check=True)
        return result.stdout.strip()

    git("init", "-q")
    identity = identity or fixture()["maintenance"]["companion_identity"]
    git("remote", "add", "origin", f"https://github.com/{identity}.git")
    (repository / ".gitignore").write_text("ignored-output/\n", encoding="utf-8")
    if versioned:
        git("add", ".gitignore")
        tree = git("write-tree")
        commit = git("commit-tree", tree, input="Generated synthetic runtime fixture\n")
        git("update-ref", "HEAD", commit)
    return repository


def make_runtime_fixture(root, *, versioned=True):
    """Create isolated native Git repositories and a fresh synthetic visibility receipt."""
    root = Path(root)
    home = root / "home"
    (home / ".pii-guard").mkdir(parents=True)
    excluded = {"http_proxy", "https_proxy", "all_proxy", "no_proxy", "curl_ca_bundle",
                "ssl_cert_file", "ssl_cert_dir", "requests_ca_bundle", "git_ssl_cainfo"}
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_") and key.lower() not in excluded}
    environment.update(HOME=str(home), USERPROFILE=str(home), XDG_CONFIG_HOME=str(home / "xdg"),
                       PROGRAMDATA=str(home / "programdata"),
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
                       GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="Synthetic User",
                       GIT_COMMITTER_NAME="Synthetic User", GIT_AUTHOR_EMAIL="user1@example.com",
                       GIT_COMMITTER_EMAIL="user1@example.com")
    sample = fixture()["maintenance"]
    receipt = home / ".pii-guard/visibility.json"
    receipt.write_text(json.dumps({"_refreshed": datetime.now(timezone.utc).isoformat(),
                                   sample["companion_identity"]: "PRIVATE",
                                   sample["other_identity"]: "PRIVATE",
                                   sample["public_identity"]: "PUBLIC"}) + "\n", encoding="utf-8")
    repository = make_runtime_repository(root / "companion", environment, versioned=versioned)
    return {"repository": repository, "home": home, "environment": environment, "receipt": receipt}


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


def feedback_cases():
    base = {'ts': '2020-01-01', 'domain': 'web-scraping', 'source': 'shard/example-source',
            'detail': 'Generated synthetic observation', 'user_correction': None}
    return {
        'legacy_gaps': [dict(base, outcome=o) for o in ('unverifiable', 'fallback_used')],
        'unknown': [dict(base, outcome='synthetic_unknown_event')],
        'unscoped_verified': [dict(base, outcome='verified')],
        'documentation_verified': [dict(base, outcome='verified', verification_scope='tool_documentation',
                                        evidence_ref='https://example.com/documentation-check')],
        'documentation_without_evidence': [dict(base, outcome='verified', verification_scope='tool_documentation')],
        'correction_event': [dict(base, outcome='user_correction')],
        'typed_failures': [dict(base, outcome=o) for o in ('transport_error', 'auth_failed', 'quota_exceeded', 'content_invalid')],
        'invalid_records': [None, 7, dict(base, ts='not-a-date', outcome='verified'),
                            dict(base, outcome=['not-a-string'])],
    }



def verification_test_source():
    return r'''"""Generator-owned synthetic regressions for private verification and truthful coverage."""
import ast
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import changelog_draft as draft
import check_doc_drift as badges
import domain_changes as domains
import git_baseline
import github_activity as activity
import l0_verify as l0
import poll_surfaces as poll
import private_cache as caches
import private_inventory as storage
from test_private_writers import companion

NOW = datetime(2031, 1, 2, tzinfo=timezone.utc)
RECENT = "2031-01-01T00:00:00Z"
OLD = "2028-01-01T00:00:00Z"
REPO = "example/synthetic"
URL = "https://github.com/" + REPO


@pytest.fixture(autouse=True)
def fixed_time(monkeypatch):
    monkeypatch.setattr(l0, "_now", NOW.replace(tzinfo=None))
    monkeypatch.setattr(l0, "_now_iso", NOW.replace(tzinfo=None).isoformat())
    monkeypatch.setattr(poll, "_now", lambda: NOW)


def github_reply(monkeypatch, payload, calls):
    def run(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
    monkeypatch.setattr(l0.subprocess, "run", run)


def npm_reply(monkeypatch, calls, modified=RECENT):
    def get(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(status_code=200, json=lambda: {
            "time": {"modified": modified}, "dist-tags": {"latest": "1.0.0"},
            "versions": {"1.0.0": {"version": "1.0.0"}}})
    monkeypatch.setattr(l0.requests, "get", get)


def invoke(module, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", [module.__file__, *args])
    return module.main()


@pytest.mark.parametrize("body_status,expected", [(200, "PASS"), (404, "BLOCK"), (503, "UNCERTAIN")])
def test_l0_content_response_controls_status_and_final_url(monkeypatch, body_status, expected):
    original = "https://example.com/source"
    final = "https://example.com/final"
    head = SimpleNamespace(status_code=200, headers={}, url=original, close=lambda: None)
    body = SimpleNamespace(status_code=body_status, headers={}, url=final, close=lambda: None,
                           iter_content=lambda **kwargs: iter([b"Synthetic service documentation"]))
    monkeypatch.setattr(l0.requests, "head", lambda *args, **kwargs: head)
    monkeypatch.setattr(l0.requests, "get", lambda *args, **kwargs: body)
    monkeypatch.setattr(l0, "_cached_or", lambda path, key, probe: l0._result(probe()))
    monkeypatch.setattr(l0, "_dns_resolves", lambda host: True)
    monkeypatch.setattr(l0, "_cert_check", lambda host: {"ok": True, "expires": None})
    result = l0.verify(original, "web")
    assert result["verdict"] == expected
    assert result["details"]["status"] == body_status
    assert result["details"]["final_url"] == final


def test_streamed_body_timeout_is_uncertain_and_closes_response(monkeypatch):
    from urllib3.exceptions import ReadTimeoutError
    closed = []
    def stream(*args, **kwargs):
        raise ReadTimeoutError(None, "https://example.com/source", "synthetic timeout")
        yield b""
    body = l0.requests.Response()
    body.status_code = 200
    body.url = "https://example.com/source"
    body.raw = SimpleNamespace(stream=stream,
                               read=lambda *args, **kwargs: next(stream()),
                               close=lambda: closed.append(True))
    head = SimpleNamespace(status_code=200, headers={}, url=body.url)
    monkeypatch.setattr(l0.requests, "head", lambda *args, **kwargs: head)
    monkeypatch.setattr(l0.requests, "get", lambda *args, **kwargs: body)
    monkeypatch.setattr(l0, "_cached_or", lambda path, key, probe: l0._result(probe()))
    monkeypatch.setattr(l0, "_dns_resolves", lambda host: True)
    monkeypatch.setattr(l0, "_cert_check", lambda host: {"ok": True, "expires": None})
    result = l0.verify(body.url, "web")
    assert result["verdict"] == "UNCERTAIN"
    assert "body inspection failed" in result["evidence"]
    assert closed == [True]


@pytest.mark.parametrize("stamp,expected", [
    ("2099-01-01T00:00:00", "UNCERTAIN"),
    ("2031-01-02T12:00:00Z", "UNCERTAIN"),
    ("2031-01-02T01:00:00+02:00", "PASS"),
    ("invalid", "UNCERTAIN"),
    ("2031-01-01T12:00:00", "PASS"),
    ("2028-01-01T00:00:00Z", "BLOCK"),
])
def test_pypi_release_timestamp_cannot_prove_future_freshness(monkeypatch, stamp, expected):
    payload = {"info": {}, "releases": {"1.0": [{"upload_time": stamp}]}}
    monkeypatch.setattr(l0.requests, "get", lambda *args, **kwargs:
                        SimpleNamespace(status_code=200, json=lambda: payload))
    monkeypatch.setattr(l0, "_cached_or", lambda path, key, probe: l0._result(probe()))
    assert l0.verify("synthetic-package", "pypi")["verdict"] == expected


def test_actual_registry_gate_covers_cards_and_index_without_network():
    root = Path(__file__).resolve().parents[1]
    directory = root / "skills/market-intel/reference/tools"
    registry = json.loads((directory / "registry.json").read_text(encoding="utf-8"))
    cards = {path.stem for path in directory.glob("*.md")
             if path.name != "index.md" and not path.name.endswith(".auto.md")}
    index = set(re.findall(r"\(([a-z0-9][a-z0-9.-]*?)\.md\)",
                           (directory / "index.md").read_text(encoding="utf-8")))
    tree = ast.parse((root / "tools/verify_matrix.py").read_text(encoding="utf-8"))
    statements = None
    for node in ast.walk(tree):
        for field in ("body", "orelse"):
            body = getattr(node, field, [])
            if not isinstance(body, list):
                continue
            for offset, item in enumerate(body):
                if (isinstance(item, ast.Assign) and len(item.targets) == 1
                        and isinstance(item.targets[0], ast.Name)
                        and item.targets[0].id == "reg_slugs"):
                    statements = body[offset:offset + 7]
    assert statements is not None and len(statements) == 7
    code = compile(ast.Module(body=statements, type_ignores=[]), "registry-gate", "exec")
    errors = []
    scope = {"reg": registry, "fs_slugs": cards, "idx_slugs": index,
             "block": lambda tag, detail: errors.append((tag, detail))}
    exec(code, scope)
    assert errors == []
    assert registry["count"] == len(registry["tools"])
    assert sum(registry["by_kind"].values()) == registry["count"]
    # Prove that the actual gate catches a new orphan card.
    scope["fs_slugs"] = cards | {"synthetic-unregistered"}
    exec(code, scope)
    assert any("synthetic-unregistered" in detail for _, detail in errors)


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_l0_transient_http_retries_without_caching(monkeypatch, status):
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, {}))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    saved, calls = [], []
    monkeypatch.setattr(l0, "save_entries", lambda *args: saved.append(args))
    def probe():
        calls.append(status)
        return {"verdict": "UNCERTAIN", "reason": f"transient HTTP {status}"}
    result = l0._cached_or("synthetic-cache", "synthetic-key", probe)
    assert result["verdict"] == "UNCERTAIN"
    assert calls == [status, status] and saved == []


def test_l0_recovered_probe_replaces_transient_observation(monkeypatch):
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, {}))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    saved = []
    monkeypatch.setattr(l0, "save_entries", lambda *args: saved.append(args))
    replies = iter([{"verdict": "UNCERTAIN", "reason": "transient HTTP 503"},
                    {"verdict": "PASS", "reason": "HTTP 200"}])
    assert l0._cached_or("synthetic-cache", "synthetic-key", lambda: next(replies))["verdict"] == "PASS"
    assert len(saved) == 1 and saved[0][1]["synthetic-key"]["verdict"] == "PASS"


@pytest.mark.parametrize("kind", ["npm", "pypi"])
@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_registry_transient_http_is_not_cached(monkeypatch, kind, status):
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, {}))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    saved, calls = [], []
    monkeypatch.setattr(l0, "save_entries", lambda *args: saved.append(args))
    def get(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(status_code=status)
    monkeypatch.setattr(l0.requests, "get", get)
    result = l0.verify("synthetic-package", kind)
    assert result["verdict"] == "UNCERTAIN"
    assert len(calls) == (1 if status == 429 else 2)
    assert saved == []


@pytest.mark.parametrize("kind", ["npm", "pypi"])
@pytest.mark.parametrize("status", [429, 503])
def test_cached_registry_transient_is_rechecked(monkeypatch, kind, status):
    key = f"{kind}:synthetic-package"
    old = {"verdict": "UNCERTAIN", "reason": f"{kind} HTTP {status}",
           "checked_at": l0._now_iso}
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, {key: old}))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    saved, calls = [], []
    monkeypatch.setattr(l0, "save_entries", lambda *args: saved.append(args))
    payload = ({"time": {"modified": RECENT}, "dist-tags": {"latest": "1.0.0"},
                "versions": {"1.0.0": {"version": "1.0.0"}}} if kind == "npm" else
               {"info": {}, "releases": {"1.0": [{"upload_time": RECENT}]}})
    def get(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(status_code=200, json=lambda: payload)
    monkeypatch.setattr(l0.requests, "get", get)
    assert l0.verify("synthetic-package", kind)["verdict"] == "PASS"
    assert len(calls) == 1
    saved_key = "npm-v2:synthetic-package" if kind == "npm" else key
    assert len(saved) == 1 and saved[0][1][saved_key]["verdict"] == "PASS"


@pytest.mark.parametrize("kind", ["npm", "pypi"])
def test_registry_retry_reports_later_rate_limit(monkeypatch, kind):
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, {}))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    saved = []
    monkeypatch.setattr(l0, "save_entries", lambda *args: saved.append(args))
    replies = iter([503, 429])
    monkeypatch.setattr(l0.requests, "get",
                        lambda *args, **kwargs: SimpleNamespace(status_code=next(replies)))
    result = l0.verify("synthetic-package", kind)
    assert result["verdict"] == "UNCERTAIN" and result["details"]["status"] == 429
    assert saved == []


@pytest.mark.parametrize("kind", ["github", "npm"])
def test_l0_private_miss_then_hit_preserves_consumer_sentinel(companion, tmp_path, monkeypatch, kind):
    repository, _, _, _ = companion
    consumer = tmp_path / "consumer"
    (consumer / "metrics").mkdir(parents=True)
    old_cache = consumer / "metrics" / ("gh-api-cache.json" if kind == "github" else "l0-cache.json")
    sentinel = b'{"synthetic-sentinel": "must remain untouched"}\n'
    old_cache.write_bytes(sentinel)
    (consumer / "storage.contract.json").write_bytes((storage.ROOT / "storage.contract.json").read_bytes())
    monkeypatch.setattr(storage, "ROOT", consumer)
    monkeypatch.setattr(l0, "ROOT", str(consumer))
    calls = []
    github_reply(monkeypatch, {"archived": False, "pushed_at": RECENT}, calls)
    npm_reply(monkeypatch, calls)
    target = URL if kind == "github" else "synthetic-package"
    assert l0.verify(target, kind)["verdict"] == "PASS"
    assert l0.verify(target, kind)["verdict"] == "PASS"
    assert len(calls) == 1
    relative = caches.GH_CACHE_PATH if kind == "github" else caches.L0_CACHE_PATH
    rows = json.loads((repository / "data" / relative).read_text(encoding="utf-8"))
    assert rows[REPO if kind == "github" else "npm-v2:synthetic-package"]["verdict"] == "PASS"
    assert old_cache.read_bytes() == sentinel
    assert sorted(p.name for p in (consumer / "metrics").iterdir()) == [old_cache.name]


@pytest.mark.parametrize("state", ["PUBLIC", "UNKNOWN", "unmanaged"])
@pytest.mark.parametrize("kind", ["github", "npm"])
def test_unproven_private_cache_refuses_before_probe(companion, tmp_path, monkeypatch, state, kind):
    repository, routes, states, _ = companion
    if state == "unmanaged":
        monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(tmp_path / "unmanaged"))
    else:
        states[routes["origin"]["fetch"][0]] = state
    calls = []
    github_reply(monkeypatch, {"archived": False, "pushed_at": RECENT}, calls)
    npm_reply(monkeypatch, calls)
    with pytest.raises(storage.InventoryError):
        l0.verify(URL if kind == "github" else "synthetic-package", kind)
    assert calls == []
    assert not (repository / "data/cache").exists()
    assert not (tmp_path / "unmanaged").exists()


@pytest.mark.parametrize("late", [False, True])
def test_cache_write_failure_is_nonzero_and_preserves_snapshot(companion, monkeypatch, late, capsys):
    repository, _, _, _ = companion
    path = repository / "data" / caches.GH_CACHE_PATH
    path.parent.mkdir(parents=True)
    before = b'{"unrelated": {"value": 17}}\n'
    path.write_bytes(before)
    calls = []
    github_reply(monkeypatch, {"archived": False, "pushed_at": RECENT}, calls)
    replace = storage.os.replace
    replacements = []
    def fail(source, destination):
        replacements.append(destination)
        if not late or len(replacements) == 2:
            raise PermissionError("synthetic write denial")
        return replace(source, destination)
    monkeypatch.setattr(storage.os, "replace", fail)
    assert invoke(l0, monkeypatch, "--url", URL, "--type", "github") == 2
    assert len(calls) == int(late)
    assert path.read_bytes() == before
    pending, = (repository / ".staging").glob("inventory-*.tmp")
    assert set(path.parent.iterdir()) == {path}
    if late:
        candidate = json.loads(pending.read_text(encoding="utf-8"))
        assert set(candidate) == {"unrelated", REPO}
        assert candidate["unrelated"] == {"value": 17}
        assert candidate[REPO]["verdict"] == "PASS"
        assert candidate[REPO]["pushed_at"] == RECENT
        assert candidate[REPO]["archived"] is False
    else:
        assert pending.read_bytes() == before
    err = capsys.readouterr().err
    assert "ERROR:" in err
    assert "cleanup refused" in err and "unpublished candidate retained" in err


def test_cache_merge_keeps_other_observations(companion):
    repository, _, _, _ = companion
    destination, cache = caches.load_cache(caches.GH_CACHE_PATH)
    assert cache == {}
    caches.prepare_write(caches.GH_CACHE_PATH, destination)
    caches.save_entries(caches.GH_CACHE_PATH, {"example/first": {"verdict": "PASS"}}, destination)
    caches.save_entries(caches.GH_CACHE_PATH, {"example/second": {"verdict": "BLOCK"}}, destination)
    assert set(json.loads((repository / "data" / caches.GH_CACHE_PATH).read_text(encoding="utf-8"))) == {
        "example/first", "example/second"}


@pytest.mark.parametrize("payload", [
    {}, [], {"archived": False}, {"archived": False, "pushed_at": "invalid"},
    {"archived": False, "pushed_at": "2032-01-01T00:00:00Z"},
    {"archived": False, "pushed_at": "2031-01-01"},
    {"archived": False, "pushed_at": "2031-01-01T00:00:00"},
    {"archived": 0, "pushed_at": RECENT}, {"archived": "false", "pushed_at": RECENT},
])
def test_l0_incomplete_github_observation_never_passes(companion, monkeypatch, payload):
    calls = []
    github_reply(monkeypatch, payload, calls)
    assert l0.verify(URL, "github")["verdict"] == "UNCERTAIN"
    assert len(calls) == 1


@pytest.mark.parametrize("archived,pushed,expected", [
    (False, RECENT, "PASS"), (False, OLD, "BLOCK"), (True, None, "BLOCK"),
    (False, None, "UNCERTAIN"), (False, "invalid", "UNCERTAIN"),
    (False, "2032-01-01T00:00:00Z", "UNCERTAIN"), ("false", RECENT, "UNCERTAIN"),
])
def test_cached_github_pass_is_reclassified_from_typed_evidence(companion, monkeypatch, archived, pushed, expected):
    repository, _, _, _ = companion
    path = repository / "data" / caches.GH_CACHE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({REPO: {"verdict": "PASS", "checked_at": l0._now_iso,
                                      "archived": archived, "pushed_at": pushed,
                                      "hostname": "github.com"}}))
    calls = []
    github_reply(monkeypatch, {"archived": False, "pushed_at": RECENT}, calls)
    assert l0.verify(URL, "github")["verdict"] == expected
    assert calls == []


@pytest.mark.parametrize("modified", ["invalid", "2032-01-01T00:00:00Z"])
def test_npm_invalid_freshness_is_uncertain(companion, monkeypatch, modified):
    npm_reply(monkeypatch, [], modified)
    assert l0.verify("synthetic-package", "npm")["verdict"] == "UNCERTAIN"


def test_matrix_current_evidence_overrides_every_cached_verdict():
    cache, blocks, warnings = {}, [], []
    def run(observation):
        return activity.activity_results(
            [REPO], {REPO: observation}, cache, NOW,
            lambda code, detail: blocks.append(code), lambda code, detail: warnings.append(code))[0]
    archived = {"ok": True, "archived": True, "pushed_at": RECENT}
    assert run(archived)["verdict"] == "BLOCK"
    assert run(archived)["verdict"] == "BLOCK"
    assert blocks == ["GHACTIVE", "GHACTIVE"]
    assert run({"ok": True, "archived": False, "pushed_at": RECENT})["verdict"] == "PASS"
    assert run({"ok": False, "err": "transient"})["verdict"] == "RATE_LIMITED"
    assert warnings == ["GHACTIVE"]
    cache[REPO] = {"verdict": "BLOCK", "checked_at": "2020-01-01T00:00:00Z"}
    assert run({"ok": True, "archived": False, "pushed_at": RECENT})["verdict"] == "PASS"
    assert run({"ok": True, "archived": False, "pushed_at": OLD})["verdict"] == "WARN"
    assert run({"ok": True, "archived": 0, "pushed_at": RECENT})["verdict"] == "RATE_LIMITED"


def test_directory_and_file_interfaces_preserve_final_private_destination(companion, tmp_path):
    repository, _, _, _ = companion
    runtime = repository / "data/runtime"
    runtime.mkdir()
    assert storage.resolve_directory().path == runtime
    assert storage.resolve_directory(path=repository).repository == repository
    file = storage.resolve_destination("profiles/twikit/cookies.json")
    storage.write_text("{}\n", "profiles/twikit/cookies.json", file)
    assert file.path.read_text(encoding="utf-8") == "{}\n"
    for target in (runtime / "missing", file.path, storage.ROOT, tmp_path):
        with pytest.raises(storage.InventoryError):
            storage.resolve_directory(path=target)
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination(path=runtime)


@pytest.mark.parametrize("state", ["PRIVATE", "PUBLIC", "UNKNOWN"])
def test_runtime_leaf_nested_repository_is_the_visibility_authority(companion, monkeypatch, state):
    repository, _, states, _ = companion
    nested = repository / "runtime"
    (nested / ".git").mkdir(parents=True)
    boundary = storage._shared_boundary()
    original_prove = boundary.prove_private_companion
    seen = []
    def prove(directory):
        seen.append(Path(directory))
        if Path(directory).is_relative_to(nested):
            if state != "PRIVATE":
                raise boundary.GitError("synthetic nested visibility")
            return SimpleNamespace(root=str(nested), repositories=("example/nested",), signature="synthetic-nested")
        return original_prove(directory)
    monkeypatch.setattr(boundary, "prove_private_companion", prove)
    if state == "PRIVATE":
        result = storage.resolve_directory(path=nested)
        assert result.repository == nested and result.identity == "example/nested"
    else:
        with pytest.raises(storage.InventoryError, match="visibility"):
            storage.resolve_directory(path=nested)
    assert seen == [nested]


def baseline_reply(monkeypatch, bodies, listing_error=False):
    prefix = domains.DOMAIN_DIRECTORY + "/"
    def run(argv, **kwargs):
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, "a" * 40, "")
        if "ls-tree" in argv:
            if listing_error:
                return subprocess.CompletedProcess(argv, 128, "", "synthetic missing tree")
            available = [prefix + name + ".md" for name in bodies]
            names = available if "-r" in argv else [name for name in available if name == argv[-1]]
            return subprocess.CompletedProcess(argv, 0, "\0".join(names) + "\0", "")
        if "show" in argv:
            name = argv[-1].split("/")[-1][:-3]
            return subprocess.CompletedProcess(argv, 0, bodies[name], "")
        raise AssertionError(argv)
    monkeypatch.setattr(git_baseline.subprocess, "run", run)


def test_whole_domain_deletion_triggers_coverage_and_deletion_gates(tmp_path, monkeypatch):
    original = "| source | route |\n| --- | --- |\n| Synthetic source | ④ |\n"
    baseline_reply(monkeypatch, {"deleted": original})
    comparison = git_baseline.Baseline(tmp_path, "main")
    historical = domains.historical_domains(comparison, {})
    assert historical == {"deleted": original}
    failures = []
    block = lambda code, detail: failures.append(code)
    assert domains.check_coverage({}, historical, domains.count_table_rows, block) == (0, 1)
    diff = "\n".join("-" + line for line in original.splitlines())
    domains.check_domain_diff("deleted", diff, original, "", re.compile(r"\d+★"), block)
    assert failures.count("COVER") == 2
    assert "DELETE" in failures
    failures.clear()
    domains.check_domain_diff("deleted", diff, original,
        "Synthetic source: D-404; https://example.com/source-evidence", re.compile(r"\d+★"), block)
    assert "DELETE" not in failures


def test_new_and_edited_domains_remain_distinct_from_deletions():
    original = "| Synthetic source | ④ |\n"
    changed = "-| Synthetic source | ④ |\n+| Synthetic source | ① |\n"
    failures = []
    block = lambda code, detail: failures.append(code)
    domains.check_coverage({"kept": original, "new": original}, {"kept": original},
                           domains.count_table_rows, block)
    assert not failures
    assert domains.check_domain_diff("kept", changed, original, "", re.compile(r"\d+★"), block) == []
    assert "DELETE" not in failures and "ROUTE" in failures
    failures.clear()
    added = domains.check_domain_diff("new", "+" + original, "", "", re.compile(r"\d+★"), block)
    assert added == ["synthetic source"] and "DELETE" not in failures


def test_failed_baseline_enumeration_is_not_examined(tmp_path, monkeypatch):
    baseline_reply(monkeypatch, {}, listing_error=True)
    comparison = git_baseline.Baseline(tmp_path, "main")
    with pytest.raises(git_baseline.BaselineError, match="NOT_EXAMINED"):
        domains.historical_domains(comparison, {"current": ""})


def test_matrix_calls_shared_gates_without_importing_its_top_level():
    tree = ast.parse(Path(__file__).with_name("verify_matrix.py").read_text(encoding="utf-8"))
    calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)}
    assert {"historical_domains", "check_coverage", "check_domain_diff", "activity_results",
            "prepare_write", "save_entries"} <= calls
    old_paths = {"metrics/l0-cache.json", "metrics/gh-api-cache.json"}
    assert not any(isinstance(node, ast.Constant) and node.value in old_paths
                   for node in ast.walk(tree) if isinstance(node, ast.Constant)
                   and isinstance(node.value, str))


def test_initializer_rejects_unimplemented_mode_before_output_and_keeps_b(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/init_config.py"
    spec = importlib.util.spec_from_file_location("synthetic_init_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "generated-config"
    with pytest.raises(SystemExit) as error:
        invoke(module, monkeypatch, "--skill", "synthetic-skill", "--out", str(target), "--mode", "A")
    assert error.value.code == 2 and not target.exists()
    assert invoke(module, monkeypatch, "--skill", "synthetic-skill", "--out", str(target), "--mode", "B") == 0
    assert json.loads((target / "registry.json").read_text(encoding="utf-8")) == {"schema_version": 1, "tools": []}
    assert "secrets/*" in (target / ".gitignore").read_text(encoding="utf-8")
    assert "Active storage mode: **B**" in (target / "secrets/README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("encoded,version", [
    ("1.2.3", "1.2.3"), ("1.2.3-rc.1", "1.2.3-rc.1"),
    ("1.2.3--rc.1", "1.2.3-rc.1"), ("1.2.3--alpha--one+build.7", "1.2.3-alpha-one+build.7"),
])
def test_badge_roundtrip_preserves_prerelease_color_and_surroundings(tmp_path, encoded, version):
    text = f"before ![Version](https://img.shields.io/badge/version-{encoded}-purple?style=flat) after\n"
    path = tmp_path / "README.md"
    path.write_text(text)
    assert badges.get_readme_version_badge(str(path)) == (version, 1)
    fixed = badges.replace_version_badge(text, "2.0.0-rc.2")
    assert fixed == "before ![Version](https://img.shields.io/badge/version-2.0.0--rc.2-purple?style=flat) after\n"
    path.write_text(fixed)
    assert badges.get_readme_version_badge(str(path)) == ("2.0.0-rc.2", 1)
    assert badges.replace_version_badge(fixed, "2.0.0-rc.2") == fixed


def npm_surface_reply(monkeypatch):
    def get(url):
        if url.endswith("/broken"):
            raise OSError("synthetic unavailable package")
        return {"downloads": 3000 if "/last-month/" in url else 2000}
    monkeypatch.setattr(poll, "_http_json", get)


def test_npm_completion_empty_failure_and_partial_are_distinct(monkeypatch):
    npm_surface_reply(monkeypatch)
    empty = poll.surface_E4_npm_velocity({})
    assert empty == [] and empty.status == "UNINITIALIZED" and empty.attempted == 0
    filtered = poll.surface_E4_npm_velocity({"E4": {"watchlist": ["synthetic-package"], "min_weekly": 1000000}})
    assert filtered == [] and filtered.status == "OK" and filtered.completed == 1
    failed = poll.surface_E4_npm_velocity({"E4": {"watchlist": ["broken"]}})
    assert failed == [] and failed.status == "DEGRADED" and failed.completed == 0
    mixed = poll.surface_E4_npm_velocity({"E4": {"watchlist": ["synthetic-package", "broken"]}})
    assert mixed.status == "DEGRADED" and mixed.completed == 1 and mixed.attempted == 2
    assert [row["key"] for row in mixed] == ["E4:synthetic-package"]


@pytest.mark.parametrize("payload", [{}, {"downloads": True}, {"downloads": -1}])
def test_npm_malformed_counts_are_unexamined(monkeypatch, payload):
    monkeypatch.setattr(poll, "_http_json", lambda url: payload)
    result = poll.surface_E4_npm_velocity({"E4": {"watchlist": ["synthetic-package"]}})
    assert result == [] and result.status == "DEGRADED"


ATOM = '<feed xmlns="http://www.w3.org/2005/Atom">{}</feed>'
VIDEO = '<entry><title>Synthetic video</title><link href="https://example.com/video"/><published>2031-01-01T00:00:00Z</published></entry>'


@pytest.mark.parametrize("response,status,count", [
    (ATOM.format(""), "OK", 0), ("<html/>", "DEGRADED", 0), ("not xml", "DEGRADED", 0),
    (ATOM.format(VIDEO), "OK", 1), (ATOM.format("<entry/>" + VIDEO), "DEGRADED", 1),
])
def test_youtube_feed_health_is_separate_from_discoveries(monkeypatch, response, status, count):
    monkeypatch.setattr(poll, "_http_get", lambda *args, **kwargs: response.encode())
    result = poll.surface_E6_youtube({"E6": {"channels": [{"name": "Synthetic", "ucid": "UCsynthetic"}]}}, 7)
    assert result.status == status and len(result) == count
    assert all(row["url"] and row["key"] != "E6:_warn" for row in result)


def test_youtube_empty_and_failed_channels_have_no_warning_candidates(monkeypatch):
    assert poll.surface_E6_youtube({}, 7).status == "UNINITIALIZED"
    monkeypatch.setattr(poll, "_resolve_ucid", lambda handle: None)
    def unavailable(*args, **kwargs):
        raise OSError("synthetic feed unavailable")
    monkeypatch.setattr(poll, "_http_get", unavailable)
    result = poll.surface_E6_youtube({"E6": {"channels": [
        {"name": "Unknown", "handle": "@synthetic"}, {"name": "Unavailable", "ucid": "UCsynthetic"}]}}, 7)
    assert result == [] and result.status == "DEGRADED"
    assert result.completed == 0 and len(result.errors) == 2


def test_poll_main_persists_partial_real_rows_and_reports_degradation(companion, tmp_path, monkeypatch, capsys):
    repository, _, _, _ = companion
    config = tmp_path / "synthetic-config.json"
    config.write_text(json.dumps({
        "E4": {"watchlist": ["synthetic-package", "broken"]},
        "E6": {"channels": [{"name": "Missing"}, {"name": "Synthetic", "ucid": "UCsynthetic"}]},
    }))
    npm_surface_reply(monkeypatch)
    monkeypatch.setattr(poll, "_http_get", lambda *args, **kwargs: ATOM.format(VIDEO).encode())
    assert invoke(poll, monkeypatch, "--config", str(config), "--only", "E4,E6") == 0
    rows = [json.loads(line) for line in (repository / "data/surface-inbox.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {row["key"] for row in rows} == {"E4:synthetic-package", "E6:https://example.com/video"}
    output = capsys.readouterr().out
    assert "SUMMARY new=2 surfaces_ok=0/2 degraded=E4,E6" in output
    assert invoke(poll, monkeypatch, "--config", str(config), "--only", "E4,E6") == 0
    assert "SUMMARY new=0 surfaces_ok=0/2 degraded=E4,E6" in capsys.readouterr().out
    assert len((repository / "data/surface-inbox.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_poll_total_failure_is_never_successful_empty(companion, tmp_path, monkeypatch, capsys):
    repository, _, _, _ = companion
    config = tmp_path / "synthetic-config.json"
    config.write_text(json.dumps({"E4": {"watchlist": ["broken"]}}))
    npm_surface_reply(monkeypatch)
    assert invoke(poll, monkeypatch, "--config", str(config), "--only", "E4") == 0
    assert "SUMMARY new=0 surfaces_ok=0/1 degraded=E4" in capsys.readouterr().out
    assert not (repository / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("slug", ["yt-dlp", "instaloader", "crawlee", "twikit"])
def test_documented_literal_destination_has_working_private_contract(companion, slug):
    repository, _, _, _ = companion
    path = Path(__file__).resolve().parents[1] / "skills/market-intel/reference/tools" / (slug + ".md")
    calls = []
    for fragment in re.findall(r"\x60([^\x60\n]+)\x60", path.read_text(encoding="utf-8")):
        try:
            tree = ast.parse(fragment)
        except SyntaxError:
            continue
        calls.extend(node for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)
                     and node.func.id in {"resolve_destination", "resolve_directory"}
                     and node.args and isinstance(node.args[0], ast.Constant)
                     and isinstance(node.args[0].value, str))
    assert calls, "The recipe must identify its file or directory destination"
    for call in calls:
        relative = call.args[0].value
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        target = repository / "data" / relative
        if call.func.id == "resolve_directory":
            assert relative.startswith("runtime/")
            with pytest.raises(storage.InventoryError):
                storage.resolve_directory(relative)
            target.mkdir(parents=True)
            assert storage.resolve_directory(relative).path == target
        else:
            assert relative.startswith("profiles/") and target.suffix == ".json"
            destination = storage.resolve_destination(relative)
            storage.write_text("{}\n", relative, destination)
            assert destination.path == target and json.loads(target.read_text(encoding="utf-8")) == {}


@pytest.mark.parametrize("slug", ["stagehand", "paper-qa"])
def test_model_recipes_do_not_prescribe_direct_provider_execution(slug):
    path = Path(__file__).resolve().parents[1] / "skills/market-intel/reference/tools" / (slug + ".md")
    body = path.read_text(encoding="utf-8")
    prohibited = re.compile(
        r"\b(?:OPENAI_API_KEY|ANTHROPIC_API_KEY)\b|"
        r"\bpqa\s+ask\b|from\s+paperqa\s+import\s+ask\b|"
        r"\.page\.(?:act|extract|observe)\s*\("
    )
    assert prohibited.search(body) is None



@pytest.mark.parametrize("observation,verdict", [
    ({"ok": True, "archived": False, "pushed_at": RECENT}, "PASS"),
    ({"ok": True, "archived": True, "pushed_at": RECENT}, "BLOCK"),
    ({"ok": True, "archived": False, "pushed_at": OLD}, "WARN"),
    ({"ok": True}, "RATE_LIMITED"),
    ({"ok": False, "err": "404"}, "BLOCK"),
])
def test_disabled_cache_skips_private_io_and_keeps_current_activity(monkeypatch, observation, verdict):
    def forbidden(*args, **kwargs):
        raise AssertionError("disabled cache must not resolve or touch private storage")
    monkeypatch.setattr(storage, "resolve_destination", forbidden)
    monkeypatch.setattr(storage, "update_text", forbidden)
    destination, cache = caches.load_cache(caches.GH_CACHE_PATH, enabled=False)
    assert destination is None and cache == {}
    assert caches.prepare_write(caches.GH_CACHE_PATH, destination, enabled=False) is None
    blocks, warnings = [], []
    entries = activity.activity_results(
        [REPO], {REPO: observation}, cache, NOW,
        lambda code, detail: blocks.append(code), lambda code, detail: warnings.append(code))
    assert entries[0]["verdict"] == verdict
    assert blocks == (["GHACTIVE"] if verdict == "BLOCK" else [])
    assert warnings == (["GHACTIVE"] if verdict in {"WARN", "RATE_LIMITED"} else [])
    assert caches.save_entries(caches.GH_CACHE_PATH, {REPO: entries[0]},
                               destination, enabled=False) is None
    assert cache[REPO] == entries[0]


def test_matrix_cache_defaults_to_private_preflight_and_merge(companion):
    repository, _, _, _ = companion
    path = repository / "data" / caches.GH_CACHE_PATH
    path.parent.mkdir(parents=True)
    before = b'{"unrelated": {"value": 17}}\n'
    path.write_bytes(before)
    destination, cache = caches.load_cache(caches.GH_CACHE_PATH)
    assert destination.path == path and cache == {"unrelated": {"value": 17}}
    caches.prepare_write(caches.GH_CACHE_PATH, destination)
    assert path.read_bytes() == before
    caches.save_entries(caches.GH_CACHE_PATH, {REPO: {"verdict": "BLOCK"}}, destination)
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "unrelated": {"value": 17}, REPO: {"verdict": "BLOCK"}}


@pytest.mark.parametrize("authority", ["missing", "unmanaged", "PUBLIC", "UNKNOWN"])
def test_matrix_cache_enabled_requires_private_authority(companion, tmp_path, monkeypatch, authority):
    repository, routes, states, _ = companion
    if authority in {"missing", "unmanaged"}:
        selected = tmp_path / "unproven-companion"
        if authority == "unmanaged":
            selected.mkdir()
        monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(selected))
    else:
        selected = repository
        states[routes["origin"]["fetch"][0]] = authority
    with pytest.raises(storage.InventoryError):
        caches.load_cache(caches.GH_CACHE_PATH)
    assert not (selected / "cache").exists()
    assert not (repository / "data/cache").exists()


@pytest.mark.parametrize("failure", ["preflight", "save"])
def test_matrix_cache_enabled_never_falls_back_after_write_failure(companion, monkeypatch, failure, capsys):
    repository, _, _, _ = companion
    path = repository / "data" / caches.GH_CACHE_PATH
    path.parent.mkdir(parents=True)
    before = b'{"unrelated": {"value": 17}}\n'
    path.write_bytes(before)
    destination, _ = caches.load_cache(caches.GH_CACHE_PATH)
    if failure == "save":
        caches.prepare_write(caches.GH_CACHE_PATH, destination)
    def denied(*args, **kwargs):
        raise PermissionError("synthetic cache write denial")
    monkeypatch.setattr(storage.os, "replace", denied)
    with pytest.raises(storage.InventoryError, match="persistence failed"):
        if failure == "preflight":
            caches.prepare_write(caches.GH_CACHE_PATH, destination)
        else:
            caches.save_entries(caches.GH_CACHE_PATH, {REPO: {"verdict": "BLOCK"}}, destination)
    assert path.read_bytes() == before
    pending, = (repository / ".staging").glob("inventory-*.tmp")
    assert set(path.parent.iterdir()) == {path}
    if failure == "save":
        assert json.loads(pending.read_text(encoding="utf-8")) == {
            "unrelated": {"value": 17}, REPO: {"verdict": "BLOCK"}}
    else:
        assert pending.read_bytes() == before
    err = capsys.readouterr().err
    assert "cleanup refused" in err and "unpublished candidate retained" in err


def test_matrix_cache_mode_is_explicit_and_keeps_network_wiring():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "tools/verify_matrix.py").read_text(encoding="utf-8"))
    assignments = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)}
    expected_mode = ast.parse('"--no-cache" not in sys.argv', mode="eval").body
    expected_network = ast.parse('"--no-net" in sys.argv', mode="eval").body
    assert ast.dump(assignments["CACHE_ENABLED"]) == ast.dump(expected_mode)
    assert ast.dump(assignments["NO_NET"]) == ast.dump(expected_network)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    cache_calls = [node for node in calls if isinstance(node.func, ast.Name)
                   and node.func.id in {"load_cache", "prepare_write", "save_entries"}]
    assert len(cache_calls) == 3
    assert all(any(keyword.arg == "enabled" and isinstance(keyword.value, ast.Name)
                   and keyword.value.id == "CACHE_ENABLED" for keyword in call.keywords)
               for call in cache_calls)
    network = next(node for node in tree.body if isinstance(node, ast.If)
                   and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not)
                   and isinstance(node.test.operand, ast.Name) and node.test.operand.id == "NO_NET"
                   and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                           and call.func.id == "load_cache" for call in ast.walk(node)))
    network_calls = [node for node in ast.walk(network) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)]
    preflight = next(node for node in network_calls if node.func.id == "prepare_write")
    fetch = next(node for node in network_calls if node.func.id == "_fetch_repo_api")
    assert preflight.lineno < fetch.lineno
    for branch in (node for node in ast.walk(network) if isinstance(node, ast.If)):
        if any(isinstance(part, ast.Name) and part.id == "CACHE_ENABLED"
               for part in ast.walk(branch.test)):
            assert not any(isinstance(call, ast.Call) and (
                isinstance(call.func, ast.Name) and call.func.id == "_fetch_repo_api"
                or isinstance(call.func, ast.Attribute) and call.func.attr == "map")
                           for call in ast.walk(branch))
    assert {"activity_results", "historical_domains", "check_coverage", "check_domain_diff"} <= {
        node.func.id for node in calls if isinstance(node.func, ast.Name)}
    workflow = (root / ".github/workflows/gate.yml").read_text(encoding="utf-8")
    commands = [line.strip() for line in workflow.splitlines()
                if "python tools/verify_matrix.py " in line and not line.lstrip().startswith("#")]
    assert len(commands) == 1
    assert "--no-cache" in commands[0] and "--base" in commands[0]
    assert "--no-net" not in commands[0]
'''


def route_migration_test_source():
    return r'''def route_migration_flags(before, current, explanation=""):
    import difflib
    diff = "\n".join(difflib.unified_diff(before.splitlines(), current.splitlines(), lineterm=""))
    flags = []
    domains.check_domain_diff("synthetic", diff, before, explanation,
        re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*([kK])?\s*★"),
        lambda code, detail: flags.append((code, detail)), current_text=current)
    return flags


@pytest.mark.parametrize("target,explanation,blocked", [
    ("Free source", "", False),
    ("Paid source", "", True),
    ("Paid source", "Other source: paid because synthetic free endpoint is unavailable.", True),
    ("Paid source", "Paid source: paid because synthetic free endpoint is unavailable.", False),
    ("Free source followed by Paid source", "", True),
    ("Unmapped selection", "", True),
])
def test_route_migration_unknown_baseline_stays_conservative(target, explanation, blocked, capsys):
    before = synthetic_domain("Unmapped historical selection")
    current = synthetic_domain(target)
    flags = route_migration_flags(before, current, explanation)
    assert ("ROUTE" in [code for code, _ in flags]) is blocked
    if target != "Unmapped selection":
        assert "WARN [ROUTE-BASELINE]" in capsys.readouterr().out


def test_route_migration_missing_old_route_is_observable_and_conservative(capsys):
    before = synthetic_domain().replace("| Free source | ④ |", "| Free source | n/a |")
    current = synthetic_domain("Free source after verification")
    flags = route_migration_flags(before, current)
    assert not any(code == "ROUTE" for code, _ in flags)
    assert "WARN [ROUTE-BASELINE]" in capsys.readouterr().out


@pytest.mark.parametrize("route", [
    "① free", "② free", "① free OSS", "② free OSS", "① free tier", "② free tier",
    "free/local", " ①   FREE   TIER ",
])
def test_route_migration_explicit_free_cell_can_be_selected(route):
    before = synthetic_domain()
    current = synthetic_domain("Paid source").replace("| Paid source | ② |", f"| Paid source | {route} |")
    assert not any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("route", ["① free", "② free OSS", "① free tier", "free/local"])
def test_route_migration_free_api_or_local_to_paid_is_a_downgrade(route):
    before = synthetic_domain().replace("| Free source | ④ |", f"| Free source | {route} |")
    current = before.replace(f"| Free source | {route} |", "| Free source | ① |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))
    assert not any(code == "ROUTE" for code, _ in route_migration_flags(
        before, current, "Free source: paid because synthetic free endpoint is unavailable."))


@pytest.mark.parametrize("route", [
    "① not free", "① free unknown", "① free trial", "① freely", "① (free)",
    "n/a", "free/local unknown", "not free/local", "unknown", "① free/local",
])
def test_route_migration_free_inference_rejects_unapproved_cell_forms(route):
    before = synthetic_domain()
    current = synthetic_domain("Paid source").replace("| Paid source | ② |", f"| Paid source | {route} |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def test_route_migration_does_not_infer_free_from_capability_or_cost_prose():
    before = synthetic_domain()
    current = synthetic_domain("Paid source").replace(
        "| Paid source | ② |", "| Paid source | ② | free/local | free tier capability |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def test_route_migration_ambiguous_old_legacy_identity_refuses():
    before = synthetic_domain("Shared API").replace("| Paid source | ② |", "\n".join([
        "| Paid source | ② |", "| Shared API (alpha) | ① |", "| Shared API (beta) | ④ |"]))
    current = before.replace("Default pick:** Shared API", "Default pick:** Free source")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" and "ambiguous" in detail.lower() for code, detail in flags)


@pytest.mark.parametrize("side", ["old", "new"])
def test_route_migration_duplicate_selected_identity_refuses(side):
    before = synthetic_domain()
    current = synthetic_domain("Stable source 1")
    if side == "old":
        before = before.replace("| Free source | ④ |", "| Free source | ④ |\n| Free source | ① |")
        current = before.replace("Default pick:** Free source", "Default pick:** Stable source 1")
    else:
        current = current.replace("| Stable source 1 | ④ |", "| Stable source 1 | ④ |\n| Stable source 1 | ① |")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" and "ambiguous" in detail.lower() for code, detail in flags)


def test_route_migration_unique_old_alias_never_proves_a_paid_baseline(capsys):
    before = synthetic_domain("Shared API").replace(
        "| Free source | ④ |", "| Free source | ④ |\n| Shared API (alpha) | ① |")
    current = before.replace("Default pick:** Shared API", "Default pick:** Paid source")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" for code, _ in flags)
    assert "WARN [ROUTE-BASELINE]" in capsys.readouterr().out


def test_route_migration_known_paid_baseline_keeps_existing_behavior(capsys):
    before = synthetic_domain("Paid source")
    current = synthetic_domain("Paid source after verification")
    assert not any(code == "ROUTE" for code, _ in route_migration_flags(before, current))
    assert "ROUTE-BASELINE" not in capsys.readouterr().out


@pytest.mark.parametrize("route,noise", [
    ("n/a", "unrelated capability ④"), ("①", "unrelated capability ④"),
    ("n/a", "unrelated note ③"), ("②", "unrelated note ③"),
])
def test_route_migration_unrelated_cell_glyphs_never_establish_a_route(route, noise):
    before = synthetic_domain("Unmapped historical selection")
    current = synthetic_domain("Paid source").replace(
        "| Paid source | ② |", f"| Paid source | {route} | {noise} |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def test_route_migration_unrelated_cell_cannot_hide_same_source_paid_downgrade():
    before = synthetic_domain().replace("| Free source | ④ |", "| Free source | ① free |")
    current = before.replace("| Free source | ① free |", "| Free source | ① | unrelated capability ④ |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def test_route_migration_paid_baseline_still_validates_new_secondary_route():
    before = synthetic_domain("Paid source").replace(
        "| Paid source | ② |", "| Paid source | ② |\n| Missing source | n/a |")
    current = before.replace("Default pick:** Paid source", "Default pick:** Paid source followed by Missing source")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("old_pick", [
    "Shared API followed by Free source", "Free source followed by Shared API",
    "Shared API (alpha) followed by Shared API",
])
def test_route_migration_exact_fallback_does_not_hide_ambiguous_old_alias(old_pick):
    before = synthetic_domain(old_pick).replace("| Paid source | ② |", "\n".join([
        "| Paid source | ② |", "| Shared API (alpha) | ① |", "| Shared API (beta) | ④ |"]))
    current = before.replace("Default pick:** " + old_pick, "Default pick:** Free source")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" and "ambiguous" in detail.lower() for code, detail in flags)


def test_route_migration_exact_full_identity_disambiguates_its_own_alias():
    before = synthetic_domain("Shared API (alpha)").replace("| Paid source | ② |", "\n".join([
        "| Paid source | ② |", "| Shared API (alpha) | ① |", "| Shared API (beta) | ④ |"]))
    current = before.replace("Default pick:** Shared API (alpha)", "Default pick:** Free source")
    assert not any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def test_route_migration_exact_fallback_does_not_hide_ambiguous_new_alias():
    before = synthetic_domain().replace("| Paid source | ② |", "\n".join([
        "| Paid source | ② |", "| Shared API (alpha) | ① |", "| Shared API (beta) | ④ |"]))
    current = before.replace("Default pick:** Free source", "Default pick:** Shared API followed by Free source")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" and "ambiguous" in detail.lower() for code, detail in flags)


@pytest.mark.parametrize("route_column", [1, 2])
def test_route_migration_follows_declared_route_header_instead_of_fixed_position(route_column):
    header = "| source | route | capability |" if route_column == 1 else "| source | capability | route |"
    free_row = "| Free source | ④ | unrelated ① |" if route_column == 1 else "| Free source | unrelated ① | ④ |"
    paid_row = "| Paid source | ① | unrelated ④ |" if route_column == 1 else "| Paid source | unrelated ④ | ① |"
    before = synthetic_domain().replace("| source | route |", header).replace(
        "| Free source | ④ |", free_row).replace("| Paid source | ② |", paid_row)
    current = before.replace("Default pick:** Free source", "Default pick:** Paid source")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("header", ["| source | capability |", "| source | route | route |"])
def test_route_migration_missing_or_ambiguous_route_header_refuses(header):
    before = synthetic_domain("Unmapped historical selection").replace("| source | route |", header)
    current = before.replace("Default pick:** Unmapped historical selection", "Default pick:** Free source")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


def route_migration_schema_source():
    return "\n".join(["# Synthetic schema"] + ["Synthetic unchanged context"] * 30 + [
        "| source | route | capability |", "| --- | --- | --- |",
        "| Free source | ④ | ① |", "| Stable source | ④ | ④ |",
        "**Default pick:** Free source", ""])


@pytest.mark.parametrize("new_header", ["| source | capability | route |", "| source | capability | detail |"])
def test_route_migration_schema_only_change_checks_effective_route(new_header):
    before = route_migration_schema_source()
    current = before.replace("| source | route | capability |", new_header)
    assert any(code == "ROUTE" and "free source" in detail.lower()
               for code, detail in route_migration_flags(before, current))


def test_route_migration_schema_only_paid_change_can_carry_scoped_reason():
    before = route_migration_schema_source()
    current = before.replace("| source | route | capability |", "| source | capability | route |")
    flags = route_migration_flags(before, current, "Free source: paid because synthetic free endpoint is unavailable.")
    assert flags == []


@pytest.mark.parametrize("declared", [True, False])
def test_route_migration_local_free_cannot_become_unknown_with_unchanged_default(declared):
    before = synthetic_domain().replace("| Free source | ④ |", "| Free source | free/local |")
    if not declared:
        before = before.replace("| source | route |", "| source | capability |")
    current = before.replace("| Free source | free/local |", "| Free source | unknown |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("route", [
    "not ④", "①; ④ unavailable", "④?", "not③", "③ unavailable", "①/④?",
    "①/② denied", "③ free (④ unavailable)", "① official maybe", "unknown ④",
])
def test_route_migration_negated_or_ambiguous_route_cell_refuses(route):
    before = synthetic_domain()
    current = synthetic_domain("Paid source").replace("| Paid source | ② |", f"| Paid source | {route} |")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("route,free", [
    ("① official", False), ("① OAuth, non-custodial", False), ("① official (local stdio) + lib", False),
    ("① watch", False), ("①/②", False), ("①/③ self-host", True),
    ("② free / ③ self-host", True), ("③ free (④ stealth tier)", True),
    ("③ L2 wrapper", True), ("④ browser/RSS", True), ("④ RSS", True),
    ("① L2", False), ("① bot-token", False), ("③ archive", True), ("③ scrape", True), ("① core", False),
])
def test_route_migration_affirmative_catalog_syntax_preserves_cost_class(route, free):
    before = synthetic_domain()
    current = synthetic_domain("Paid source").replace("| Paid source | ② |", f"| Paid source | {route} |")
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" for code, _ in flags) is not free


@pytest.mark.parametrize("target,blocked", [("Free source", False), ("Unmapped selection", True), ("Paid source", True)])
def test_route_migration_introduced_default_is_also_validated(target, blocked):
    before = synthetic_domain().replace("**Default pick:** Free source\n", "")
    current = before + "\n**Default pick:** " + target + "\n"
    flags = route_migration_flags(before, current)
    assert any(code == "ROUTE" for code, _ in flags) is blocked
'''


def route_migration_a04_test_source():
    return r'''def route_migration_semantic_domain(default="Alpha."):
    return "\n".join(["# Domain: synthetic"] + ["Synthetic unchanged context"] * 30 + [
        "| source | route | capability |", "| --- | --- | --- |",
        "| Alpha | ④ | search |", "| Beta | ② | export |",
        "| Gamma | n/a | archive |", "| Delta | ③ | local index |",
        "", "**Default pick:** " + default, ""])


@pytest.mark.parametrize("selection", [
    "Main workflow → Alpha.\nSecondary workflow → MissingSource.",
    "Alpha followed by MissingSource.", "Alpha + MissingSource.",
    "Alpha.\nUse MissingSource.", "Main → Alpha; secondary → MissingSource.",
])
def test_route_migration_unknown_explicit_secondary_refuses(selection):
    before = route_migration_semantic_domain()
    current = route_migration_semantic_domain(selection)
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("selection", [
    "Main workflow → Alpha.\nSecondary workflow → Delta.",
    "Alpha followed by Delta.", "Alpha + Delta.",
    "Alpha.\nUse Delta.", "Main → Alpha; secondary → Delta.",
])
def test_route_migration_registered_explicit_secondary_passes(selection):
    assert route_migration_flags(route_migration_semantic_domain(),
                                 route_migration_semantic_domain(selection)) == []


@pytest.mark.parametrize("secondary,blocked", [("Gamma", True), ("Delta", False)])
def test_route_migration_retained_secondary_revalidated_on_default_edit(secondary, blocked):
    before = route_migration_semantic_domain("Main workflow → Alpha.\nArchive workflow → " + secondary + ".")
    current = before.replace(secondary + ".\n", secondary + " after access checks.\n")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current)) is blocked


def test_route_migration_removed_unresolved_secondary_no_longer_selected():
    before = route_migration_semantic_domain("Main workflow → Alpha.\nArchive workflow → Gamma.")
    current = route_migration_semantic_domain("Main workflow → Alpha after access checks.")
    assert route_migration_flags(before, current) == []


@pytest.mark.parametrize("opening,closing", [
    ("```markdown", "```"), ("~~~markdown", "~~~"),
    ("   ```markdown", "   ```"), ("````markdown", "```"),
])
def test_route_migration_fenced_table_cannot_supply_selected_source(opening, closing):
    before = route_migration_semantic_domain()
    example = "\n".join(["Example only:", opening, "| source | route |", "| --- | --- |",
                          "| SampleTool | ③ |", closing, ""])
    before += "\n" + example
    current = before.replace("Default pick:** Alpha.", "Default pick:** SampleTool.")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("table,blocked", [
    ("| source | route |\n| --- | --- |\n| SampleTool | ③ |", False),
    ("| source | route |\n| SampleTool | ③ |", True),
    ("    | source | route |\n    | --- | --- |\n    | SampleTool | ③ |", True),
])
def test_route_migration_requires_actual_rendered_source_table(table, blocked):
    before = route_migration_semantic_domain()
    current = before.replace("**Default pick:** Alpha.", table + "\n\n**Default pick:** SampleTool.")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current)) is blocked


@pytest.mark.parametrize("reason", [
    "no free route is false; Alpha remains free and supports the required operation.",
    "paid because no free route is false; Alpha remains free and supports the required operation.",
    "paid because the free endpoint is unavailable?",
    "paid because the synthetic restriction is false.",
    "paid because the free route is available and supports the required operation.",
    "paid because maybe the free route is unavailable.",
    "why paid: the free route remains available for this operation.",
    "no free route",
])
def test_route_migration_refuted_or_unresolved_paid_reason_refuses(reason):
    before = route_migration_semantic_domain()
    current = route_migration_semantic_domain("Beta.")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current, "Beta: " + reason))


@pytest.mark.parametrize("reason", [
    "paid because the required export operation is unavailable through Alpha, as verified in the synthetic operation comparison.",
    "paid because synthetic restriction",
    "paid because no free route exists.",
    "why paid: the required export operation is unavailable through Alpha.",
    "free route unavailable: synthetic endpoint restriction.",
])
def test_route_migration_affirmative_supported_paid_reason_passes(reason):
    before = route_migration_semantic_domain()
    current = route_migration_semantic_domain("Beta.")
    assert route_migration_flags(before, current, "Beta: " + reason) == []


def test_route_migration_explanation_mentions_do_not_become_selections():
    before = route_migration_semantic_domain()
    current = route_migration_semantic_domain(
        "Beta: paid because the required export operation is unavailable through Gamma.")
    assert route_migration_flags(before, current) == []

@pytest.mark.parametrize("replacement,reason,blocked", [
    ("Gamma", "", True), ("Delta", "", False),
    ("Gamma", "Gamma: paid because the required operation is unavailable on Alpha.", False),
    ("Gamma", "Beta: paid because the required operation is unavailable on Alpha.", True),
])
def test_route_migration_secondary_keeps_its_own_historical_cost(replacement, reason, blocked):
    before = route_migration_semantic_domain("Main workflow → Beta.\nArchive workflow → Alpha.")
    before = before.replace("| Gamma | n/a |", "| Gamma | ② |")
    current = before.replace("Archive workflow → Alpha.", "Archive workflow → " + replacement + ".")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current, reason)) is blocked


def test_route_migration_paid_primary_retained_while_free_secondary_is_added():
    before = route_migration_semantic_domain("Main workflow → Beta.")
    current = route_migration_semantic_domain("Main workflow → Beta.\nArchive workflow → Alpha.")
    assert route_migration_flags(before, current) == []


def test_route_migration_reordered_paid_secondary_cannot_take_free_primary_role():
    before = route_migration_semantic_domain("Alpha followed by Beta.")
    current = route_migration_semantic_domain("Beta followed by Alpha.")
    assert any(code == "ROUTE" for code, _ in route_migration_flags(before, current))


@pytest.mark.parametrize("reason", [
    "Beta: paid because the synthetic free endpoint is unavailable.\nBeta: no free route is false.",
    "Beta: no free route is false.\nBeta: paid because the synthetic free endpoint is unavailable.",
    "Beta: paid because an unrelated endpoint is unavailable; Alpha remains free and supports the operation.",
])
def test_route_migration_conflicting_paid_reason_is_unresolved(reason):
    assert any(code == "ROUTE" for code, _ in route_migration_flags(
        route_migration_semantic_domain(), route_migration_semantic_domain("Beta."), reason))

'''


def route_migration_a05_test_source():
    return r'''
@pytest.mark.parametrize("reason", [
    "paid because Alpha is not restricted for the required operation.",
    "paid because the word 'blocked' is merely a documentation example.",
    "paid because the word blocked is merely a documentation example.",
    "paid because the documentation contains unavailable.",
    "paid because no free route exists is a quoted claim.",
])
def test_route_migration_requires_a_complete_affirmative_limitation(reason):
    assert any(code == "ROUTE" for code, _ in route_migration_flags(
        route_migration_semantic_domain(), route_migration_semantic_domain("Beta."), "Beta: " + reason))


@pytest.mark.parametrize("reason", [
    "Beta: paid because Alpha is unavailable.\nBeta: Alpha is available and supports the required operation.",
    "Beta: Alpha is available and supports the required operation.\nBeta: paid because Alpha is unavailable.",
])
def test_route_migration_unmarked_conflicting_scoped_statement_refuses(reason):
    assert any(code == "ROUTE" for code, _ in route_migration_flags(
        route_migration_semantic_domain(), route_migration_semantic_domain("Beta."), reason))


@pytest.mark.parametrize("selection,blocked", [
    ("Alpha for search, MissingSource for export.", True),
    ("Alpha for search, Beta for export.", True),
    ("Alpha for search after current-session checks.", False),
    ("Beta → Alpha.", True),
    ("Alpha → Delta.", False),
    ("Main workflow → Alpha.", False),
])
def test_route_migration_full_qualifier_and_arrow_operands(selection, blocked):
    assert any(code == "ROUTE" for code, _ in route_migration_flags(
        route_migration_semantic_domain(), route_migration_semantic_domain(selection))) is blocked


@pytest.mark.parametrize("reason", [
    "paid because Alpha is unavailable for the required operation.",
    "paid because synthetic restriction",
    "paid because no free route exists.",
])
def test_route_migration_whole_limitation_positive_controls(reason):
    assert route_migration_flags(route_migration_semantic_domain(),
                                 route_migration_semantic_domain("Beta."), "Beta: " + reason) == []


def test_route_migration_star_removal_normalizes_parenthesis_whitespace_only():
    before = route_migration_semantic_domain().replace("| Delta | ③ | local index |",
        "| Delta | ③ | local index |\n| Synthetic source (example/tool 45★) | ④ | lookup |")
    current = before.replace("Default pick:** Alpha.", "Default pick:** Synthetic source (example/tool).")
    assert route_migration_flags(before, current) == []
'''


def final_gate_test_source():
    return r'''# Generated native and pure regressions for the final matrix-gate review.
from test_private_writers import native_companion


def synthetic_domain(default="Free source"):
    return "\n".join(["# Domain: synthetic", "last_verified: 2031-02"]
        + ["Synthetic unchanged context"] * 30
        + ["| source | route |", "| --- | --- |", "| Free source | ④ |", "| Paid source | ② |"]
        + [f"| Stable source {number} | ④ |" for number in range(20)]
        + [f"**Default pick:** {default}", ""])


def synthetic_domain_flags(current, explanation=""):
    import difflib
    before = synthetic_domain()
    diff = "\n".join(difflib.unified_diff(before.splitlines(), current.splitlines(), lineterm=""))
    flags = []
    domains.check_domain_diff("synthetic", diff, before, explanation,
        re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*([kK])?\s*★"),
        lambda code, detail: flags.append((code, detail)))
    return flags


@pytest.mark.parametrize("target,explanation,blocked", [
    ("Paid source", "", True),
    ("Paid source", "Other source: paid because synthetic free endpoint is unavailable.", True),
    ("Paid source", "Paid source: paid because synthetic free endpoint is unavailable.", False),
    ("Paid source: paid because synthetic free endpoint is unavailable", "", False),
    ("Free source", "", False),
    ("Stable source 1", "", False),
])
def test_default_selection_route_gate_binds_the_recommended_source(target, explanation, blocked):
    flags = synthetic_domain_flags(synthetic_domain(target), explanation)
    assert ("ROUTE" in [code for code, _ in flags]) is blocked
    assert not any(code in {"COVER", "CHURN", "DELETE"} for code, _ in flags)


@pytest.mark.parametrize("before_pick,after_pick,blocked", [
    ("\nFree source", "\nPaid source", True),
    ("Start with Free source for research.", "Start with Free source for research tasks.", False),
    ("Free source", "Free source is unavailable; use Paid source.", True),
])
def test_default_recommendation_block_handles_wrapping_and_prose(before_pick, after_pick, blocked):
    import difflib
    before = synthetic_domain().replace("**Default pick:** Free source", "**Default pick:**" + before_pick)
    current = before.replace("**Default pick:**" + before_pick, "**Default pick:**" + after_pick)
    diff = "\n".join(difflib.unified_diff(before.splitlines(), current.splitlines(), lineterm=""))
    flags = []
    domains.check_domain_diff("synthetic", diff, before, "", re.compile(r"\d+★"),
                              lambda code, detail: flags.append(code))
    assert ("ROUTE" in flags) is blocked


@pytest.mark.parametrize("explanation,blocked", [
    ("", True),
    ("Paid source: D-404; https://example.com/other-evidence", True),
    ("Free source extra: D-404; https://example.com/other-evidence", True),
    ("D-404; https://example.com/unscoped-evidence", True),
    ("Free source: D-404; https://example.com/source-evidence", False),
])
def test_deletion_gate_requires_each_removed_source_identity(explanation, blocked):
    current = synthetic_domain().replace("| Free source | ④ |\n", "")
    flags = synthetic_domain_flags(current, explanation)
    assert ("DELETE" in [code for code, _ in flags]) is blocked
    assert not any(code == "CHURN" for code, _ in flags)


def test_deletion_gate_does_not_share_one_sources_evidence_with_another():
    current = synthetic_domain().replace("| Free source | ④ |\n", "").replace("| Paid source | ② |\n", "")
    flags = synthetic_domain_flags(current, "Free source: D-404; https://example.com/source-evidence")
    deletions = [detail.lower() for code, detail in flags if code == "DELETE"]
    assert len(deletions) == 1 and "paid source" in deletions[0]


@pytest.mark.parametrize("explanation,blocked", [
    ("", True),
    ("Paid source: paid because synthetic restriction", True),
    ("Free source: paid because synthetic restriction", False),
])
def test_table_route_change_keeps_source_specific_explanations(explanation, blocked):
    current = synthetic_domain().replace("| Free source | ④ |", "| Free source | ② |")
    flags = synthetic_domain_flags(current, explanation)
    assert ("ROUTE" in [code for code, _ in flags]) is blocked


@pytest.mark.parametrize("pricing,expected", [
    ("## alpha\nSynthetic undated.\n## beta\nlast_verified: 2031-01\n", None),
    ("## alpha-extra\nlast_verified: 2030-12\n## alpha\nlast_verified: 2031-01\n", "2031-01"),
    ("## alpha-extra\nlast_verified: 2030-12\n", None),
    ("## alpha\n### Notes\nlast_verified: 2031-01\n## beta\n", "2031-01"),
    ("## alpha\n# Other group\nlast_verified: 2031-01\n", None),
    ("## alpha\nSynthetic undated.\n##\nlast_verified: 2031-01\n", None),
    ("## alpha `last_verified: 2031-01`\n## beta `last_verified: 2030-12`\n", "2031-01"),
])
def test_metrics_date_stays_in_its_own_domain_section(tmp_path, monkeypatch, pricing, expected):
    root = tmp_path / "synthetic-metrics"
    reference = root / "skills/market-intel/reference"
    (reference / "domains").mkdir(parents=True)
    (reference / "volatile").mkdir()
    (reference / "domains/alpha.md").write_text("| Synthetic source | ④ |\n", encoding="utf-8")
    (reference / "volatile/pricing-install.md").write_text(pricing, encoding="utf-8")
    monkeypatch.setattr(subprocess, "run", lambda argv, **kwargs:
        subprocess.CompletedProcess(argv, 0, "a" * 7 + "\n", ""))
    source = Path(__file__).with_name("emit_metrics.py")
    monkeypatch.setattr(sys, "argv", ["emit_metrics.py", "--period", "2031-03"])
    namespace = {"__name__": "__main__", "__file__": str(root / "tools/emit_metrics.py")}
    exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)
    rows = (root / "metrics/history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    result = json.loads(rows[0])
    assert result["per_domain"]["alpha"]["last_verified"] == expected
    assert result["global"]["total_sources"] == 1


def synthetic_matrix_tree(native_companion, baseline_overrides=None):
    repository = native_companion["repository"]
    reference = repository / "skills/market-intel/reference"
    bodies = {
        "CONSTITUTION.md": "Synthetic immutable rules.\n",
        "CHANGELOG.md": "Synthetic fixture only.\n",
        "skills/market-intel/SKILL.md": "L1 L5\n" + "\n".join(f"{n}. **Synthetic guardrail**" for n in range(1, 9)),
        "skills/market-intel/reference/sources-index.md": "①②③④\n[Synthetic](domains/synthetic.md)\n",
        "skills/market-intel/reference/domains/synthetic.md": synthetic_domain(),
        "skills/market-intel/reference/volatile/pricing-install.md": "## alpha `last_verified: 2031-02`\nSynthetic pricing.\n## beta `last_verified: 2031-01`\nOther pricing.\n",
        "skills/market-intel/reference/tools/index.md": "[Synthetic](synthetic-source.md)\n",
        "skills/market-intel/reference/tools/synthetic-source.md": "# Synthetic source\n## Last verified: 2031-02\n",
        "skills/market-intel/reference/tools/registry.json": json.dumps({"tools": [
            {"slug": "synthetic-source", "kind": "saas", "domain": "synthetic"}]}),
    }
    bodies.update(baseline_overrides or {})
    for relative, payload in bodies.items():
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    def git(*args, input=None):
        return subprocess.run(["git", "-C", str(repository), *args],
            env=native_companion["environment"], input=input, capture_output=True,
            text=True, encoding="utf-8", check=True).stdout.strip()
    git("add", "--", ".")
    tree = git("write-tree")
    commit = git("commit-tree", tree, "-p", "HEAD", input="Generated synthetic matrix baseline\n")
    git("update-ref", "HEAD", commit)
    return repository, reference, commit


def execute_synthetic_matrix(repository, commit, monkeypatch):
    import datetime as calendar
    class FixedDate(calendar.date):
        @classmethod
        def today(cls):
            return cls(2031, 3, 1)
    monkeypatch.setattr(calendar, "date", FixedDate)
    monkeypatch.setattr(sys, "argv", ["verify_matrix.py", "--no-net", "--no-cache", "--base", commit])
    source = Path(__file__).with_name("verify_matrix.py")
    namespace = {"__name__": "__main__", "__file__": str(repository / "tools/verify_matrix.py")}
    with pytest.raises(SystemExit) as status:
        exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)
    return status.value.code, namespace


@pytest.mark.parametrize("location,date,blocked", [
    ("domains/synthetic.md", "2031-01", True),
    ("volatile/pricing-install.md", "2031-01", True),
    ("tools/synthetic-source.md", "2031-01", True),
    ("tools/synthetic-source.md", "2031-02", False),
    ("tools/synthetic-source.md", "2031-03", False),
    ("tools/synthetic-source.md", "2031-04", True),
    ("tools/synthetic-source.md", "2031-00", True),
    ("tools/synthetic-source.md", "2031-02-30", True),
])
def test_native_matrix_freshness_compares_the_verified_baseline(
        native_companion, monkeypatch, capsys, location, date, blocked):
    repository, reference, commit = synthetic_matrix_tree(native_companion)
    target = reference / location
    target.write_text(target.read_text(encoding="utf-8").replace("2031-02", date), encoding="utf-8")
    code, scope = execute_synthetic_matrix(repository, commit, monkeypatch)
    fresh = [message for message in scope["fails"] if "[FRESH]" in message]
    assert bool(fresh) is blocked, capsys.readouterr().out
    assert code == (1 if blocked else 0)


@pytest.mark.parametrize("pricing,blocked", [
    ("## beta `last_verified: 2031-01`\nOther pricing.\n## alpha `last_verified: 2031-02`\nSynthetic pricing.\n", False),
    ("## alpha `last_verified: 2031-01`\nSynthetic pricing.\n## beta `last_verified: 2031-03`\nOther pricing.\n", True),
    ("## alpha\nSynthetic pricing without a date.\n## beta `last_verified: 2031-01`\nOther pricing.\n", True),
])
def test_native_matrix_freshness_tracks_sections_by_identity(native_companion, monkeypatch, capsys, pricing, blocked):
    repository, reference, commit = synthetic_matrix_tree(native_companion)
    (reference / "volatile/pricing-install.md").write_text(pricing, encoding="utf-8")
    code, scope = execute_synthetic_matrix(repository, commit, monkeypatch)
    fresh = [message for message in scope["fails"] if "[FRESH]" in message]
    assert bool(fresh) is blocked, capsys.readouterr().out
    assert code == (1 if blocked else 0)


@pytest.mark.parametrize("relative,before,after", [
    ("volatile/pricing-install.md",
     "## alpha `last_verified: 2031-02` (stars verified 2031-02-01)\n",
     "## alpha `last_verified: 2031-03` (stars verified 2031-03-01)\n"),
    ("tools/synthetic-source.md", "# Synthetic source\n## Last verified: 2031-00\n",
     "# Synthetic source\n## Last verified: 2031-02\n"),
])
def test_native_matrix_freshness_allows_valid_evidence_repairs(
        native_companion, monkeypatch, capsys, relative, before, after):
    repository, reference, commit = synthetic_matrix_tree(native_companion, {
        "skills/market-intel/reference/" + relative: before})
    (reference / relative).write_text(after, encoding="utf-8")
    code, scope = execute_synthetic_matrix(repository, commit, monkeypatch)
    assert code == 0 and not scope["fails"], capsys.readouterr().out


@pytest.mark.parametrize("state", ["present", "missing", "missing-directory"])
def test_native_matrix_requires_its_authoritative_registry(native_companion, monkeypatch, capsys, state):
    repository, reference, commit = synthetic_matrix_tree(native_companion)
    if state == "missing":
        (reference / "tools/registry.json").unlink()
    elif state == "missing-directory":
        for path in (reference / "tools").iterdir():
            path.unlink()
        (reference / "tools").rmdir()
    code, scope = execute_synthetic_matrix(repository, commit, monkeypatch)
    registry = [message for message in scope["fails"] if "[REGISTRY]" in message]
    assert bool(registry) is (state != "present"), capsys.readouterr().out
    assert code == (0 if state == "present" else 1)
'''


def deployment_test_source():
    return r'''
def deployment_case(tmp_path, monkeypatch):
    """Run embedded production functions with synthetic Git and real temporary files."""
    import hashlib

    script = Path(__file__).resolve().with_name("deploy_skill.sh")
    source = script.read_text(encoding="utf-8").split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    tree = ast.parse(source, filename=str(script))
    assert isinstance(tree.body[-1], ast.Try)
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == "deploy" for node in ast.walk(tree.body[-1]))
    namespace = {"__name__": "synthetic_deployment_contract", "__file__": str(script)}
    exec(compile(ast.Module(body=tree.body[:-1], type_ignores=[]), str(script), "exec"), namespace)
    repo, live = tmp_path / "repo", tmp_path / "live"
    skill = repo / "skills" / "market-intel"
    skill.mkdir(parents=True)
    live.mkdir()
    payloads = {"SKILL.md": b"# Synthetic skill\n", "current.md": b"Current synthetic instruction\n"}
    old = {"obsolete.md": b"Old synthetic instruction\n", "custom.txt": b"Synthetic custom note\n"}
    for name, payload in payloads.items():
        (skill / name).write_bytes(payload)
    for name, payload in old.items():
        (live / name).write_bytes(payload)
    blobs = {hashlib.sha1(payload).hexdigest(): payload for payload in payloads.values()}
    entries = b"".join(
        f"100644 blob {hashlib.sha1(payload).hexdigest()}\tskills/market-intel/{name}\0".encode()
        for name, payload in payloads.items())
    case = {"namespace": namespace, "repo": repo, "live": live, "skill": skill,
            "payloads": payloads, "old": old, "calls": [], "gate_calls": 0,
            "control": "", "commit": "a" * 40, "published": "a" * 40}

    def run(argv, *, cwd, check, **kwargs):
        assert Path(cwd) == repo
        assert check is True
        args = list(map(str, argv))
        case["calls"].append(args)
        if args[0] != "git":
            assert args == [sys.executable, "tools/verify_matrix.py", "--no-net", "--no-cache"]
            case["gate_calls"] += 1
            if case["control"] == "gate-failure":
                raise subprocess.CalledProcessError(23, args)
            if case["control"] == "gate-dirty":
                (skill / "current.md").write_bytes(b"Synthetic source changed during gate\n")
            return SimpleNamespace(returncode=0, stdout=b"")
        command = tuple(args[1:])
        if command == ("rev-parse", "--show-toplevel"):
            result = str(repo).encode()
        elif command == ("status", "--porcelain=v1", "--untracked-files=all"):
            result = b" M synthetic\n" if any((skill / name).read_bytes() != payload
                       for name, payload in payloads.items()) else b""
        elif command in {("checkout", "main", "--quiet"),
                         ("pull", "--quiet", "--ff-only", "origin", "main")}:
            if case["control"] == command[0] + "-failure":
                raise subprocess.CalledProcessError(23, args)
            result = b""
        elif command == ("branch", "--show-current"):
            result = b"main\n"
        elif command == ("rev-parse", "HEAD"):
            result = case["commit"].encode()
        elif command == ("rev-parse", "refs/remotes/origin/main"):
            result = case["published"].encode()
        elif command == ("ls-tree", "-rz", "--full-tree", case["commit"], "--", "skills/market-intel/"):
            result = entries
        elif len(command) == 3 and command[:2] == ("cat-file", "blob"):
            result = blobs[command[2]]
        else:
            raise AssertionError(f"Unexpected synthetic Git request: {command}")
        return SimpleNamespace(returncode=0, stdout=result)

    monkeypatch.setattr(subprocess, "run", run)
    return case


def deployment_old_bytes(directory, expected):
    assert {path.name: path.read_bytes() for path in directory.iterdir()} == expected


@pytest.mark.parametrize("control", ["checkout-failure", "pull-failure", "gate-failure", "gate-dirty"])
def test_deployment_stops_before_mutation_on_source_or_gate_failure(tmp_path, monkeypatch, control):
    case = deployment_case(tmp_path, monkeypatch)
    case["control"] = control
    with pytest.raises((RuntimeError, subprocess.CalledProcessError)):
        case["namespace"]["deploy"](case["repo"], case["live"])
    deployment_old_bytes(case["live"], case["old"])
    assert not list(tmp_path.glob(".live.*"))
    if control in {"checkout-failure", "pull-failure"}:
        assert case["gate_calls"] == 0


def test_deployment_rejects_unpublished_head_before_gate(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    case["published"] = "b" * 40
    with pytest.raises(RuntimeError, match="published"):
        case["namespace"]["deploy"](case["repo"], case["live"])
    deployment_old_bytes(case["live"], case["old"])
    assert case["gate_calls"] == 0
    assert not list(tmp_path.glob(".live.*"))


def test_deployment_rejects_dirty_source_before_checkout(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    (case["skill"] / "current.md").write_bytes(b"Synthetic uncommitted instruction\n")
    with pytest.raises(RuntimeError, match="clean"):
        case["namespace"]["deploy"](case["repo"], case["live"])
    deployment_old_bytes(case["live"], case["old"])
    assert not any(command[1] == "checkout" for command in case["calls"])
    assert case["gate_calls"] == 0
    assert not list(tmp_path.glob(".live.*"))


def test_deployment_replaces_whole_legacy_leaf_and_retains_every_old_file(tmp_path, monkeypatch):
    import hashlib

    case = deployment_case(tmp_path, monkeypatch)
    case["namespace"]["deploy"](case["repo"], case["live"])
    assert {path.name for path in case["live"].iterdir()} == {
        "SKILL.md", "current.md", ".market-intel-deployment.json"}
    for name, payload in case["payloads"].items():
        assert (case["live"] / name).read_bytes() == payload
    backups = list(tmp_path.glob(".live.backup-*"))
    assert len(backups) == 1
    deployment_old_bytes(backups[0], case["old"])
    manifest = json.loads((case["live"] / ".market-intel-deployment.json").read_text())
    assert manifest["commit"] == case["commit"]
    assert {name: row["sha256"] for name, row in manifest["files"].items()} == {
        name: hashlib.sha256(payload).hexdigest() for name, payload in case["payloads"].items()}


def deployment_fail_promotion(case, monkeypatch):
    namespace = case["namespace"]
    original = namespace["move_to_empty"]
    observations = []

    def move(source, destination, *args, **kwargs):
        if Path(destination) == case["live"] and Path(source).name.startswith(".live.stage-"):
            observations.append("promotion-failure")
            raise OSError("Synthetic final promotion failure")
        return original(source, destination, *args, **kwargs)

    monkeypatch.setitem(namespace, "move_to_empty", move)
    return observations


def test_deployment_failed_promotion_restores_old_bytes_and_keeps_backup(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    observations = deployment_fail_promotion(case, monkeypatch)
    with pytest.raises(OSError, match="promotion failure"):
        case["namespace"]["deploy"](case["repo"], case["live"])
    assert observations == ["promotion-failure"]
    deployment_old_bytes(case["live"], case["old"])
    backups = list(tmp_path.glob(".live.backup-*"))
    assert len(backups) == 1
    deployment_old_bytes(backups[0], case["old"])


@pytest.mark.parametrize("replacement", ["directory", "alias"])
def test_deployment_restore_collision_never_receives_copied_bytes(tmp_path, monkeypatch, replacement):
    case = deployment_case(tmp_path, monkeypatch)
    namespace = case["namespace"]
    promotion = deployment_fail_promotion(case, monkeypatch)
    original = namespace["shutil"].copytree
    observations = []
    retained = {"sentinel.txt": b"Synthetic destination retained bytes\n"}
    outside = tmp_path / "unrelated-restore-target"
    outside.mkdir()
    (outside / "sentinel.txt").write_bytes(retained["sentinel.txt"])

    def copy(source, destination, *args, **kwargs):
        destination = Path(destination)
        if destination.name.startswith(".live.restore-") and not observations:
            observations.append(destination)
            if destination.exists():
                destination.rename(tmp_path / "held-empty-restore")
            if replacement == "alias":
                if os.name == "nt":
                    import _winapi
                    _winapi.CreateJunction(str(outside), str(destination))
                else:
                    destination.symlink_to(outside, target_is_directory=True)
            else:
                destination.mkdir()
                (destination / "sentinel.txt").write_bytes(retained["sentinel.txt"])
        return original(source, destination, *args, **kwargs)

    monkeypatch.setattr(namespace["shutil"], "copytree", copy)
    with pytest.raises(OSError, match="promotion failure"):
        namespace["deploy"](case["repo"], case["live"])
    assert promotion == ["promotion-failure"]
    assert len(observations) == 1
    deployment_old_bytes(outside, retained)
    deployment_old_bytes(observations[0], retained)
    backups = list(tmp_path.glob(".live.backup-*"))
    assert len(backups) == 1
    deployment_old_bytes(backups[0], case["old"])
    assert not case["live"].exists()


def test_deployment_restore_never_overwrites_new_empty_live_directory(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    namespace = case["namespace"]
    original = namespace["move_to_empty"]
    observations = []

    def move(source, destination, *args, **kwargs):
        if Path(destination) == case["live"]:
            if Path(source).name.startswith(".live.stage-"):
                raise OSError("Synthetic final promotion failure")
            if Path(source).name.startswith(".live.restore-"):
                case["live"].mkdir()
                info = case["live"].stat()
                observations.append((info.st_dev, info.st_ino))
        return original(source, destination, *args, **kwargs)

    monkeypatch.setitem(namespace, "move_to_empty", move)
    with pytest.raises(OSError, match="promotion failure"):
        namespace["deploy"](case["repo"], case["live"])
    assert len(observations) == 1
    info = case["live"].stat()
    assert (info.st_dev, info.st_ino) == observations[0]
    assert list(case["live"].iterdir()) == []
    backups = list(tmp_path.glob(".live.backup-*"))
    assert len(backups) == 1
    deployment_old_bytes(backups[0], case["old"])


def test_deployment_rollback_does_not_quarantine_substituted_live_directory(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    namespace = case["namespace"]
    original = namespace["tree_state"]
    observations = []
    unrelated = {"unrelated.txt": b"Synthetic unrelated directory bytes\n"}

    def state(path):
        if Path(path) == case["live"] and (case["live"] / "current.md").is_file() and not observations:
            observations.append("live-substituted")
            case["live"].rename(tmp_path / "held-promoted-tree")
            case["live"].mkdir()
            (case["live"] / "unrelated.txt").write_bytes(unrelated["unrelated.txt"])
            raise RuntimeError("Synthetic live directory substitution")
        return original(path)

    monkeypatch.setitem(namespace, "tree_state", state)
    with pytest.raises(RuntimeError, match="substitution"):
        namespace["deploy"](case["repo"], case["live"])
    assert observations == ["live-substituted"]
    deployment_old_bytes(case["live"], unrelated)
    backups = list(tmp_path.glob(".live.backup-*"))
    assert len(backups) == 1
    deployment_old_bytes(backups[0], case["old"])
    assert not any((path / "unrelated.txt").exists() for path in tmp_path.glob(".live.failed-*"))


def test_deployment_rejects_hardlinked_live_file_before_mutation(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    outside = tmp_path / "outside.txt"
    payload = b"Synthetic outside bytes\n"
    outside.write_bytes(payload)
    os.link(outside, case["live"] / "linked.txt")
    with pytest.raises(RuntimeError, match="Hardlinked"):
        case["namespace"]["deploy"](case["repo"], case["live"])
    assert outside.read_bytes() == payload
    assert (case["live"] / "linked.txt").read_bytes() == payload
    assert case["calls"] == []
    assert not list(tmp_path.glob(".live.*"))


def test_deployment_manifest_creation_does_not_truncate_inserted_hardlink(tmp_path, monkeypatch):
    case = deployment_case(tmp_path, monkeypatch)
    outside = tmp_path / "outside-manifest.txt"
    before = b"Synthetic external manifest sentinel\n"
    outside.write_bytes(before)
    original = Path.open
    observations = []

    def opened(path, *args, **kwargs):
        if (path.name == ".market-intel-deployment.json"
                and path.parent.name.startswith(".live.stage-") and not observations):
            observations.append(path)
            os.link(outside, path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    with pytest.raises((OSError, RuntimeError)):
        case["namespace"]["deploy"](case["repo"], case["live"])
    assert len(observations) == 1
    assert outside.read_bytes() == before
    deployment_old_bytes(case["live"], case["old"])
'''


def final_review_test_source():
    return r'''# Generated final-review regressions with synthetic provider and Git observations.


@pytest.fixture
def memory_cache(monkeypatch):
    rows = {}
    monkeypatch.setattr(l0, "load_cache", lambda path: (None, rows))
    monkeypatch.setattr(l0, "prepare_write", lambda *args: None)
    monkeypatch.setattr(l0, "save_entries", lambda path, entries, destination: rows.update(entries))
    return rows


def web_last_modified(monkeypatch, status, age_seconds):
    from datetime import timedelta
    modified = ((l0._now - timedelta(seconds=age_seconds)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                if age_seconds is not None else None)
    calls = []
    def response(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(status_code=status, headers={"Last-Modified": modified},
                               url="https://example.com/source", close=lambda: None)
    monkeypatch.setattr(l0.requests, "head", response)
    monkeypatch.setattr(l0.requests, "get", response)
    monkeypatch.setattr(l0, "_dns_resolves", lambda host: True)
    monkeypatch.setattr(l0, "_cert_check", lambda host: {"ok": True, "expires": None})
    return modified, calls


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize("age_seconds,expected", [
    (None, "UNCERTAIN"), (-800 * 86400, "UNCERTAIN"), (-1, "UNCERTAIN"),
    (0, "PASS"), (86400, "PASS"), (360 * 86400, "PASS"),
    (360 * 86400 + 1, "UNCERTAIN"), (800 * 86400, "UNCERTAIN"),
])
def test_web_antibot_requires_past_last_modified_within_interval(
        monkeypatch, memory_cache, status, age_seconds, expected):
    modified, calls = web_last_modified(monkeypatch, status, age_seconds)
    result = l0.verify("https://example.com/source", "web")
    assert result["verdict"] == expected
    assert result["details"]["last_modified"] == modified
    observed_calls = len(calls)
    assert l0.verify("https://example.com/source", "web")["verdict"] == expected
    if expected == "PASS":
        assert len(calls) == observed_calls
    else:
        assert len(calls) > observed_calls
        assert "web:https://example.com/source" not in memory_cache


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize("age_seconds", [-800 * 86400, -1, None, 800 * 86400])
def test_web_antibot_rechecks_legacy_pass_with_invalid_last_modified(
        monkeypatch, memory_cache, status, age_seconds):
    modified, calls = web_last_modified(monkeypatch, status, age_seconds)
    memory_cache["web:https://example.com/source"] = {
        "verdict": "PASS", "checked_at": l0._now_iso, "status": status,
        "reason": f"anti-bot {status} but DNS+cert healthy and unchecked Last-Modified",
        "last_modified": modified, "dns_ok": True, "cert_ok": True, "registry_mode": False}
    assert l0.verify("https://example.com/source", "web")["verdict"] == "UNCERTAIN"
    assert calls
    assert l0.verify("https://example.com/source", "web")["verdict"] == "UNCERTAIN"


@pytest.mark.parametrize("status", [401, 403])
def test_web_antibot_invalid_cached_pass_can_recover_with_new_fresh_evidence(
        monkeypatch, memory_cache, status):
    web_last_modified(monkeypatch, status, 86400)
    key = "web:https://example.com/source"
    memory_cache[key] = {"verdict": "PASS", "checked_at": l0._now_iso, "status": status,
                         "last_modified": "Thu, 01 Jan 2099 00:00:00 GMT"}
    assert l0.verify("https://example.com/source", "web")["verdict"] == "PASS"
    assert memory_cache[key]["last_modified"] == "Wed, 01 Jan 2031 00:00:00 GMT"


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize("age_seconds", [None, -800 * 86400])
def test_registry_antibot_does_not_require_web_last_modified(
        monkeypatch, memory_cache, status, age_seconds):
    _, calls = web_last_modified(monkeypatch, status, age_seconds)
    assert l0.verify("https://example.com/source", "web-registry")["verdict"] == "PASS"
    observed_calls = len(calls)
    assert l0.verify("https://example.com/source", "web-registry")["verdict"] == "PASS"
    assert len(calls) == observed_calls


def npm_payload(latest):
    return {"time": {"modified": RECENT}, "dist-tags": {"latest": "1.0.0"},
            "versions": {"1.0.0": latest, "0.9.0": {"deprecated": "synthetic old release"}}}


@pytest.mark.parametrize("metadata,expected", [
    ({"version": "1.0.0"}, "PASS"),
    ({"version": "1.0.0", "deprecated": "synthetic retired release"}, "BLOCK"),
    ({"version": "1.0.0", "deprecated": ""}, "PASS"),
    ({"version": "1.0.0", "deprecated": False}, "UNCERTAIN"),
    ({"version": "1.0.0", "deprecated": []}, "UNCERTAIN"),
    ({}, "UNCERTAIN"), ({"version": None}, "UNCERTAIN"),
    ({"version": 1}, "UNCERTAIN"), ({"version": "0.9.0"}, "UNCERTAIN"),
    (None, "UNCERTAIN"), ([], "UNCERTAIN"),
])
def test_npm_verdict_uses_latest_version_metadata(monkeypatch, memory_cache, metadata, expected):
    payload = npm_payload(metadata)
    monkeypatch.setattr(l0.requests, "get", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: payload))
    assert l0.verify("synthetic-package", "npm")["verdict"] == expected


@pytest.mark.parametrize("payload", [
    [], None, {"time": {"modified": RECENT}},
    {"time": {"modified": RECENT}, "dist-tags": [], "versions": {}},
    {"time": {"modified": RECENT}, "dist-tags": {"latest": ""}, "versions": {}},
    {"time": {"modified": RECENT}, "dist-tags": {"latest": []}, "versions": {}},
    {"time": {"modified": RECENT}, "dist-tags": {"latest": "1.0.0"}, "versions": []},
    {"time": {"modified": RECENT}, "dist-tags": {"latest": "1.0.0"}, "versions": {}},
])
def test_npm_missing_or_invalid_latest_evidence_is_uncertain(monkeypatch, memory_cache, payload):
    monkeypatch.setattr(l0.requests, "get", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: payload))
    assert l0.verify("synthetic-package", "npm")["verdict"] == "UNCERTAIN"


def test_npm_legacy_cache_does_not_preserve_unchecked_pass(monkeypatch, memory_cache):
    memory_cache["npm:synthetic-package"] = {"verdict": "PASS", "checked_at": l0._now_iso,
                                            "reason": "synthetic unchecked cache"}
    payload = npm_payload({"version": "1.0.0", "deprecated": "synthetic retired release"})
    monkeypatch.setattr(l0.requests, "get", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: payload))
    assert l0.verify("synthetic-package", "npm")["verdict"] == "BLOCK"


def public_gh_response(argv, **kwargs):
    host = argv[argv.index("--hostname") + 1] if "--hostname" in argv else os.environ.get("GH_HOST")
    public = host == "github.com"
    payload = {"archived": public, "pushed_at": RECENT, "s": 12, "a": public, "p": RECENT,
               "items": [{"full_name": REPO, "html_url": URL if public else "https://github.example.invalid/" + REPO,
                          "stargazers_count": 12}], "incomplete_results": False}
    return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")


@pytest.fixture
def hostile_gh_host(monkeypatch):
    monkeypatch.setenv("GH_HOST", "github.example.invalid")
    monkeypatch.setattr(subprocess, "run", public_gh_response)


def test_l0_public_github_request_ignores_inherited_host(hostile_gh_host, memory_cache):
    result = l0.verify(URL, "github")
    assert result["verdict"] == "BLOCK"
    assert memory_cache[REPO]["hostname"] == "github.com"


@pytest.mark.parametrize("hostname", [None, "github.example.invalid"])
@pytest.mark.parametrize("verdict", ["PASS", "BLOCK"])
def test_l0_legacy_or_other_host_cache_is_rechecked(monkeypatch, memory_cache, hostname, verdict):
    memory_cache[REPO] = {"verdict": verdict, "archived": verdict == "BLOCK", "pushed_at": RECENT,
                         "checked_at": l0._now_iso, "hostname": hostname}
    expected = "BLOCK" if verdict == "PASS" else "PASS"
    payload = {"archived": expected == "BLOCK", "pushed_at": RECENT}
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""))
    assert l0.verify(URL, "github")["verdict"] == expected
    assert memory_cache[REPO]["hostname"] == "github.com"


def matrix_nodes():
    source = Path(__file__).with_name("verify_matrix.py").read_text(encoding="utf-8")
    return ast.parse(source).body


def test_matrix_public_github_request_and_cache_are_host_bound(hostile_gh_host):
    nodes = matrix_nodes()
    fetch = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == "_fetch_repo_api")
    namespace = {"subprocess": subprocess, "json": json}
    exec(compile(ast.Module(body=[fetch], type_ignores=[]), "matrix-fetch", "exec"), namespace)
    result = namespace["_fetch_repo_api"](REPO)
    assert result["archived"] is True
    saved = {}
    namespace.update(NO_NET=False, repos=[REPO], repo_api={REPO: result}, gh_cache={}, _now_ts=NOW,
                     activity_results=activity.activity_results, block=lambda *a: None, warn=lambda *a: None,
                     GH_CACHE_PATH="synthetic-cache", gh_destination=None, CACHE_ENABLED=True,
                     save_entries=lambda path, entries, *a, **k: saved.update(entries), InventoryError=RuntimeError)
    cache_block = next(node for node in nodes if isinstance(node, ast.If)
                       and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                               and call.func.id == "activity_results" for call in ast.walk(node)))
    exec(compile(ast.Module(body=[cache_block], type_ignores=[]), "matrix-cache", "exec"), namespace)
    assert saved[REPO]["hostname"] == "github.com"


def test_poller_public_search_ignores_inherited_host(hostile_gh_host):
    rows = poll.surface_E2_github_velocity({"E2": {"topics": ["synthetic-topic"]}}, 7)
    assert rows.status == "OK" and rows.completed == 1
    assert rows[0]["url"] == URL


@pytest.fixture
def synthetic_draft_inputs(monkeypatch):
    monkeypatch.setattr(draft, "_reconfigure_stdout_utf8", lambda: None)
    monkeypatch.setattr(draft, "require_call", lambda: None)
    monkeypatch.setattr(draft, "parse_latest_changelog_version", lambda: "1.0.0")
    monkeypatch.setattr(draft, "parse_plugin_version", lambda: "1.0.1")
    monkeypatch.setattr(draft, "extract_top_entry_text", lambda: "Synthetic previous entry")


@pytest.mark.parametrize("failed_flag", ["--stat", "--name-status"])
def test_failed_git_diff_stops_draft_before_model(monkeypatch, synthetic_draft_inputs, failed_flag, capsys):
    def git(argv):
        if argv[0] == "log":
            return 0, "abc1234 synthetic change", ""
        if failed_flag in argv:
            return 128, "synthetic partial output", "synthetic diff failure"
        return 0, "", ""
    monkeypatch.setattr(draft, "_git", git)
    monkeypatch.setattr(draft, "run_claude", lambda prompt: pytest.fail("collection failure must stop before model"))
    assert draft.main(["--since", "HEAD~1"]) == 1
    output = capsys.readouterr()
    assert "git diff" in output.err and failed_flag in output.err and "synthetic diff failure" in output.err
    assert output.out == ""


def test_successfully_empty_git_diff_can_be_drafted(monkeypatch, synthetic_draft_inputs, capsys):
    monkeypatch.setattr(draft, "_git", lambda argv: (0, "abc1234 synthetic change" if argv[0] == "log" else "", ""))
    def model(prompt):
        assert "(no diff stats)" in prompt and "(no name-status)" in prompt
        return 0, "Synthetic draft", ""
    monkeypatch.setattr(draft, "run_claude", model)
    assert draft.main(["--since", "HEAD~1"]) == 0
    assert "Synthetic draft" in capsys.readouterr().out


@pytest.mark.parametrize("surface", ["E4", "E6"])
def test_unconfigured_surface_is_not_counted_as_success(monkeypatch, tmp_path, surface, capsys):
    monkeypatch.setattr(poll.private_inventory, "resolve_destination",
                        lambda *a, **k: SimpleNamespace(path=tmp_path / "synthetic-inbox", identity="example/private"))
    monkeypatch.setattr(poll, "_http_json", lambda *a, **k: pytest.fail("unconfigured surface must not request data"))
    monkeypatch.setattr(poll, "_http_get", lambda *a, **k: pytest.fail("unconfigured surface must not request data"))
    monkeypatch.setattr(poll.sys, "argv", ["poll_surfaces", "--config", str(tmp_path / "absent.json"),
                                         "--only", surface, "--dry-run"])
    assert poll.main() == 0
    output = capsys.readouterr().out
    assert "UNINITIALIZED" in output and "surfaces_ok=0/1" in output
    assert "degraded=" + surface in output
'''


def discovery_test_source():
    return r'''"""Generated synthetic discovery coverage; no network or live inventory is used."""
import datetime as dt
from types import SimpleNamespace

import pytest

from test_private_writers import companion, load_writer

SINCE = dt.date(2031, 1, 1)
ATOM = '<feed xmlns="http://www.w3.org/2005/Atom">{}</feed>'
VIDEO = ('<entry><title>Synthetic tool update</title>'
         '<link href="https://example.com/synthetic-video"/>'
         '<published>2031-01-02T00:00:00Z</published>'
         '<description>Synthetic evidence.</description></entry>')


def response(payload=None, *, text="", status=200):
    def decode():
        if isinstance(payload, Exception):
            raise payload
        return payload
    return SimpleNamespace(status_code=status, text=text, json=decode)


@pytest.fixture
def discovery(monkeypatch):
    module = load_writer("discover")
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected HTTP request")
    monkeypatch.setattr(module.requests, "get", forbidden)
    monkeypatch.setattr(module, "_today", lambda: "2031-01-03")
    return module


@pytest.mark.parametrize("configuration", ["shipped", "empty", "invalid"])
def test_e6_unconfigured_fails_without_observation_or_write(
        configuration, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    if configuration == "empty":
        monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [])
    elif configuration == "invalid":
        monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                            [("Synthetic A", ""), ("Synthetic B", None)])
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e6", "--out", str(target)]) == 1
    captured = capsys.readouterr()
    assert "E6: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert "configured=0 attempted=0 completed=0" in captured.err
    assert "set verified UCIDs" in captured.err
    assert not target.parent.exists()


@pytest.mark.parametrize("failure", ["http", "request", "xml", "root"])
def test_e6_all_failed_feeds_are_not_empty_success(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [("Synthetic", "UCsynthetic")])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        return response(text={"xml": "<feed", "root": "<html/>"}.get(failure, ""),
                        status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    with pytest.raises(RuntimeError, match="no usable Atom feeds"):
        discovery.channel_e6_youtube(SINCE)
    assert len(calls) == 1
    assert "configured=1 attempted=1 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [ATOM.format(""), ATOM.format(
    VIDEO.replace("2031-01-02", "2030-01-02"))])
def test_e6_valid_empty_observation_allows_success_without_write(
        payload, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [("Synthetic", "UCsynthetic")])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k: response(text=payload))
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e6", "--since", str(SINCE), "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E6: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert not target.parent.exists()


@pytest.mark.parametrize("failure", ["http", "request", "xml", "root"])
def test_e6_partial_failure_keeps_valid_feed_rows(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                        [("Synthetic failed", "UCfailed"), ("Synthetic ready", "UCready")])
    def get(url, **kwargs):
        if url.endswith("UCready"):
            return response(text=ATOM.format(VIDEO))
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        return response(text={"xml": "<feed", "root": "<html/>"}.get(failure, ""),
                        status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    rows = discovery.channel_e6_youtube(SINCE)
    assert len(rows) == 1 and rows[0]["name"] == "Synthetic ready: Synthetic tool update"
    assert rows[0]["url"] == "https://example.com/synthetic-video"
    assert "configured=2 attempted=2 completed=1" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["http", "request", "json", "shape", "count", "boolean", "negative"])
def test_e4_no_valid_pairs_fails(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        payload = {
            "json": ValueError("synthetic malformed JSON"), "shape": {},
            "count": {"downloads": [{}]}, "boolean": {"downloads": [{"downloads": True}]},
            "negative": {"downloads": [{"downloads": -1}]},
        }.get(failure, {"downloads": []})
        return response(payload, status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    with pytest.raises(RuntimeError, match="no usable npm response pairs"):
        discovery.channel_e4_npm(SINCE)
    assert len(calls) == (1 if failure == "request" else 2)
    assert "configured=1 attempted=1 completed=0" in capsys.readouterr().err


def test_e4_unconfigured_is_not_a_completed_observation(discovery, monkeypatch, capsys):
    monkeypatch.setattr(discovery, "NPM_PACKAGES", [])
    with pytest.raises(RuntimeError, match="no usable npm response pairs"):
        discovery.channel_e4_npm(SINCE)
    assert "configured=0 attempted=0 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [{"downloads": []}, {"downloads": [{"downloads": 1}]}])
def test_e4_valid_empty_or_below_threshold_allows_success(
        payload, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k: response(payload))
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e4", "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E4: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert not target.parent.exists()


def test_e4_partial_results_and_failure_logs_keep_package_order(discovery, monkeypatch, capsys):
    packages = ["synthetic-fail-a", "synthetic-ready-a", "synthetic-fail-b", "synthetic-ready-b"]
    monkeypatch.setattr(discovery, "NPM_PACKAGES", packages)
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        package = url.rsplit("/", 1)[1]
        return response({"downloads": [{"downloads": 1000}]},
                        status=503 if "fail" in package else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    rows = discovery.channel_e4_npm(SINCE)
    assert [row["name"] for row in rows] == ["synthetic-ready-a", "synthetic-ready-b"]
    assert all(row["surface"] == "E4" for row in rows)
    assert len(calls) == 8
    errors = capsys.readouterr().err
    assert errors.index("synthetic-fail-a") < errors.index("synthetic-fail-b")
    assert "configured=4 attempted=4 completed=2" in errors


@pytest.mark.parametrize("failed_period", ["last-week", "last-month"])
@pytest.mark.parametrize("failure", ["http", "request", "shape"])
@pytest.mark.parametrize("mixed", [False, True])
def test_e4_one_failed_period_never_completes_a_package(
        failed_period, failure, mixed, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    packages = ["synthetic-half"] + (["synthetic-complete"] if mixed else [])
    monkeypatch.setattr(discovery, "NPM_PACKAGES", packages)
    def get(url, **kwargs):
        period, package = url.rsplit("/", 2)[-2:]
        if package == "synthetic-half" and period == failed_period:
            if failure == "request":
                raise discovery.requests.RequestException("Synthetic failed period")
            return response({} if failure == "shape" else {"downloads": []},
                            status=503 if failure == "http" else 200)
        return response({"downloads": [{"downloads": 1000}]})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e4", "--out", str(target)]) == (0 if mixed else 1)
    output = capsys.readouterr()
    assert f"configured={len(packages)} attempted={len(packages)} completed={int(mixed)}" in output.err
    assert "synthetic-half: failed" in output.err
    if mixed:
        contents = target.read_text(encoding="utf-8")
        assert "synthetic-complete" in contents and "synthetic-half" not in contents
        assert "E4: 1 candidates" in output.out
    else:
        assert "E4: FAIL" in output.out and not target.parent.exists()


@pytest.mark.parametrize("healthy_empty", [False, True])
def test_default_sweep_requires_a_completed_channel(
        healthy_empty, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if "/downloads/range/" in url:
            return response(status=503)
        if healthy_empty and "huggingface.co/api/spaces" in url:
            return SimpleNamespace(json=lambda: [], raise_for_status=lambda: None)
        raise discovery.requests.RequestException("synthetic unavailable source")
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--out", str(target)]) == (0 if healthy_empty else 1)
    captured = capsys.readouterr()
    assert f"failures: {5 if healthy_empty else 6}/6" in captured.out
    assert "E4: FAIL" in captured.out and "E6: FAIL" in captured.out
    assert not any("youtube.com" in url for url in calls)
    assert not target.parent.exists()


def test_main_persists_partial_discovery_from_real_channel(
        discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                        [("Synthetic failed", "UCfailed"), ("Synthetic ready", "UCready")])
    monkeypatch.setattr(discovery.requests, "get",
                        lambda url, **k: response(text=ATOM.format(VIDEO),
                                                 status=503 if url.endswith("UCfailed") else 200))
    target = repository / "data/deliverables/reports/discovery.md"
    assert discovery.main(["--channel", "e6", "--since", str(SINCE), "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert "https://example.com/synthetic-video" in content
    assert "Synthetic failed:" not in content
    assert "E6: 1 candidates" in capsys.readouterr().out


def observation_response(payload=None, *, text="", status=200):
    reply = response(payload, text=text, status=status)
    def raise_for_status():
        if status >= 400:
            raise RuntimeError("synthetic HTTP failure")
    reply.raise_for_status = raise_for_status
    return reply


@pytest.mark.parametrize("channel,payload,text", [
    ("e1", None, "<html/>"),
    ("e1", None, "<rss/>"),
    ("e1", None, "<rss><wrong/></rss>"),
    ("e1", None, "<rss><channel/><channel/></rss>"),
    ("e1", None, "<wrapper><rss><channel/></rss></wrapper>"),
    ("e1", None, '<feed xmlns="https://example.com/not-atom"/>'),
    ("e1", None, "<feed"),
    ("e2", None, ""),
    ("e2", {}, ""),
    ("e2", [], ""),
    ("e2", {"items": None}, ""),
    ("e2", {"items": {}}, ""),
    ("e2", {"items": "synthetic"}, ""),
    ("e2", {"items": [None]}, ""),
    ("e2", {"items": ["synthetic"]}, ""),
    ("e3", None, ""),
    ("e3", {}, ""),
    ("e3", {"error": "synthetic"}, ""),
    ("e3", "", ""),
    ("e3", 0, ""),
    ("e3", False, ""),
    ("e3", [None], ""),
    ("e3", ["synthetic"], ""),
    ("e5", None, ""),
    ("e5", {}, ""),
    ("e5", [], ""),
    ("e5", {"hits": None}, ""),
    ("e5", {"hits": {}}, ""),
    ("e5", {"hits": "synthetic"}, ""),
    ("e5", {"hits": [None]}, ""),
    ("e5", {"hits": ["synthetic"]}, ""),
])
@pytest.mark.parametrize("through_main", [False, True])
def test_malformed_response_never_completes_an_observation(
        channel, payload, text, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response(payload, text=text)
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/malformed-observation.md"
    if through_main:
        assert discovery.main(["--channel", channel, "--since", str(SINCE),
                               "--out", str(target)]) == 1
        summary = capsys.readouterr()
        assert channel.upper() + ": FAIL" in summary.out
        assert "failures: 1/1" in summary.out
        assert not target.parent.exists()
    else:
        with pytest.raises((RuntimeError, ValueError, discovery.ET.ParseError)):
            discovery.CHANNELS[channel](SINCE)
    assert len(calls) == 1


@pytest.mark.parametrize("channel,payload,text", [
    ("e1", None, "<rss><channel/></rss>"),
    ("e1", None, ATOM.format("")),
    ("e1", None, "<feed/>"),
    ("e2", {"items": []}, ""),
    ("e3", [], ""),
    ("e5", {"hits": []}, ""),
])
def test_valid_empty_envelope_is_a_completed_observation(
        channel, payload, text, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    monkeypatch.setattr(discovery.requests, "get",
                        lambda *a, **k: observation_response(payload, text=text))
    target = repository / "data/deliverables/uncreated/valid-empty.md"
    assert discovery.main(["--channel", channel, "--since", str(SINCE),
                           "--out", str(target)]) == 0
    summary = capsys.readouterr()
    assert channel.upper() + ": 0 candidates" in summary.out
    assert "failures: 0/1" in summary.out
    assert not target.parent.exists()


@pytest.mark.parametrize("topics", [[], ["", None, "  "], [None]])
@pytest.mark.parametrize("through_main", [False, True])
def test_e2_unconfigured_fails_without_http_or_output(
        topics, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics)
    # The discovery fixture already makes any HTTP attempt fail this test.
    target = repository / "data/deliverables/uncreated/unconfigured-topics.md"
    if through_main:
        assert discovery.main(["--channel", "e2", "--out", str(target)]) == 1
        assert "E2: FAIL" in capsys.readouterr().out
        assert not target.parent.exists()
    else:
        with pytest.raises(RuntimeError, match="no usable GitHub topic responses"):
            discovery.channel_e2_github(SINCE)
        assert "configured=0 attempted=0 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["shape", "json", "http", "request"])
@pytest.mark.parametrize("failed_first", [False, True])
def test_e2_partial_topic_failure_keeps_valid_rows_in_private_output(
        failure, failed_first, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    topics = ["synthetic-failed", "synthetic-ready"]
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics if failed_first else topics[::-1])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if "synthetic-ready" in url:
            return observation_response({"items": [{
                "full_name": "synthetic-owner/synthetic-tool",
                "html_url": "https://example.com/synthetic-github-tool",
                "stargazers_count": 75, "created_at": "2031-01-02T00:00:00Z",
                "description": "Synthetic useful observation.",
            }]})
        if failure == "request":
            raise discovery.requests.RequestException("synthetic unavailable topic")
        return observation_response(
            ValueError("synthetic malformed JSON") if failure == "json" else {},
            status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/reports/partial-github.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count("https://example.com/synthetic-github-tool") == 1
    assert "synthetic-owner/synthetic-tool" in content
    assert "topic:synthetic-failed" not in content
    assert len(calls) == 2
    summary = capsys.readouterr()
    assert "E2: 1 candidates" in summary.out
    assert "configured=2 attempted=2 completed=1" in summary.err
    assert "synthetic-failed: failed" in summary.err


@pytest.mark.parametrize("healthy", [None, "e1-rss", "e1-atom", "e2", "e3", "e5"])
def test_default_sweep_distinguishes_invalid_bodies_from_valid_empty(
        healthy, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if url == discovery.PULSEMCP_FEED:
            feed = {"e1-rss": "<rss><channel/></rss>", "e1-atom": ATOM.format("")}
            return observation_response(text=feed.get(healthy, "<html/>"))
        if "api.github.com/search/repositories" in url:
            return observation_response({"items": []} if healthy == "e2" else {})
        if url == discovery.HF_SPACES_URL:
            return observation_response([] if healthy == "e3" else {})
        if url == discovery.HN_API:
            return observation_response({"hits": []} if healthy == "e5" else {})
        if "/downloads/range/" in url:
            return observation_response(status=503)
        pytest.fail("unexpected synthetic surface request")
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/whole-sweep.md"
    assert discovery.main(["--since", str(SINCE), "--out", str(target)]) == (
        1 if healthy is None else 0)
    summary = capsys.readouterr()
    assert f"failures: {6 if healthy is None else 5}/6" in summary.out
    assert not any("youtube.com" in url for url in calls)
    assert not target.parent.exists()


@pytest.mark.parametrize("channel,payload,text,expected_url", [
    ("e1", None,
     "<rss><channel><item/><item><title>Synthetic feed tool</title>"
     "<link>https://example.com/synthetic-feed-tool</link>"
     "<pubDate>2031-01-02</pubDate></item></channel></rss>",
     "https://example.com/synthetic-feed-tool"),
    ("e1", None, ATOM.format("<entry/>" + VIDEO),
     "https://example.com/synthetic-video"),
    ("e3", [{}, {"id": "synthetic-owner/synthetic-space",
                 "lastModified": "2031-01-02T00:00:00Z", "likes": 3,
                 "trendingScore": 2, "cardData": {"title": "Synthetic space"}}], "",
     "https://huggingface.co/spaces/synthetic-owner/synthetic-space"),
    ("e5", {"hits": [{"title": "Synthetic below threshold", "points": 1},
                    {"objectID": "synthetic-item", "title": "Synthetic HN tool",
                     "url": "https://example.com/synthetic-hn-tool", "points": 30}]}, "",
     "https://example.com/synthetic-hn-tool"),
])
def test_schema_valid_partial_candidates_still_persist(
        channel, payload, text, expected_url, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery.requests, "get",
                        lambda *a, **k: observation_response(payload, text=text))
    target = repository / "data/deliverables/reports/partial-candidates.md"
    assert discovery.main(["--channel", channel, "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count(expected_url) == 1
    assert "Synthetic below threshold" not in content
    assert channel.upper() + ": 1 candidates" in capsys.readouterr().out


@pytest.mark.parametrize("has_items", [False, True])
@pytest.mark.parametrize("through_main", [False, True])
def test_e2_incomplete_topic_never_completes_or_writes(
        has_items, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-incomplete"])
    items = [{"full_name": "synthetic-owner/partial-tool",
              "html_url": "https://example.com/partial-github-tool",
              "stargazers_count": 75, "description": "Synthetic partial observation."}] if has_items else []
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response({"incomplete_results": True, "items": items})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/incomplete-github.md"
    if through_main:
        assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                               "--out", str(target)]) == 1
    else:
        with pytest.raises(RuntimeError, match="no usable GitHub topic responses"):
            discovery.channel_e2_github(SINCE)
    captured = capsys.readouterr()
    assert "incomplete_results=true" in captured.err
    assert "configured=1 attempted=1 completed=0" in captured.err
    assert "completed=1" not in captured.err
    if through_main:
        assert "E2: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert len(calls) == 1 and not target.parent.exists()


@pytest.mark.parametrize("incomplete_first", [False, True])
def test_e2_incomplete_topic_preserves_completed_topics_only(
        incomplete_first, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    topics = ["synthetic-incomplete", "synthetic-empty", "synthetic-ready"]
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics if incomplete_first else topics[::-1])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        incomplete = "synthetic-incomplete" in url
        items = [] if "synthetic-empty" in url else [{
            "full_name": "synthetic-owner/partial-tool" if incomplete else "synthetic-owner/ready-tool",
            "html_url": "https://example.com/partial-github-tool" if incomplete else
                        "https://example.com/ready-github-tool",
            "stargazers_count": 75, "description": "Synthetic observation.",
        }]
        return observation_response({"incomplete_results": incomplete, "items": items})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/reports/complete-topics.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count("https://example.com/ready-github-tool") == 1
    assert "partial-github-tool" not in content and "synthetic-owner/partial-tool" not in content
    assert len(calls) == 3
    captured = capsys.readouterr()
    assert "E2: 1 candidates" in captured.out
    assert "configured=3 attempted=3 completed=2" in captured.err
    assert "synthetic-incomplete: failed" in captured.err and "incomplete_results=true" in captured.err


def test_e2_explicit_complete_empty_response_remains_success(
        discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-empty"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response({"total_count": 0, "incomplete_results": False, "items": []})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/complete-empty-github.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E2: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert len(calls) == 1 and not target.parent.exists()


@pytest.mark.parametrize("invalid_flag", [None, 1, "false"])
def test_e2_malformed_completeness_metadata_is_not_empty_success(
        invalid_flag, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-invalid"])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k:
                        observation_response({"incomplete_results": invalid_flag, "items": []}))
    target = repository / "data/deliverables/uncreated/invalid-completeness.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 1
    captured = capsys.readouterr()
    assert "expected boolean incomplete_results" in captured.err
    assert "configured=1 attempted=1 completed=0" in captured.err
    assert "E2: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert not target.parent.exists()


import copy
import io
import json


@pytest.fixture
def poller(monkeypatch):
    module = load_writer("poll_surfaces")
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected provider request")
    monkeypatch.setattr(module, "_http_json", forbidden)
    monkeypatch.setattr(module, "_gh_json", forbidden)
    monkeypatch.setattr(module.urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(module, "_now", lambda: dt.datetime(2031, 1, 3, tzinfo=dt.timezone.utc))
    return module


def set_poll_payload(poller, monkeypatch, surface, payload):
    if surface == "E1":
        monkeypatch.setattr(poller.urllib.request, "urlopen",
                            lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    else:
        monkeypatch.setattr(poller, "_gh_json" if surface == "E2" else "_http_json",
                            lambda *a, **k: copy.deepcopy(payload))


def invoke_poll(poller, monkeypatch, tmp_path, surface, *, dry_run=False):
    configuration = tmp_path / "synthetic-poll-config.json"
    configuration.write_text(json.dumps({"E2": {"topics": ["synthetic-topic"]}}), encoding="utf-8")
    argv = ["poll_surfaces.py", "--only", surface, "--config", str(configuration)]
    if dry_run:
        argv.append("--dry-run")
    monkeypatch.setattr(poller.sys, "argv", argv)
    return poller.main()


@pytest.mark.parametrize("surface,key", [("E1", "servers"), ("E2", "items"), ("E3", None), ("E5", "hits")])
@pytest.mark.parametrize("malformation", ["missing", "error", "null", "scalar", "row", "rows_type"])
def test_poll_invalid_envelopes_never_count_as_success(
        surface, key, malformation, poller, companion, tmp_path, monkeypatch, capsys):
    invalid = {"missing": {}, "error": {"error": "synthetic provider failure"},
               "null": None, "scalar": "synthetic", "row": [None], "rows_type": {}}
    payload = invalid[malformation]
    if key is not None and malformation not in {"missing", "error"}:
        payload = {key: payload}
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    output = capsys.readouterr().out
    assert "DEGRADED" in output and "surfaces_ok=0/1" in output
    assert "new=0" in output and f"degraded={surface}" in output
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,payload", [
    ("E1", {"servers": []}), ("E2", {"items": [], "incomplete_results": False}),
    ("E3", []), ("E5", {"hits": []})])
def test_poll_valid_empty_envelope_completes_without_writing(
        surface, payload, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    output = capsys.readouterr().out
    assert "surfaces_ok=1/1" in output and "degraded=none" in output and "new=0" in output
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,key", [("E1", "servers"), ("E2", "items"), ("E5", "hits")])
def test_poll_error_envelope_cannot_be_hidden_by_empty_result_field(
        surface, key, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, {key: [], "error": "synthetic provider error"})
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    assert "surfaces_ok=0/1" in capsys.readouterr().out
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,payload,key", [
    ("E1", {"servers": [
        {"name": "synthetic-visible", "github_stars": 100, "external_url": "https://example.com/e1"},
        {"name": "synthetic-filtered", "github_stars": 1}]}, "E1:synthetic-visible"),
    ("E3", [{"id": "example-org/synthetic-visible", "trendingScore": 5},
             {"id": "example-org/synthetic-filtered", "trendingScore": -1}],
     "E3:example-org/synthetic-visible"),
    ("E5", {"hits": [{"objectID": "synthetic-visible", "title": "Synthetic tool", "points": 50},
                       {"objectID": "synthetic-filtered", "title": "Synthetic minor", "points": 1}]},
     "E5:synthetic-visible"),
])
def test_poll_valid_nonempty_responses_keep_original_filters_and_fields(
        surface, payload, key, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    row = json.loads((companion[0] / "data/surface-inbox.jsonl").read_text(encoding="utf-8"))
    assert row["key"] == key and row["surface"] == surface and row["discovered_at"]
    assert "surfaces_ok=1/1" in capsys.readouterr().out


@pytest.mark.parametrize("topics", [[], [None], [""], "synthetic-topic"])
def test_poll_e2_unconfigured_cannot_claim_a_completed_request(poller, monkeypatch, topics):
    with pytest.raises(ValueError, match="nonempty topic"):
        poller.surface_E2_github_velocity({"E2": {"topics": topics}}, 7)


def github_observation(name):
    return {"full_name": "example-org/" + name, "html_url": "https://example.com/" + name,
            "stargazers_count": 100, "created_at": "2031-01-02T00:00:00Z",
            "description": "Synthetic useful observation."}


@pytest.mark.parametrize("failure", ["request", "shape", "json"])
@pytest.mark.parametrize("failed_first", [False, True])
def test_poll_e2_retains_successes_in_both_topic_orders(
        failure, failed_first, poller, monkeypatch):
    topics = ["synthetic-ready", "synthetic-failed", "synthetic-later"]
    if failed_first:
        topics.insert(0, topics.pop(1))
    calls = []
    def request(path):
        calls.append(path)
        if "synthetic-failed" in path:
            if failure == "shape":
                return {"message": "synthetic provider failure"}
            raise (RuntimeError("synthetic transport failure") if failure == "request" else
                   ValueError("synthetic malformed JSON"))
        name = "synthetic-ready" if "synthetic-ready" in path else "synthetic-later"
        return {"items": [github_observation(name), github_observation("synthetic-shared")],
                "incomplete_results": False}
    monkeypatch.setattr(poller, "_gh_json", request)
    result = poller.surface_E2_github_velocity({"E2": {"topics": topics}}, 7)
    assert result.status == "DEGRADED" and result.completed == 2 and result.attempted == 3
    names = [row["title"] for row in result]
    expected = [topic for topic in topics if topic != "synthetic-failed"]
    assert names == ["example-org/" + expected[0], "example-org/synthetic-shared", "example-org/" + expected[1]]
    assert len(calls) == 3 and len(result.errors) == 1


@pytest.mark.parametrize("flag", [True, None, 1, "false"])
def test_poll_e2_incomplete_or_invalid_completion_cannot_be_all_green(
        flag, poller, companion, tmp_path, monkeypatch, capsys):
    payload = {"incomplete_results": flag, "items": [github_observation("synthetic-partial")]}
    set_poll_payload(poller, monkeypatch, "E2", payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, "E2") == 0
    output = capsys.readouterr().out
    assert "DEGRADED" in output and "surfaces_ok=0/1" in output and "0/1 requests complete" in output
    target = companion[0] / "data/surface-inbox.jsonl"
    if flag is True:
        row = json.loads(target.read_text(encoding="utf-8"))
        assert row["title"] == "example-org/synthetic-partial"
        assert row["raw"]["incomplete_results"] is True
        assert "incomplete_results=true" in output
    else:
        assert not target.exists()


def test_poll_main_retains_partial_topic_rows_without_duplicate_replay(
        poller, companion, tmp_path, monkeypatch, capsys):
    def request(path):
        if "synthetic-failed" in path:
            raise RuntimeError("synthetic transport failure")
        return {"items": [github_observation("synthetic-retained")], "incomplete_results": False}
    monkeypatch.setattr(poller, "_gh_json", request)
    cfg = tmp_path / "synthetic-poll-config.json"
    cfg.write_text(json.dumps({"E2": {"topics": ["synthetic-ready", "synthetic-failed"]}}))
    monkeypatch.setattr(poller.sys, "argv", ["poll_surfaces.py", "--config", str(cfg), "--only", "E2"])
    assert poller.main() == 0
    target = companion[0] / "data/surface-inbox.jsonl"
    first = target.read_bytes()
    assert json.loads(first)["title"] == "example-org/synthetic-retained"
    assert "surfaces_ok=0/1" in capsys.readouterr().out
    assert poller.main() == 0
    assert target.read_bytes() == first
    assert "new=0" in capsys.readouterr().out
'''


def first_use_test_source():
    return r'''"""Generated first-use and input-boundary regressions using synthetic records."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import check_all
import console
import incident_helper as incident
import test_check_all as registration
from test_private_writers import companion

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULES = sorted(path.name for directory in ("tools", "tests")
                      for path in (ROOT / directory).glob("test_*.py"))
INCIDENT = {"slug": "synthetic-tool", "outcome": "dead", "detail": "Synthetic endpoint is gone.",
            "domain": "finance-markets", "d_code": "D-404"}
INVALID_DOMAINS = ["../synthetic-private-note", "/synthetic-private-note",
                   r"C:\synthetic-private-note", "nested/synthetic-note",
                   r"nested\synthetic-note", "unknown-domain", "", None, 0, [], {}]


def config_script(name):
    import importlib.util
    source = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("synthetic_config_" + source.stem, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def populate_config(directory):
    from make_fixtures import configured_doctor_files
    for relative, content in configured_doctor_files().items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


@pytest.mark.parametrize("relative", ["registry.json", ".gitignore", "tools/.gitkeep",
                                       "secrets/README.md", "secrets/.gitkeep"])
@pytest.mark.parametrize("force,linked", [(False, True), (True, True), (True, False)])
def test_initializer_preflights_every_output_before_mutation(tmp_path, monkeypatch, relative, force, linked):
    import sys
    outside = tmp_path / "synthetic-outside"
    retained = b"Synthetic retained bytes\n"
    outside.write_bytes(retained)
    directory = tmp_path / "configuration"
    target = directory / relative
    target.parent.mkdir(parents=True)
    if linked:
        os.link(outside, target)
    else:
        target.write_bytes(retained)
    before = {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
              for path in directory.rglob("*")}
    args = ["init_config.py", "--skill", "synthetic-skill", "--out", str(directory)]
    monkeypatch.setattr(sys, "argv", args + (["--force"] if force else []))
    result = config_script("init_config.py").main()
    assert outside.read_bytes() == retained
    if linked:
        assert result != 0
        after = {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
                 for path in directory.rglob("*")}
        assert after == before, "all output paths must be checked before any output is changed"
    else:
        assert result == 0 and target.read_bytes() != retained
        assert json.loads((directory / "registry.json").read_text()) == {"schema_version": 1, "tools": []}


@pytest.mark.parametrize("mode", ["A", "B"])
def test_config_doctor_honors_declared_storage_mode(tmp_path, monkeypatch, mode):
    import sys
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill", "--out", str(tmp_path)])
    assert config_script("init_config.py").main() == 0
    populate_config(tmp_path)
    if mode == "A":
        (tmp_path / ".gitignore").write_text("# Mode A: private credential backup\n", encoding="utf-8")
        (tmp_path / "secrets/README.md").write_text("Active storage mode: A. Synthetic private fixture.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_config.py", "--skill", "synthetic-skill", "--config-dir", str(tmp_path)])
    assert config_script("verify_config.py").main() == 0


@pytest.mark.parametrize("declaration,ignored,accepted", [
    ("Active storage mode: **A**", False, True),
    ("Active storage mode: C", True, False),
    ("Active storage mode: A\nActive storage mode: B", True, False),
    ("Active storage mode: B", False, False),
    ("Synthetic legacy configuration", True, True),
    ("Synthetic legacy configuration", False, False),
])
def test_config_doctor_applies_explicit_and_legacy_policy(
        tmp_path, monkeypatch, declaration, ignored, accepted):
    import sys
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill", "--out", str(tmp_path)])
    assert config_script("init_config.py").main() == 0
    populate_config(tmp_path)
    (tmp_path / "secrets/README.md").write_text(declaration + "\n", encoding="utf-8")
    if not ignored:
        (tmp_path / ".gitignore").write_text("# Synthetic unexcluded configuration\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_config.py", "--skill", "synthetic-skill", "--config-dir", str(tmp_path)])
    assert (config_script("verify_config.py").main() == 0) is accepted


def document_writer(writer, directory, monkeypatch):
    from test_private_writers import load_writer
    if writer == "incident":
        monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
        return "web-scraping", lambda: incident.apply_shard_edit(
            "web-scraping", "Synthetic old row", "Synthetic new row")
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", directory)
    return "example-source", lambda: feedback.bump_last_verified({"example-source": "2020-01-01"})


def native_junction(target, alias):
    try:
        import _winapi
        create = _winapi.CreateJunction
    except (ImportError, AttributeError):
        pytest.skip("native Windows directory junctions unavailable")
    try:
        create(str(target), str(alias))
    except OSError as exc:
        pytest.skip(f"native Windows directory junctions unavailable: {exc}")


@pytest.mark.parametrize("writer", ["incident", "feedback"])
def test_document_writers_reject_native_junction_before_read(tmp_path, monkeypatch, writer):
    directory = tmp_path / "docs"
    outside = tmp_path / "outside"
    outside.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = outside / (slug + ".md")
    before = b"## Last verified: 2019-01\nSynthetic old row\n"
    target.write_bytes(before)
    native_junction(outside, directory)
    with patch.object(Path, "open", side_effect=AssertionError("aliased document was opened")), \
            patch("builtins.open", side_effect=AssertionError("aliased document was opened")):
        with pytest.raises(ValueError):
            write()
    assert target.read_bytes() == before
    assert sorted(path.name for path in outside.iterdir()) == [target.name]


@pytest.mark.parametrize("position", ["root", "parent"])
def test_initializer_rejects_native_junction_before_mutation(tmp_path, monkeypatch, position):
    import sys
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "synthetic-retained.txt"
    sentinel.write_bytes(b"Synthetic retained bytes\n")
    directory = tmp_path / "configuration"
    alias = directory
    if position == "parent":
        directory.mkdir()
        alias = directory / "secrets"
    native_junction(outside, alias)
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill",
                                     "--out", str(directory), "--force"])
    assert config_script("init_config.py").main() != 0
    assert sorted(path.name for path in outside.iterdir()) == [sentinel.name]
    assert sentinel.read_bytes() == b"Synthetic retained bytes\n"
    if position == "parent":
        assert list(directory.iterdir()) == [alias]


def test_initializer_atomic_replace_failure_preserves_prior_file(tmp_path, monkeypatch):
    import sys
    before = b"Synthetic retained registry\n"
    target = tmp_path / "registry.json"
    target.write_bytes(before)
    def fail_replace(*_args):
        raise OSError("Synthetic replace failure")
    monkeypatch.setattr(os, "replace", fail_replace)
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill",
                                     "--out", str(tmp_path), "--force"])
    assert config_script("init_config.py").main() != 0
    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("writer", ["incident", "feedback"])
@pytest.mark.parametrize("alias", ["regular", "hardlink", "symlink"])
def test_document_writers_reject_aliases_before_reading(tmp_path, monkeypatch, writer, alias):
    before = b"# Synthetic tool\n\n## Last verified: 2019-01\n\nSynthetic old row\n"
    outside = tmp_path / "outside.md"
    outside.write_bytes(before)
    directory = tmp_path / "docs"
    directory.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = directory / (slug + ".md")
    if alias == "hardlink":
        os.link(outside, target)
    elif alias == "symlink":
        try:
            target.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"native symlinks unavailable: {exc}")
    else:
        target.write_bytes(before)
    if alias == "regular":
        write()
        assert target.read_bytes() != before
    else:
        with patch.object(Path, "open", side_effect=AssertionError("aliased document was opened")), \
                patch("builtins.open", side_effect=AssertionError("aliased document was opened")):
            with pytest.raises(ValueError):
                write()
        assert target.read_bytes() == before
    assert outside.read_bytes() == before
    assert sorted(path.name for path in directory.iterdir()) == [target.name]


@pytest.mark.parametrize("writer", ["incident", "feedback"])
@pytest.mark.parametrize("change", ["hardlink", "content", "replacement", "replace-failure"])
def test_document_writers_recheck_before_atomic_replace(tmp_path, monkeypatch, writer, change):
    directory = tmp_path / "docs"
    directory.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = directory / (slug + ".md")
    before = b"## Last verified: 2019-01\nSynthetic old row\n"
    replacement = before if change == "replacement" else b"Synthetic concurrent edit\n"
    target.write_bytes(before)
    outside = tmp_path / "outside.md"
    outside.write_bytes(replacement)
    original_fsync = os.fsync
    reached = []
    def change_after_flush(descriptor):
        original_fsync(descriptor)
        reached.append(True)
        if change == "hardlink":
            target.unlink()
            os.link(outside, target)
        elif change == "replacement":
            candidate = tmp_path / "replacement.md"
            candidate.write_bytes(replacement)
            os.replace(candidate, target)
        elif change == "content":
            target.write_bytes(replacement)
    monkeypatch.setattr(os, "fsync", change_after_flush)
    if change == "replace-failure":
        def fail_replace(*_args):
            raise OSError("Synthetic replacement failure")
        monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises((ValueError, OSError)):
        write()
    assert reached == [True]
    assert outside.read_bytes() == replacement
    assert target.read_bytes() == (before if change == "replace-failure" else replacement)
    assert sorted(path.name for path in directory.iterdir()) == [target.name]


@pytest.mark.parametrize("timestamp", ["2020-01-01", "2099-01-01"])
def test_future_feedback_is_visible_without_bumping(tmp_path, monkeypatch, capsys, timestamp):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    doc = tmp_path / "example-source.md"
    before = "## Last verified: 2019-01\n"
    doc.write_text(before, encoding="utf-8")
    row = dict(feedback_cases()["documentation_verified"][0], ts=timestamp, domain="")
    ledger = tmp_path / "synthetic.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    entries = feedback.load_live_runs(ledger, "2019-01-01")
    assert entries == [row], "future observations must remain visible, not be discarded"
    buckets = feedback.bucket_entries(entries)
    monkeypatch.setattr(feedback, "live_runs_path", lambda: ledger)
    status = feedback.main(["--mode", "bump", "--since", "2019-01-01"])
    if timestamp.startswith("2099"):
        assert buckets["auto_bump_slugs"] == {}
        assert buckets["timestamp_issues"][0]["reason"] == "future_timestamp"
        assert status == 1 and "timestamp" in capsys.readouterr().out.lower()
        assert doc.read_text(encoding="utf-8") == before
        results = feedback.bump_last_verified({"example-source": timestamp})
        assert results[0]["status"] == "review_required"
        assert doc.read_text(encoding="utf-8") == before
    else:
        assert status == 0
        assert "## Last verified: 2020-01" in doc.read_text(encoding="utf-8")


def test_feedback_orders_timestamps_as_instants_and_uses_utc_month(tmp_path, monkeypatch):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    earlier = "2020-03-01T00:30:00+02:00"
    later = "2020-02-29T23:00:00Z"
    row = feedback_cases()["documentation_verified"][0]
    for order in ([earlier, later], [later, earlier]):
        buckets = feedback.bucket_entries([dict(row, ts=stamp) for stamp in order])
        assert buckets["auto_bump_slugs"] == {"example-source": later}
    doc = tmp_path / "example-source.md"
    doc.write_text("## Last verified: 2019-01\n", encoding="utf-8")
    result = feedback.bump_last_verified({"example-source": earlier})
    assert result[0]["new"] == "2020-02"
    assert "## Last verified: 2020-02" in doc.read_text(encoding="utf-8")


@pytest.mark.parametrize("timestamp", ["0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"])
def test_feedback_out_of_range_utc_instants_require_review(tmp_path, monkeypatch, timestamp):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    row = dict(feedback_cases()["documentation_verified"][0], ts=timestamp)
    ledger = tmp_path / "synthetic.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    entries = feedback.load_live_runs(ledger, "2019-01-01")
    assert len(entries) == 1 and entries[0]["outcome"] == "invalid_record"
    buckets = feedback.bucket_entries([row])
    assert buckets["timestamp_issues"][0]["reason"] == "invalid_timestamp"
    assert buckets["auto_bump_slugs"] == {}
    result = feedback.bump_last_verified({"example-source": timestamp})
    assert result[0]["status"] == "review_required"


def test_requests_is_a_direct_runtime_dependency():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert any(re.match(r"requests(?:[<=>!~;\[\s]|$)", line.strip(), re.I)
               for line in requirements if not line.lstrip().startswith("#"))
    development = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert re.search(r"(?m)^\s*-r\s+requirements\.txt\s*$", development)


@pytest.mark.parametrize("selection", ["MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR",
                                       "MARKET_INTEL_DATA_DIR"])
@pytest.mark.parametrize("with_registry", [False, True])
@pytest.mark.parametrize("nested_data", [False, True])
def test_refresh_reads_only_its_selected_companion(
        selection, with_registry, nested_data, companion, tmp_path, monkeypatch):
    selected, _, _, _ = companion
    other = tmp_path / ".market-intel-config"
    other.mkdir()
    other_registry = other / "registry.json"
    other_bytes = b'{"tools":[{"slug":"synthetic-other","installed":true}]}\n'
    other_registry.write_bytes(other_bytes)
    if with_registry:
        (selected / "registry.json").write_text(
            '{"tools":[{"slug":"synthetic-selected","installed":true}]}\n', encoding="utf-8")
    data = selected / "data" if nested_data else selected
    if nested_data:
        data.mkdir(exist_ok=True)
    else:
        (selected / "data").rmdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR", "MARKET_INTEL_DATA_DIR"):
        monkeypatch.delenv(key, raising=False)
    if selection == "MARKET_INTEL_DATA_DIR":
        monkeypatch.setenv("MARKET_INTEL_CONFIG", str(other))
        monkeypatch.setenv(selection, str(data))
    else:
        monkeypatch.setenv(selection, str(selected))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    original_expanduser = os.path.expanduser
    monkeypatch.setattr(os.path, "expanduser",
                        lambda value: str(tmp_path) if value == "~" else original_expanduser(value))
    for probe in ("probe_mcp", "probe_clis", "probe_python_modules"):
        monkeypatch.setattr(console, probe, lambda: {})
    reads = []
    original_read = console.read_json
    def read(path, default=None):
        reads.append(Path(path))
        assert Path(path) == selected / "registry.json"
        return original_read(path, default=default)
    monkeypatch.setattr(console, "read_json", read)
    if not nested_data or selection == "MARKET_INTEL_DATA_DIR":
        # A missing canonical data/ or conflicting config override must fail before collection.
        with pytest.raises(console.private_inventory.InventoryError):
            console.load_snapshot(refresh=True)
        assert reads == []
        assert other_registry.read_bytes() == other_bytes
        return
    snapshot, status = console.load_snapshot(refresh=True)
    collected = snapshot["companion"]
    assert collected["path"] == str(selected)
    assert collected["present"] is with_registry
    assert set(collected["tools"]) == ({"synthetic-selected"} if with_registry else set())
    assert reads == ([selected / "registry.json"] if with_registry else [])
    assert json.loads((data / "inventory/availability-cache.json").read_text(encoding="utf-8")) == snapshot
    assert "PRIVATE companion" in status
    assert other_registry.read_bytes() == other_bytes
    assert not (other / "inventory").exists()


@pytest.mark.parametrize("removed", TEST_MODULES)
def test_registration_detects_each_missing_test_module(removed, monkeypatch, capsys):
    altered = dict(check_all.MANIFEST)
    assert removed in altered
    del altered[removed]
    candidate = SimpleNamespace(MANIFEST=altered, EXCLUDED=dict(check_all.EXCLUDED),
                                checker_path=check_all.checker_path)
    monkeypatch.setattr(registration, "load", lambda: candidate)
    registration.failures.clear()
    try:
        if removed == "test_console.py":
            with pytest.raises(KeyError, match="test_console.py"):
                registration.main()
        else:
            assert registration.main() == 1
        assert "every checker in tools/ is registered in MANIFEST or EXCLUDED" in registration.failures
        assert removed in capsys.readouterr().out
    finally:
        registration.failures.clear()


def test_unified_runner_executes_all_required_test_modules(monkeypatch):
    executed = []
    monkeypatch.setattr(check_all.sys, "argv", ["check_all.py"])
    monkeypatch.setattr(check_all, "run", lambda name, args: executed.append(name) or 0)
    assert check_all.main() == 0
    assert set(TEST_MODULES) <= set(executed)
    assert "test_verification_contract.py" in executed
    assert all(check_all.MANIFEST[name][2] for name in TEST_MODULES)


@pytest.mark.parametrize("domain", INVALID_DOMAINS)
def test_incident_rejects_invalid_model_domain_before_followups(domain, monkeypatch, capsys):
    data = dict(INCIDENT, domain=domain)
    model = SimpleNamespace(data=data)
    with patch.object(incident, "_llmcall", return_value=model) as parse, \
            patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected follow-up")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file read")):
        with pytest.raises(SystemExit) as exc:
            incident.parse_incident("Synthetic incident.")
        assert exc.value.code == 1 and parse.call_count == 1
        assert incident.run(data, apply=True) == 1
        assert parse.call_count == 1
    assert "invalid incident" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["slug", "outcome", "detail", "domain", "d_code"])
@pytest.mark.parametrize("value", [None, 1, [], {}])
def test_incident_rejects_wrong_field_types_before_drafting(field, value, monkeypatch):
    data = dict(INCIDENT)
    data[field] = value
    with patch.object(incident, "_llmcall", side_effect=AssertionError("unexpected model")), \
            patch.object(incident, "_prompt_yn", side_effect=AssertionError("unexpected prompt")), \
            patch.object(incident, "apply_live_runs_append", side_effect=AssertionError("unexpected append")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        assert incident.run(data, apply=True) == 1


@pytest.mark.parametrize("domain", INVALID_DOMAINS)
def test_both_shard_helpers_reject_invalid_domain_before_any_io(domain):
    with patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected model")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        with pytest.raises(ValueError, match="domain"):
            incident.suggest_shard_edit("synthetic-tool", "D-404", domain, "Synthetic evidence.")
        with pytest.raises(ValueError, match="domain"):
            incident.suggest_shard_edit("synthetic-tool", "none", domain, "Synthetic evidence.")
        with pytest.raises(ValueError, match="domain"):
            incident.apply_shard_edit(domain, "Synthetic before", "Synthetic after")


@pytest.mark.parametrize("operation", ["suggest", "apply"])
def test_shard_helpers_reject_canonical_escape(operation, tmp_path, monkeypatch):
    directory = tmp_path / "domains"
    directory.mkdir()
    shard = directory / "finance-markets.md"
    shard.write_text("Synthetic original\n", encoding="utf-8")
    outside = tmp_path / "synthetic-private-note.md"
    original = b"Synthetic outside content\n"
    outside.write_bytes(original)
    monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
    realpath = os.path.realpath
    def canonical(path):
        return str(outside) if os.fspath(path) == str(shard) else realpath(path)
    monkeypatch.setattr(os.path, "realpath", canonical)
    with patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected model")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        with pytest.raises(ValueError, match="outside"):
            if operation == "suggest":
                incident.suggest_shard_edit("synthetic-tool", "D-404", "finance-markets", "Synthetic.")
            else:
                incident.apply_shard_edit("finance-markets", "Synthetic", "Changed")
    assert outside.read_bytes() == original
    assert shard.read_text(encoding="utf-8") == "Synthetic original\n"


def test_valid_incident_preserves_draft_and_explicit_apply(tmp_path, monkeypatch):
    directory = tmp_path / "domains"
    directory.mkdir()
    shard = directory / "finance-markets.md"
    before, after = "| synthetic-tool | usable |", "| synthetic-tool | retired |"
    shard.write_text(before + "\n", encoding="utf-8")
    index = tmp_path / "sources-index.md"
    index.write_text("Synthetic index\n", encoding="utf-8")
    monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
    monkeypatch.setattr(incident, "SOURCES_INDEX", str(index))
    model_inputs = []
    def draft(prompt, stdin_payload=None):
        model_inputs.append((prompt, stdin_payload))
        return f"FROM:\n{before}\nTO:\n{after}\nNOTES:\nSynthetic review." if stdin_payload else "Synthetic commit draft"
    monkeypatch.setattr(incident, "_run_claude", draft)
    appended = []
    monkeypatch.setattr(incident, "apply_live_runs_append", appended.append)
    monkeypatch.setattr(incident, "_prompt_yn", lambda prompt: True)
    assert incident.run(deepcopy(INCIDENT), apply=False) == 0
    assert shard.read_text(encoding="utf-8") == before + "\n"
    assert appended == []
    assert incident.run(deepcopy(INCIDENT), apply=True) == 0
    assert shard.read_text(encoding="utf-8") == after + "\n"
    assert len(appended) == 1 and json.loads(appended[0])["source"] == "shard/" + INCIDENT["slug"]
    assert [body for _, body in model_inputs if body is not None] == [before + "\n", before + "\n"]
'''


def checker_test_source():
    return r'''#!/usr/bin/env python3
"""The one property check_all.py has to keep: no checker is missing from it.

check_all.py only removes the "I ran the wrong one" failure if it actually covers everything. The
moment a ninth checker lands and nobody adds it to MANIFEST, this repo is back to having an orphan,
and the entry point is worse than nothing because it looks like coverage. So the coverage claim is
asserted against the directory listing rather than trusted.

  python tools/test_check_all.py
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Same shape the fleet inventory uses. Kept here rather than imported so a change to check_all.py
# cannot quietly change what this test considers a checker.
CHECKER = re.compile(r"(check|verify|guard|gate|budget|boundary)[a-z_0-9]*\.py$", re.I)
SELF = {"check_all.py"}

failures = []


def check(label, cond, detail=""):
    if cond:
        print("  ok    " + label)
    else:
        print("  FAIL  " + label + ("  <- " + detail if detail else ""))
        failures.append(label)


def load():
    spec = importlib.util.spec_from_file_location("check_all", os.path.join(HERE, "check_all.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ca = load()
    on_disk = {f for f in os.listdir(HERE)
               if f.endswith(".py") and (CHECKER.search(f) or f.startswith("test_"))
               and f not in SELF}
    tests_dir = os.path.join(os.path.dirname(HERE), "tests")
    baseline_tests = {f: os.path.join(tests_dir, f) for f in os.listdir(tests_dir)
                      if f.startswith("test_") and f.endswith(".py")}
    on_disk.update(baseline_tests)
    registered = set(ca.MANIFEST) | set(ca.EXCLUDED)

    # 1. THE DEFECT THIS FILE EXISTS FOR.
    missing = sorted(on_disk - registered)
    check("every checker in tools/ is registered in MANIFEST or EXCLUDED",
          not missing, "unregistered: " + ", ".join(missing))

    # 2. The mirror: a manifest entry with no file is a broken manifest, and check_all returns 2 for
    #    it at runtime. Catch it here instead, where the message is cheaper to read.
    shared = {"pii_guard.py": "guards", "data_boundary.py": "guards", "dash_guard.py": "style"}
    expected = {n: os.path.join(os.path.dirname(HERE), kit, "tools", n) for n, kit in shared.items()}
    expected.update(baseline_tests)
    ghosts = sorted(n for n in ca.MANIFEST if not os.path.isfile(expected.get(n, os.path.join(HERE, n))))
    check("every MANIFEST entry exists on disk", not ghosts, "missing files: " + ", ".join(ghosts))
    for name, path in expected.items():
        check(name + " resolves to its declared suite location", ca.checker_path(name) == path)
    check("offline console regressions are required", ca.MANIFEST["test_console.py"][2])
    check("L0 live probes require explicit network mode", ca.MANIFEST["l0_verify.py"][1])

    # 3. An exclusion without a reason is an orphan with extra steps.
    unreasoned = sorted(n for n, why in ca.EXCLUDED.items() if not (why or "").strip())
    check("every EXCLUDED entry carries a written reason", not unreasoned,
          "no reason: " + ", ".join(unreasoned))

    # 4. `required` is the only thing that can turn a red into a pass, so it must be a deliberate,
    #    explained minority rather than the way entries get added.
    not_required = [n for n, (_a, _n, req, _d) in ca.MANIFEST.items() if not req]
    check("at most one checker is marked not-required", len(not_required) <= 1,
          "not required: " + ", ".join(sorted(not_required)))
    for n in not_required:
        desc = ca.MANIFEST[n][3]
        check("not-required %s explains why in its description" % n,
              len(desc) > 40 and ("pre-existing" in desc or "owned" in desc), desc)

    # 5. NEGATIVE CONTROL. A test that cannot fail proves nothing, so prove this one can: pretend a
    #    new checker appeared and confirm the coverage assertion goes red for it.
    fake = "verify_nothing_at_all.py"
    would_fail = fake not in registered and bool(CHECKER.search(fake))
    check("the coverage assertion would reject an unregistered newcomer", would_fail,
          "a new checker named %r would NOT have been caught" % fake)

    print("")
    if failures:
        print("test_check_all: %d FAILED" % len(failures))
        return 1
    print("test_check_all: all cases passed (%d checker(s) on disk, %d registered)"
          % (len(on_disk), len(registered)))
    return 0


def test_checker_manifest():
    """Run the standalone manifest assertions during ordinary pytest collection."""
    failures.clear()
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
'''


def private_writer_test_source():
    return r'''"""Generated synthetic destination and concurrent-writer regressions; no live calls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import private_inventory as storage
from make_fixtures import (
    fixture, make_runtime_fixture, make_runtime_repository,
    runtime_transport_cases, runtime_visibility_cases,
)

SAMPLE = fixture()["maintenance"]


@dataclass(frozen=True)
class SyntheticProof:
    root: str
    repositories: tuple
    signature: str


@pytest.fixture
def native_companion(tmp_path, monkeypatch):
    generated = make_runtime_fixture(tmp_path)
    for key in list(os.environ):
        if key not in generated["environment"]:
            monkeypatch.delenv(key)
    for key, value in generated["environment"].items():
        monkeypatch.setenv(key, value)
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(generated["repository"] / "data"))
    (generated["repository"] / "data").mkdir(exist_ok=True)
    return generated


@pytest.mark.parametrize("label,remote,configuration,environment,accepted", runtime_transport_cases())
def test_native_private_proof_rejects_unsafe_transport(
        native_companion, monkeypatch, label, remote, configuration, environment, accepted):
    repository = native_companion["repository"]
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin", remote], check=True)
    for key, value in configuration.items():
        subprocess.run(["git", "-C", str(repository), "config", key, value], check=True)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    original_run = subprocess.run
    forbidden = []

    def local_only(command, *args, **kwargs):
        if command[0] == "git":
            return original_run(command, *args, **kwargs)
        forbidden.append(command[0])
        if command[0] == "gh":
            return subprocess.CompletedProcess(command, 0, json.dumps(
                {"nameWithOwner": SAMPLE["companion_identity"], "visibility": "PRIVATE"}), "")
        if command[0] == "ssh":
            return subprocess.CompletedProcess(command, 0, "hostname github.com\n", "")
        pytest.fail("a transport command was executed")

    monkeypatch.setattr(subprocess, "run", local_only)
    if accepted:
        destination = storage.resolve_destination()
        assert destination.repository == repository
    else:
        with pytest.raises(storage.InventoryError):
            storage.resolve_destination()
    assert forbidden == [], "fresh synthetic receipts require only local Git metadata reads"
    assert not (repository / "data/inventory").exists()


@pytest.mark.parametrize("identity,accepted", [
    (SAMPLE["other_identity"], True), (SAMPLE["public_identity"], False),
    ("example/unknown", False),
])
def test_native_nested_repository_is_authoritative(native_companion, identity, accepted):
    repository = native_companion["repository"]
    assert storage.resolve_directory(path=repository).repository == repository
    nested = make_runtime_repository(repository / "runtime", native_companion["environment"], identity)
    if accepted:
        selected = storage.resolve_directory(path=nested)
        assert selected.repository == nested and selected.identity == identity
    else:
        with pytest.raises(storage.InventoryError):
            storage.resolve_directory(path=nested)
    assert not (nested / "inventory").exists()


@pytest.mark.parametrize("failure", ["ignored", "unversioned"])
def test_native_storage_requirements_are_preserved(native_companion, failure):
    repository = native_companion["repository"]
    target = repository / "ignored-output/record.json" if failure == "ignored" else repository / "data/deliverables/report.json"
    if failure == "unversioned":
        subprocess.run(["git", "-C", str(repository), "update-ref", "-d", "HEAD"], check=True)
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination(path=target)
    assert not target.exists()


@pytest.mark.parametrize("change", ["stable", "public", "other-private", "same-identity-url", "lexical-target"])
def test_native_publication_rechecked_before_replace(native_companion, monkeypatch, change):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/synthetic.json"
    target.parent.mkdir(parents=True)
    before, after = "Synthetic retained bytes\n", "Synthetic replacement bytes\n"
    target.write_text(before, encoding="utf-8")
    lexical = repository / "data/deliverables/reports/selected.json"
    selected_path = [target]
    if change == "lexical-target":
        original_resolve = Path.resolve
        monkeypatch.setattr(Path, "resolve", lambda path, *a, **k:
                            selected_path[0] if path == lexical else original_resolve(path, *a, **k))
    selected = storage.resolve_destination(path=lexical if change == "lexical-target" else target)
    real_fsync = os.fsync
    def change_after_flush(descriptor):
        real_fsync(descriptor)
        identity = {"public": SAMPLE["public_identity"], "other-private": SAMPLE["other_identity"],
                    "same-identity-url": SAMPLE["companion_identity"]}.get(change)
        if identity:
            suffix = "" if change == "same-identity-url" else ".git"
            subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin",
                            "https://github.com/" + identity + suffix], check=True)
        elif change == "lexical-target":
            selected_path[0] = repository / "data/deliverables/reports/other.json"
    monkeypatch.setattr(os, "fsync", change_after_flush)
    if change == "stable":
        storage.write_text(after, "reports/synthetic.json", selected)
        assert target.read_text(encoding="utf-8") == after
    else:
        with pytest.raises(storage.InventoryError):
            storage.write_text(after, "reports/synthetic.json", selected)
        assert target.read_text(encoding="utf-8") == before
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == (0 if change == "stable" else 1)
    if pending:
        assert pending[0].read_text(encoding="utf-8") == after
    assert not (target.parent / "other.json").exists()


def test_native_same_identity_route_change_is_revalidated(native_companion):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/result.json"
    selected = storage.resolve_destination(path=target)
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin",
                    "https://github.com/" + SAMPLE["companion_identity"]], check=True)
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_text("{}\n", "reports/result.json", selected)
    assert not target.parent.exists()


def test_native_explicit_target_retains_lexical_selection(native_companion, monkeypatch):
    repository = native_companion["repository"]
    lexical = repository / "data/deliverables/selected.json"
    selected_target = [repository / "data/deliverables/first.json"]
    original_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        return selected_target[0] if path == lexical else original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    selected = storage.resolve_destination(path=lexical)
    assert selected.requested_path == lexical and selected.path == selected_target[0]
    selected_target[0] = repository / "data/deliverables/second.json"
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_text("{}\n", "reports/result.json", selected)
    assert not (repository / "data/deliverables/first.json").exists()
    assert not (repository / "data/deliverables/second.json").exists()


def test_native_effective_git_rewrite_cannot_hide_physical_public_route(native_companion, monkeypatch):
    repository = native_companion["repository"]
    public = "https://github.com/" + SAMPLE["public_identity"] + ".git"
    private = "https://github.com/" + SAMPLE["companion_identity"] + ".git"
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin", public], check=True)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url." + private + ".insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", public)
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()
    assert not (repository / "data/inventory").exists()


@pytest.mark.parametrize("label,payload", runtime_visibility_cases())
def test_native_invalid_visibility_receipt_refuses_before_writes(native_companion, label, payload):
    native_companion["receipt"].write_text(payload, encoding="utf-8")
    with pytest.raises(storage.InventoryError, match="visibility"):
        storage.resolve_destination()
    assert not (native_companion["repository"] / "inventory").exists()


@pytest.fixture
def companion(tmp_path, monkeypatch):
    repository = tmp_path / "companion"
    (repository / ".git").mkdir(parents=True)
    (repository / "data").mkdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(repository / "data"))
    routes = {"origin": {"fetch": [SAMPLE["companion_identity"]],
                          "push": [SAMPLE["companion_identity"]]}}
    visibility = {SAMPLE["companion_identity"]: "PRIVATE", SAMPLE["other_identity"]: "PRIVATE",
                  SAMPLE["public_identity"]: "PUBLIC"}
    configuration = []

    class ProofError(RuntimeError):
        pass

    def prove(directory):
        if not Path(directory).is_relative_to(repository):
            raise ProofError("synthetic unmanaged directory")
        if any(line.split(None, 1)[1] not in routes for line in configuration):
            raise ProofError("synthetic missing publication remote")
        identities = sorted({identity for route in routes.values()
                             for values in route.values() for identity in values})
        if any(visibility.get(identity) != "PRIVATE" for identity in identities):
            raise ProofError("synthetic PUBLIC or UNKNOWN visibility")
        return SyntheticProof(str(repository), tuple(identities), json.dumps([routes, configuration], sort_keys=True))

    def read(proof, *arguments):
        if arguments == ("rev-parse", "--verify", "HEAD"):
            return subprocess.CompletedProcess(arguments, 0, "1" * 40, "")
        if arguments[:4] == ("check-ignore", "--no-index", "-q", "--"):
            return subprocess.CompletedProcess(arguments, 1, "", "")
        raise AssertionError(arguments)

    boundary = SimpleNamespace(prove_private_companion=prove, read_private_companion_git=read, GitError=ProofError)
    monkeypatch.setattr(storage, "_shared_boundary", lambda: boundary)
    contract_boundary = SimpleNamespace(prove_private_companion=lambda directory, *_: prove(directory),
                                        read_private_companion_git=read, GitError=ProofError)
    monkeypatch.setattr(storage._storage_contract(), "load_boundary", lambda: contract_boundary)
    return repository, routes, visibility, configuration


@pytest.mark.parametrize("visibility", ["PUBLIC", "UNKNOWN"])
def test_every_effective_push_destination_must_be_private(companion, visibility):
    repository, routes, states, _ = companion
    routes["origin"]["push"].append(SAMPLE["public_identity"])
    states[SAMPLE["public_identity"]] = visibility
    with pytest.raises(storage.InventoryError, match="visibility"):
        storage.resolve_destination()
    assert set(repository.iterdir()) == {repository / ".git", repository / "data"}


def test_all_remotes_and_configured_push_remotes_are_verified(companion):
    _, routes, _, configuration = companion
    routes["publish"] = {"fetch": [SAMPLE["other_identity"]], "push": [SAMPLE["public_identity"]]}
    configuration.append("remote.pushdefault publish")
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()
    routes["publish"]["push"] = [SAMPLE["other_identity"]]
    destination = storage.resolve_destination()
    assert set(destination.identity.split(", ")) == {SAMPLE["companion_identity"], SAMPLE["other_identity"]}
    configuration[:] = ["branch.main.pushremote absent-remote"]
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()


def test_publication_route_change_is_rechecked_before_write(companion):
    repository, routes, _, _ = companion
    selected = storage.resolve_destination()
    routes["origin"]["push"] = [SAMPLE["other_identity"]]
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_snapshot(fixture()["inventory"], selected)
    assert not (repository / "data/inventory").exists()


def test_explicit_destinations_use_final_private_repository(companion, tmp_path):
    repository, _, _, _ = companion
    selected = storage.resolve_destination("reports/feedback.json", path=repository / "data/deliverables/reports/result.json")
    storage.write_text("synthetic\n", "reports/feedback.json", selected)
    assert selected.path.read_text() == "synthetic\n"
    for target in (storage.ROOT / "inventory/research.json", tmp_path / "unmanaged/result.json"):
        with pytest.raises(storage.InventoryError):
            storage.resolve_destination("reports/feedback.json", path=target)


def test_serialized_updates_preserve_both_generated_rows(companion):
    repository, _, _, _ = companion
    selected = storage.resolve_destination("metrics/live-runs.jsonl")
    start = threading.Barrier(2)
    rows = SAMPLE["ledger"][:2]
    def append(row):
        start.wait(timeout=5)
        storage.update_text(lambda body: body + json.dumps(row) + "\n",
                            "metrics/live-runs.jsonl", selected)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(append, rows))
    observed = [json.loads(line) for line in selected.path.read_text().splitlines()]
    assert sorted(row["outcome"] for row in observed) == sorted(row["outcome"] for row in rows)
    assert list(selected.path.parent.iterdir()) == [selected.path]
    before = selected.path.read_bytes()
    with patch.object(storage.os, "replace", side_effect=PermissionError("synthetic denial")):
        with pytest.raises(storage.InventoryError):
            storage.update_text(lambda body: body + json.dumps(SAMPLE["ledger"][2]) + "\n",
                                "metrics/live-runs.jsonl", selected)
    assert selected.path.read_bytes() == before
    pending, = (repository / ".staging").glob("inventory-*.tmp")
    assert pending.read_text() == before.decode() + json.dumps(SAMPLE["ledger"][2]) + "\n"
    assert set(selected.path.parent.iterdir()) == {selected.path}


def load_writer(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke(writer, args):
    with patch.object(sys, "argv", [writer.__file__, *args]):
        return writer.main()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces", "feedback-bump"])
def test_writers_refuse_unproven_output_before_observation(name, tmp_path, monkeypatch):
    writer = load_writer(name)
    target = tmp_path / "unmanaged/result.json"
    def unproven(*args, **kwargs):
        raise storage.InventoryError("synthetic unproven destination")
    monkeypatch.setattr(storage, "resolve_destination", unproven)
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: pytest.fail("observation preceded validation")})
        args = ["--out", str(target)]
    elif name == "poll_surfaces":
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: pytest.fail("observation preceded validation")})
        args = ["--inbox", str(target)]
    else:
        monkeypatch.setattr(writer, "live_runs_path", lambda: pytest.fail("ledger read preceded output validation"))
        args = ["--out", str(target)]
    assert invoke(writer, args) == 2
    assert not target.parent.exists()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces", "feedback-bump"])
def test_writers_persist_only_to_verified_private_override(name, companion, monkeypatch):
    repository, _, _, _ = companion
    writer = load_writer(name)
    target = repository / "data/deliverables/reports/result.json"
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: [deepcopy(SAMPLE["discovery"])]})
        args = ["--out", str(target)]
    elif name == "poll_surfaces":
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: [deepcopy(SAMPLE["surface"])]})
        args = ["--inbox", str(target)]
    else:
        ledger = repository / "data/metrics/live-runs.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(json.dumps(SAMPLE["ledger"][0]) + "\n", encoding="utf-8")
        monkeypatch.setattr(writer, "live_runs_path", lambda: ledger)
        args = ["--out", str(target), "--since", "2030-01-01"]
    assert invoke(writer, args) in (0, 1)
    assert target.is_file()
    assert target.read_text(encoding="utf-8").strip()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces"])
def test_polling_dry_run_does_not_create_output_directories(name, companion, monkeypatch):
    repository, _, _, _ = companion
    writer = load_writer(name)
    target = repository / "data/deliverables/uncreated/result.json"
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: [deepcopy(SAMPLE["discovery"])]})
        args = ["--out", str(target), "--dry-run"]
    else:
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: [deepcopy(SAMPLE["surface"])]})
        args = ["--inbox", str(target), "--dry-run"]
    assert invoke(writer, args) == 0
    assert not target.parent.exists()


def test_feedback_preserves_all_generated_outcomes():
    module = load_writer("feedback-bump")
    rows = fixture()["maintenance"]["ledger"]
    result = module.bucket_entries(rows)
    assert set(result["by_outcome"]) == {row["outcome"] for row in rows}
    assert {row["outcome"] for row in result["open_questions"] if "outcome" in row} == {
        "coverage_gap", "fallback_used", "unverifiable", "transport_error",
        "auth_failed", "quota_exceeded", "content_invalid"}


def test_writer_reader_and_generated_schema_share_the_published_vocabulary():
    import incident_helper
    import ledger_schema
    from live_run_contract import VALID_OUTCOMES
    assert set(ledger_schema.OUTCOMES) == VALID_OUTCOMES
    assert set(ledger_schema.schema()["properties"]["outcome"]["enum"]) == VALID_OUTCOMES
    for row in fixture()["maintenance"]["ledger"]:
        incident_helper._validate_incident({"slug": "synthetic-tool", "outcome": row["outcome"],
                                           "detail": row["detail"], "domain": "finance-markets",
                                           "d_code": "none"})
'''


def incident_boundary_test_source():
    return r'''"""Incident DATA and model boundaries; all records come from synthetic fixtures."""
import json
from unittest.mock import patch

import pytest
import incident_helper
import model_adapter
import private_inventory
from make_fixtures import fixture
from test_private_writers import companion


def test_missing_model_adapter_reports_setup_without_provider_details(monkeypatch, capsys):
    def missing(_name):
        raise ImportError("synthetic credential")
    monkeypatch.setattr(model_adapter.importlib, "import_module", missing)
    with pytest.raises(model_adapter.ModelUnavailable, match="CONFIG.md#model-adapter") as exc:
        model_adapter.call("synthetic prompt")
    assert "synthetic credential" not in str(exc.value)
    assert model_adapter.main(["--check"]) == 3
    assert "UNINITIALIZED" in capsys.readouterr().err


def test_model_adapter_forwards_only_the_callers_options(monkeypatch):
    from types import SimpleNamespace
    calls = []
    reply = object()
    def configured(prompt, **options):
        calls.append((prompt, options))
        return reply
    monkeypatch.setattr(model_adapter.importlib, "import_module",
                        lambda _name: SimpleNamespace(call=configured))
    assert model_adapter.call("synthetic prompt", schema={"type": "object"}) is reply
    assert calls == [("synthetic prompt", {"schema": {"type": "object"}})]


def test_noncallable_model_interface_is_uninitialized(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(model_adapter.importlib, "import_module",
                        lambda _name: SimpleNamespace(call=None))
    with pytest.raises(model_adapter.ModelUnavailable):
        model_adapter.require_call()


def test_missing_adapter_stops_changelog_before_source_reads(monkeypatch, capsys):
    import changelog_draft
    def missing():
        raise model_adapter.ModelUnavailable()
    monkeypatch.setattr(changelog_draft, "require_call", missing)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: pytest.fail("must not read the changelog"))
    assert changelog_draft.main(["--since", "HEAD~1"]) == 3
    assert "UNINITIALIZED" in capsys.readouterr().err


def test_missing_adapter_never_becomes_an_incident_fallback(monkeypatch):
    def missing(*args, **kwargs):
        raise model_adapter.ModelUnavailable()
    monkeypatch.setattr(incident_helper, "_llmcall", missing)
    with pytest.raises(model_adapter.ModelUnavailable):
        incident_helper.suggest_commit_message("synthetic-tool", "none", "finance-markets", "Synthetic incident.")


def test_changelog_refuses_unproven_output_before_reading_input(monkeypatch, tmp_path, capsys):
    import changelog_draft
    monkeypatch.setattr(changelog_draft, "require_call", lambda: None)
    def refuse(*args, **kwargs):
        raise private_inventory.InventoryError("synthetic unproven destination")
    monkeypatch.setattr(private_inventory, "resolve_destination", refuse)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: pytest.fail("must validate output before reading the changelog"))
    target = tmp_path / "draft.md"
    assert changelog_draft.main(["--since", "HEAD~1", "--out", str(target)]) == 2
    assert not target.exists()
    assert "destination" in capsys.readouterr().err


@pytest.mark.parametrize("write_fails", [False, True])
def test_changelog_uses_verified_atomic_output(companion, monkeypatch, write_fails):
    import changelog_draft
    repository, _, _, _ = companion
    sample = fixture()["maintenance"]
    text = sample["discovery"]["one_line_pitch"]
    target = repository / "data/deliverables/reports" / "draft.md"
    target.parent.mkdir(parents=True)
    target.write_text(text, encoding="utf-8")
    monkeypatch.setattr(changelog_draft, "require_call", lambda: None)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: sample["release"]["version"])
    monkeypatch.setattr(changelog_draft, "parse_plugin_version",
                        lambda: sample["release"]["version"])
    monkeypatch.setattr(changelog_draft, "extract_top_entry_text", lambda: text)
    monkeypatch.setattr(changelog_draft, "collect_git_data",
                        lambda _since: {"log": sample["release"]["commit"], "stat": "", "name_status": ""})
    monkeypatch.setattr(changelog_draft, "run_claude", lambda _prompt: (0, text, ""))
    if write_fails:
        def refuse(*args):
            raise PermissionError("synthetic write denial")
        monkeypatch.setattr(private_inventory.os, "replace", refuse)
    assert changelog_draft.main(["--since", "HEAD~1", "--out", str(target)]) == (2 if write_fails else 0)
    expected = text if write_fails else text + "\n" + changelog_draft.FOOTER
    assert target.read_text(encoding="utf-8") == expected
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == (1 if write_fails else 0)
    if pending:
        assert pending[0].read_text(encoding="utf-8") == text + "\n" + changelog_draft.FOOTER
    assert set(target.parent.iterdir()) == {target}


def test_incident_requires_private_destination_before_any_write(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(tmp_path))
    with patch.object(private_inventory, "_shared_boundary", side_effect=private_inventory.InventoryError("synthetic unversioned directory")):
        with pytest.raises(private_inventory.InventoryError):
            incident_helper.apply_live_runs_append(json.dumps(fixture()["inventory"]))
    assert not (tmp_path / "metrics").exists()


def test_incident_uses_canonical_destination_and_atomic_write(companion, monkeypatch):
    repository = companion[0]
    target = repository / "data/metrics/live-runs.jsonl"
    target.parent.mkdir(parents=True)
    old = json.dumps(fixture()["inventory"]) + "\n"
    target.write_text(old, encoding="utf-8")
    with patch.object(private_inventory.os, "replace", side_effect=PermissionError("synthetic credential must never appear")):
        with pytest.raises(private_inventory.InventoryError, match="persistence failed"):
            incident_helper.apply_live_runs_append(json.dumps(fixture()["evidence"]))
    assert target.read_text(encoding="utf-8") == old
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == 1
    assert pending[0].read_text(encoding="utf-8") == old + json.dumps(fixture()["evidence"]) + "\n"
    assert set(target.parent.iterdir()) == {target}


def test_incident_model_bridge_inherits_defaults_and_hides_provider_errors(capsys):
    class Reply:
        error = "synthetic credential must never appear"
        text = "synthetic private reply must never appear"
        def __bool__(self):
            return False
    with patch.object(incident_helper, "_llmcall", return_value=Reply()) as model:
        with pytest.raises(RuntimeError):
            incident_helper._run_claude("synthetic prompt")
        assert model.call_args.kwargs == {}
        with pytest.raises(SystemExit):
            incident_helper.parse_incident("synthetic prompt")
        assert "timeout" not in model.call_args.kwargs
    output = capsys.readouterr()
    assert "synthetic credential" not in output.err
    assert "synthetic private reply" not in output.err


def test_model_exception_is_reported_without_provider_credentials(capsys):
    with patch.object(incident_helper, "_llmcall", side_effect=RuntimeError("synthetic credential")):
        with pytest.raises(RuntimeError, match="inspect private provider diagnostics") as exc:
            incident_helper._run_claude("synthetic prompt")
        assert "synthetic credential" not in str(exc.value)
        with pytest.raises(SystemExit):
            incident_helper.parse_incident("synthetic prompt")
    assert "synthetic credential" not in capsys.readouterr().err


def test_draft_model_call_has_no_provider_preflight_or_default_overrides():
    import changelog_draft
    class Reply:
        text = "Synthetic draft"
        def __bool__(self):
            return True
    with patch.object(changelog_draft, "_llmcall", return_value=Reply()) as model:
        assert changelog_draft.run_claude("synthetic prompt") == (0, "Synthetic draft", "")
        model.assert_called_once_with("synthetic prompt")
    with patch.object(changelog_draft, "_llmcall", side_effect=RuntimeError("synthetic credential")):
        code, text, error = changelog_draft.run_claude("synthetic prompt")
    assert code != 0 and text == ""
    assert "synthetic credential" not in error


def test_private_proof_module_must_exist_before_any_metadata_commands(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(private_inventory, "ROOT", tmp_path / "consumer")
    private_inventory._shared_boundary.cache_clear()
    try:
        with patch.object(subprocess, "run", side_effect=AssertionError("no metadata command before module validation")):
            with pytest.raises(private_inventory.InventoryError, match="initialize the guards"):
                private_inventory._shared_boundary()
    finally:
        private_inventory._shared_boundary.cache_clear()
'''


def console_test_source():
    return r'''#!/usr/bin/env python3
"""Offline console regressions. Dependencies are doubled in process; run inside independent pre-import containment."""
from __future__ import annotations

from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURE = json.loads((ROOT / "tests/fixtures/console.json").read_text(encoding="utf-8"))


class ConsoleTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(subprocess, "Popen", side_effect=AssertionError("unexpected process")))
        self.stack.enter_context(patch.object(socket, "socket", side_effect=AssertionError("unexpected network")))
        sandbox = {key: os.environ[key] for key in ("TMP", "TEMP", "TMPDIR", "HOME", "USERPROFILE")
                   if key in os.environ}
        self.stack.enter_context(patch.dict(os.environ, sandbox, clear=True))
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        sys.path.insert(0, str(HERE))
        self.addCleanup(sys.path.remove, str(HERE))
        spec = importlib.util.spec_from_file_location("console_under_test", HERE / "console.py")
        self.console = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.console)
        self.console.AVAIL_CACHE = str(self.tmp / "legacy-cache.json")
        self.console.GH_CACHE = str(self.tmp / "no-catalog-health.json")
        self.stack.enter_context(patch.object(self.console, "probe_mcp", side_effect=AssertionError("unexpected MCP probe")))
        self.stack.enter_context(patch.object(self.console, "probe_clis", side_effect=AssertionError("unexpected CLI probe")))
        self.stack.enter_context(patch.object(self.console, "probe_python_modules", side_effect=AssertionError("unexpected library probe")))
        self.stack.enter_context(patch.object(self.console, "probe_companion", side_effect=AssertionError("unexpected companion probe")))

    def invoke(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = self.console.main(argv)
        return code, out.getvalue(), err.getvalue()

    def refresh_commands(self, slug=None):
        slug = slug or FIXTURE["tool"]["slug"]
        return (["--refresh"], ["--refresh", "status"], ["status", "--refresh"],
                ["--refresh", "tool", slug], ["tool", "--refresh", slug], ["tool", slug, "--refresh"],
                ["--refresh", "connect", slug], ["connect", "--refresh", slug], ["connect", slug, "--refresh"])

    def test_catalog_reads_do_not_probe_or_write(self):
        for args in (["status", "--domain", "finance-markets"], ["tool", "github-mcp"], ["connect", "github-mcp"]):
            with self.subTest(args=args):
                with patch.object(self.console.private_inventory, "resolve_destination",
                                  side_effect=AssertionError("cold commands must not validate inventory")):
                    code, out, _ = self.invoke(args)
                self.assertEqual(code, 0)
                self.assertTrue(out.strip())
                self.assertNotIn("fresh inventory", out)
                self.assertNotIn("PRIVATE companion", out)
                self.assertFalse(Path(self.console.AVAIL_CACHE).exists())

    def test_inventory_presence_never_proves_operation(self):
        tool = {"slug": "github-mcp", "name": "GitHub MCP", "kind": "repo", "domain": "frontier-research"}
        state = self.console.compute_states(tool, deepcopy(FIXTURE["inventory"]), {})
        self.assertEqual(state["available_now"], self.console.NO)

    def test_catalog_reads_neither_legacy_nor_private_repo_health_cache(self):
        original = self.console.read_json
        def catalog_only(path, default=None):
            self.assertEqual(path, self.console.REGISTRY)
            return original(path, default)
        with patch.object(self.console, "read_json", side_effect=catalog_only):
            code, out, _ = self.invoke(["tool", "github-mcp"])
        self.assertEqual(code, 0)
        self.assertIn("not inspected by the catalog console", out)

    def test_uninitialized_refresh_refuses_before_collecting_inventory(self):
        os.environ["MARKET_INTEL_CONFIG"] = str(self.tmp / "missing")
        with patch.object(self.console, "build_snapshot", side_effect=AssertionError("inventory must follow destination validation")):
            code, _, err = self.invoke(["status", "--refresh"])
        self.assertNotEqual(code, 0)
        self.assertIn("inventory", err.lower())
        self.assertFalse((self.tmp / "missing").exists())

    def evidence(self):
        payload = deepcopy(FIXTURE["evidence"])
        return {"host": payload["host"], "session_id": payload["session_id"], "payload": payload}

    def classify(self, context=None, **kwargs):
        context = self.evidence() if context is None else context
        instant = datetime.fromisoformat(FIXTURE["evidence"]["capabilities"][0]["observed_at"])
        return self.console.host_capabilities.classify(context, "github-mcp", "search", now=instant, **kwargs)

    def test_current_selected_operation_with_all_proofs_is_available(self):
        state = self.classify()
        self.assertEqual(state["status"], "available-now")
        self.assertEqual((state["access"], state["operation"]), ("exposed", "ready"))
        for key in ("reason", "host", "session_id", "source_id", "capability_id", "observed_at", "observation_method"):
            self.assertTrue(state[key].strip())

    def test_foreign_host_or_session_is_setup_in_both_directions(self):
        for active, other in (("codex", "claude"), ("claude", "codex")):
            for key, wrong in (("host", other), ("session_id", "different-session")):
                with self.subTest(active=active, key=key):
                    context = self.evidence()
                    context["host"] = context["payload"]["host"] = active
                    context["payload"][key] = wrong
                    self.assertEqual(self.classify(context)["status"], "setup")

    def test_unattributed_malformed_and_schema_drift_fail_closed(self):
        cases = [None, [], {}, {"schema_version": 2}, {"schema_version": True}]
        for payload in cases:
            with self.subTest(payload=payload):
                context = self.evidence()
                context["payload"] = payload
                self.assertEqual(self.classify(context)["status"], "setup")
        for field, value in (("observed_at", "not-a-time"), ("observed_at", "2031-01-02T03:04:05"),
                             ("host", "foreign-host"), ("session_id", "foreign-session")):
            with self.subTest(field=field, value=value):
                context = self.evidence()
                context["payload"]["capabilities"][0][field] = value
                self.assertEqual(self.classify(context)["status"], "setup")

    def test_source_and_capability_are_exact_not_fuzzy(self):
        for field, value in (("source_id", "github-mcp-other"), ("capability_id", "read")):
            context = self.evidence()
            context["payload"]["capabilities"][0][field] = value
            state = self.classify(context)
            self.assertEqual(state["status"], "setup")
            self.assertEqual(state["source_id"], FIXTURE["tool"]["source_id"])
            self.assertEqual(state["capability_id"], FIXTURE["tool"]["capability_id"])
            self.assertEqual((state["access"], state["operation"]), ("unproven", "unproven"))
            self.assertNotIn("observed_at", state)

    def test_missing_evidence_preserves_requested_identity_without_observed_proof(self):
        empty = self.evidence()
        empty["payload"]["capabilities"] = []
        instant = datetime.fromisoformat(FIXTURE["evidence"]["provenance"]["observed_at"])
        tool = FIXTURE["tool"]
        for context in (None, {"error": "supply current-session capability evidence"}, empty):
            with self.subTest(context=context):
                state = self.console.host_capabilities.classify(
                    context, tool["source_id"], tool["capability_id"], now=instant)
                self.assertEqual(state["status"], "setup")
                self.assertEqual(state["source_id"], tool["source_id"])
                self.assertEqual(state["capability_id"], tool["capability_id"])
                self.assertEqual((state["access"], state["operation"]), ("unproven", "unproven"))
                self.assertTrue(state["reason"].strip())
                for field in ("host", "session_id", "observed_at", "observation_method"):
                    self.assertNotIn(field, state)

    def test_freshness_limits_are_inclusive(self):
        for age, expected in ((900, "available-now"), (900.001, "setup"), (-60, "available-now"), (-60.001, "setup")):
            with self.subTest(age=age):
                context = self.evidence()
                row = context["payload"]["capabilities"][0]
                row["observed_at"] = (datetime.fromisoformat(row["observed_at"]) - timedelta(seconds=age)).isoformat()
                self.assertEqual(self.classify(context)["status"], expected)

    def test_latest_auth_failure_and_simultaneous_failure_defeat_success(self):
        for seconds in (0, 1):
            for reverse in (False, True):
                with self.subTest(seconds=seconds, reverse=reverse):
                    context = self.evidence()
                    rows = context["payload"]["capabilities"]
                    failure = deepcopy(rows[0])
                    failure["authentication"] = "failed"
                    failure["observed_at"] = (datetime.fromisoformat(failure["observed_at"]) + timedelta(seconds=seconds)).isoformat()
                    rows.append(failure)
                    if reverse:
                        rows.reverse()
                    state = self.classify(context)
                    self.assertEqual(state["status"], "setup")
                    self.assertIn("authentication failed", state["reason"])

    def test_exposure_auth_execution_and_content_each_require_proof(self):
        for field, value in (("exposed", False), ("exposed", "true"), ("execution", "failed"),
                             ("authentication", "unknown"), ("response_valid", "http-200"), ("response_valid", "login-page"),
                             ("supported", "true"), ("supported", None)):
            with self.subTest(field=field, value=value):
                context = self.evidence()
                context["payload"]["capabilities"][0][field] = value
                state = self.classify(context)
                self.assertEqual(state["status"], "setup")
                self.assertTrue(state["reason"].strip())

    def test_hard_gap_requires_explicit_attributed_unsupported_evidence(self):
        context = self.evidence()
        row = context["payload"]["capabilities"][0]
        row["supported"] = False
        self.assertEqual(self.classify(context)["status"], "hard-gap")
        row["supported"] = "false"
        self.assertEqual(self.classify(context)["status"], "setup")

    def test_newer_recovery_can_replace_older_auth_failure(self):
        context = self.evidence()
        older = deepcopy(context["payload"]["capabilities"][0])
        older["authentication"] = "failed"
        older["observed_at"] = (datetime.fromisoformat(older["observed_at"]) - timedelta(seconds=1)).isoformat()
        context["payload"]["capabilities"].append(older)
        self.assertEqual(self.classify(context)["status"], "available-now")

    def test_tool_report_binds_evidence_and_separates_access_from_operation(self):
        payload = deepcopy(FIXTURE["evidence"])
        payload["capabilities"][0]["observed_at"] = datetime.now(timezone.utc).isoformat()
        payload["provenance"]["observed_at"] = payload["capabilities"][0]["observed_at"]
        path = self.tmp / "capabilities with spaces.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        os.environ.update(MARKET_INTEL_HOST=payload["host"], MARKET_INTEL_SESSION_ID=payload["session_id"],
                          MARKET_INTEL_CAPABILITIES=str(path))
        with patch.object(self.console, "load_registry", return_value={"tools": [FIXTURE["tool"]]}):
            code, out, _ = self.invoke(["tool", "synthetic-display", "--capability", "search"])
        self.assertEqual(code, 0)
        for line in ("status: available-now", "access: exposed", "operation: ready", "host: codex",
                     "session_id: fixture-session", "source_id: github-mcp", "capability_id: search",
                     "observed_at:", "observation_method: current-session-adapter"):
            self.assertIn(line, out)
        self.assertRegex(out, r"reason: [^\s][^\n]+")

    def test_malformed_evidence_keeps_catalog_journey_useful(self):
        path = self.tmp / "invalid.json"
        path.write_text("not json", encoding="utf-8")
        os.environ["MARKET_INTEL_CAPABILITIES"] = str(path)
        code, out, _ = self.invoke(["tool", "github-mcp"])
        self.assertEqual(code, 0)
        self.assertIn("status: setup", out)
        self.assertIn("reason:", out)

    def test_selected_cli_results_bind_requested_identity_with_or_without_evidence(self):
        for entrypoint in ("tool", "connect"):
            for slug in (FIXTURE["tool"]["slug"], FIXTURE["tool"]["source_id"]):
                tool = dict(FIXTURE["tool"], slug=slug)
                for override in (False, True):
                    capability = tool["capability_id"] + ("-selected" if override else "")
                    for case in ("missing", "empty", "foreign-source", "foreign-capability", "matching"):
                        with self.subTest(entrypoint=entrypoint, slug=slug, override=override, case=case):
                            payload = deepcopy(FIXTURE["evidence"])
                            row = payload["capabilities"][0]
                            row["capability_id"] = capability
                            row["observed_at"] = datetime.now(timezone.utc).isoformat()
                            payload["provenance"]["observed_at"] = row["observed_at"]
                            if case == "empty":
                                payload["capabilities"] = []
                            elif case == "foreign-source":
                                row["source_id"] += "-other"
                            elif case == "foreign-capability":
                                row["capability_id"] += "-other"
                            os.environ.update(MARKET_INTEL_HOST=payload["host"],
                                              MARKET_INTEL_SESSION_ID=payload["session_id"])
                            os.environ.pop("MARKET_INTEL_CAPABILITIES", None)
                            if case != "missing":
                                path = self.tmp / "selected-capabilities.json"
                                path.write_text(json.dumps(payload), encoding="utf-8")
                                os.environ["MARKET_INTEL_CAPABILITIES"] = str(path)
                            args = [entrypoint, slug]
                            if override:
                                args += ["--capability", capability]
                            with patch.object(self.console, "load_registry", return_value={"tools": [tool]}):
                                code, out, err = self.invoke(args)
                            self.assertEqual((code, err), (0, ""))
                            lines = dict(line.strip().split(": ", 1)
                                         for line in out.splitlines() if ": " in line)
                            self.assertEqual(lines["source_id"], tool["source_id"])
                            self.assertEqual(lines["capability_id"], capability)
                            self.assertTrue(lines["reason"].strip())
                            if case == "matching":
                                self.assertEqual(lines["status"], "available-now")
                                self.assertEqual((lines["access"], lines["operation"]), ("exposed", "ready"))
                                for field in ("host", "session_id", "observed_at"):
                                    self.assertEqual(lines[field], row[field])
                                self.assertEqual(lines["observation_method"], payload["provenance"]["observation_method"])
                            else:
                                self.assertEqual(lines["status"], "setup")
                                self.assertEqual((lines["access"], lines["operation"]), ("unproven", "unproven"))
                                for field in ("host", "session_id", "observed_at", "observation_method"):
                                    self.assertNotIn(field, lines)
                                self.assertNotIn("status: available-now", out)

    def fake_repository(self, name="private companion", visibility="PRIVATE"):
        root = self.tmp / name
        (root / ".git").mkdir(parents=True)
        self.repo_visibility = getattr(self, "repo_visibility", {})
        self.repo_visibility[root.resolve()] = visibility
        return root

    def fake_proof(self, directory):
        """Only synthetic proof results; native guard behavior is covered separately."""
        directory = Path(directory)
        repository = next((path for path in (directory, *directory.parents)
                           if path.resolve() in self.repo_visibility), None)
        if repository is None or self.repo_visibility[repository.resolve()] != "PRIVATE":
            raise RuntimeError("synthetic unproven companion")
        return SimpleNamespace(root=str(repository), repositories=("example/companion",),
                               signature=str(repository))

    def fake_query(self, proof, *arguments):
        if arguments == ("rev-parse", "--verify", "HEAD"):
            return subprocess.CompletedProcess(arguments, 0, "1" * 40, "")
        if arguments[:4] == ("check-ignore", "--no-index", "-q", "--"):
            return subprocess.CompletedProcess(arguments, 1, "", "")
        raise AssertionError(arguments)

    def install_fake_boundary(self):
        boundary = SimpleNamespace(prove_private_companion=self.fake_proof,
                                   read_private_companion_git=self.fake_query, GitError=RuntimeError)
        self.stack.enter_context(patch.object(self.console.private_inventory, "_shared_boundary",
                                             return_value=boundary))
        return boundary

    def test_refresh_writes_private_inventory_and_reports_verified_repository(self):
        companion = self.fake_repository()
        self.install_fake_boundary()
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        target = companion / "inventory/availability-cache.json"
        # Generator-backed slugs cover both the MCP guide and its earlier non-MCP return.
        for slug in (FIXTURE["tool"]["slug"], FIXTURE["tool"]["source_id"]):
            tool = dict(FIXTURE["tool"], slug=slug)
            for args in self.refresh_commands(slug):
                with self.subTest(args=args), \
                        patch.object(self.console, "load_registry", return_value={"tools": [tool]}), \
                        patch.object(self.console, "build_snapshot", return_value=deepcopy(FIXTURE["inventory"])):
                    code, out, err = self.invoke(args)
                    self.assertEqual((code, err), (0, ""))
                    self.assertEqual(out.count("fresh inventory; PRIVATE companion example/companion"), 1)
                    self.assertNotIn(str(companion), out)
                    self.assertEqual(json.loads(target.read_text(encoding="utf-8")), FIXTURE["inventory"])
        self.assertFalse((companion / ".gitignore").exists())

    def test_public_unknown_and_unmanaged_destinations_refuse_without_writes(self):
        for visibility in ("PUBLIC", "UNKNOWN", None):
            with self.subTest(visibility=visibility):
                companion = self.fake_repository(str(visibility), visibility)
                os.environ["MARKET_INTEL_DATA_DIR"] = str(companion)
                self.install_fake_boundary()
                code, _, err = self.invoke(["--refresh"])
                self.assertEqual(code, 2)
                self.assertIn("inventory", err)
                self.assertFalse((companion / "inventory").exists())
        loose = self.tmp / "unmanaged"
        loose.mkdir()
        os.environ["MARKET_INTEL_DATA_DIR"] = str(loose)
        code, _, _ = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertFalse((loose / "inventory").exists())

    def test_final_nested_repository_visibility_wins_over_parent(self):
        companion = self.fake_repository()
        nested = self.fake_repository("private companion/inventory", "PUBLIC")
        os.environ["MARKET_INTEL_DATA_DIR"] = str(companion)
        self.install_fake_boundary()
        code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("visibility", err)
        self.assertFalse((nested / "availability-cache.json").exists())

    def test_consumer_tree_is_rejected_before_any_external_process(self):
        os.environ["MARKET_INTEL_DATA_DIR"] = str(ROOT)
        code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("consumer source tree", err)

    def test_canonical_alias_to_public_destination_is_rejected(self):
        companion = self.fake_repository()
        public = self.fake_repository("public target", "PUBLIC")
        self.install_fake_boundary()
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        original_resolve = Path.resolve
        lexical = companion / "inventory/availability-cache.json"
        def resolve(path, *args, **kwargs):
            # Pure canonicalization double: real link behavior is an integration check.
            return public / "availability-cache.json" if path == lexical else original_resolve(path, *args, **kwargs)
        with patch.object(Path, "resolve", resolve):
            code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("visibility", err)
        self.assertFalse((public / "availability-cache.json").exists())

    def test_failed_replace_preserves_previous_snapshot_and_returns_failure(self):
        companion = self.fake_repository()
        self.install_fake_boundary()
        target = companion / "inventory/availability-cache.json"
        target.parent.mkdir()
        previous = json.dumps(FIXTURE["inventory"]).encode("utf-8")
        target.write_bytes(previous)
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        with patch.object(self.console, "build_snapshot", return_value=deepcopy(FIXTURE["inventory"])), \
                patch.object(os, "replace", side_effect=PermissionError("synthetic denial")):
            for args in self.refresh_commands():
                with self.subTest(args=args):
                    retained = set(target.parent.glob(".inventory-*"))
                    code, out, err = self.invoke(args)
                    self.assertEqual(code, 2)
                    self.assertIn("persistence failed", err)
                    self.assertIn("cleanup refused", err)
                    self.assertIn("unpublished candidate retained", err)
                    self.assertEqual(out, "")
                    self.assertEqual(target.read_bytes(), previous)
                    pending = set(target.parent.glob(".inventory-*"))
                    self.assertTrue(retained <= pending)
                    self.assertEqual(len(pending - retained), 1)
                    candidate, = pending - retained
                    self.assertEqual(json.loads(candidate.read_text(encoding="utf-8")), FIXTURE["inventory"])
                    self.assertEqual(set(target.parent.iterdir()), {target, *pending})

    def test_directory_permission_failure_is_explicit(self):
        companion = self.fake_repository()
        self.install_fake_boundary()
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        with patch.object(self.console, "build_snapshot", return_value=deepcopy(FIXTURE["inventory"])), \
                patch.object(Path, "mkdir", side_effect=PermissionError("synthetic denial")):
            code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("persistence failed", err)
        self.assertFalse((companion / "inventory").exists())

    def test_visibility_proof_and_git_ignore_denials_are_explicit(self):
        companion = self.fake_repository()
        os.environ["MARKET_INTEL_DATA_DIR"] = str(companion)
        boundary = self.install_fake_boundary()
        for failure in ("malformed receipt", "missing identity", "PUBLIC", "UNKNOWN"):
            with self.subTest(failure=failure), patch.object(
                    boundary, "prove_private_companion", side_effect=RuntimeError(failure)):
                code, _, err = self.invoke(["--refresh"])
                self.assertEqual(code, 2)
                self.assertIn("visibility", err)
                self.assertFalse((companion / "inventory").exists())
        def ignored(proof, *arguments):
            if arguments[0] == "check-ignore":
                return subprocess.CompletedProcess(arguments, 0, "", "")
            return self.fake_query(proof, *arguments)
        with patch.object(boundary, "read_private_companion_git", side_effect=ignored):
            code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("version control", err)
        self.assertFalse((companion / "inventory").exists())

    def test_visibility_process_failure_is_not_available(self):
        companion = self.fake_repository()
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        boundary = self.install_fake_boundary()
        with patch.object(boundary, "prove_private_companion", side_effect=RuntimeError("synthetic executable denial")):
            code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("could not be verified", err)
        self.assertNotIn("synthetic executable denial", err)

    def test_unrelated_source_error_is_not_reported_as_boundary_refusal(self):
        companion = self.fake_repository()
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        self.install_fake_boundary()
        with patch.object(self.console, "build_snapshot", side_effect=TypeError("synthetic source defect")):
            with self.assertRaisesRegex(TypeError, "source defect"):
                self.invoke(["--refresh"])
        self.assertFalse((companion / "inventory").exists())

    def test_changed_destination_refuses_before_write(self):
        companion = self.fake_repository()
        alternate = self.fake_repository("alternate companion")
        os.environ["MARKET_INTEL_CONFIG"] = str(companion)
        self.install_fake_boundary()
        def changed_snapshot():
            os.environ["MARKET_INTEL_CONFIG"] = str(alternate)
            return deepcopy(FIXTURE["inventory"])
        with patch.object(self.console, "build_snapshot", side_effect=changed_snapshot):
            code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("changed during refresh", err)
        self.assertFalse((companion / "inventory").exists())
        self.assertFalse((alternate / "inventory").exists())

    def test_explicit_missing_override_cannot_fall_back_to_existing_private_config(self):
        companion = self.fake_repository()
        os.environ.update(MARKET_INTEL_CONFIG=str(companion), MARKET_INTEL_DATA_DIR=str(self.tmp / "missing"))
        code, _, err = self.invoke(["--refresh"])
        self.assertEqual(code, 2)
        self.assertIn("missing", err)
        self.assertFalse((companion / "inventory").exists())

    def test_connect_guidance_uses_selected_host(self):
        os.environ["MARKET_INTEL_HOST"] = "codex"
        code, out, _ = self.invoke(["connect", "github-mcp"])
        self.assertEqual(code, 0)
        self.assertIn("Codex MCP settings", out)

    def test_filters_and_option_order_preserve_cli_journeys(self):
        for args in (["--capability", "search", "tool", "github-mcp"],
                     ["tool", "github-mcp", "--capability", "search"],
                     ["status", "--state", "setup"], ["status", "--state", "hard-gap"]):
            with self.subTest(args=args):
                code, out, _ = self.invoke(args)
                self.assertEqual(code, 0)
                self.assertTrue(out.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''





def successor_incident_test_source():
    return r'''

def incident_draft_output(monkeypatch, tmp_path, capsys, d_code="D-STALE", selection=None):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for name in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    for name, value in (selection or {}).items():
        monkeypatch.setenv(name, str(value))
    monkeypatch.setattr(incident_helper, "suggest_shard_edit", lambda *args: "Synthetic shard draft")
    monkeypatch.setattr(incident_helper, "sources_index_advisory", lambda *args: "Synthetic index draft")
    monkeypatch.setattr(incident_helper, "suggest_commit_message", lambda *args: "Synthetic commit draft")
    code = incident_helper.run({"slug": "synthetic-source", "outcome": "dead",
        "detail": "Synthetic evidence awaiting review", "domain": "finance-markets", "d_code": d_code}, False)
    assert code == 0
    return capsys.readouterr().out


@pytest.mark.parametrize("d_code,required", [
    ("D-404", ("api 404", "archived")),
    ("D-PRICE", ("official", "url", "date")),
    ("D-STALE", ("18 months", "and", "verified replacement")),
    ("D-TOS", ("official policy", "route")),
    ("D-SUPERSEDED", ("named", "verified")),
])
def test_incident_draft_uses_canonical_death_evidence(monkeypatch, tmp_path, capsys, d_code, required):
    text = incident_draft_output(monkeypatch, tmp_path, capsys, d_code)
    rationale = text.split("rationale:", 1)[1].splitlines()[0].lower()
    assert all(term in rationale for term in required)
    assert not any(term in rationale for term in (">12mo", "nxdomain", "captcha", "account bans"))


@pytest.mark.parametrize("choice", ["explicit", "alias", "home", "xdg", "priority"])
def test_incident_draft_uses_selected_companion_checker(monkeypatch, tmp_path, capsys, choice):
    selected = tmp_path / {"home": ".market-intel-config", "xdg": ".config/market-intel-config"}.get(choice, "selected config")
    checker = selected / "scripts/sync-check.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("# Generated synthetic checker; never executed.\n", encoding="utf8")
    selection = {}
    if choice in {"explicit", "priority"}:
        selection["MARKET_INTEL_CONFIG"] = selected
    elif choice == "alias":
        selection["MARKET_INTEL_CONFIG_DIR"] = selected
    if choice == "priority":
        selection["MARKET_INTEL_CONFIG_DIR"] = tmp_path / "missing lower priority"
    text = incident_draft_output(monkeypatch, tmp_path, capsys, selection=selection)
    if choice == "xdg":
        assert str(checker.resolve()) not in text
        return
    assert str(checker.resolve()) in text
    assert "python " in text and "<username>" not in text
    assert "Expect: slug" not in text
    assert "GAP:" not in text and "SKIP:" not in text


@pytest.mark.parametrize("case", ["absent", "explicit-missing", "explicit-file", "missing-checker"])
def test_incident_draft_reports_config_gaps_without_fallback(monkeypatch, tmp_path, capsys, case):
    selection = {}
    if case != "absent":
        selected = tmp_path / "selected config"
        selection["MARKET_INTEL_CONFIG"] = selected
        if case == "explicit-file":
            selected.write_text("Synthetic invalid companion path\n", encoding="utf8")
        elif case == "missing-checker":
            selected.mkdir()
        fallback = tmp_path / ".market-intel-config/scripts"
        fallback.mkdir(parents=True)
        (fallback / "sync-check.py").write_text("# Synthetic fallback must not win\n", encoding="utf8")
    text = incident_draft_output(monkeypatch, tmp_path, capsys, selection=selection)
    assert ("SKIP:" if case == "absent" else "GAP:") in text
    assert "  python " not in text and "<username>" not in text
'''


def successor_private_test_source():
    return r'''

def test_temporary_cleanup_refuses_replaced_directory_junction(native_companion, monkeypatch, capsys):
    repository = native_companion["repository"]
    reports = repository / ".staging"
    reports.mkdir(parents=True)
    target = repository / "data/deliverables/result.json"
    target.parent.mkdir(parents=True)
    before = json.dumps(fixture()["inventory"], sort_keys=True).encode()
    target.write_bytes(before)
    other = make_runtime_repository(repository.parent / "other", native_companion["environment"], SAMPLE["other_identity"])
    selected = storage.resolve_destination(path=target)
    original = storage._revalidate
    calls, observed = [], {}
    def changed(relative, destination):
        calls.append(relative)
        if len(calls) == 2:
            pending, = (repository / ".staging").glob("inventory-*.tmp")
            held = repository / "held-reports"
            assert reports.resolve().is_relative_to(repository.parent.resolve())
            assert held.absolute().is_relative_to(repository.parent.resolve())
            reports.rename(held)
            sentinel = other / pending.name
            sentinel.write_bytes(before)
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(other), str(reports))
            else:
                reports.symlink_to(other, target_is_directory=True)
            observed.update(sentinel=sentinel, held=held, temporary=pending.name)
        return original(relative, destination)
    monkeypatch.setattr(storage, "_revalidate", changed)
    with pytest.raises(storage.InventoryError):
        storage.write_text("Synthetic replacement\n", "reports/result.json", selected)
    assert observed["sentinel"].read_bytes() == before
    assert target.read_bytes() == before
    assert (observed["held"] / observed["temporary"]).is_file()
    assert "cleanup refused" in capsys.readouterr().err


def test_temporary_cleanup_refuses_replaced_file(native_companion, monkeypatch, capsys):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/result.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"Synthetic original target\n")
    selected = storage.resolve_destination(path=target)
    original = storage._revalidate
    calls, observed = [], {}
    def changed(relative, destination):
        calls.append(relative)
        if len(calls) == 2:
            pending, = (repository / ".staging").glob("inventory-*.tmp")
            held = target.parent / "held-temporary"
            pending.rename(held)
            pending.write_bytes(b"Synthetic unrelated replacement\n")
            observed.update(pending=pending, held=held)
            # Publication must detect the substituted ordinary file itself.
        return original(relative, destination)
    monkeypatch.setattr(storage, "_revalidate", changed)
    with pytest.raises(storage.InventoryError, match="temporary file changed identity"):
        storage.write_text("Synthetic replacement\n", "reports/result.json", selected)
    assert observed["pending"].read_bytes() == b"Synthetic unrelated replacement\n"
    assert observed["held"].read_text() == "Synthetic replacement\n"
    assert target.read_bytes() == b"Synthetic original target\n"
    assert "cleanup refused" in capsys.readouterr().err
'''


def successor_lock_test_source():
    return r'''


@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_preserves_substituted_parent(tmp_path, monkeypatch, failed, companion):
    tmp_path = companion[0]
    parent, held, other = (tmp_path / name for name in (".staging", "held", "other"))
    parent.mkdir()
    other.mkdir()
    target = parent / "ledger.jsonl"
    selected = storage.Destination(target, tmp_path, "example/companion")
    lock = storage._update_lock_path(selected)
    sentinel = other / lock.name
    sentinel.write_bytes(b"Synthetic unrelated lock\n")
    real_open, real_close = storage.os.open, storage.os.close
    observed = {}
    def open_lock(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == lock.name:
            observed["descriptor"] = descriptor
        return descriptor
    def close_lock(descriptor):
        real_close(descriptor)
        if descriptor == observed.get("descriptor"):
            parent.rename(held)
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(other), str(parent))
            else:
                parent.symlink_to(other, target_is_directory=True)
            observed["substituted"] = True
    monkeypatch.setattr(storage.os, "open", open_lock)
    if real_open in os.supports_dir_fd:
        monkeypatch.setattr(storage.os, "supports_dir_fd", os.supports_dir_fd | {open_lock})
    monkeypatch.setattr(storage.os, "close", close_lock)
    if failed:
        with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
            with storage._exclusive_update(selected):
                raise storage.InventoryError("Synthetic transaction failure")
    else:
        with storage._exclusive_update(selected):
            pass
    assert observed.get("substituted") is True
    assert sentinel.read_bytes() == b"Synthetic unrelated lock\n"
    assert not (held / lock.name).exists()


@pytest.mark.parametrize("case", ["ordinary", "handled-outer", "failed-current"])
def test_native_lock_close_failure_tracks_current_transaction(tmp_path, monkeypatch, capsys, case, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
    lock = storage._update_lock_path(selected)
    real_open, real_close = storage.os.open, storage.os.close
    observed = {}
    def open_lock(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == lock.name:
            observed["descriptor"] = descriptor
        return descriptor
    def fail_close(descriptor):
        if descriptor == observed.get("descriptor"):
            raise OSError("Synthetic owned descriptor close failure")
        real_close(descriptor)
    monkeypatch.setattr(storage.os, "open", open_lock)
    if real_open in os.supports_dir_fd:
        monkeypatch.setattr(storage.os, "supports_dir_fd", os.supports_dir_fd | {open_lock})
    monkeypatch.setattr(storage.os, "close", fail_close)
    def transaction():
        with storage._exclusive_update(selected):
            if case == "failed-current":
                raise storage.InventoryError("Synthetic primary transaction failure")
    try:
        if case == "handled-outer":
            try:
                raise ValueError("Synthetic already handled outer error")
            except ValueError:
                with pytest.raises(storage.InventoryError, match="cleanup refused"):
                    transaction()
        else:
            expected = "primary transaction failure" if case == "failed-current" else "cleanup refused"
            with pytest.raises(storage.InventoryError, match=expected):
                transaction()
        if case == "failed-current":
            assert "cleanup refused" in capsys.readouterr().err
    finally:
        if "descriptor" in observed:
            real_close(observed["descriptor"])
    assert not lock.exists()


def test_native_lock_repeated_acquisition_and_failure_recovery(tmp_path, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
    lock = storage._update_lock_path(selected)
    for unused in range(2):
        with storage._exclusive_update(selected):
            with pytest.raises(storage.InventoryError, match="lock is busy"):
                with storage._exclusive_update(selected, timeout=0):
                    pytest.fail("A concurrent acquisition must not enter")
        assert not lock.exists()
    with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
        with storage._exclusive_update(selected):
            raise storage.InventoryError("Synthetic transaction failure")
    assert not lock.exists()
    with storage._exclusive_update(selected):
        pass
    assert not lock.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor contract")
@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_anchors_parent_during_transaction(tmp_path, failed, companion):
    tmp_path = companion[0]
    parent, held = (tmp_path / name for name in (".staging", "held"))
    parent.mkdir()
    selected = storage.Destination(parent / "ledger.jsonl", tmp_path, "example/companion")
    lock = storage._update_lock_path(selected)
    def transaction():
        with storage._exclusive_update(selected):
            parent.rename(held)
            parent.mkdir()
            lock.write_bytes(b"Synthetic unrelated lock\n")
            if failed:
                raise storage.InventoryError("Synthetic transaction failure")
    if failed:
        with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
            transaction()
    else:
        transaction()
    assert lock.read_bytes() == b"Synthetic unrelated lock\n"
    assert not (held / lock.name).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor contract")
@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_refuses_replaced_entry(tmp_path, capsys, failed, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
    lock, held = storage._update_lock_path(selected), tmp_path / "held-lock"
    message = "Synthetic transaction failure" if failed else "cleanup refused"
    with pytest.raises(storage.InventoryError, match=message):
        with storage._exclusive_update(selected):
            lock.rename(held)
            lock.write_bytes(b"Synthetic unrelated lock\n")
            if failed:
                raise storage.InventoryError("Synthetic transaction failure")
    assert lock.read_bytes() == b"Synthetic unrelated lock\n"
    assert held.is_file()
    if failed:
        assert "cleanup refused" in capsys.readouterr().err
'''


def successor_gate_test_source():
    return r'''

@pytest.mark.parametrize("scenario", ["unchanged-multiple", "regressed-section", "new-ambiguity", "corrected-single"])
def test_card_marker_contract_rejects_ambiguity_and_allows_correction(native_companion, monkeypatch, capsys, scenario):
    multiple = "# Synthetic card\n## API\nLast verified: 2031-02\n## Pricing\nLast verified: 2031-02\n"
    single = "# Synthetic card\n## Last verified: 2031-02\n"
    before = single if scenario == "new-ambiguity" else multiple
    current = single if scenario == "corrected-single" else multiple
    if scenario == "regressed-section":
        current = current.replace("2031-02", "2031-01", 1)
    relative = "skills/market-intel/reference/tools/synthetic-source.md"
    repository, reference, commit = synthetic_matrix_tree(native_companion, {relative: before})
    (reference / "tools/synthetic-source.md").write_text(current, encoding="utf8")
    code, scope = execute_synthetic_matrix(repository, commit, monkeypatch)
    fresh = [message for message in scope["fails"] if "[FRESH]" in message]
    if scenario == "corrected-single":
        assert code == 0 and not fresh, capsys.readouterr().out
    else:
        assert code == 1 and any("ambiguous" in message for message in fresh), capsys.readouterr().out
'''



def human_review_test_source():
    return r'''"""Generated synthetic C7 approval and rewritten-baseline controls."""
import difflib
import json
import re

import pytest

import domain_changes
from human_review import ReviewError, content_hash, load_review, resolve_ci_baseline, review_matches


BASE = "1" * 40
REPLACED = "2" * 40
HEAD = "3" * 40
BEFORE = "# Earlier synthetic catalog\n\n| Source | Route |\n| --- | --- |\n| Synthetic | ④ |\n"
AFTER = "# Updated synthetic catalog\n\n| Source | Route |\n| --- | --- |\n| Replacement | ① |\n"


def receipt():
    return {"version": 1, "baseline": BASE, "replaced_baseline": REPLACED,
            "domains": {"synthetic": {"before": content_hash(BEFORE), "after": content_hash(AFTER)}}}


def test_absent_review_does_not_authorize_churn():
    assert load_review(None) is None
    assert load_review("") is None
    assert not review_matches(None, BASE, "synthetic", BEFORE, AFTER)


@pytest.mark.parametrize("malformation", ["json", "duplicate", "list", "extra", "version-bool",
    "version-unknown", "commit-short", "commit-empty", "domains-empty", "domain-path", "hash-short",
    "hash-extra", "hash-list"])
def test_malformed_review_is_rejected(malformation):
    data = receipt()
    if malformation == "json":
        raw = "{"
    elif malformation == "duplicate":
        raw = json.dumps(data)[:-1] + ', "version": 1}'
    else:
        if malformation == "list": data = []
        elif malformation == "extra": data["waive"] = True
        elif malformation == "version-bool": data["version"] = True
        elif malformation == "version-unknown": data["version"] = 2
        elif malformation == "commit-short": data["baseline"] = "1"
        elif malformation == "commit-empty": data["replaced_baseline"] = ""
        elif malformation == "domains-empty": data["domains"] = {}
        elif malformation == "domain-path": data["domains"]["../synthetic"] = data["domains"].pop("synthetic")
        elif malformation == "hash-short": data["domains"]["synthetic"]["after"] = "3"
        elif malformation == "hash-extra": data["domains"]["synthetic"]["waive"] = True
        elif malformation == "hash-list": data["domains"]["synthetic"] = []
        raw = json.dumps(data)
    with pytest.raises(ReviewError):
        load_review(raw)


@pytest.mark.parametrize("changed", ["none", "baseline", "domain", "before", "after", "missing-after"])
def test_review_requires_exact_history_domain_and_content(changed):
    approved = load_review(json.dumps(receipt()))
    baseline, domain, before, after = BASE, "synthetic", BEFORE, AFTER
    if changed == "baseline": baseline = "4" * 40
    if changed == "domain": domain = "different"
    if changed == "before": before += "Unreviewed earlier row\n"
    if changed == "after": after += "Unreviewed new row\n"
    if changed == "missing-after": after = None
    assert review_matches(approved, baseline, domain, before, after) is (changed == "none")


def test_content_hash_matches_universal_newline_git_reads():
    assert content_hash(BEFORE) == content_hash(BEFORE.replace("\n", "\r\n"))


@pytest.mark.parametrize("approved", [False, True])
def test_review_only_satisfies_churn_and_preserves_other_vetoes(approved, capsys):
    changes = "".join(difflib.unified_diff(BEFORE.splitlines(True), AFTER.splitlines(True)))
    flags = []
    domain_changes.check_domain_diff(
        "synthetic", changes, BEFORE, "", re.compile(r"\d+★"),
        lambda code, message: flags.append(code), current_text=AFTER,
        human_review=receipt() if approved else None, baseline_commit=BASE)
    assert ("CHURN" in flags) is not approved
    assert "DELETE" in flags
    assert ("PASS [CHURN-REVIEW]" in capsys.readouterr().out) is approved


def fake_git(*, parents=None, missing=()):
    calls = []
    def run(*arguments):
        calls.append(arguments)
        if arguments[:3] == ("rev-parse", "--verify", "--end-of-options"):
            reference = arguments[3].removesuffix("^{commit}")
            if reference in missing:
                raise ReviewError("synthetic missing commit")
            return HEAD if reference == "HEAD" else reference
        assert arguments == ("rev-list", "--parents", "-n", "1", HEAD)
        return " ".join([HEAD, *(parents if parents is not None else [BASE])])
    return run, calls


def test_rewrite_baseline_requires_explicit_mapping_and_parent_proof():
    git, calls = fake_git(missing=(REPLACED,))
    assert resolve_ci_baseline(REPLACED, "HEAD", receipt(), git=git) == BASE
    assert ("rev-list", "--parents", "-n", "1", HEAD) in calls
    assert all(REPLACED + "^{commit}" not in call for call in calls)


@pytest.mark.parametrize("parents", [[], ["4" * 40], [BASE, "4" * 40]])
def test_rewrite_never_uses_an_unreviewed_or_multi_commit_parent(parents):
    git, _ = fake_git(parents=parents)
    with pytest.raises(ReviewError, match="single parent"):
        resolve_ci_baseline(REPLACED, "HEAD", receipt(), git=git)


@pytest.mark.parametrize("review", [None, receipt()])
def test_missing_normal_baseline_never_falls_back_to_parent(review):
    missing = "5" * 40
    git, _ = fake_git(missing=(missing,))
    with pytest.raises(ReviewError, match="missing commit"):
        resolve_ci_baseline(missing, "HEAD", review, git=git)


def test_same_baseline_review_keeps_normal_multi_commit_comparison():
    review = receipt()
    review["replaced_baseline"] = BASE
    git, calls = fake_git(parents=["4" * 40])
    assert resolve_ci_baseline(BASE, "HEAD", review, git=git) == BASE
    assert not any(call[0] == "rev-list" for call in calls)


def test_normal_baseline_preserves_full_requested_history():
    requested = "4" * 40
    git, calls = fake_git()
    assert resolve_ci_baseline(requested, "HEAD", receipt(), git=git) == requested
    assert not any(call[0] == "rev-list" for call in calls)


def test_self_comparison_is_never_accepted():
    git, _ = fake_git()
    with pytest.raises(ReviewError, match="equals"):
        resolve_ci_baseline(HEAD, "HEAD", None, git=git)
'''


def generate(out=None, *, check=False):
    sample = fixture()
    objects = {
        "tests/fixtures/console.json": sample,
        "inventory/availability-cache.json.example": sample["inventory"],
        "inventory/host-capabilities.json.example": sample["evidence"],
        "skills/market-intel/reference/live-run-schema.json": schema(),
    }
    payloads = {name: (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
                for name, value in objects.items()}
    payloads["tests/fixtures/live-runs.json"] = (
        json.dumps(feedback_cases(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
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
    payloads["tools/test_verification_contract.py"] = (
        verification_test_source() + "\n\n" + final_review_test_source() + "\n\n" + final_gate_test_source() + "\n\n" + route_migration_test_source() + "\n\n" + route_migration_a04_test_source() + "\n\n" + route_migration_a05_test_source() + "\n\n" + deployment_test_source() + successor_gate_test_source()).encode("utf-8")
    payloads['tools/test_discovery_contract.py'] = discovery_test_source().encode("utf-8")
    payloads['tools/test_first_use_contract.py'] = first_use_test_source().encode("utf-8")
    payloads['tools/test_check_all.py'] = checker_test_source().encode("utf-8")
    payloads['tools/test_console.py'] = console_test_source().encode("utf-8")
    payloads['tools/test_private_writers.py'] = (private_writer_test_source() + successor_private_test_source() + successor_lock_test_source()).encode("utf-8")
    payloads['tools/test_incident_boundary.py'] = (incident_boundary_test_source() + successor_incident_test_source()).encode("utf-8")
    payloads['tools/test_human_review.py'] = human_review_test_source().encode("utf-8")
    manifest = {
        "generator": "tools/make_fixtures.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed_or_recipe_id": RECIPE,
        "synthetic_origin": True,
        "files": {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
    }
    payloads["tests/fixtures/manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
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
        print("fixtures: differs from generator: " + ", ".join(mismatches)
              if mismatches else "fixtures: reproducible")
    return 1 if mismatches else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="generate flat comparison files in this directory")
    parser.add_argument("--check", action="store_true", help="verify fixture bytes without writing")
    args = parser.parse_args()
    raise SystemExit(generate(args.out, check=args.check))


def artifact_write_scenario():
    """Generate fictional artifact-admission paths and content without reading runtime state."""
    return {'allowed': 'data/metrics/live-runs.jsonl', 'undeclared': 'unowned/result.json', 'content': {'schema_version': 1, 'label': 'Synthetic transaction'}}


def configured_doctor_files():
    """Create a fictional selected capability without inspecting an installed account."""
    return {
        "registry.json": json.dumps({"schema_version": 1, "tools": [
            {"slug": "synthetic-tool", "installed": True}]}),
        "tools/synthetic-tool/claude.json.template": '{"mcpServers": {}}\n',
        "tools/synthetic-tool/env.template": "# Synthetic credential-free tool\n",
    }
