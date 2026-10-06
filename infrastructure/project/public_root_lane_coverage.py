"""Real in-memory coverage observations, exact source mapping and confined JSON."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from coverage import Coverage
from coverage import files as coverage_files

import infrastructure.core.implementation_custody as custody

SCHEMA = "template-root-lane-coverage-data-v2"


def measurement(root: Path) -> Coverage:
    """Measure the selected SDK package, including outside a checkout or tiny owned Root."""
    return Coverage(data_file=None, config_file=str(root / "pyproject.toml"), source=[], source_pkgs=["infrastructure"])


def capture(measured: Coverage, implementation: dict[str, Any]) -> dict[str, Any]:
    """Serialize actual CoverageData arcs without a caller-controlled SQLite path."""
    package_root = Path(custody.__file__).resolve().parent.parent
    data = measured.get_data()
    if not data.has_arcs():
        raise ValueError("Root lane requires actual branch coverage")
    files = []
    for name in sorted(data.measured_files()):
        path = Path(name).absolute()
        if path.resolve(strict=True) != path or not path.is_relative_to(package_root):
            raise ValueError("Root lane coverage escaped its actual selected SDK source")
        relative = path.relative_to(package_root).as_posix()
        expected = implementation["files"].get("infrastructure/" + relative)
        if path.suffix != ".py" or not isinstance(expected, str) or custody.source_file_digest(path) != expected:
            raise ValueError("Root lane coverage source differs from its authenticated implementation")
        files.append(
            {"path": relative, "source_sha256": expected, "arcs": [list(arc) for arc in data.arcs(name) or []]}
        )
    if not files:
        raise ValueError("Root lane coverage observed no SDK source")
    return {"schema_version": SCHEMA, "files": files}


def merge(measured: Coverage, raw: object, implementation: dict[str, Any]) -> None:
    """Reconstruct actual public source arcs; no pickle or SQLite deserialization."""
    if (
        not isinstance(raw, dict)
        or set(raw) != {"schema_version", "files"}
        or raw["schema_version"] != SCHEMA
        or not isinstance(raw["files"], list)
        or not raw["files"]
    ):
        raise ValueError("Root lane coverage input is missing or unsupported")
    package_root = Path(custody.__file__).resolve().parent.parent
    seen: set[str] = set()
    arcs: dict[str, list[tuple[int, int]]] = {}
    for row in raw["files"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "source_sha256", "arcs"}
            or not isinstance(row["path"], str)
            or row["path"] in seen
            or "\\" in row["path"]
            or "\0" in row["path"]
            or any(part in ("", ".", "..") for part in row["path"].split("/"))
            or not row["path"].endswith(".py")
            or row["source_sha256"] != implementation["files"].get("infrastructure/" + row["path"])
            or not isinstance(row["arcs"], list)
            or any(
                not isinstance(arc, list)
                or len(arc) != 2
                or any(type(line) is not int or abs(line) > 10_000_000 for line in arc)
                for arc in row["arcs"]
            )
        ):
            raise ValueError("Root lane coverage contains foreign, repeated or unbound public source arcs")
        path = package_root / row["path"]
        if path.resolve(strict=True) != path or custody.source_file_digest(path) != row["source_sha256"]:
            raise ValueError("Root lane measured source changed before aggregation")
        seen.add(row["path"])
        arcs[str(path)] = [(arc[0], arc[1]) for arc in row["arcs"]]
    measured.get_data().add_arcs(arcs)


def report(measured: Coverage) -> dict[str, Any]:
    """Call the actual public JSON reporter into memory for canonical atomic writing."""
    stream = io.StringIO()
    with redirect_stdout(stream):
        measured.json_report(outfile="-", pretty_print=True)
    value = json.loads(stream.getvalue())
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict) or not value["files"]:
        raise ValueError("Root lane coverage reporter returned no actual public source")
    # Coverage names files relative to the process working directory when they
    # lie below it and absolute otherwise. Producer workers run inside the
    # measured Root while independent readers may run elsewhere, so key every
    # file canonically by its SDK path ("infrastructure/...") instead.
    package_root = Path(custody.__file__).resolve().parent.parent
    relative_directory = Path(coverage_files.relative_directory())
    canonical: dict[str, Any] = {}
    for name, row in value["files"].items():
        path = Path(name) if Path(name).is_absolute() else relative_directory / name
        if ".." in path.parts or not path.is_relative_to(package_root):
            raise ValueError("Root lane coverage report names a source outside the selected SDK")
        key = "infrastructure/" + path.relative_to(package_root).as_posix()
        if key in canonical:
            raise ValueError("Root lane coverage report repeats a selected SDK source")
        canonical[key] = row
    value["files"] = dict(sorted(canonical.items()))
    return value
