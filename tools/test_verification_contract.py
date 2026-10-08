"""Generator-owned synthetic regressions for private verification and truthful coverage."""
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


# Generated final-review regressions with synthetic provider and Git observations.


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


# Generated native and pure regressions for the final matrix-gate review.
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


def route_migration_flags(before, current, explanation=""):
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


def route_migration_semantic_domain(default="Alpha."):
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
