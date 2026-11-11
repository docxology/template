"""Observed analysis prerequisites for standalone canonical manuscript hydration."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from infrastructure.core.analysis_data_custody import MAX_FILE_BYTES
from infrastructure.core.files.secure_write import hold_confined_directory, read_bytes_confined

HYDRATION_SCRIPT = "scripts/z_generate_manuscript_variables.py"
HYDRATION_STAGE_KEY = f"hydration:{HYDRATION_SCRIPT}"
HYDRATION_INPUT_UNAVAILABLE = "hydration-analysis-input-unavailable"


@dataclass(frozen=True)
class _HydrationPrerequisite:
    artifact: str
    owner_module: str
    parsed_empty: bool = False


_PREREQUISITES = {
    "templates/template_active_inference": _HydrationPrerequisite(
        "output/data/parameter_sweep.csv", "manuscript.variables"
    ),
    "templates/template_code_project": _HydrationPrerequisite(
        "output/data/optimization_results.csv", "template_code_project.core.manuscript_variables", parsed_empty=True
    ),
    "templates/template_gold_refinement": _HydrationPrerequisite(
        "output/data/refinery_results.json", "template_gold_refinement.manuscript_variables"
    ),
    "templates/template_methods_paper": _HydrationPrerequisite(
        "output/data/compiled_plans.json", "template_methods_paper.manuscript_variables", parsed_empty=True
    ),
}
_PREREQUISITES_BY_ARTIFACT = {entry.artifact: entry for entry in _PREREQUISITES.values()}


def _valid_empty_sha256(prerequisite: _HydrationPrerequisite, digest: object) -> bool:
    return digest is None or (
        prerequisite.parsed_empty
        and isinstance(digest, str)
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def supports_hydration_recovery(scope: str) -> bool:
    """Recognize only the reviewed standalone template producers."""
    return scope in _PREREQUISITES


def canonical_hydration_artifact(repo: Path, project: Path, argv: object, stage_key: str) -> str | None:
    root = repo.absolute() / "projects"
    project = project.absolute()
    if (
        stage_key != HYDRATION_STAGE_KEY
        or argv != [str(project / HYDRATION_SCRIPT)]
        or not project.is_relative_to(root)
    ):
        return None
    prerequisite = _PREREQUISITES.get(project.relative_to(root).as_posix())
    return prerequisite.artifact if prerequisite is not None else None


@dataclass(frozen=True)
class _InputSnapshot:
    project_root: Path
    artifact: str
    directories: tuple[tuple[int, int], ...]
    file_identity: tuple[int, int, int, int, int] | None
    sha256: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "artifact": self.artifact,
            "directories": [list(directory) for directory in self.directories],
            "file_identity": list(self.file_identity) if self.file_identity is not None else None,
            "sha256": self.sha256,
        }

    def follows(self, initial: object) -> bool:
        if self.file_identity is not None:
            return _same_json(self.to_dict(), initial)
        # The actual hydration prelude may create a previously absent output
        # directory. All initially present ancestors and the absent target
        # must still agree. The eventual observation holds the full new chain.
        return any(
            _same_json(replace(self, directories=self.directories[:length]).to_dict(), initial)
            for length in range(1, len(self.directories) + 1)
        )


def _same_json(expected: object, actual: object) -> bool:
    # A JSON bool must not satisfy comparison against an integer identity.
    return json.dumps(expected, sort_keys=True) == json.dumps(actual, sort_keys=True)


def _directory_identity(item: os.stat_result) -> tuple[int, int]:
    return item.st_dev, item.st_ino


def _file_identity(item: os.stat_result) -> tuple[int, int, int, int, int]:
    if not stat.S_ISREG(item.st_mode):
        raise ValueError("Hydration prerequisite must be a regular file")
    return item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns


def _stat_at(descriptor: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def capture_hydration_input(
    project: Path, artifact: str, *, prepare_receipt_output: bool = False
) -> _InputSnapshot | None:
    """Observe a real bounded target or its absence through held directory descriptors."""
    if artifact not in _PREREQUISITES_BY_ARTIFACT:
        return None
    project = project.absolute()
    relative = Path(artifact)
    try:
        root_identity = _directory_identity(project.lstat())
        with ExitStack() as stack:
            held = stack.enter_context(hold_confined_directory(project, Path(), expected_root_identity=root_identity))
            held_directories = [held]
            directories = [root_identity]
            parent = Path()
            for name in relative.parts[:-1]:
                item = _stat_at(held.descriptor, name)
                # The controller's own leaf writer needs output even in a
                # pristine project. Establish that ancestor before observing
                # it, while leaving the actual prerequisite tree untouched.
                create = item is None and prepare_receipt_output and name == "output"
                if item is None and not create:
                    if not all(item.matches_path() for item in held_directories):
                        return None
                    if _stat_at(held.descriptor, name) is not None:
                        return None
                    return _InputSnapshot(project, artifact, tuple(directories), None, None)
                parent /= name
                held = stack.enter_context(
                    hold_confined_directory(project, parent, expected_root_identity=root_identity, create=create)
                )
                identity = _directory_identity(os.fstat(held.descriptor))
                if item is not None and (identity != _directory_identity(item) or not stat.S_ISDIR(item.st_mode)):
                    return None
                held_directories.append(held)
                directories.append(identity)
            item = _stat_at(held.descriptor, relative.name)
            if item is None:
                if not all(item.matches_path() for item in held_directories):
                    return None
                if _stat_at(held.descriptor, relative.name) is not None:
                    return None
                return _InputSnapshot(project, artifact, tuple(directories), None, None)
            file_identity = _file_identity(item)
            content = read_bytes_confined(
                project, project / relative, max_bytes=MAX_FILE_BYTES, expected_root_identity=root_identity
            )
            actual = _stat_at(held.descriptor, relative.name)
            if (
                actual is None
                or _file_identity(actual) != file_identity
                or not all(item.matches_path() for item in held_directories)
            ):
                return None
            return _InputSnapshot(
                project, artifact, tuple(directories), file_identity, hashlib.sha256(content).hexdigest()
            )
    except (OSError, ValueError):
        return None


@dataclass(frozen=True)
class HydrationInputObservation:
    """The prerequisite reached by the actual producer, with its exact custody."""

    _snapshot: _InputSnapshot

    @property
    def artifact(self) -> str:
        return self._snapshot.artifact

    @property
    def state(self) -> Literal["missing", "parsed-empty"]:
        return "missing" if self._snapshot.file_identity is None else "parsed-empty"

    def matches_current(self, project_root: Path) -> bool:
        return self._snapshot == capture_hydration_input(project_root, self.artifact)

    def to_dict(self) -> dict[str, object]:
        return {**self._snapshot.to_dict(), "state": self.state}


def _matches_project_error(project: Path, prerequisite: _HydrationPrerequisite, error: FileNotFoundError) -> bool:
    # The producer owns the missing/parsed-empty classification. Only its
    # loaded, physically bound class may nominate the declared prerequisite.
    module = sys.modules.get(prerequisite.owner_module)
    if module is None or type(error).__module__ != prerequisite.owner_module:
        return False
    namespace = vars(module)
    if type(error) is not namespace.get("RequiredAnalysisInputUnavailable"):
        return False
    project = project.absolute()
    source = project / "src" / Path(*prerequisite.owner_module.split(".")).with_suffix(".py")
    path = vars(error).get("path")
    try:
        return (
            namespace.get("__file__") == str(source)
            and source.is_file()
            and source.resolve(strict=True) == source
            and isinstance(path, Path)
            and path == project / prerequisite.artifact
        )
    except (OSError, RuntimeError):
        return False


def observe_hydration_failure(
    project: Path, artifact: str, initial: object, error: FileNotFoundError
) -> HydrationInputObservation | None:
    prerequisite = _PREREQUISITES_BY_ARTIFACT.get(artifact)
    if prerequisite is None or not _matches_project_error(project, prerequisite, error):
        return None
    empty_sha256 = vars(error).get("empty_sha256")
    if not _valid_empty_sha256(prerequisite, empty_sha256):
        return None
    current = capture_hydration_input(project, artifact)
    if current is not None and current.sha256 == empty_sha256 and current.follows(initial):
        return HydrationInputObservation(current)
    return None


def verify_hydration_observation(
    project: Path, artifact: str, initial: object, reported: object
) -> HydrationInputObservation | None:
    current = capture_hydration_input(project, artifact)
    if current is None or not current.follows(initial):
        return None
    observation = HydrationInputObservation(current)
    if observation.state == "parsed-empty" and not _PREREQUISITES_BY_ARTIFACT[artifact].parsed_empty:
        return None
    return observation if _same_json(observation.to_dict(), reported) else None


@dataclass(frozen=True)
class HydrationRecoveryCompletion:
    """Validated original-process identity and its accepted typed observation."""

    observation: HydrationInputObservation
    run_id: str
    stage_key: str
    request_digest: str
    analysis_nonce: str
    worker_pid: int


@dataclass
class HydrationRecoveryEvidence:
    """Optional same-invocation output. Disk receipts cannot populate this holder."""

    completion: HydrationRecoveryCompletion | None = None

    @property
    def observation(self) -> HydrationInputObservation | None:
        return self.completion.observation if self.completion is not None else None
