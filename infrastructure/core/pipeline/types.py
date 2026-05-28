"""Pipeline type definitions — dataclasses and named tuples.

Extracted from pipeline.py to reduce file size and allow
other modules to import types without pulling in the full
PipelineExecutor and its heavy dependency chain.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple


@dataclass(frozen=True)
class StageContract:
    """Declarative contract for a pipeline stage.

    Contracts are intentionally metadata-first. They make expected artifacts,
    acceptance criteria, gate policy, and rollback targets explicit without
    moving business logic into the pipeline layer.
    """

    input_artifacts: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()
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

    auto_execute: bool = True
    pause_before: bool = False
    pause_after: bool = False
    require_approval: bool = False
    allow_guidance: bool = True
    timeout_seconds: int = 86400
    auto_proceed_on_timeout: bool = False


@dataclass(frozen=True)
class PipelineControlConfig:
    """Opt-in advisory controls loaded from pipeline YAML and CLI flags."""

    hitl_mode: str = "full-auto"
    smart_pause_action: str = "report"
    custom_gate_stages: tuple[int, ...] = ()
    stage_policies: dict[int, StagePolicy] = field(default_factory=dict)
    stage_policy_fields: dict[int, frozenset[str]] = field(default_factory=dict, repr=False, compare=False)


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
        skip_llm: Whether to skip LLM stages.
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
    skip_llm: bool = False
    resume: bool = False
    hitl_mode: str = "full-auto"
    control: PipelineControlConfig = field(default_factory=PipelineControlConfig)
    total_stages: int = 10

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

    @property
    def is_skipped(self) -> bool:
        """Stage was skipped: not successful and exited with code 0."""
        return not self.success and self.exit_code == 0


class StageSpec(NamedTuple):
    """Specification for a single pipeline stage.

    NamedTuple is intentional: callers unpack (name, func) positionally
    and the pair is logically immutable once defined.
    """

    name: str
    func: Callable[[], bool]
    contract: StageContract = StageContract()
    hooks: StageHooks = StageHooks()
