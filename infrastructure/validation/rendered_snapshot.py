"""Current rendered-input snapshot and validation-report commitments."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import (
    collect_current_artifact_manifest,
    compute_sha256,
    validate_artifact_manifest,
)
from infrastructure.core.project_paths import resolve_project_root, resolve_source_manuscript_dir
from infrastructure.rendering.manuscript_composition import (
    COMPOSITION_RELATIVE_PATH,
    ManuscriptComposition,
    build_manuscript_composition,
    read_manuscript_composition,
)
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.output.artifacts import read_artifact_manifest

VALIDATED_INPUTS_SCHEMA_VERSION = "template-validated-rendered-inputs-v1"

_IMPLEMENTATION_ROOTS = ("infrastructure", "scripts")
_ROOT_CONFIG_PATHS = (".gitignore", ".python-version", "pyproject.toml", "uv.lock")
_CACHE_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "htmlcov",
    }
)
_PROJECT_EXCLUDED_PARTS = _CACHE_PARTS | {"output", "tests"}
_CONFIG_SUFFIXES = frozenset({".toml", ".yaml", ".yml"})
_CONFIG_NAMES = frozenset(
    {
        ".python-version",
        ".zenodo.json",
        "CITATION.cff",
        "Dockerfile",
        "codemeta.json",
        "environment.yml",
        "uv.lock",
    }
)
_GENERATED_MANUSCRIPT_NAMES = frozenset(
    {
        "00_00_transmission_begin.md",
        "99_zz_transmission_end.md",
    }
)


class RenderedSnapshotError(ValueError):
    """Raised when current rendered evidence is incomplete or inconsistent."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Fingerprint:
    """Hash and cardinality for a deterministic set of named files."""

    sha256: str
    file_count: int


@dataclass(frozen=True)
class EvidenceFile:
    """Digest-bound evidence file outside the recursive output fingerprint."""

    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ManuscriptConsumption:
    """Canonical source mapped to a hydrated input or actual combined artifact."""

    rendered_path: str
    rendered_sha256: str
    source_path: str | None
    source_sha256: str | None


@dataclass(frozen=True)
class CurrentRenderedSnapshot:
    """Current inputs and outputs that one validation run must commit."""

    project: str
    stage: Fingerprint
    source: Fingerprint
    config: Fingerprint
    output: Fingerprint
    artifact_manifest: EvidenceFile
    composition_manifest: EvidenceFile
    combined_manuscript: EvidenceFile
    consumed_manuscript: tuple[ManuscriptConsumption, ...]

    def validated_inputs_dict(self) -> dict[str, object]:
        """Return the exact deterministic commitment embedded in validation reports."""
        return {
            "schema_version": VALIDATED_INPUTS_SCHEMA_VERSION,
            "project": self.project,
            "fingerprints": {
                "stage": asdict(self.stage),
                "source": asdict(self.source),
                "config": asdict(self.config),
                "output": asdict(self.output),
            },
            "artifact_manifest": asdict(self.artifact_manifest),
            "composition_manifest": asdict(self.composition_manifest),
            "combined_manuscript": asdict(self.combined_manuscript),
            "consumed_manuscript": [asdict(row) for row in self.consumed_manuscript],
        }


@dataclass(frozen=True)
class _FileRecord:
    key: str
    path: Path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _relative_to_permitted(path: Path, permitted: list[Path]) -> str | None:
    """Return *path* relative to the first permitted root that contains it."""
    for allowed in permitted:
        try:
            return path.relative_to(allowed).as_posix()
        except ValueError:
            continue
    return None


