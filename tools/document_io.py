"""Read and atomically edit one ordinary document inside a selected directory."""
from __future__ import annotations

import os
from pathlib import Path
import stat
import tempfile


class DocumentError(ValueError):
    """An unsafe, changed, or unreadable document cannot be edited."""


def _identity(info):
    identity = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    # Windows stat/fstat can disagree on creation time for the same open file.
    return identity if os.name == "nt" else (*identity, info.st_ctime_ns)


def _inspect(path, directory):
    target = Path(path).absolute()
    if target.parent != Path(directory).absolute():
        raise DocumentError("document must be directly inside the selected directory")
    for current in (*reversed(target.parents), target):
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise DocumentError("document path must not contain filesystem aliases")
        if current == target:
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise DocumentError("document must be an ordinary file without hardlinks")
        elif not stat.S_ISDIR(info.st_mode):
            raise DocumentError("document parent must be an ordinary directory")
    return _identity(info)


def _revalidate(path, directory, expected):
    if _inspect(path, directory) != expected:
        raise DocumentError("document changed during the edit; review it and retry")


def read_document(path, directory):
    """Refuse aliases before reading and bind the content to its file identity."""
    try:
        expected = _inspect(path, directory)
        with Path(path).open("r", encoding="utf-8-sig") as stream:
            opened = os.fstat(stream.fileno())
            if opened.st_nlink != 1 or _identity(opened) != expected:
                raise DocumentError("document changed before reading")
            content = stream.read()
        _revalidate(path, directory, expected)
        return content, expected
    except (OSError, UnicodeError) as exc:
        raise DocumentError("document is unreadable; no edit was applied") from exc


def replace_document(path, directory, content, expected):
    """Replace after a final identity check; failed writes preserve the old file."""
    target = Path(path)
    temporary = None
    created = None
    try:
        _revalidate(target, directory, expected)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=target.parent, prefix=".document-", delete=False) as stream:
            temporary = Path(stream.name)
            created = os.fstat(stream.fileno())
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        pending = temporary.lstat()
        if not os.path.samestat(created, pending) or pending.st_nlink != 1:
            raise DocumentError("document temporary file changed before replacement")
        _revalidate(target, directory, expected)
        os.replace(temporary, target)
        temporary = None
    except (OSError, UnicodeError) as exc:
        raise DocumentError("document persistence failed; prior content was preserved") from exc
    finally:
        if temporary is not None:
            try:
                pending = temporary.lstat()
                if created is None or not os.path.samestat(created, pending):
                    raise DocumentError("document temporary file changed; cleanup refused")
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise DocumentError("document temporary file cleanup failed") from exc
