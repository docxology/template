"""Pipeline type definitions — dataclasses and named tuples.

Extracted from pipeline.py to reduce file size and allow
other modules to import types without pulling in the full
PipelineExecutor and its heavy dependency chain.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, NamedTuple

from infrastructure.core.pipeline.outcomes import StageOutcome

if TYPE_CHECKING:
    from infrastructure.core.pipeline.incremental import IncrementalConfig


def _default_incremental_config() -> "IncrementalConfig":
    """Build the default (disabled) incremental config.

    Imported lazily to avoid a circular import: ``incremental`` imports
    ``StageContract`` from this module. The default is always feature-OFF, so
    existing pipelines are unaffected.
    """
    from infrastructure.core.pipeline.incremental import IncrementalConfig

    return IncrementalConfig()


@dataclass(frozen=True)
class StageContract:
    """Declarative contract for a pipeline stage.

    Contracts are intentionally metadata-first. They make expected artifacts,
    acceptance criteria, gate policy, and rollback targets explicit without
    moving business logic into the pipeline layer.
    """

    input_artifacts: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()
    mutable_artifacts: tuple[str, ...] = ()
    definition_of_done: str = ""
    failure_code: str = ""
    retry_policy: int = 0
    gate: str | None = None
    rollback_to: str | None = None


@dataclass(frozen=True)
class StageHooks:
    """Explicit hook commands declared by a stage.

    Commands are tuples of argv parts; they are executed with ``shell=False`` by
    :mod:`infrastructure.core.pipeline.hooks`.
    """

    pre_stage: tuple[tuple[str, ...], ...] = ()
    post_stage: tuple[tuple[str, ...], ...] = ()
    on_fail: tuple[tuple[str, ...], ...] = ()
    on_pause: tuple[tuple[str, ...], ...] = ()
    timeout_seconds: int = 30
    run_in_ci: bool = False


@dataclass(frozen=True)
class StagePolicy:
    """Human intervention policy for a single pipeline stage."""

    pause_before: bool = False
    pause_after: bool = False
    require_approval: bool = False
    allow_guidance: bool = True
    timeout_seconds: int = 86400
    auto_proceed_on_timeout: bool = False

    def __post_init__(self) -> None:
        for name in ("pause_before", "pause_after", "require_approval", "allow_guidance", "auto_proceed_on_timeout"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"Stage policy {name} must be a boolean")
        if type(self.timeout_seconds) is not int or self.timeout_seconds <= 0:
            raise ValueError("Stage policy timeout_seconds must be a positive integer")


@dataclass(frozen=True)
class PipelineControlConfig:
    """Opt-in advisory controls loaded from pipeline YAML and CLI flags."""

    hitl_mode: str = "full-auto"
    smart_pause_action: str = "report"
    custom_gate_stages: tuple[int, ...] = ()
    stage_policies: dict[int, StagePolicy] = field(default_factory=dict)
    stage_policy_fields: dict[int, frozenset[str]] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.hitl_mode, str) or self.hitl_mode not in {
            "full-auto",
            "gate-only",
            "checkpoint",
            "custom",
        }:
            raise ValueError("Invalid human intervention mode")
        if not isinstance(self.smart_pause_action, str) or self.smart_pause_action not in {"report", "pause"}:
            raise ValueError("Invalid smart_pause_action")
        if (
            not isinstance(self.custom_gate_stages, tuple)
            or any(type(number) is not int or number <= 0 for number in self.custom_gate_stages)
            or len(set(self.custom_gate_stages)) != len(self.custom_gate_stages)
        ):
            raise ValueError("Custom gate stages must be unique positive integers")
        if not isinstance(self.stage_policies, dict) or any(
            type(number) is not int or number <= 0 or not isinstance(policy, StagePolicy)
            for number, policy in self.stage_policies.items()
        ):
            raise ValueError("Stage policies require positive integer keys and typed policies")


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution.

    Attributes:
        project_name: Name of the project directory (e.g. 'template_code_project').
        repo_root: Absolute path to the repository root.
        projects_dir: Name of the active projects directory relative to repo_root.
            Default 'projects'. Set to a typed subfolder such as
            'projects/working' to run a project that hasn't been promoted to the
            active pool yet.
        clean: Whether to clean outputs before running.
        skip_infra: Whether to skip infrastructure tests.
        resume: Whether to resume from the last checkpoint.
        hitl_mode: Lightweight human-in-the-loop policy. Defaults to
            ``full-auto`` so existing pipelines keep running without pauses.
        total_stages: Total number of pipeline stages (for ETA display).
    """

    project_name: str
    repo_root: Path
    projects_dir: str = "projects"
    clean: bool = True
    skip_infra: bool = False
    resume: bool = False
    hitl_mode: str = "full-auto"
    control: PipelineControlConfig = field(default_factory=PipelineControlConfig)
    incremental: "IncrementalConfig" = field(default_factory=lambda: _default_incremental_config())
    pipeline_path: Path | None = None
    total_stages: int = 10
    mode: str = "core"
    run_timeout_seconds: float = 14400.0
    shared_infrastructure: bool = False

    def __post_init__(self) -> None:
        import math

        if self.mode not in {"core", "live"}:
            raise ValueError("mode must be core or live")
        for name in ("clean", "skip_infra", "resume", "shared_infrastructure"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be an exact boolean")
        if (
            isinstance(self.run_timeout_seconds, bool)
            or not math.isfinite(self.run_timeout_seconds)
            or self.run_timeout_seconds <= 0
        ):
            raise ValueError("run_timeout_seconds must be positive and finite")

    @property
    def project_dir(self) -> Path:
        """Absolute path to this project's source directory.

        Resolves ``projects_dir`` relative to ``repo_root``, then appends
        ``project_name``.  This is the single canonical path used throughout
        the pipeline instead of repeating ``repo_root / 'projects' / project_name``.

        Examples:
            PipelineConfig(project_name='myproj', repo_root=Path('/repo'))
            → /repo/projects/myproj

            PipelineConfig(project_name='myproj', repo_root=Path('/repo'),
                           projects_dir='projects/working')
            → /repo/projects/working/myproj
        """
        return self.repo_root / self.projects_dir / self.project_name

    @property
    def runtime_output_dir(self) -> Path:
        """Separate shared run records from the selected project's deliverables."""
        if not self.shared_infrastructure:
            return self.project_dir / "output"
        relative = Path(self.projects_dir) / self.project_name
        if relative.is_absolute() or any(part in {".", ".."} for part in relative.parts):
            raise ValueError("Shared runtime namespace requires a confined project identity")
        return self.repo_root / "output" / ".pipeline" / "shared_infrastructure" / relative


@dataclass
class PipelineStageResult:
    """Result from a pipeline stage execution."""

    stage_num: int
    stage_name: str
    success: bool
    duration: float
    exit_code: int = 0
    error_message: str = ""
    exception_type: str = ""
    hitl_pause: bool = False
    stage_completed: bool = True
    lessons: tuple[str, ...] = field(default_factory=tuple)
    stage_key: str = ""
    outcome: StageOutcome | None = None
    input_digest: str = ""
    output_digest: str = ""

    @property
    def is_skipped(self) -> bool:
        """Stage was skipped with a classified SKIPPED outcome (never inferred from exit 0)."""
        return self.outcome is not None and self.outcome.status.value == "skipped"


class StageSpec(NamedTuple):
    """Specification for a single pipeline stage.

    NamedTuple is intentional: the specification is logically immutable once
    defined. ``key`` carries the stable machine-facing identity from
    ``pipeline.yaml`` so orchestration does not have to infer lifecycle
    boundaries from a user-facing stage name.
    """

    name: str
    func: Callable[[], bool | StageOutcome]
    contract: StageContract = StageContract()
    hooks: StageHooks = StageHooks()
    key: str | None = None
    allow_skip: bool = False
    policy: StagePolicy | None = None
