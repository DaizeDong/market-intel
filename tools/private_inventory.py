"""Validate the final PRIVATE Git destination before inventory or incident writes."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from functools import lru_cache
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
RELATIVE_PATH = Path("inventory/availability-cache.json")


class InventoryError(RuntimeError):
    """An expected destination or persistence failure, safe to report in the CLI."""


@dataclass(frozen=True)
class Destination:
    path: Path
    repository: Path
    identity: str
    requested_path: Path | None = None
    publication: tuple = ()


@lru_cache(maxsize=1)
def _shared_boundary():
    """Load the supported proof API; an old or absent kit cannot authorize writes."""
    source = ROOT / "guards/tools/data_boundary.py"
    try:
        spec = importlib.util.spec_from_file_location("market_intel_data_boundary", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (OSError, ImportError, ValueError) as exc:
        raise InventoryError("PRIVATE proof is unavailable; initialize the guards submodule") from exc
    if not all(callable(getattr(module, name, None)) for name in (
            "prove_private_companion", "read_private_companion_git", "GitError")):
        raise InventoryError("PRIVATE proof is unavailable; update the guards submodule")
    return module


def _data_directory():
    """Use shared discovery for defaults; an explicit missing path never falls back."""
    explicit = os.environ.get("MARKET_INTEL_DATA_DIR")
    if explicit:
        directory = Path(explicit).expanduser()
    else:
        config = os.environ.get("MARKET_INTEL_CONFIG") or os.environ.get("MARKET_INTEL_CONFIG_DIR")
        if config:
            companion = Path(config).expanduser()
            if not companion.is_dir():
                raise InventoryError("inventory companion is missing; initialize a PRIVATE versioned companion")
            directory = companion / "data" if (companion / "data").is_dir() else companion
        else:
            resolver = ROOT / "guards/tools/datadir.py"
            if not resolver.is_file():
                raise InventoryError("inventory resolver is missing; initialize the guards submodule")
            spec = importlib.util.spec_from_file_location("market_intel_datadir", resolver)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                directory = module.resolve_data_dir("market-intel", create=False)
            except (module.DataDirInsideOwnRepo, module.CompanionUnproven) as exc:
                raise InventoryError("inventory companion cannot be resolved safely") from exc
    if directory is None or not directory.is_dir():
        raise InventoryError("inventory DATA is missing; set MARKET_INTEL_CONFIG to a PRIVATE versioned companion")
    return directory


def _resolve_destination(relative_path, path, directory):
    """Resolve symlinks and the nearest containing repository without creating paths."""
    try:
        relative_path = Path(relative_path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise InventoryError("DATA destination must be a relative companion path")
        lexical = Path(path).expanduser().absolute() if path is not None else _data_directory().absolute() / relative_path
        try:
            target = lexical.resolve()
        except RuntimeError as exc:
            raise InventoryError("inventory destination contains a filesystem link loop") from exc
        if lexical.is_relative_to(ROOT) or target.is_relative_to(ROOT.resolve()):
            raise InventoryError("inventory cannot be stored inside the consumer source tree")
        if any(part.lower() == ".git" for part in target.parts):
            raise InventoryError("inventory cannot be stored inside Git metadata")
        if directory and not target.is_dir():
            raise InventoryError("private runtime destination requires an existing directory")
        ancestor = target if directory else target.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        if not ancestor.is_dir() or (target.exists() and not (target.is_dir() if directory else target.is_file())):
            raise InventoryError("inventory destination is not a file in a directory")
        boundary = _shared_boundary()
        try:
            proof = boundary.prove_private_companion(ancestor)
            repository = Path(proof.root).resolve()
            if not target.is_relative_to(repository) or repository.is_relative_to(ROOT.resolve()):
                raise InventoryError("inventory destination is not outside the consumer source tree")
            boundary.read_private_companion_git(proof, "rev-parse", "--verify", "HEAD")
            ignored = boundary.read_private_companion_git(
                proof, "check-ignore", "--no-index", "-q", "--",
                target.relative_to(repository).as_posix())
        except boundary.GitError as exc:
            raise InventoryError(
                "inventory destination visibility or Git storage could not be verified; "
                "use a versioned PRIVATE companion with a fresh visibility receipt") from exc
        if ignored.returncode != 1:
            raise InventoryError("inventory must be eligible for version control; destination is ignored or cannot be checked")
        identity = ", ".join(proof.repositories)
        publication = (tuple(proof.repositories), proof.signature)
        return Destination(target, repository, identity, lexical if path is not None else None, publication)
    except (OSError, ValueError) as exc:
        raise InventoryError("inventory destination is inaccessible or invalid") from exc


def resolve_destination(relative_path=RELATIVE_PATH, *, path=None):
    """Verify a file destination; the file itself may not exist yet."""
    return _resolve_destination(relative_path, path, False)


def resolve_directory(relative_path=Path("runtime"), *, path=None):
    """Verify an existing directory, including a repository rooted at that directory."""
    return _resolve_destination(relative_path, path, True)


def write_snapshot(snapshot, destination=None):
    """Atomic replacement preserves an earlier snapshot on serialization/write failure."""
    try:
        payload = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    except (TypeError, ValueError, UnicodeError) as exc:
        raise InventoryError("inventory serialization failed; previous snapshot was preserved") from exc
    return write_text(payload, RELATIVE_PATH, destination)


def write_text(payload, relative_path, destination=None):
    """Atomically publish UTF-8 text; retain unpublished temporaries after failure."""
    current = _revalidate(relative_path, destination)

    temporary = None
    try:
        current.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=current.path.parent, prefix=".inventory-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        current = _revalidate(relative_path, current)
        os.replace(temporary, current.path)
        temporary = None
    except (OSError, UnicodeError) as exc:
        raise InventoryError("inventory persistence failed; previous snapshot was preserved") from exc
    finally:
        if temporary is not None:
            # A failed proof may mean this pathname now traverses another directory.
            # Retaining the file avoids a check-then-unlink race and keeps the original error.
            print(f"inventory temporary cleanup refused after publication failure; "
                  f"unpublished candidate retained (created at {temporary})", file=sys.stderr)
    return current


def _revalidate(relative_path, destination):
    kwargs = {"path": destination.requested_path} if destination is not None and destination.requested_path is not None else {}
    current = resolve_destination(relative_path, **kwargs)
    if destination is not None and current != destination:
        raise InventoryError("inventory destination changed during refresh; retry after checking the companion")
    return current


@contextmanager
def _exclusive_update(destination, timeout=10):
    """An exclusive lock file serializes cooperating processes; stale locks fail closed."""
    lock = destination.path.with_name("." + destination.path.name + ".lock")
    descriptor = None
    directory = None
    transaction_failed = False
    deadline = time.monotonic() + timeout
    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if os.name == "nt":
            flags |= os.O_TEMPORARY
        elif (not hasattr(os, "O_DIRECTORY")
              or any(operation not in os.supports_dir_fd for operation in (os.open, os.stat, os.unlink))
              or os.stat not in os.supports_follow_symlinks):
            raise InventoryError("private ledger requires anchored lock operations on this platform")
        destination.path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            directory = os.open(lock.parent, os.O_RDONLY | os.O_DIRECTORY)
        while descriptor is None:
            try:
                if directory is None:
                    descriptor = os.open(lock, flags, 0o600)
                else:
                    descriptor = os.open(lock.name, flags, 0o600, dir_fd=directory)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise InventoryError("private ledger lock is busy; check active writers or recover a stale lock")
                time.sleep(0.025)
        yield
    except OSError as exc:
        transaction_failed = True
        raise InventoryError("private ledger lock failed; previous ledger was preserved") from exc
    except BaseException:
        transaction_failed = True
        raise
    finally:
        cleanup_error = None
        try:
            if descriptor is not None and directory is not None:
                owned = os.fstat(descriptor)
                current = os.stat(lock.name, dir_fd=directory, follow_symlinks=False)
                if (not stat.S_ISREG(current.st_mode)
                        or (owned.st_dev, owned.st_ino) != (current.st_dev, current.st_ino)):
                    raise InventoryError("private ledger lock identity changed")
                # The directory handle anchors cleanup across parent renames.
                # Cooperating writers must not replace the live lock entry itself.
                os.unlink(lock.name, dir_fd=directory)
        except (OSError, NotImplementedError, InventoryError) as exc:
            cleanup_error = exc
        finally:
            # Windows deletes the owned temporary lock when its descriptor closes.
            for handle in (descriptor, directory):
                if handle is not None:
                    try:
                        os.close(handle)
                    except OSError as exc:
                        if cleanup_error is None:
                            cleanup_error = exc
        if cleanup_error is not None:
            message = ("private ledger lock cleanup refused; owned lock may remain "
                       f"(created at {lock}); inspect the private companion")
            if transaction_failed:
                print(message, file=sys.stderr)
            else:
                raise InventoryError(message) from cleanup_error


def update_text(transform, relative_path, destination=None):
    """Lock the complete revalidate/read/transform/atomic-write transaction."""
    selected = _revalidate(relative_path, destination)
    with _exclusive_update(selected):
        current = _revalidate(relative_path, selected)
        try:
            previous = current.path.read_text(encoding="utf-8-sig") if current.path.exists() else ""
        except (OSError, UnicodeError) as exc:
            raise InventoryError("private ledger is unreadable; previous ledger was preserved") from exc
        return write_text(transform(previous), relative_path, current)
