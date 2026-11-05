"""Executable artifact prerequisites and immutable consumed-input custody."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from infrastructure.core.pipeline.artifacts import declared_output_paths
from infrastructure.core.pipeline.fingerprints import canonical_digest, paths_digest, tree_records
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult, StageContract, StageSpec

REPOSITORY_INPUT_ROOTS = frozenset(
    {
        "infrastructure",
        "scripts",
        "tests",
        "docs",
        "fonds",
        "rules",
        "tools",
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        "pipeline.yaml",
    }
)


class InputContractError(ValueError):
    """Required consumed inputs are missing, unsafe, or changed."""


class OutputContractError(ValueError):
    """A successful producer did not establish its declared artifacts."""


def declared_input_paths(repo_root: Path, project_dir: Path, contract: StageContract) -> tuple[Path, ...]:
    """Resolve root infrastructure and project inputs without treating both as outputs."""
    slug = (
        project_dir.absolute().relative_to((repo_root / "projects").absolute()).as_posix()
        if project_dir.absolute().is_relative_to((repo_root / "projects").absolute())
        else project_dir.name
    )
    paths: list[Path] = []
    for raw in contract.input_artifacts:
        rendered = Path(raw.replace("{project}", slug).rstrip("/"))
        if not rendered.parts or rendered.is_absolute() or ".." in rendered.parts:
            raise InputContractError("Consumed inputs must use confined relative paths")
        if rendered.parts[0] == "projects":
            candidate = repo_root / rendered
            if not candidate.absolute().is_relative_to(project_dir.absolute()):
                raise InputContractError("Cross-project consumed inputs require an explicit custody contract")
        elif rendered.parts[0] in REPOSITORY_INPUT_ROOTS or str(rendered).startswith(f"output/{slug}"):
            candidate = repo_root / rendered
        else:
            candidate = project_dir / rendered
        assert_safe_path(candidate, repo_root=repo_root, project_dir=project_dir)
        paths.append(candidate)
    return tuple(paths)


def assert_safe_path(path: Path, *, repo_root: Path, project_dir: Path) -> None:
    """Reject symlink substitutions beneath the selected canonical roots."""
    anchors = (project_dir.absolute(), repo_root.absolute())
    anchor = next((root for root in anchors if path.absolute().is_relative_to(root)), None)
    if anchor is None:
        raise InputContractError("Artifact path is outside the declared roots")
    current = anchor
    for part in path.absolute().relative_to(anchor).parts:
        current /= part
        if current.is_symlink():
            raise InputContractError(f"Artifact custody refuses symlink: {current}")


@dataclass(frozen=True)
class InputSnapshot:
    paths: tuple[Path, ...]
    mutable_paths: frozenset[Path]
    output_root: Path
    digest: str
    members: dict[str, str] = field(default_factory=dict)

    def diagnostic_members(self) -> dict[str, str]:
        """Return the original observation's bounded, non-authoritative diagnostics."""
        return dict(self.members)

    def _observation(self) -> tuple[str, dict[str, str]]:
        """Derive the unchanged complete identity and diagnostics from one census."""
        rows: list[tuple[int, str]] = []
        members: dict[str, str] = {}
        for index, path in enumerate(self.paths):
            if path.absolute() in self.mutable_paths:
                continue
            source = not path.absolute().is_relative_to(self.output_root)
            excluded = self.mutable_paths | (frozenset({self.output_root}) if source else frozenset())
            records = tree_records(path, source=source, excluded_roots=excluded, output_roots=(self.output_root,))
            # paths_digest((path,)) uses path.parent as its lexical base. Keep
            # that identity while sharing this boundary's actual file census.
            rows.append((len(rows), canonical_digest([(path.name, records)])))
            for relative, kind, digest in records:
                if len(members) < 512:
                    members[f"{index}:{path.name if relative == '.' else relative}"] = f"{kind}:{digest}"
        return canonical_digest(rows), members

    def current_digest(self) -> str:
        return self._observation()[0]


def capture_inputs(config: PipelineConfig, contract: StageContract) -> InputSnapshot:
    """Require prerequisites, preserving explicit in-place producer declarations."""
    return capture_inputs_at(config.repo_root, config.project_dir, contract)


def capture_inputs_at(repo_root: Path, project_dir: Path, contract: StageContract) -> InputSnapshot:
    """Use the same confined artifact contract in controllers and fresh workers."""
    paths = declared_input_paths(repo_root, project_dir, contract)
    mutable = frozenset(
        path.absolute()
        for path in declared_output_paths(
            repo_root, project_dir, StageContract(output_artifacts=contract.mutable_artifacts)
        )
    )
    outputs = declared_output_paths(repo_root, project_dir, contract)
    if any(not any(path.is_relative_to(output) for output in outputs) for path in mutable):
        raise InputContractError("Mutable artifacts must be within declared producer outputs")
    for path in paths:
        if not path.exists() and path.absolute() not in mutable:
            raise InputContractError(f"Required input artifact is missing: {path}")
    snapshot = InputSnapshot(paths, mutable, (project_dir / "output").absolute(), "")
    digest, members = snapshot._observation()
    return replace(snapshot, digest=digest, members=members)


def require_outputs(config: PipelineConfig, contract: StageContract) -> str:
    """Validate every declared producer output before checkpoint or cache recording."""
    paths = declared_output_paths(config.repo_root, config.project_dir, contract)
    for path in paths:
        assert_safe_path(path, repo_root=config.repo_root, project_dir=config.project_dir)
        if not path.exists():
            raise OutputContractError(f"Required output artifact is missing: {path}")
    return paths_digest(paths, stable_output=True, output_roots=((config.project_dir / "output").absolute(),))


def contract_failure(stage_num: int, spec: StageSpec, exc: ValueError) -> PipelineStageResult:
    """Map custody failure to a visible typed outcome without executing a child."""
    status = StageStatus.BLOCKED if isinstance(exc, InputContractError) else StageStatus.FAILED
    code = 75 if status == StageStatus.BLOCKED else 1
    key = spec.key or spec.name
    return PipelineStageResult(
        stage_num,
        spec.name,
        False,
        0.0,
        code,
        str(exc),
        stage_completed=False,
        stage_key=key,
        outcome=StageOutcome(key, status, child_exit_code=None, diagnostic=str(exc)),
    )


def validate_completion(
    config: PipelineConfig, spec: StageSpec, result: PipelineStageResult, snapshot: InputSnapshot
) -> PipelineStageResult | None:
    """Recheck consumed bytes and required artifacts for completed children."""
    result.input_digest = snapshot.digest
    if not result.stage_completed or not (result.success or result.hitl_pause):
        return None
    try:
        if snapshot.current_digest() != snapshot.digest:
            raise InputContractError("Consumed input contents changed during execution")
        if result.outcome is None or not (result.outcome.child_exit_code == 2 and result.outcome.receipt_validated):
            result.output_digest = require_outputs(config, spec.contract)
    except (OSError, ValueError) as exc:
        error = exc if isinstance(exc, InputContractError) else OutputContractError(str(exc))
        return contract_failure(result.stage_num, spec, error)
    return None
