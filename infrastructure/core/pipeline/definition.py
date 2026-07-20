"""Deterministic pipeline source resolution for pipeline YAML lookups."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from importlib import resources as importlib_resources
from pathlib import Path

__all__ = [
    "PipelinePurpose",
    "PipelineSourceOrigin",
    "PipelineSource",
    "PipelineSourceResolutionError",
    "resolve_pipeline_source",
]


class PipelinePurpose(str, Enum):
    """Why a pipeline definition is being resolved."""

    EXECUTION = "execution"
    METHODS = "methods"


class PipelineSourceOrigin(str, Enum):
    """Typed provenance for the winning resolution branch."""

    EXPLICIT = "explicit"
    PROJECT_METHODS = "project_methods"
    PROJECT_PIPELINE = "project_pipeline"
    REPOSITORY_PIPELINE = "repository_pipeline"
    PACKAGE_DATA = "package_data"


@dataclass(frozen=True, slots=True)
class PipelineSource:
    """Resolved pipeline source with stable provenance."""

    path: Path
    origin: PipelineSourceOrigin
    purpose: PipelinePurpose


class PipelineSourceResolutionError(RuntimeError):
    """Raised when no valid pipeline source can be resolved."""


def _normalize_root(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _resolve_against(base: Path, candidate: Path | str) -> Path:
    raw_path = Path(candidate).expanduser()
    resolved = raw_path if raw_path.is_absolute() else base / raw_path
    return resolved.resolve(strict=False)


def _package_pipeline_path() -> Path | None:
    resource = importlib_resources.files("infrastructure.core.pipeline").joinpath("pipeline.yaml")
    # Wheels are installed unpacked by supported Python installers, so the
    # package Traversable's stable string form is a real filesystem path. Do
    # not use ``os.fspath``: the Traversable protocol intentionally does not
    # promise ``PathLike`` and strict typing must remain valid on Python 3.10.
    path = Path(str(resource)).resolve(strict=False)
    return path if path.is_file() else None


def _candidate_paths(
    *,
    repo_root: Path,
    project_root: Path | None,
    purpose: PipelinePurpose,
) -> tuple[tuple[PipelineSourceOrigin, Path], ...]:
    candidates: list[tuple[PipelineSourceOrigin, Path]] = []
    if project_root is not None and purpose is PipelinePurpose.METHODS:
        candidates.append((PipelineSourceOrigin.PROJECT_METHODS, project_root / "methods_pipeline.yaml"))
    if project_root is not None:
        candidates.append((PipelineSourceOrigin.PROJECT_PIPELINE, project_root / "pipeline.yaml"))
    candidates.append(
        (
            PipelineSourceOrigin.REPOSITORY_PIPELINE,
            repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml",
        )
    )
    package_path = _package_pipeline_path()
    if package_path is not None:
        candidates.append((PipelineSourceOrigin.PACKAGE_DATA, package_path))
    return tuple(candidates)


def _raise_invalid_candidate(origin: PipelineSourceOrigin, path: Path, *, purpose: PipelinePurpose) -> None:
    raise PipelineSourceResolutionError(
        f"Resolved {origin.value} pipeline candidate is not a file for purpose {purpose.value!r}: {path}"
    )


def resolve_pipeline_source(
    repo_root: Path | str,
    project_root: Path | str | None = None,
    explicit_path: Path | str | None = None,
    purpose: PipelinePurpose = PipelinePurpose.EXECUTION,
) -> PipelineSource:
    """Resolve the pipeline definition source using stable precedence."""

    normalized_repo_root = _normalize_root(repo_root)
    normalized_project_root = None if project_root is None else _resolve_against(normalized_repo_root, project_root)
    normalized_purpose = purpose if isinstance(purpose, PipelinePurpose) else PipelinePurpose(purpose)

    if explicit_path is not None:
        resolved_explicit = _resolve_against(normalized_repo_root, explicit_path)
        if not resolved_explicit.exists():
            raise PipelineSourceResolutionError(
                f"Explicit pipeline path does not exist for purpose {normalized_purpose.value!r}: "
                f"{resolved_explicit} (repo_root={normalized_repo_root})"
            )
        if not resolved_explicit.is_file():
            _raise_invalid_candidate(
                PipelineSourceOrigin.EXPLICIT,
                resolved_explicit,
                purpose=normalized_purpose,
            )
        return PipelineSource(
            path=resolved_explicit,
            origin=PipelineSourceOrigin.EXPLICIT,
            purpose=normalized_purpose,
        )

    checked: list[str] = []
    for origin, candidate_path in _candidate_paths(
        repo_root=normalized_repo_root,
        project_root=normalized_project_root,
        purpose=normalized_purpose,
    ):
        if not candidate_path.exists():
            checked.append(f"{origin.value}: {candidate_path} (missing)")
            continue
        if not candidate_path.is_file():
            _raise_invalid_candidate(origin, candidate_path, purpose=normalized_purpose)
        return PipelineSource(
            path=candidate_path,
            origin=origin,
            purpose=normalized_purpose,
        )

    checked_text = "\n".join(f"- {entry}" for entry in checked) or "- no candidates generated"
    raise PipelineSourceResolutionError(
        "Unable to resolve a pipeline source.\n"
        f"purpose={normalized_purpose.value}\n"
        f"repo_root={normalized_repo_root}\n"
        f"project_root={normalized_project_root}\n"
        f"checked:\n{checked_text}"
    )
