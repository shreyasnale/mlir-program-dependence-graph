"""Utilities for locating the CIRCT optimizer executable.

The thesis slicing prototype should not depend on a developer-specific
absolute Windows path.  This helper provides a deterministic resolution
order:

1. an explicitly supplied path;
2. CIRCT_OPT environment variable;
3. circt-opt / circt-opt.exe available on PATH.

The caller remains responsible for reporting a useful error when no
executable can be found.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_circt_opt(explicit_path: str | None = None) -> str | None:
    """Return a usable circt-opt path, or None if it cannot be resolved."""
    candidates: list[str] = []

    if explicit_path:
        candidates.append(explicit_path)

    env_path = os.environ.get("CIRCT_OPT")
    if env_path:
        candidates.append(env_path)

    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return str(path.resolve())

    for executable in ("circt-opt", "circt-opt.exe"):
        found = shutil.which(executable)
        if found:
            return found

    return None
