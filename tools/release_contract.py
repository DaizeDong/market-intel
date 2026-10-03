"""Strict, side-effect-free interpretation of release checker output."""
import json
import re
import sys


class ReleaseError(ValueError):
    """A release gate did not return complete, internally consistent evidence."""


def validate_sync(returncode, output):
    if type(returncode) is not int or returncode != 0:
        raise ReleaseError("sync checker failed; a nonzero exit is never an A-only pass")
    buckets = {}
    for line in output.splitlines():
        match = re.match(r"^\s*\[\s*(\d+)\s*\]\s+([A-G])\s", line)
        if match:
            count, bucket = match.groups()
            if bucket in buckets:
                raise ReleaseError("sync checker repeated a bucket")
            buckets[bucket] = int(count)
    if set(buckets) != set("ABCDEFG"):
        raise ReleaseError("sync checker omitted required A-G bucket evidence")
    if any(buckets[bucket] for bucket in "BCDEFG"):
        raise ReleaseError("sync checker reports unreconciled B-G drift")
    return {"status": "passed", "buckets": buckets}


def validate_doc(returncode, output, version):
    try:
        data = json.loads(output)
    except (ValueError, TypeError) as exc:
        raise ReleaseError("doc checker did not return JSON evidence") from exc
    if not isinstance(data, dict) or set(data) != {"canonical", "drifts", "exit_code"}:
        raise ReleaseError("doc checker returned an incomplete result")
    canonical, drifts = data["canonical"], data["drifts"]
    if (not isinstance(canonical, dict) or canonical.get("version") != version
            or any(type(canonical.get(key)) is not int or canonical[key] < 1
                   for key in ("domain_count", "tool_count"))
            or not isinstance(drifts, list)):
        raise ReleaseError("doc checker canonical values are missing or disagree with the release")
    if any(not isinstance(row, dict) or row.get("severity") not in ("fail", "warn")
           or not isinstance(row.get("field"), str) or not row["field"]
           or not isinstance(row.get("location"), str) or not row["location"] for row in drifts):
        raise ReleaseError("doc checker returned invalid drift evidence")
    computed = 1 if any(row["severity"] == "fail" for row in drifts) else (2 if drifts else 0)
    if (type(returncode) is not int or type(data["exit_code"]) is not int
            or returncode != computed or data["exit_code"] != computed):
        raise ReleaseError("doc checker exit and evidence disagree")
    if computed == 1:
        raise ReleaseError("doc checker reports blocking drift")
    return {"status": "warning" if computed == 2 else "passed", "drifts": drifts}


def validate_refs(branch, head, main, remote, tag):
    if branch != "main" or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) or head != main:
        raise ReleaseError("release must use the verified HEAD of main")
    rows = {}
    for line in remote.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] in rows:
            raise ReleaseError("remote ref evidence is malformed or duplicated")
        rows[fields[1]] = fields[0]
    if rows != {"refs/heads/main": head, "refs/tags/" + tag: head}:
        raise ReleaseError("published main and tag do not both resolve to the release commit")
    return {"status": "passed", "commit": head}


def main():
    try:
        request = json.load(sys.stdin)
        kind = request.pop("kind")
        validators = {"sync": validate_sync, "doc": validate_doc, "refs": validate_refs}
        result = validators[kind](**request)
    except (KeyError, TypeError, ValueError) as exc:
        print("release: NOT_EXAMINED or BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
