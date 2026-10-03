"""Generated synthetic C7 approval and rewritten-baseline controls."""
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
