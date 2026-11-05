"""Current canonical local-provider graph, shared by release preparation."""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def provider_dependencies(root: Path, metadata: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Resolve held metadata's local providers against the exact public roster."""
    root = root.absolute()
    locations = {root: "root", **{root / "projects" / scope: scope for scope in PUBLIC_PROJECT_NAMES}}

    def normalize(value: str) -> str:
        return re.sub(r"[-_.]+", "-", value).lower()

    if set(metadata) != {"root", *PUBLIC_PROJECT_NAMES}:
        raise ValueError("provider metadata must contain the exact canonical roster")
    edges = {}
    for scope, payload in metadata.items():
        base = root if scope == "root" else root / "projects" / scope
        providers = []
        for package, declaration in payload.get("tool", {}).get("uv", {}).get("sources", {}).items():
            if not isinstance(declaration, dict) or "path" not in declaration:
                raise ValueError("release preparation requires explicit local provider declarations")
            location = Path(os.path.abspath(base / declaration["path"]))
            provider = locations.get(location)
            if provider is None or normalize(metadata[provider]["project"]["name"]) != normalize(package):
                raise ValueError("local provider is outside the canonical public package roster")
            providers.append(provider)
        edges[scope] = sorted(set(providers))
    return edges


def provider_order(root: Path, metadata: dict[str, dict[str, Any]]) -> list[str]:
    """Order the complete held graph, refusing cycles."""
    edges = provider_dependencies(root, metadata)
    order: list[str] = []
    visiting: set[str] = set()

    def visit(scope: str) -> None:
        if scope in visiting:
            raise ValueError("release provider graph contains a cycle")
        if scope not in order:
            visiting.add(scope)
            for provider in edges[scope]:
                visit(provider)
            visiting.remove(scope)
            order.append(scope)

    for scope in ("root", *PUBLIC_PROJECT_NAMES):
        visit(scope)
    return order


def current_provider_graph(root: Path) -> dict[str, list[str]]:
    """Read today's confined metadata; no proposed version transaction is needed."""
    metadata = {}
    for scope in ("root", *PUBLIC_PROJECT_NAMES):
        relative = "pyproject.toml" if scope == "root" else f"projects/{scope}/pyproject.toml"
        metadata[scope] = tomllib.loads(read_bytes_confined(root, root / relative, max_bytes=1024 * 1024).decode())
    provider_order(root, metadata)
    return provider_dependencies(root, metadata)


__all__ = ["current_provider_graph", "provider_dependencies", "provider_order"]
