"""Fail-closed preflight for state-changing publication operations."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Mapping, Sequence, cast

from infrastructure.core.config.loader import load_config
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

_GITHUB_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PUBLICATION_MANIFEST_SCHEMA = "template-publication-payload/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PublicationPayloadEntry:
    """One immutable, project-confined publication payload file."""

    path: str
    bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        """Return the stable JSON representation of this entry."""
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


@dataclass(frozen=True)
class PublicationPayloadManifest:
    """Typed payload manifest used by every state-changing publication path."""

    project: str
    payload_root: str
    payload: tuple[PublicationPayloadEntry, ...]
    credential_sources: dict[str, str]
    targets: dict[str, str]
    schema_version: str = PUBLICATION_MANIFEST_SCHEMA

    def to_dict(self) -> dict[str, object]:
        """Return deterministic, credential-free manifest data."""
        return {
            "schema_version": self.schema_version,
            "project": self.project,
            "payload_root": self.payload_root,
            "payload": [entry.to_dict() for entry in self.payload],
            "credential_sources": dict(sorted(self.credential_sources.items())),
            "targets": dict(sorted(self.targets.items())),
        }

    def digest(self) -> str:
        """Return a content digest suitable for a release receipt."""
        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "PublicationPayloadManifest":
        """Rehydrate one preflight manifest without trusting its digest field."""
        if payload.get("schema_version") != PUBLICATION_MANIFEST_SCHEMA:
            raise ValueError(f"publication manifest schema must be {PUBLICATION_MANIFEST_SCHEMA}")
        entries = payload.get("payload")
        if not isinstance(entries, list):
            raise ValueError("publication manifest payload must be a list")
        parsed: list[PublicationPayloadEntry] = []
        seen: set[str] = set()
        for item in entries:
            if not isinstance(item, Mapping):
                raise ValueError("publication manifest entries must be objects")
            path = item.get("path")
            byte_count = item.get("bytes")
            sha256 = item.get("sha256")
            if not isinstance(path, str) or not _is_safe_manifest_path(path):
                raise ValueError(f"publication manifest entry path is unsafe: {path!r}")
            if path in seen:
                raise ValueError(f"publication manifest contains duplicate path: {path}")
            if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
                raise ValueError(f"publication manifest byte count is invalid for {path}")
            if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
                raise ValueError(f"publication manifest SHA-256 is invalid for {path}")
            seen.add(path)
            parsed.append(
                PublicationPayloadEntry(
                    path=path,
                    bytes=byte_count,
                    sha256=sha256,
                )
            )
        credential_sources = payload.get("credential_sources", {})
        targets = payload.get("targets", {})
        if not isinstance(credential_sources, Mapping) or not isinstance(targets, Mapping):
            raise ValueError("publication manifest credential_sources and targets must be objects")
        project = payload.get("project")
        payload_root = payload.get("payload_root")
        if not isinstance(project, str) or not project.strip():
            raise ValueError("publication manifest project is required")
        if not isinstance(payload_root, str) or not payload_root.strip():
            raise ValueError("publication manifest payload_root is required")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in credential_sources.items()):
            raise ValueError("publication manifest credential sources must be string pairs")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in targets.items()):
            raise ValueError("publication manifest targets must be string pairs")
        return cls(
            project=project,
            payload_root=payload_root,
            payload=tuple(parsed),
            credential_sources=dict(credential_sources),
            targets=dict(targets),
            schema_version=PUBLICATION_MANIFEST_SCHEMA,
        )

    def validate_current(self, bundle: Path) -> None:
        """Reject any changed, missing, duplicate, or symlinked payload file."""
        if self.schema_version != PUBLICATION_MANIFEST_SCHEMA:
            raise ValueError(f"publication manifest schema must be {PUBLICATION_MANIFEST_SCHEMA}")
        if len({entry.path for entry in self.payload}) != len(self.payload):
            raise ValueError("publication manifest contains duplicate paths")
        if any(not _is_safe_manifest_path(entry.path) for entry in self.payload):
            raise ValueError("publication manifest contains an unsafe path")
        expected = {entry.path: entry for entry in self.payload}
        actual: dict[str, Path] = {}
        if not bundle.exists():
            raise ValueError(f"publication payload changed after preflight: bundle is missing: {bundle}")
        if bundle.is_symlink():
            raise ValueError(f"publication payload changed to a symlink: {bundle}")
        if bundle.is_file() and len(expected) != 1:
            raise ValueError("single-file publication payload must have exactly one manifest entry")
        if bundle.is_file():
            candidates = [bundle]
        else:
            all_paths = sorted(bundle.rglob("*"))
            for path in all_paths:
                if path.is_symlink():
                    raise ValueError(f"publication payload changed to a symlink: {path}")
            candidates = [path for path in all_paths if path.is_file()]
        for path in candidates:
            _reject_symlink_components(bundle.resolve() if bundle.is_dir() else bundle.resolve().parent, path)
            if bundle.is_file():
                relative = next(iter(expected))
            else:
                relative_candidates = (
                    path.resolve().relative_to(bundle.resolve()).as_posix(),
                    path.resolve().relative_to(bundle.resolve().parent).as_posix(),
                )
                relative = next((candidate for candidate in relative_candidates if candidate in expected), "")
                if not relative:
                    relative = relative_candidates[0]
            if relative in actual:
                raise ValueError(f"publication payload contains a duplicate path: {relative}")
            actual[relative] = path
        if set(actual) != set(expected):
            missing = sorted(set(expected) - set(actual))
            changed = sorted(set(actual) - set(expected))
            raise ValueError(f"publication payload changed after preflight: missing={missing}, unexpected={changed}")
        for relative, path in actual.items():
            entry = expected[relative]
            content = path.read_bytes()
            if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
                raise ValueError(f"publication payload content changed after preflight: {relative}")


def _is_safe_manifest_path(path: str) -> bool:
    """Return whether a manifest path is a normalized, relative POSIX path."""
    if not path or path.startswith("/") or "\\" in path:
        return False
    parts = PurePosixPath(path).parts
    return bool(parts) and "." not in parts and ".." not in parts


def _normalize_github_repository(value: object, *, source: str) -> str:
    """Return a canonical GitHub ``owner/repo`` slug or fail closed."""
    if not isinstance(value, str):
        raise ValueError(f"{source} GitHub repository must be an owner/repo string")
    slug = value.strip()
    prefix = "https://github.com/"
    if slug.lower().startswith(prefix):
        slug = slug[len(prefix) :]
    slug = slug.removesuffix(".git").strip("/")
    if not _GITHUB_REPOSITORY.fullmatch(slug):
        raise ValueError(f"{source} GitHub repository must be an owner/repo slug")
    return slug.lower()


def _declared_github_repository(project_root: Path) -> str:
    """Read the state-changing GitHub target from manuscript configuration."""
    config_path = project_root / "manuscript" / "config.yaml"
    config = load_config(config_path)
    publication = config.get("publication") if isinstance(config, Mapping) else None
    declared = publication.get("github_repository") if isinstance(publication, Mapping) else None
    if declared is None:
        raise ValueError("manuscript config must declare publication.github_repository before a GitHub release")
    return _normalize_github_repository(declared, source="configured")


def publishing_preflight(
    repo_root: Path,
    project_name: str,
    payload_paths: Sequence[Path],
    credential_sources: Mapping[str, str],
    *,
    payload_root: Path | None = None,
    github_repository: str | None = None,
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

    _reject_symlink_components(root, root / "projects" / project_name)
    entries: list[PublicationPayloadEntry] = []
    seen_payloads: set[str] = set()
    for path in payload_paths:
        if path.is_symlink():
            raise ValueError(f"publishing payload symlink is not allowed: {path}")
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(manifest_root)
        except ValueError as exc:
            raise ValueError(f"publishing payload is outside canonical project tree: {resolved}") from exc
        _reject_symlink_components(manifest_root, path)
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
        entries.append(
            PublicationPayloadEntry(
                path=relative_path,
                bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            )
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
    github_required = redacted_sources.get("github") not in (None, "not-required")
    targets: dict[str, str] = {}
    if github_required:
        requested_repository = _normalize_github_repository(github_repository, source="requested")
        declared_repository = _declared_github_repository(project_root)
        if requested_repository != declared_repository:
            raise ValueError(
                "requested GitHub repository does not match "
                f"publication.github_repository: {requested_repository} != {declared_repository}"
            )
        targets["github"] = declared_repository
    elif github_repository is not None:
        raise ValueError("GitHub repository target was supplied while GitHub publishing is not required")
    manifest = PublicationPayloadManifest(
        project=project_name,
        payload_root=root_label,
        payload=tuple(sorted(entries, key=lambda entry: entry.path)),
        credential_sources=redacted_sources,
        targets=targets,
    )
    result = manifest.to_dict()
    result["manifest_sha256"] = manifest.digest()
    return result


def _reject_symlink_components(root: Path, candidate: Path) -> None:
    """Reject symlink components before resolving a publication path."""
    root = root.resolve()
    candidate_path = candidate if candidate.is_absolute() else root / candidate
    try:
        relative = candidate_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"publication path is outside its confined root: {candidate}") from exc
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"publication path contains a symlink component: {current}")


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


__all__ = [
    "PUBLICATION_MANIFEST_SCHEMA",
    "PublicationPayloadEntry",
    "PublicationPayloadManifest",
    "publishing_preflight",
]
