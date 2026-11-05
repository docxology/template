"""Native archive structure and exact public source/export parity."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import re
import tomllib
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.archive_members import bounded_members
from infrastructure.reporting.readiness_receipts import public_resource_source_paths, public_source_paths
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _embedded_export(
    content: bytes,
    scope: str,
    manifest: dict[str, Any],
    expected: dict[str, str],
    dependencies: list[str],
) -> None:
    """Only the bound public producer schema may accompany exported source."""
    try:
        embedded = json.loads(content)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("embedded export metadata is not valid public JSON") from error
    keys = {
        "schema_version",
        "source_project",
        "exported_project",
        "source_commit",
        "infrastructure_version",
        "resource_dependencies",
        "files",
    }
    commit = manifest.get("source_commit")
    if (
        scope == "root"
        or not isinstance(embedded, dict)
        or set(embedded) != keys
        or type(embedded.get("schema_version")) is not int
        or embedded["schema_version"] != 2
        or embedded.get("source_project") != scope
        or embedded.get("exported_project") != Path(scope).name
        or not isinstance(commit, str)
        or re.fullmatch("[0-9a-f]{40}", commit) is None
        or embedded.get("source_commit") != commit
        or embedded.get("infrastructure_version") != manifest.get("platform_version")
        or embedded.get("resource_dependencies") != dependencies
        or embedded.get("files") != expected
    ):
        raise ValueError("embedded export metadata differs from its public source/version binding")


def validate_wheel_members(archive: zipfile.ZipFile, imported_modules: list[str]) -> None:
    """Bind imports to a complete WHEEL/RECORD inventory, including exact bytes."""
    names = bounded_members(archive)
    wheel = [name for name in names if name.endswith(".dist-info/WHEEL")]
    record = [name for name in names if name.endswith(".dist-info/RECORD")]
    if len(wheel) != 1 or len(record) != 1 or b"Wheel-Version: 1.0" not in archive.read(wheel[0]):
        raise ValueError("installed artifact is not a complete wheel")
    rows = list(csv.reader(StringIO(archive.read(record[0]).decode())))
    if any(len(row) != 3 for row in rows) or {row[0] for row in rows} != names or len(rows) != len(names):
        raise ValueError("wheel RECORD omits or invents members")
    for name, digest, size in rows:
        if name == record[0]:
            if digest or size:
                raise ValueError("wheel RECORD must omit its self-referential digest")
            continue
        content = archive.read(name)
        expected = "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
        if digest != expected or size != str(len(content)):
            raise ValueError("wheel RECORD differs from its exact member bytes")
    for module in imported_modules:
        path = module.replace(".", "/")
        if not any(
            name in {f"{path}.py", f"{path}/__init__.py"} or name.startswith(path + "/") and name.endswith(".py")
            for name in names
        ):
            raise ValueError("claimed imported module does not belong to the installed wheel")


def validate_wheel_source(scope: str, archive: zipfile.ZipFile, reader: SnapshotReader) -> None:
    """Bind the complete Root SDK or exact project implementation/resources."""
    base = reader.root if scope == "root" else reader.root / "projects" / scope
    source_root = base / "infrastructure" if scope == "root" else base / "src"
    sources = public_source_paths(reader.root, None if scope == "root" else scope)
    names = bounded_members(archive)
    expected: dict[str, str] = {}
    python_files: list[tuple[str, ...]] = []
    licenses: dict[str, bytes] = {}
    package_dirs: dict[str, str] = {}
    if scope != "root" and (base / "pyproject.toml").is_file():
        metadata = tomllib.loads(reader.read(f"projects/{scope}/pyproject.toml").content.decode())
        declared = metadata.get("tool", {}).get("setuptools", {}).get("package-dir", {})
        if not isinstance(declared, dict):
            raise ValueError("wheel package directory declaration must be a mapping")
        for package, directory in declared.items():
            if (
                not isinstance(package, str)
                or package
                and not all(part.isidentifier() for part in package.split("."))
                or not isinstance(directory, str)
                or "\\" in directory
                or directory != Path(directory).as_posix()
                or not directory.startswith("src")
                or any(part in {".", "..", ""} or part.startswith(".") for part in directory.split("/"))
                or Path(directory).parts[0] != "src"
            ):
                raise ValueError("wheel package directories must name exact public source subtrees")
            package_dirs[package] = directory.removeprefix("src").removeprefix("/")
    for path in sources:
        if path.is_relative_to(source_root):
            relative = path.relative_to(source_root).as_posix()
            candidates: tuple[str, ...] = (
                (f"infrastructure/{relative}",) if scope == "root" else (relative, f"src/{relative}")
            )
            mappings = [
                (package, directory)
                for package, directory in package_dirs.items()
                if not directory or relative.startswith(directory + "/")
            ]
            if mappings:
                depth = max(len(Path(directory).parts) for _, directory in mappings)
                mapped = set()
                for package, directory in mappings:
                    if len(Path(directory).parts) == depth:
                        suffix = relative.removeprefix(directory + "/") if directory else relative
                        mapped.add((package.replace(".", "/") + "/" + suffix).removeprefix("/"))
                if len(mapped) != 1:
                    raise ValueError("wheel source has ambiguous declared package locations")
                candidates = tuple(mapped)
            source = reader.read(path.relative_to(reader.root).as_posix())
            for candidate in candidates:
                expected[candidate] = source.sha256
            if path.suffix == ".py":
                python_files.append(candidates)
        elif path.parent == base and re.fullmatch(
            r"(?:LICENSE|LICENCE|COPYING|NOTICE)(?:[.-][A-Za-z0-9_.-]+)?", path.name
        ):
            licenses[path.name] = reader.read(path.relative_to(reader.root).as_posix()).content
    if not python_files:
        raise ValueError("installed acceptance has no current Python implementation")
    required_resources: set[str] = set()
    if scope == "templates/template_literature_meta_analysis":
        required_resources.add("template_literature_meta_analysis/deep_research/fixtures/recorded_report.json")
    if scope == "templates/template_pools_rules_tools":
        config = tomllib.loads(reader.read(f"projects/{scope}/export.toml").content.decode())
        dependencies = config.get("template_export", {}).get("cross_root_dependencies")
        if dependencies != ["fonds/templates", "rules/templates", "tools/templates"]:
            raise ValueError("installed pools resources differ from their exact public declaration")
        for dependency in dependencies:
            root = reader.root / dependency
            for path in public_resource_source_paths(reader.root, dependency):
                source = reader.read(path.relative_to(reader.root).as_posix())
                relative = path.relative_to(root).as_posix()
                name = f"template_pools_rules_tools/_template_resources/{dependency}/{relative}"
                expected[name] = source.sha256
                required_resources.add(name)
    for candidates in python_files:
        members = [name for name in candidates if name in names]
        if len(members) != 1:
            raise ValueError("wheel implementation differs from current exact source bytes")
    if not required_resources <= names:
        raise ValueError("installed wheel omitted declared public resource members")
    if scope == "root" and not set(expected).issubset(names):
        raise ValueError("root wheel omitted current exact SDK source members")
    metadata_roots = {Path(name).parts[0] for name in names if Path(name).parts[0].endswith(".dist-info")}
    if len(metadata_roots) != 1:
        raise ValueError("wheel must contain one distribution metadata root")
    metadata_root = next(iter(metadata_roots))
    generated = {
        f"{metadata_root}/{name}" for name in ("METADATA", "WHEEL", "RECORD", "top_level.txt", "entry_points.txt")
    }
    for name in names:
        if name in generated:
            continue
        parts = Path(name).parts
        if len(parts) == 3 and parts[:2] == (metadata_root, "licenses") and parts[2] in licenses:
            if archive.read(name) != licenses[parts[2]]:
                raise ValueError("wheel license bytes differ from current public source")
            continue
        if name not in expected or hashlib.sha256(archive.read(name)).hexdigest() != expected[name]:
            raise ValueError(f"wheel contains unbound or private member bytes outside current exact source: {name}")


def validate_source_archive(scope: str, manifest: dict[str, Any], bundle: bytes, reader: SnapshotReader) -> None:
    """Require the complete current source and declared bundled public resources."""
    base = reader.root if scope == "root" else reader.root / "projects" / scope
    expected: dict[str, str] = {}
    exact_sizes: dict[str, int] = {}
    dependencies: list[str] = []
    for path in public_source_paths(reader.root, None if scope == "root" else scope):
        source = reader.read(path.relative_to(reader.root).as_posix())
        relative = path.relative_to(base).as_posix()
        expected[relative] = source.sha256
        exact_sizes[relative] = len(source.content)
    if scope != "root" and (base / "export.toml").is_file():
        config = tomllib.loads(reader.read(f"projects/{scope}/export.toml").content.decode())
        dependencies = config.get("template_export", {}).get("cross_root_dependencies", [])
        allowed = {"fonds/templates", "rules/templates", "tools/templates", "infrastructure"}
        if (
            not isinstance(dependencies, list)
            or any(not isinstance(value, str) for value in dependencies)
            or len(dependencies) != len(set(dependencies))
            or set(dependencies) - allowed
        ):
            raise ValueError("export resource declarations are invalid")
        for dependency in dependencies:
            root = reader.root / dependency
            for path in public_resource_source_paths(reader.root, dependency):
                source = reader.read(path.relative_to(reader.root).as_posix())
                relative = f"_template_resources/{dependency}/{path.relative_to(root).as_posix()}"
                expected[relative] = source.sha256
                exact_sizes[relative] = len(source.content)
    if not expected:
        raise ValueError("export has no source files")
    with zipfile.ZipFile(BytesIO(bundle)) as archive:
        source_names = {
            item.filename
            for item in archive.infolist()
            if not item.is_dir() and item.filename != ".template-export.json"
        }
        if source_names != set(expected) or manifest.get("files") != expected:
            raise ValueError("export archive/manifest omitted or invented source members")
        if ".template-export.json" in archive.namelist():
            metadata_size = archive.getinfo(".template-export.json").file_size
            if not 0 <= metadata_size <= 64 * 1024 * 1024:
                raise ValueError("embedded export metadata exceeds the bounded byte ceiling")
            exact_sizes[".template-export.json"] = metadata_size
        names = bounded_members(archive, exact_sizes=exact_sizes)
        if ".template-export.json" in names:
            _embedded_export(archive.read(".template-export.json"), scope, manifest, expected, dependencies)
            names.remove(".template-export.json")
        if names != set(expected) or manifest.get("files") != expected:
            raise ValueError("export archive/manifest omitted or invented source members")
        if any(hashlib.sha256(archive.read(name)).hexdigest() != expected[name] for name in names):
            raise ValueError("export archive member bytes differ from the current exact source")
