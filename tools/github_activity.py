"""Deterministic GitHub activity decisions from current, typed observations."""
import datetime


def months_old(value, now):
    if not isinstance(value, str) or "T" not in value:
        return None
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        stamp = stamp.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        current = now.replace(tzinfo=None) if now.tzinfo is None else now.astimezone(
            datetime.timezone.utc).replace(tzinfo=None)
        if stamp > current:
            return None
        return (current - stamp).total_seconds() / (86400 * 30.44)
    except (ValueError, TypeError, OverflowError):
        return None


def activity_entry(repo, observation, now, stale_months=12):
    entry = {"repo": repo, "pushed_at": None, "archived": None,
             "verdict": "RATE_LIMITED", "reason": "missing or invalid activity evidence",
             "checked_at": now.isoformat()}
    if not isinstance(observation, dict) or observation.get("ok") is not True:
        error = observation.get("err") if isinstance(observation, dict) else None
        if error == "404":
            entry.update(verdict="BLOCK", reason="404 not found")
        elif error == "unparseable":
            entry["reason"] = "unparseable activity response"
        else:
            entry["reason"] = "could not check current activity"
        return entry
    pushed_at, archived = observation.get("pushed_at"), observation.get("archived")
    entry.update(pushed_at=pushed_at, archived=archived)
    if archived is True:
        entry.update(verdict="BLOCK", reason="archived upstream")
        return entry
    age = months_old(pushed_at, now)
    if archived is not False or age is None:
        return entry
    if age > stale_months:
        entry.update(verdict="WARN", reason=f"pushed_at {pushed_at[:10]} is ~{int(age)}mo old (>{stale_months}mo)")
    else:
        entry.update(verdict="PASS", reason=f"pushed_at {pushed_at[:10]} within {stale_months}mo")
    return entry


def activity_results(repos, observations, cache, now, block, warn):
    """The matrix already fetched current evidence; a cached verdict cannot replace it."""
    results = []
    for repo in repos:
        entry = activity_entry(repo, observations.get(repo), now)
        if entry["verdict"] == "BLOCK":
            block("GHACTIVE", f"{repo}: {entry['reason']}")
        elif entry["verdict"] in {"WARN", "RATE_LIMITED"}:
            warn("GHACTIVE", f"{repo}: {entry['reason']}")
        results.append(entry)
        cache[repo] = entry
    return results
