#!/usr/bin/env python3
"""Load the operator's optional llmcall interface without choosing providers."""
from __future__ import annotations

import argparse
import importlib
import sys


class ModelUnavailable(RuntimeError):
    """The configured model interface cannot be imported or is incompatible."""

    def __init__(self):
        super().__init__(
            "UNINITIALIZED: the optional llmcall interface is unavailable. "
            "Install the operator's configured llmcall package into this Python "
            "environment; see CONFIG.md#model-adapter. "
            "Then run: python tools/model_adapter.py --check"
        )


def require_call():
    """Resolve the installed interface; importing it does not verify provider access."""
    try:
        operation = getattr(importlib.import_module("llmcall"), "call", None)
    except Exception:
        raise ModelUnavailable() from None
    if not callable(operation):
        raise ModelUnavailable()
    return operation


def call(prompt, **options):
    """Forward only the caller's arguments, preserving installed routing defaults."""
    return require_call()(prompt, **options)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True,
                        help="check the import interface without calling a provider")
    parser.parse_args(argv)
    try:
        require_call()
    except ModelUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 3
    print("llmcall interface available; provider execution and authentication NOT CHECKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
