"""Fail-closed preflight for state-changing publication operations."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def publishing_preflight(
    repo_root: Path,
    project_name: str,
    payload_paths: Sequence[Path],
    credential_sources: Mapping[str, str],
) -> dict[str, object]:
    """Validate a public payload and return a redacted, exact manifest.

    The result contains credential *sources* only; secret values are never
    accepted by this API and therefore cannot leak into logs or receipts.
    """
    root = repo_root.resolve()
    if project_name not in PUBLIC_PROJECT_NAMES:
        raise ValueError(f"publishing refuses local-only or unknown project: {project_name}")
    project_root = (root / "projects" / project_name).resolve()
    if not project_root.is_dir():
        raise ValueError(f"public project does not exist: {project_name}")

    manifest: list[dict[str, object]] = []
    for path in payload_paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"publishing payload is outside canonical project tree: {resolved}") from exc
        if not resolved.is_file():
            raise ValueError(f"publishing payload does not exist: {resolved}")
        manifest.append({"path": relative.as_posix(), "bytes": resolved.stat().st_size})

    allowed_sources = {"cli", "environment", "missing", "not-required"}
    redacted_sources = dict(sorted(credential_sources.items()))
    if any(source not in allowed_sources for source in redacted_sources.values()):
        raise ValueError("credential source summary contains an unsupported value")
    return {
        "project": project_name,
        "payload": manifest,
        "credential_sources": redacted_sources,
    }


__all__ = ["publishing_preflight"]