def _iter_tree_files(
    root: Path,
    *,
    repo_root: Path,
    excluded_parts: frozenset[str] = _PROJECT_EXCLUDED_PARTS,
    extra_root: Path | None = None,
) -> Iterator[_FileRecord]:
    """Walk files while following only confined, acyclic symlinks.

    Confinement means the repository, plus ``extra_root`` when one is given.

    ``extra_root`` exists for projects that are symlinked into the repository
    rather than stored inside it. A private sidecar checkout linked in at
    ``projects/working/<name>`` resolves outside ``repo_root``, and refusing it
    made the entire tree unreadable even though that tree is precisely what the
    snapshot was asked to describe. Callers pass the project root they are
    already walking, so the guard still rejects a symlink escaping BOTH the
    repository and the declared project, which is the case it exists for.

    The boundary is never widened by default: a caller that declares no extra
    root gets the repository-only behavior unchanged.

    Args:
        root: Directory to walk.
        repo_root: Repository the snapshot claims to describe.
        excluded_parts: Path components to skip.
        extra_root: An additional permitted containment root, or None.
    """
    root = root.absolute()
    repository = repo_root.resolve()
    permitted = [repository]
    if extra_root is not None:
        permitted.append(extra_root.resolve())
    if not root.exists():
        return

    def visit(display_dir: Path, actual_dir: Path, ancestors: frozenset[Path]) -> Iterator[_FileRecord]:
        resolved_dir = actual_dir.resolve(strict=True)
        if not any(_is_relative_to(resolved_dir, allowed) for allowed in permitted):
            raise RenderedSnapshotError("SOURCE_SYMLINK_ESCAPE", f"source directory escapes repository: {display_dir}")
        if resolved_dir in ancestors:
            raise RenderedSnapshotError("SOURCE_SYMLINK_CYCLE", f"source symlink cycle: {display_dir}")
        try:
            children = sorted(actual_dir.iterdir(), key=lambda child: child.name)
        except OSError as exc:
            raise RenderedSnapshotError("SOURCE_UNREADABLE", f"cannot read {display_dir}: {exc}") from exc
        next_ancestors = ancestors | {resolved_dir}
        for child in children:
            display = display_dir / child.name
            if child.name in excluded_parts:
                continue
            try:
                if child.is_symlink():
                    target = child.resolve(strict=True)
                    target_key = _relative_to_permitted(target, permitted)
                    if target_key is None:
                        raise RenderedSnapshotError(
                            "SOURCE_SYMLINK_ESCAPE",
                            f"source symlink escapes repository: {display}",
                        )
                    if target.is_dir():
                        try:
                            display_key = display.absolute().relative_to(repo_root.absolute()).as_posix()
                        except ValueError as exc:
                            raise RenderedSnapshotError(
                                "SOURCE_SYMLINK_ESCAPE",
                                f"source symlink display path escapes repository: {display}",
                            ) from exc
                        for nested in visit(display, target, next_ancestors):
                            yield _FileRecord(
                                f"{nested.key} @symlink={display_key}->{target_key}",
                                nested.path,
                            )
                    elif target.is_file():
                        yield _FileRecord(f"{display.as_posix()} -> {target_key}", target)
                    else:
                        raise RenderedSnapshotError(
                            "SOURCE_SYMLINK_INVALID",
                            f"source symlink is not a file or directory: {display}",
                        )
                elif child.is_dir():
                    yield from visit(display, child, next_ancestors)
                elif child.is_file():
                    yield _FileRecord(display.as_posix(), child)
            except OSError as exc:
                raise RenderedSnapshotError("SOURCE_UNREADABLE", f"cannot inspect {display}: {exc}") from exc

    yield from visit(root, root, frozenset())


def _relative_record(record: _FileRecord, root: Path) -> _FileRecord:
    prefix = root.absolute().as_posix().rstrip("/") + "/"
    return _FileRecord(record.key.removeprefix(prefix), record.path)


def _repository_root_for(path: Path, fallback: Path) -> Path:
    """Find the nearest Git worktree for *path*, including nested checkouts."""
    candidate = path.resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / ".git").exists():
            return directory
        if directory == fallback.resolve():
            break
    return fallback


