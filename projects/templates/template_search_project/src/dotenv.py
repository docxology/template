"""Tiny ``.env`` loader (no third-party dependency).

Reads ``KEY=value`` lines, ignores blanks and ``#`` comments, supports
optional double / single quotes around values. Sets keys into
``os.environ`` only when they are not already set, so explicit shell
exports always win.

Why not python-dotenv?

The infrastructure layer is dependency-light by design. The Paperclip
key is the only secret most users of this project will need; a 30-line
loader keeps the project standalone and avoids pulling another package
into every CI run.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

_KV_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_QUOTED_RE = re.compile(r"^([\"'])(.*)\1$")


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse the contents of a ``.env`` file into a dict."""
    out: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _KV_RE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Strip surrounding quotes if present.
        q = _QUOTED_RE.match(value)
        if q:
            value = q.group(2)
        out[key] = value
    return out


def load_dotenv(
    path: Path | str | None = None,
    *,
    override: bool = False,
    extra_paths: Iterable[Path | str] = (),
) -> dict[str, str]:
    """Load *path* (and *extra_paths*) into :data:`os.environ`.

    Args:
        path: Primary ``.env`` path. When ``None``, defaults to ``./.env``
            in the current working directory.
        override: When ``True``, overwrite existing environment variables.
            By default, existing values win.
        extra_paths: Additional paths to load *after* *path*.

    Returns:
        Map of ``{key: value}`` actually applied to the environment.
    """
    candidates: list[Path] = []
    if path is None:
        candidates.append(Path(".env"))
    else:
        candidates.append(Path(path))
    candidates.extend(Path(p) for p in extra_paths)

    applied: dict[str, str] = {}
    for candidate in candidates:
        if not candidate.exists():
            continue
        for k, v in parse_dotenv(candidate.read_text(encoding="utf-8")).items():
            if not override and k in os.environ:
                continue
            os.environ[k] = v
            applied[k] = v
    return applied
