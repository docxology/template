"""Source-owned canonical public package dependency declarations and closure."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from packaging.requirements import Requirement as PackageRequirement
from packaging.utils import canonicalize_name

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def package_metadata(root: Path, scope: str, reader: SnapshotReader) -> dict:
    """Read one canonical public pyproject from the shared immutable observation."""
    if scope != "root" and scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("local dependency selection is outside canonical public scope")
    relative = "pyproject.toml" if scope == "root" else f"projects/{scope}/pyproject.toml"
    return tomllib.loads(reader.read(relative).content.decode())


def declared_local_dependencies(
    root: Path, scope: str, *, reader: SnapshotReader | None = None
) -> dict[str, PackageRequirement]:
    """Admit only declared dependencies resolving to exact canonical public scopes."""
    root = root.absolute()
    reader = reader or SnapshotReader(root)
    base = root if scope == "root" else root / "projects" / scope
    metadata = package_metadata(root, scope, reader)
    dependencies = metadata.get("project", {}).get("dependencies", [])
    sources = metadata.get("tool", {}).get("uv", {}).get("sources", {})
    if not isinstance(dependencies, list) or not isinstance(sources, dict):
        raise ValueError("local dependency declarations must be source-owned lists and mappings")
    result = {}
    for dependency in dependencies:
        if not isinstance(dependency, str):
            raise ValueError("package requirement must be a string")
        declaration = PackageRequirement(dependency)
        key = canonicalize_name(declaration.name)
        matches = [value for name, value in sources.items() if canonicalize_name(name) == key]
        if len(matches) > 1:
            raise ValueError("local provider declaration must have one unambiguous source")
        entry: object = matches[0] if matches else {}
        if not isinstance(entry, dict):
            raise ValueError("local provider declaration must have one unambiguous source")
        if "path" not in entry:
            continue
        if not isinstance(entry["path"], str):
            raise ValueError("local provider path must be a string")
        location = Path(os.path.abspath(base / entry["path"]))
        candidates = {root: "root", **{root / "projects" / name: name for name in PUBLIC_PROJECT_NAMES}}
        provider = candidates.get(location)
        if provider is None:
            raise ValueError("local provider path is outside canonical public scope")
        identity = package_metadata(root, provider, reader).get("project", {}).get("name")
        if not isinstance(identity, str) or canonicalize_name(identity) != key or provider in result:
            raise ValueError("local provider package identity is ambiguous or mismatched")
        result[provider] = declaration
    return result


def local_dependency_closure(root: Path, scope: str, *, reader: SnapshotReader | None = None) -> tuple[str, ...]:
    """Resolve each source-owned transitive provider once and refuse dependency cycles."""
    reader = reader or SnapshotReader(root)
    ordered: list[str] = []
    visiting: set[str] = set()

    def visit(selected: str) -> None:
        if selected in visiting:
            raise ValueError("canonical local provider dependency cycle")
        visiting.add(selected)
        for provider in declared_local_dependencies(root, selected, reader=reader):
            if provider not in ordered:
                visit(provider)
                ordered.append(provider)
        visiting.remove(selected)

    visit(scope)
    return tuple(ordered)


__all__ = ["package_metadata", "declared_local_dependencies", "local_dependency_closure"]