def _cached_paths(repo_root: Path) -> set[Path] | None:
    """Return cached paths for one worktree, independent of global Git helpers."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [
                "git",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedcache=false",
                "-C",
                str(repo_root),
                "ls-files",
                "--cached",
                "-z",
            ],
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return {(repo_root / raw.decode("utf-8")).absolute() for raw in completed.stdout.split(b"\0") if raw}


def _cached_records(records: Iterable[_FileRecord], repo_root: Path) -> list[_FileRecord]:
    """Keep files cached by their nearest Git worktree, including nested repos."""
    candidates = list(records)
    by_root: dict[Path, list[_FileRecord]] = {}
    for record in candidates:
        root = _repository_root_for(record.path, repo_root)
        by_root.setdefault(root, []).append(record)
    cached_by_root = {root: _cached_paths(root) for root in by_root}
    if any(paths is None for paths in cached_by_root.values()):
        return candidates
    return [
        record
        for root, grouped in by_root.items()
        for record in grouped
        if record.path.resolve() in (cached_by_root[root] or set())
    ]


def _fingerprint(records: Iterable[_FileRecord]) -> Fingerprint:
    normalized = sorted(records, key=lambda record: record.key)
    digest = hashlib.sha256()
    for record in normalized:
        digest.update(record.key.encode())
        digest.update(b"\0")
        digest.update(compute_sha256(record.path).encode())
        digest.update(b"\n")
    return Fingerprint(digest.hexdigest(), len(normalized))


def _stage_records(repo_root: Path) -> list[_FileRecord]:
    records: list[_FileRecord] = []
    for relative in _IMPLEMENTATION_ROOTS:
        stage_root = repo_root / relative
        records.extend(
            _relative_record(record, repo_root)
            for record in _iter_tree_files(
                stage_root,
                repo_root=repo_root,
                excluded_parts=_CACHE_PARTS,
            )
        )
    cached = _cached_records(records, repo_root)
    if not cached:
        raise RenderedSnapshotError("STAGE_SOURCE_MISSING", "no cached stage implementation files found")
    return cached


def _is_config_path(path: str) -> bool:
    candidate = Path(path.split(" -> ", maxsplit=1)[0])
    name = candidate.name
    return (
        candidate.suffix.lower() in _CONFIG_SUFFIXES
        or name in _CONFIG_NAMES
        or name.startswith("requirements")
        or "config" in name.lower()
    )


def _project_records(repo_root: Path, project_root: Path) -> tuple[list[_FileRecord], list[_FileRecord]]:
    source: list[_FileRecord] = []
    config: list[_FileRecord] = []
    manuscript_root = resolve_source_manuscript_dir(project_root).absolute()
    # The project tree is what this snapshot describes, so the project root is a
    # permitted containment root even when the project is symlinked in from
    # outside the repository. The stage-implementation walk keeps the
    # repository-only boundary: stage code must live in the repository.
    for raw_record in _iter_tree_files(project_root, repo_root=repo_root, extra_root=project_root):
        record = _relative_record(raw_record, project_root)
        candidate = Path(record.key.split(" -> ", maxsplit=1)[0])
        if candidate.parts and candidate.parts[0] == "docs":
            display = project_root / candidate
            if not _is_relative_to(display.absolute(), manuscript_root):
                continue
        if candidate.name in {"AGENTS.md", "README.md", "SYNTAX.md", "TO-DO.md", "TODO.md"}:
            continue
        (config if _is_config_path(record.key) else source).append(record)
    for relative in _ROOT_CONFIG_PATHS:
        path = repo_root / relative
        if path.is_file():
            config.append(_FileRecord(f"@root/{relative}", path))
    source = _cached_records(source, repo_root)
    config = _cached_records(config, repo_root)
    if not source:
        raise RenderedSnapshotError("PROJECT_SOURCE_MISSING", "no cached project source files found")
    if not config:
        raise RenderedSnapshotError("PROJECT_CONFIG_MISSING", "no cached project configuration files found")
    return source, config


def _evidence_file(project_root: Path, path: Path) -> EvidenceFile:
    try:
        relative = path.resolve().relative_to(project_root.resolve()).as_posix()
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("EVIDENCE_PATH_ESCAPE", f"evidence path escapes project: {path}") from exc
    return EvidenceFile(relative, path.stat().st_size, compute_sha256(path))


def _output_records(project_root: Path) -> tuple[list[_FileRecord], EvidenceFile]:
    output_dir = project_root / "output"
    manifest_path = output_dir / "reports" / "artifact_manifest.json"
    try:
        stored = read_artifact_manifest(manifest_path)
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_MISSING", "artifact manifest is missing") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", f"cannot read artifact manifest: {exc}") from exc
    validation = validate_artifact_manifest(stored, project_dir=project_root)
    if validation.issues:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", "; ".join(validation.issues))
    try:
        current = collect_current_artifact_manifest(output_dir)
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("OUTPUT_TREE_INVALID", str(exc)) from exc
    if current.issues:
        raise RenderedSnapshotError("OUTPUT_TREE_INVALID", "; ".join(current.issues))
    current_by_path = {entry.path: entry for entry in current.entries}
    stored_by_path = {entry.path: entry for entry in stored.entries}
    if len(stored_by_path) != len(stored.entries):
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", "artifact manifest has duplicate paths")
    stored_paths = set(stored_by_path)
    current_paths = set(current_by_path)
    if stored_paths != current_paths:
        missing = sorted(current_paths - stored_paths)
        extra = sorted(stored_paths - current_paths)
        details = []
        if missing:
            details.append("unattested stable output: " + ", ".join(missing))
        if extra:
            details.append("manifest-only output: " + ", ".join(extra))
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INCOMPLETE", "; ".join(details))
    stale = sorted(
        path
        for path in current_paths
        if stored_by_path[path].size_bytes != current_by_path[path].size_bytes
        or stored_by_path[path].sha256 != current_by_path[path].sha256
    )
    if stale:
        raise RenderedSnapshotError(
            "ARTIFACT_MANIFEST_INVALID",
            "artifact manifest has stale hashes: " + ", ".join(stale),
        )
    if not current_by_path:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_EMPTY", "stable output tree is empty")
    records = [_FileRecord(path, project_root / path) for path in sorted(current_by_path)]
    return records, _evidence_file(project_root, manifest_path)


def _validate_composition(
    project_root: Path,
    project: str,
    rendered_inputs: list[Path],
) -> tuple[ManuscriptComposition, EvidenceFile, EvidenceFile]:
    path = project_root / COMPOSITION_RELATIVE_PATH
    try:
        stored = read_manuscript_composition(path)
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("COMPOSITION_MISSING", "render-boundary composition evidence is missing") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("COMPOSITION_INVALID", f"cannot read composition evidence: {exc}") from exc
    if stored.project != project:
        raise RenderedSnapshotError("COMPOSITION_INVALID", f"composition project must be {project}")
    combined_path = project_root / stored.combined_path
    try:
        current = build_manuscript_composition(project_root, project, rendered_inputs, combined_path)
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("COMPOSITION_INVALID", str(exc)) from exc
    if stored != current:
        raise RenderedSnapshotError(
            "COMPOSITION_DRIFT",
            "ordered render inputs or tracked combined Markdown changed after composition",
        )
    return stored, _evidence_file(project_root, path), _evidence_file(project_root, combined_path)


def _manuscript_consumption(
    project_root: Path,
    project: str,
) -> tuple[tuple[ManuscriptConsumption, ...], EvidenceFile, EvidenceFile]:
    source_root = resolve_source_manuscript_dir(project_root)
    source_paths = discover_manuscript_files(source_root)
    source_by_relative = {path.relative_to(source_root).as_posix(): path for path in source_paths}
    if not source_by_relative:
        raise RenderedSnapshotError("MANUSCRIPT_SOURCE_MISSING", "no canonical manuscript inputs discovered")
    hydrated_root = project_root / "output" / "manuscript"
    hydrated_paths = discover_manuscript_files(hydrated_root) if hydrated_root.is_dir() else []
    rendered_inputs = hydrated_paths or source_paths
    composition, composition_file, combined_file = _validate_composition(project_root, project, rendered_inputs)

    rows: list[ManuscriptConsumption] = []
    if hydrated_paths:
        hydrated_relative = {path.relative_to(hydrated_root).as_posix() for path in hydrated_paths}
        missing = sorted(set(source_by_relative) - hydrated_relative)
        if missing:
            raise RenderedSnapshotError(
                "UNCONSUMED_MANUSCRIPT",
                "canonical inputs absent from hydrated render tree: " + ", ".join(missing),
            )
        for path in hydrated_paths:
            relative = path.relative_to(hydrated_root).as_posix()
            source = source_by_relative.get(relative)
            if source is None and path.name not in _GENERATED_MANUSCRIPT_NAMES:
                raise RenderedSnapshotError(
                    "UNDECLARED_RENDERED_MANUSCRIPT",
                    f"hydrated manuscript has no canonical source: {relative}",
                )
            rows.append(
                ManuscriptConsumption(
                    rendered_path=path.relative_to(project_root).as_posix(),
                    rendered_sha256=compute_sha256(path),
                    source_path=source.relative_to(project_root).as_posix() if source else None,
                    source_sha256=compute_sha256(source) if source else None,
                )
            )
    else:
        for source in source_paths:
            rows.append(
                ManuscriptConsumption(
                    rendered_path=composition.combined_path,
                    rendered_sha256=composition.combined_sha256,
                    source_path=source.relative_to(project_root).as_posix(),
                    source_sha256=compute_sha256(source),
                )
            )
    return tuple(rows), composition_file, combined_file


def build_current_rendered_snapshot(repo_root: Path | str, project: str) -> CurrentRenderedSnapshot:
    """Build the current complete rendered snapshot without reading its validation report."""
    root = Path(repo_root).resolve()
    project_root = resolve_project_root(root, project)
    source_records, config_records = _project_records(root, project_root)
    output_records, artifact_manifest = _output_records(project_root)
    consumption, composition_manifest, combined_manuscript = _manuscript_consumption(project_root, project)
    return CurrentRenderedSnapshot(
        project=project,
        stage=_fingerprint(_stage_records(root)),
        source=_fingerprint(source_records),
        config=_fingerprint(config_records),
        output=_fingerprint(output_records),
        artifact_manifest=artifact_manifest,
        composition_manifest=composition_manifest,
        combined_manuscript=combined_manuscript,
        consumed_manuscript=consumption,
    )


def validate_green_report_payload(payload: Any, project: str) -> Mapping[str, object]:
    """Validate report check/summary consistency and return validated inputs."""
    if not isinstance(payload, Mapping):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation report must be a mapping")
    checks = payload.get("checks")
    figure_issues = payload.get("figure_issues")
    summary = payload.get("summary")
    if (
        not isinstance(checks, Mapping)
        or not checks
        or not all(isinstance(name, str) and isinstance(result, bool) for name, result in checks.items())
    ):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation checks must be a non-empty bool mapping")
    if not isinstance(figure_issues, list):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation figure_issues must be a list")
    if not isinstance(summary, Mapping):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation summary must be a mapping")
    passed = sum(result is True for result in checks.values())
    failed = sum(result is False for result in checks.values())
    expected = {
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "figure_issues_count": len(figure_issues),
        "all_passed": failed == 0 and not figure_issues,
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise RenderedSnapshotError("VALIDATION_REPORT_INCONSISTENT", "validation summary contradicts checks")
    if expected["all_passed"] is not True:
        raise RenderedSnapshotError("VALIDATION_NOT_GREEN", "validation checks are not fully green")
    validated_inputs = payload.get("validated_inputs")
    if not isinstance(validated_inputs, Mapping):
        raise RenderedSnapshotError(
            "VALIDATION_INPUTS_MISSING",
            "validation report lacks a rendered-input commitment",
        )
    if validated_inputs.get("project") != project:
        raise RenderedSnapshotError("VALIDATION_INPUTS_INVALID", f"validated input project must be {project}")
    return validated_inputs


def read_committed_validation_report(
    repo_root: Path | str,
    project: str,
    current: CurrentRenderedSnapshot,
) -> EvidenceFile:
    """Require an internally green report committed to the exact current snapshot."""
    root = Path(repo_root).resolve()
    project_root = resolve_project_root(root, project)
    path = project_root / "output" / "reports" / "validation_report.json"
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("VALIDATION_REPORT_MISSING", "validation report is missing") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", f"cannot read validation report: {exc}") from exc
    validated_inputs = validate_green_report_payload(payload, project)
    if dict(validated_inputs) != current.validated_inputs_dict():
        raise RenderedSnapshotError(
            "VALIDATION_INPUTS_DRIFT",
            "validation report was not generated for the exact current rendered snapshot",
        )
    return _evidence_file(project_root, path)


def rendered_manuscript_paths(project_root: Path) -> tuple[Path, ...]:
    """Return combined Markdown first, then hydrated-only evidence paths."""
    paths: list[Path] = []
    combined = project_root / "output" / "web" / "_combined_manuscript.md"
    if combined.is_file():
        paths.append(combined)
    hydrated_root = project_root / "output" / "manuscript"
    if hydrated_root.is_dir():
        paths.extend(
            path for path in discover_manuscript_files(hydrated_root) if path.suffix.lower() in {".md", ".rmd"}
        )
    return tuple(dict.fromkeys(paths))


__all__ = [
    "CurrentRenderedSnapshot",
    "EvidenceFile",
    "Fingerprint",
    "ManuscriptConsumption",
    "RenderedSnapshotError",
    "VALIDATED_INPUTS_SCHEMA_VERSION",
    "build_current_rendered_snapshot",
    "read_committed_validation_report",
    "rendered_manuscript_paths",
    "validate_green_report_payload",
]
