"""Generated release evidence exercises rejection paths without Git or publication."""
import copy
import json
from pathlib import Path

import pytest

from make_fixtures import fixture
from release_contract import ReleaseError, validate_doc, validate_refs, validate_sync


def test_sync_requires_success_and_complete_buckets():
    sample = fixture()["maintenance"]["release"]
    assert validate_sync(0, sample["sync"])["status"] == "passed"
    for code, output in ((1, sample["sync"]), (2, ""), (0, ""),
                         (0, sample["sync"].splitlines()[0]),
                         (0, sample["sync"] + "\n" + sample["sync"].splitlines()[0]),
                         (0, sample["sync"].replace("[0] B", "[1] B"))):
        with pytest.raises(ReleaseError):
            validate_sync(code, output)


def test_doc_distinguishes_valid_warning_from_process_failure():
    sample = fixture()["maintenance"]["release"]
    clean = sample["doc"]
    assert validate_doc(0, json.dumps(clean), sample["version"])["status"] == "passed"
    warning = copy.deepcopy(clean)
    warning["drifts"], warning["exit_code"] = [sample["warning"]], 2
    assert validate_doc(2, json.dumps(warning), sample["version"])["status"] == "warning"
    bad = [({}, 0), (clean, 2), (warning, 0)]
    for change in ({"exit_code": 3}, {"drifts": [{}]}, {"canonical": {}}, {"exit_code": False}):
        bad.append(({**clean, **change}, 0))
    for data, code in bad:
        with pytest.raises(ReleaseError):
            validate_doc(code, json.dumps(data), sample["version"])
    for code, output in ((2, "can't open file"), (1, "Traceback"), (127, "")):
        with pytest.raises(ReleaseError):
            validate_doc(code, output, sample["version"])
    with pytest.raises(ReleaseError):
        validate_doc(0, json.dumps(clean), "different")
    warning["drifts"][0]["severity"], warning["exit_code"] = "fail", 1
    with pytest.raises(ReleaseError):
        validate_doc(1, json.dumps(warning), sample["version"])


def test_publication_requires_matching_main_and_tag():
    sample = fixture()["maintenance"]["release"]
    commit, tag = sample["commit"], "v" + sample["version"]
    remote = f"{commit}\trefs/heads/main\n{commit}\trefs/tags/{tag}"
    assert validate_refs("main", commit, commit, remote, tag)["commit"] == commit
    for branch, main, output in (("feature", commit, remote), ("", commit, remote),
                                 ("main", "b" * 40, remote), ("main", commit, ""),
                                 ("main", commit, remote.splitlines()[0]),
                                 ("main", commit, remote + "\n" + remote.splitlines()[0]),
                                 ("main", commit, remote.replace(commit, "b" * 40))):
        with pytest.raises(ReleaseError):
            validate_refs(branch, commit, main, output, tag)


def test_release_wires_preflight_before_publication():
    # Static integration only. Executing release is a separately authorized operation.
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools/release.ps1").read_text(encoding="utf-8")
    assert script.index("--json --no-cache") < script.index("if ($DryRun)") < script.index("& git tag")
    assert script.index("Assert-Contract @{kind='sync'") < script.index("if ($DryRun)")
    assert "git push --atomic origin" in script and "kind='refs'" in script
    assert "Read-Git -GitArguments @('symbolic-ref'" in script
    assert "$env:GIT_OPTIONAL_LOCKS = '0'" in script
    assert "--fix" not in script and "git commit" not in script
