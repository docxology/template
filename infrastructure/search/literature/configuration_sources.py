"""Text streams over immutable admitted YAML bytes, preserving file diagnostics."""

from __future__ import annotations

from io import StringIO
from pathlib import Path


class ConfigTextStream(StringIO):
    """An in-memory config stream with the original source name and newline policy."""

    def __init__(self, path: Path | str, source_bytes: bytes) -> None:
        if type(source_bytes) is not bytes:
            raise TypeError("admitted configuration source must be immutable bytes")
        super().__init__(source_bytes.decode("utf-8"), newline=None)
        self.name = str(path)


__all__ = ["ConfigTextStream"]
