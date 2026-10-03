#!/usr/bin/env python3
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
