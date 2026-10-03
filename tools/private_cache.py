"""Optional observation caches; persisted entries require the verified PRIVATE companion."""
import json
from pathlib import Path

import private_inventory as storage

GH_CACHE_PATH = Path("cache/gh-api-cache.json")
L0_CACHE_PATH = Path("cache/l0-cache.json")


def _decode(payload):
    try:
        cache = json.loads(payload) if payload.strip() else {}
    except (ValueError, UnicodeError) as exc:
        raise storage.InventoryError("private verification cache is malformed; preserve and repair it") from exc
    if not isinstance(cache, dict):
        raise storage.InventoryError("private verification cache must be an object")
    return cache


def load_cache(relative_path, *, enabled=True):
    """An explicit disabled cache neither reads nor resolves persistent storage."""
    if enabled is False:
        return None, {}
    destination = storage.resolve_destination(relative_path)
    try:
        payload = destination.path.read_text(encoding="utf-8") if destination.path.exists() else ""
    except (OSError, UnicodeError) as exc:
        raise storage.InventoryError("private verification cache is unreadable") from exc
    return destination, _decode(payload)


def prepare_write(relative_path, destination, *, enabled=True):
    """Preflight enabled persistence before observations; disabled mode performs no I/O."""
    if enabled is False:
        return None
    def preserve(previous):
        _decode(previous)
        return previous or "{}\n"
    return storage.update_text(preserve, relative_path, destination)


def save_entries(relative_path, entries, destination, *, enabled=True):
    """Merge enabled persistence; only an explicit disabled policy skips the write."""
    if enabled is False:
        return None
    def merge(previous):
        cache = _decode(previous)
        cache.update(entries)
        return json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return storage.update_text(merge, relative_path, destination)
