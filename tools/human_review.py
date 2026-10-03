"""Match an operator-supplied C7 review to exact public source content and history."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys


REVIEW_ENV = "MARKET_INTEL_C7_REVIEW"


class ReviewError(ValueError):
    """A review or historical comparison could not be verified."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError("duplicate review field")
        result[key] = value
    return result


def load_review(raw):
    """Read trusted operator configuration; empty configuration grants no approval."""
    if not raw:
        return None
    try:
        review = json.loads(raw, object_pairs_hook=_unique_object)
    except (ValueError, TypeError) as exc:
        raise ReviewError("invalid C7 review JSON") from exc
    fields = {"version", "baseline", "replaced_baseline", "domains"}
    if not isinstance(review, dict) or set(review) != fields or type(review["version"]) is not int:
        raise ReviewError("invalid C7 review fields")
    if review["version"] != 1:
        raise ReviewError("unsupported C7 review version")
    for name in ("baseline", "replaced_baseline"):
        if not isinstance(review[name], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", review[name]):
            raise ReviewError("invalid C7 review commit")
    domains = review["domains"]
    if not isinstance(domains, dict) or not domains:
        raise ReviewError("C7 review has no domain content")
    for domain, hashes in domains.items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", domain):
            raise ReviewError("invalid C7 review domain")
        if not isinstance(hashes, dict) or set(hashes) != {"before", "after"}:
            raise ReviewError("invalid C7 review content fields")
        if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
               for value in hashes.values()):
            raise ReviewError("invalid C7 review content hash")
    return review


def content_hash(text):
    """Use the same universal-newline content read by the historical matrix checks."""
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")).hexdigest()


def review_matches(review, baseline, domain, before, after):
    if review is None or baseline != review["baseline"] or after is None:
        return False
    return review["domains"].get(domain) == {
        "before": content_hash(before), "after": content_hash(after)}


def _git(*arguments):
    try:
        result = subprocess.run(["git", *arguments], check=True, capture_output=True,
                                text=True, encoding="utf-8", timeout=30)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ReviewError("Git could not verify the CI baseline") from exc
    return result.stdout.strip()


def resolve_ci_baseline(requested, candidate, review, *, git=_git):
    """Accept only an explicit rewrite mapping and its verified single-parent candidate."""
    head = git("rev-parse", "--verify", "--end-of-options", candidate + "^{commit}")
    replacement = (review is not None and requested == review["replaced_baseline"]
                   and review["baseline"] != review["replaced_baseline"])
    reference = review["baseline"] if replacement else requested
    base = git("rev-parse", "--verify", "--end-of-options", reference + "^{commit}")
    if base == head:
        raise ReviewError("baseline equals the candidate")
    if replacement:
        parents = git("rev-list", "--parents", "-n", "1", head).split()
        if parents != [head, base] or base != review["baseline"]:
            raise ReviewError("rewrite baseline is not the explicitly reviewed single parent")
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolve-base", required=True)
    parser.add_argument("--candidate", default="HEAD")
    args = parser.parse_args()
    try:
        review = load_review(os.environ.get(REVIEW_ENV))
        print(resolve_ci_baseline(args.resolve_base, args.candidate, review))
    except ReviewError as exc:
        print(f"NOT_EXAMINED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
