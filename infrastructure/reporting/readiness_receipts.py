"""Source-bound acceptance profiles; receipts do not establish execution provenance."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from infrastructure.core.pipeline.fingerprints import canonical_digest, paths_digest, tree_records
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.artifacts._inventory import collect_stable_output_inventory
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import PUBLIC_ROOT_FILES, SnapshotReader

SCHEMA_VERSION = "template-release-readiness-receipt-v2"
_READINESS_SOURCE_METADATA_NAMES = frozenset({".DS_Store", ".git"})
AcceptanceState = Literal["pass", "fail", "blocked", "unknown"]


@dataclass(frozen=True)
class GateEvidence:
    """One required acceptance, with an explicit failure/absence boundary."""

    id: str
    state: AcceptanceState
    profile: str = "candidate"
    artifact: str | None = None
    diagnostic: str = ""


def aggregate_state(states: tuple[AcceptanceState, ...]) -> AcceptanceState:
    """Invalid evidence dominates blockers, then missing evidence."""
    for state in ("fail", "blocked", "unknown"):
        if state in states:
            return state
    return "pass" if states else "unknown"


@dataclass(frozen=True)
class ReadinessEvidence:
    """Candidate acceptance and published acceptance are separate profiles."""

    available: bool = False
    current: bool = False
    source: str | None = None
    source_fingerprint: str | None = None
    candidate_state: AcceptanceState = "unknown"
    released_state: AcceptanceState = "unknown"
    gates: tuple[GateEvidence, ...] = ()
    issues: tuple[str, ...] = ("required acceptance receipt not supplied",)
    verified_tag: str | None = None
    published_version: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize local custody without granting production authorization."""
        return asdict(self)


def project_source_identity(repo_root: Path, project: str) -> str:
    """Bind source/config/locks apart from exact declared runtime locations."""
    root = repo_root / "projects" / project
    return paths_digest((root,), source=True, excluded_roots=_project_runtime_roots(root))


def _project_runtime_roots(root: Path) -> frozenset[Path]:
    """Keep project-root test/build controls distinct from nested authored inputs."""
    roots = {
        root / name
        for name in ("output", ".hypothesis", ".coverage", ".coverage.project", "coverage_project.json", "htmlcov")
    }
    roots.update(path for path in (root / "src").glob("*.egg-info"))
    return frozenset(path.absolute() for path in roots)


def deliverable_identity(repo_root: Path, project: str, *, path_admission: Callable[[Path], None] | None = None) -> str:
    """Use the existing shippable inventory and reject unavailable Git custody."""
    root = repo_root / "projects" / project / "output"
    if not root.exists():
        return canonical_digest([])
    inventory = collect_stable_output_inventory(root)
    if inventory.issues:
        raise ValueError("cannot establish public deliverable inventory")
    if path_admission is not None:
        for path in inventory.files:
            path_admission(path)
    return canonical_digest(
        [
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(read_bytes_confined(repo_root, path, max_bytes=64 * 1024 * 1024)).hexdigest(),
            )
            for path in inventory.files
        ]
    )


def _public_roots(repo_root: Path) -> tuple[tuple[Path, ...], frozenset[Path]]:
    roots = [repo_root / name for name in ("infrastructure", "scripts", "tests", "docs", ".github")]
    projects = [repo_root / "projects" / name for name in PUBLIC_PROJECT_NAMES]
    roots.extend(projects)
    roots.extend(
        repo_root / name for name in ("fonds/templates", "rules/templates", "tools/templates", ".agents/skills")
    )
    roots.extend(repo_root / name for name in sorted(PUBLIC_ROOT_FILES) if (repo_root / name).is_file())
    excluded = {path for project in projects for path in _project_runtime_roots(project)}
    excluded.update(
        repo_root / "infrastructure/steganography/kmyth" / relative
        for relative in ("bin", "lib", "obj", "logger/obj", "utils/obj")
    )
    return tuple(roots), frozenset(excluded)


def public_source_paths(repo_root: Path, project: str | None = None) -> tuple[Path, ...]:
    """Inventory exact declared public source without private/control roots."""
    roots, excluded = _public_roots(repo_root)
    if project is not None:
        if project not in PUBLIC_PROJECT_NAMES:
            raise ValueError("source scope is not a canonical public project")
        roots = (repo_root / "projects" / project,)
    paths = set()
    for root in roots:
        for relative, kind, _ in tree_records(
            root, source=True, excluded_roots=excluded, excluded_names=_READINESS_SOURCE_METADATA_NAMES
        ):
            if kind == "file":
                paths.add(root if relative == "." else root / relative)
    return tuple(sorted(paths))


def public_resource_source_paths(repo_root: Path, dependency: str) -> tuple[Path, ...]:
    """Use the public source boundary for a declared cross-root resource tree."""
    if dependency not in {"fonds/templates", "rules/templates", "tools/templates", "infrastructure"}:
        raise ValueError("resource scope is not a declared public dependency")
    root = repo_root / dependency
    if not root.is_dir():
        raise FileNotFoundError("declared public resource tree is unavailable")
    _, excluded = _public_roots(repo_root)
    reader = SnapshotReader(repo_root)

    def admit(path: Path) -> None:
        reader.public_path(
            path.relative_to(repo_root).as_posix() + ("/.reference-directory-policy" if path == root else "")
        )

    return tuple(
        root if relative == "." else root / relative
        for relative, kind, _ in tree_records(
            root,
            source=True,
            excluded_roots=excluded,
            excluded_names=_READINESS_SOURCE_METADATA_NAMES,
            path_admission=admit,
        )
        if kind == "file"
    )


def source_fingerprint(repo_root: Path, *, path_admission: Callable[[Path], None] | None = None) -> str:
    """Bind public source and stable deliverables; never traverse private mirrors."""
    repo_root = repo_root.resolve()
    roots, excluded = _public_roots(repo_root)
    return canonical_digest(
        {
            "sources": paths_digest(
                roots,
                source=True,
                excluded_roots=excluded,
                excluded_names=_READINESS_SOURCE_METADATA_NAMES,
                path_admission=path_admission,
            ),
            "deliverables": {
                name: deliverable_identity(repo_root, name, path_admission=path_admission)
                for name in PUBLIC_PROJECT_NAMES
            },
        }
    )


def collect_readiness_evidence(
    repo_root: Path,
    receipt_path: Path | None,
) -> ReadinessEvidence:
    """Validate required scope, semantics, versions, and exact source/artifact custody.

    Execution provenance remains the caller's responsibility. This does not
    contact providers or invent publication/model/process acceptance.
    """
    from infrastructure.reporting.release_readiness_profile import collect_profile
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    return collect_profile(repo_root.resolve(), receipt_path, SnapshotReader(repo_root.resolve()))
