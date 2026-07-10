"""File-digest helper shared by the proof writer and the output verifier."""

from __future__ import annotations

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str:  # pragma: no cover - integration-tested by the dev generator
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
