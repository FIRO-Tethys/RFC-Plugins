"""Shared helper for validating optional module dependencies with friendly errors."""
from __future__ import annotations

import importlib
from typing import Iterable


def require(packages: Iterable[str], extra: str) -> None:
    """Raise a clear ImportError if any package in ``packages`` is missing.

    Modules call this from their ``validate_dependencies()`` function so that
    drivers fail at instantiation with an actionable message rather than at
    module import with a raw ModuleNotFoundError.

    Args:
        packages: Distribution names to attempt to import.
        extra: The pyproject extra that pulls in these packages (e.g. ``"weather"``).

    Raises:
        ImportError: With a message naming the missing packages and the exact
            ``pip install`` command to fix the gap.
    """
    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        names = ", ".join(repr(p) for p in missing)
        raise ImportError(
            f"rfc-plugins[{extra}] requires {names}. "
            f"Install with: pip install 'rfc-plugins[{extra}]'"
        )
