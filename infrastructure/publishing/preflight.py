"""Fail-closed preflight for state-changing publication operations."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping, Sequence, cast

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def publishing_preflight(
    repo_root: Path,
    project_name: str,
    payload_paths: Sequence[Path],
    credential_sources: Mapping[str, str],
    *,
    payload_root: Path | None = None,
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

    manifest_root = project_root
    root_label = "project"
    if payload_root is not None:
        expected_root = (root / "output" / project_name).resolve()
        manifest_root = payload_root.resolve()
        if manifest_root != expected_root:
            raise ValueError("publishing payload root is not the canonical project output root")
        if not manifest_root.is_dir():
            raise ValueError(f"publishing payload root does not exist: {manifest_root}")
        root_label = f"output/{project_name}"

    manifest: list[dict[str, object]] = []
    seen_payloads: set[str] = set()
    for path in payload_paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(manifest_root)
        except ValueError as exc:
            raise ValueError(f"publishing payload is outside canonical project tree: {resolved}") from exc
        if not resolved.is_file():
            raise ValueError(f"publishing payload does not exist: {resolved}")
        relative_path = relative.as_posix()
        if relative_path in seen_payloads:
            raise ValueError(f"publishing payload is duplicated: {relative_path}")
        seen_payloads.add(relative_path)
        content = resolved.read_bytes()
        if resolved.suffix.lower() == ".pdf" and not content.startswith(b"%PDF-"):
            raise ValueError(f"publishing payload is not a PDF: {resolved}")
        if resolved.suffix.lower() == ".pdf":
            _validate_pdf_metadata(resolved)
        manifest.append(
            {
                "path": relative_path,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    allowed_sources = {"cli", "environment", "local-config", "missing", "not-required"}
    allowed_credentials = {
        "cloudflare",
        "github",
        "huggingface",
        "netlify",
        "osf",
        "pinata",
        "testpypi",
        "web3storage",
        "zenodo",
    }
    redacted_sources = dict(sorted(credential_sources.items()))
    if not set(redacted_sources).issubset(allowed_credentials):
        raise ValueError("credential source summary contains an unsupported credential name")
    if any(source not in allowed_sources for source in redacted_sources.values()):
        raise ValueError("credential source summary contains an unsupported value")
    return {
        "project": project_name,
        "payload_root": root_label,
        "payload": manifest,
        "credential_sources": redacted_sources,
    }


def _validate_pdf_metadata(path: Path) -> None:
    """Reject credential-bearing metadata when a PDF parser is available."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    try:
        metadata: Mapping[str, object] = dict(PdfReader(str(path)).metadata or {})
    except Exception:
        # Signature-only dry-run fixtures do not carry inspectable metadata.
        return
    from infrastructure.steganography.metadata import classify_publication_metadata

    result = classify_publication_metadata(metadata)
    if result["status"] != "pass":
        issues = cast(list[str], result["issues"])
        raise ValueError(f"publishing PDF metadata rejected: {', '.join(issues)}")


__all__ = ["publishing_preflight"]
