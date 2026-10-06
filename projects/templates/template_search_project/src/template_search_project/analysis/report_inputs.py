"""Held own-input bytes for informational review findings, separate from imports."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprint_files import anchored_parent, open_directory, observation

_IGNORED = frozenset(
    {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".DS_Store", ".git"}
)


@dataclass(frozen=True)
class ReportInputs:
    """Immutable captured bytes/inventory; identities stay out of public digests."""

    files: Mapping[str, bytes]
    directories: tuple[str, ...]
    identities: Mapping[str, tuple]
    presence: Mapping[str, bool]
    manifest: Mapping[str, str]

    def materialize(self, destination: Path) -> None:
        for relative in self.directories:
            (destination / relative).mkdir(parents=True, exist_ok=True)
        for relative, raw in self.files.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)


def _presence(root: Path) -> dict[str, bool]:
    result = {"reading_report": False, "combined_pdf": False}
    with anchored_parent(root / "output") as parent:
        if parent is None:
            raise ValueError("current report output presence requires a real project")
        try:
            metadata = os.stat("output", dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return result
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("current report output presence requires a confined real directory")
        with open_directory(parent, "output") as output:
            try:
                reading = os.stat("reading_report.md", dir_fd=output, follow_symlinks=False)
            except FileNotFoundError:
                reading = None
            if reading is not None:
                if not stat.S_ISREG(reading.st_mode):
                    raise ValueError("reading_report.md presence requires a regular file")
                result["reading_report"] = True
            try:
                pdf = os.stat("pdf", dir_fd=output, follow_symlinks=False)
            except FileNotFoundError:
                pdf = None
            if pdf is not None:
                if not stat.S_ISDIR(pdf.st_mode):
                    raise ValueError("current report PDF presence requires a real directory")
                with open_directory(output, "pdf") as directory:
                    for name in os.listdir(directory):
                        if name.endswith("_combined.pdf"):
                            metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
                            if not stat.S_ISREG(metadata.st_mode):
                                raise ValueError("current report PDF presence requires regular files")
                            result["combined_pdf"] = True
    return result


def capture_report_inputs(root: Path, root_identity: tuple[int, int]) -> ReportInputs:
    """Freeze complete consumed visible source/data under held no-follow paths."""
    files: dict[str, bytes] = {}
    directories: list[str] = []
    identities: dict[str, tuple] = {}
    count, total = 0, 0

    def names_in(descriptor: int, expected_count: int | None = None) -> list[str]:
        nonlocal count
        names: list[str] = []
        with os.scandir(descriptor) as entries:
            for entry in entries:
                if expected_count is None:
                    count += 1
                    if count > 20000:
                        raise ValueError("report source entry ceiling exceeded")
                elif len(names) >= expected_count:
                    raise ValueError("report source directory changed during capture")
                names.append(entry.name)
        return sorted(names)

    def visit(descriptor: int, relative: Path, depth: int) -> None:
        nonlocal total
        if depth > 32:
            raise ValueError("report source depth ceiling exceeded")
        before = os.fstat(descriptor)
        identities[relative.as_posix()] = observation(before)
        names = names_in(descriptor)
        for name in names:
            if name in _IGNORED or relative == Path(".") and (name.startswith(".") or name == "output"):
                continue
            if name == ".env" or name.startswith(".env.") and not name.endswith((".example", ".template")):
                raise ValueError("report source cannot consume private credential filenames")
            path = relative / name
            metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode):
                directories.append(path.as_posix())
                with open_directory(descriptor, name) as child:
                    if observation(os.fstat(child)) != observation(metadata):
                        raise ValueError("report source directory changed before capture")
                    visit(child, path, depth + 1)
            elif stat.S_ISREG(metadata.st_mode):
                raw = read_bytes_confined(root, root / path, expected_root_identity=root_identity)
                if observation(os.stat(name, dir_fd=descriptor, follow_symlinks=False)) != observation(metadata):
                    raise ValueError("report source file changed during capture")
                total += len(raw)
                if total > 64 * 1024 * 1024:
                    raise ValueError("report source total byte ceiling exceeded")
                files[path.as_posix()] = raw
                identities[path.as_posix()] = observation(metadata)
            else:
                raise ValueError("report source requires real directories and regular files, no symlinks")
        if names != names_in(descriptor, len(names)) or observation(os.fstat(descriptor)) != observation(before):
            raise ValueError("report source directory changed during capture")

    with anchored_parent(root) as parent:
        if parent is None:
            raise ValueError("report requires a real source root")
        with open_directory(parent, root.name) as descriptor:
            current = os.fstat(descriptor)
            if (current.st_dev, current.st_ino) != root_identity:
                raise ValueError("report source root changed after admission")
            visit(descriptor, Path("."), 0)
    present = _presence(root)
    manifest = {path: hashlib.sha256(raw).hexdigest() for path, raw in files.items()}
    manifest["@directory-inventory"] = hashlib.sha256(json.dumps(sorted(directories)).encode()).hexdigest()
    manifest["@informational-output-presence"] = hashlib.sha256(
        json.dumps(present, sort_keys=True).encode()
    ).hexdigest()
    return ReportInputs(
        MappingProxyType(files),
        tuple(directories),
        MappingProxyType(identities),
        MappingProxyType(present),
        MappingProxyType(manifest),
    )
