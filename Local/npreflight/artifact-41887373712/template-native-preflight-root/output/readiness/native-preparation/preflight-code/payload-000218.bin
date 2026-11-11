"""Immutable resolved execution contracts shared by previews and workers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol
from collections.abc import Sequence

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.pipeline.plan_custody import FrozenPlanSources
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    StageContract,
    StageHooks,
    StagePolicy,
    StageSpec,
)
from infrastructure.core.pipeline.outcomes import StageOutcome
from infrastructure.core.pipeline.target_contracts import canonical_target_contract, effective_target_tags

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor

PLAN_SCHEMA_VERSION = 3
_CANONICAL_METHODS = {
    "_run_clean_outputs": None,
    "run_project_tests": "scripts/pipeline/stage_01_test.py",
    "run_infrastructure_tests": "scripts/pipeline/stage_01_test.py",
}


def _admit_target(repo_root: Path, project: str, script: str | None, method: str | None, args: Sequence[str]) -> None:
    """Reject unavailable canonical targets before constructing execution state."""
    from infrastructure.core.files.secure_write import read_bytes_confined
    from infrastructure.core.pipeline.stages import resolve_pipeline_script_path

    if method is not None:
        if method not in _CANONICAL_METHODS:
            raise ValueError(f"Unsupported canonical method target: {method}")
        if args:
            raise ValueError(f"Canonical method target does not accept arguments: {method}")
        script = _CANONICAL_METHODS[method]
    if script is not None:
        selected = script.replace("{project}", project)
        try:
            resolved = resolve_pipeline_script_path(repo_root, selected)
            # Admission retains the lexical boundary: an internal symlink must
            # not silently select a different executable from its declaration.
            read_bytes_confined(repo_root, repo_root / selected)
            if resolved != (repo_root / selected).absolute():
                raise ValueError("target must be a real repository file")
        except (OSError, ValueError) as exc:
            raise ValueError(f"Unavailable canonical script target {selected}: {exc}") from exc


class PlanResolutionContext(Protocol):
    """Read-only inputs needed by the shared plan compiler."""

    config: PipelineConfig

    def _explicit_plan_control(self) -> PipelineControlConfig | None: ...


def resolve_plan_control_config(config: PipelineConfig) -> PipelineControlConfig:
    """Apply the canonical definition, project, CLI, and explicit control policy."""
    sources = FrozenPlanSources.capture(config)
    loaded = sources.control(config)
    sources.verify(config)
    return loaded


@dataclass
class _ReadOnlyResolutionContext:
    config: PipelineConfig
    control: PipelineControlConfig | None

    def _explicit_plan_control(self) -> PipelineControlConfig | None:
        return self.control


def compile_execution_plan(
    config: PipelineConfig,
    control: PipelineControlConfig | None = None,
    *,
    skip_clean: bool | None = None,
    target_stage: str | None = None,
    target_stages: tuple[str, ...] | None = None,
) -> ExecutionPlan:
    """Resolve the current contract without creating an executor or outputs.

    ``control`` supplies an already-resolved control configuration. When omitted,
    the same configuration policy as execution is used. No logging handlers,
    telemetry collectors, checkpoints, or output directories are created.
    """
    context = _ReadOnlyResolutionContext(config, control)
    return resolve_execution_plan(
        context,
        skip_clean=not config.clean if skip_clean is None else skip_clean,
        target_stage=target_stage,
        target_stages=target_stages,
    )


@dataclass(frozen=True)
class PlannedStage:
    key: str
    name: str
    script: str | None
    method: str | None
    arguments: tuple[str, ...]
    dependencies: tuple[str, ...]
    tags: tuple[str, ...]
    contract: StageContract
    hooks: StageHooks
    policy: StagePolicy
    allow_skip: bool

    @property
    def validation_boundary(self) -> bool:
        """Seal evidence at canonical validation regardless of its declared key."""
        return self.key == "validate" or canonical_target_contract(self.script, self.method).validation_boundary

    @property
    def cacheable(self) -> bool:
        """Cleanup, setup, publication, and live effects always execute."""
        from infrastructure.core.runtime.python_binding import is_analysis_capability

        excluded = {"clean", "setup", "live", "llm", "archival", "metadata", "bundle"}
        return (
            not is_analysis_capability(self.key, self.script, self.method)
            and canonical_target_contract(self.script, self.method).cacheable
            and self.key not in {"clean", "setup", "copy", "archival_publication"}
            and not excluded.intersection(self.tags)
            and not (self.policy.require_approval or self.policy.pause_before or self.policy.pause_after)
        )


@dataclass(frozen=True)
class ExecutionPlan:
    project: str
    mode: str
    stages: tuple[PlannedStage, ...]
    source_identity: str
    definition_identity: str
    provenance: str
    run_timeout_seconds: float
    hitl_mode: str = "full-auto"
    smart_pause_action: str = "report"
    schema_version: int = PLAN_SCHEMA_VERSION
    environment_identity: str = ""

    @property
    def expected_stage_keys(self) -> tuple[str, ...]:
        return tuple(stage.key for stage in self.stages)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: object, *, expected_digest: str | None = None) -> ExecutionPlan:
        """Load an exact transported contract without resolving source again."""
        from infrastructure.core.pipeline.plan_serialization import plan_from_payload

        return plan_from_payload(payload, expected_digest=expected_digest)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def admit_targets(self, repo_root: Path) -> None:
        """Check selected executable authority without re-resolving its DAG."""
        for stage in self.stages:
            _admit_target(repo_root, self.project, stage.script, stage.method, stage.arguments)

    def bind(self, executor: PipelineExecutor) -> list[StageSpec]:
        """Bind targets after resolution; executable closures never enter the contract."""
        specs: list[StageSpec] = []
        for stage in self.stages:
            target: Callable[[], bool | StageOutcome]
            if stage.script:

                def invoke(selected: PlannedStage = stage) -> StageOutcome:
                    assert selected.script is not None
                    return executor._run_script(
                        selected.script, *selected.arguments, allow_skip_code=selected.allow_skip
                    )

                target = invoke
            else:
                target = getattr(executor, stage.method or "")
                if not callable(target):
                    raise ValueError(f"Unimplemented method target: {stage.method}")
            specs.append(
                StageSpec(stage.name, target, stage.contract, stage.hooks, stage.key, stage.allow_skip, stage.policy)
            )
        return specs


def resolve_execution_plan(
    executor: PlanResolutionContext,
    *,
    skip_clean: bool,
    target_stage: str | None = None,
    target_stages: tuple[str, ...] | None = None,
) -> ExecutionPlan:
    """Resolve a project's effective DAG once, then select without implicit execution."""
    explicit = executor._explicit_plan_control()
    sources = FrozenPlanSources.capture(executor.config, explicit)
    config = sources.configuration
    path = sources.paths[0]
    control = sources.control(config)
    dag = sources.dag()
    declarations = tuple(dag.sorted_stages())
    declarations = tuple(
        replace(stage, tags=list(effective_target_tags(stage.tags, stage.script, stage.method)))
        for stage in declarations
    )
    identities = {stage.name: stage.key for stage in declarations}
    source_ordinals = {stage.key: index for index, stage in enumerate(declarations, 1)}
    definition_identity = canonical_digest([asdict(stage) for stage in declarations])
    if target_stage is not None and target_stages is not None:
        raise ValueError("Select target_stage or target_stages, not both")
    requested = (target_stage,) if target_stage is not None else target_stages
    if requested is not None:
        if not requested or len(requested) != len(set(requested)):
            raise ValueError("Explicit stage selection must be nonempty and unique")
        selected = [stage for stage in declarations if stage.key in requested or stage.name in requested]
        recognized = {token for stage in selected for token in (stage.key, stage.name)}
        if any(token not in recognized for token in requested):
            raise ValueError(f"Unknown stage selection: {requested}")
        if config.mode == "core" and any({"live", "llm"}.intersection(stage.tags) for stage in selected):
            raise ValueError("Selected stages require explicit --mode live")
    else:
        excluded_tags = set(dag.opt_in_tags) | {"paid"}
        if config.mode == "core":
            excluded_tags.update({"llm", "live"})
        selected = [
            stage
            for stage in declarations
            if not excluded_tags.intersection(stage.tags)
            and not canonical_target_contract(stage.script, stage.method).opt_in
            and not (
                skip_clean and (stage.key == "clean" or canonical_target_contract(stage.script, stage.method).clean)
            )
            and not (
                config.skip_infra
                and (
                    stage.key == "infra_tests"
                    or canonical_target_contract(stage.script, stage.method, stage.args).infrastructure_tests
                )
            )
        ]
    if not selected:
        raise ValueError("Execution plan requires a nonempty selected stage set")
    from infrastructure.core.runtime.python_binding import is_analysis_capability

    for stage in selected:
        _admit_target(config.repo_root, config.project_name, stage.script, stage.method, stage.args)
    if any(is_analysis_capability(stage.key, stage.script, stage.method) for stage in selected):
        from infrastructure.core.analysis_timeout import analysis_run_timeout_seconds
        from infrastructure.core.pipeline.stages import build_stage_subprocess_env
        from infrastructure.core.script_discovery import discover_analysis_scripts

        scripts = discover_analysis_scripts(config.repo_root, config.project_name, project_dir=config.project_dir)
        analysis_run_timeout_seconds(
            len(scripts),
            build_stage_subprocess_env(config.repo_root, config.project_dir, mode=config.mode),
        )
    stages: list[PlannedStage] = []
    for stage in selected:
        assert stage.key is not None
        arguments = tuple(stage.args)
        if stage.script and "--project" not in arguments:
            arguments += ("--project", config.project_name)
        policy = control.stage_policies.get(source_ordinals[stage.key], StagePolicy())
        if control.hitl_mode == "custom" and source_ordinals[stage.key] in control.custom_gate_stages:
            policy = replace(policy, pause_after=True)
        stages.append(
            PlannedStage(
                stage.key,
                stage.name,
                Path(stage.script.replace("{project}", config.project_name)).as_posix() if stage.script else None,
                stage.method,
                arguments,
                tuple(str(identities[name]) for name in stage.depends_on),
                tuple(stage.tags),
                stage.contract,
                stage.hooks,
                policy,
                stage.allow_skip,
            )
        )
    sources.verify(executor.config, executor._explicit_plan_control())
    return ExecutionPlan(
        config.project_name,
        config.mode,
        tuple(stages),
        sources.source_identity,
        definition_identity,
        str(path.relative_to(config.repo_root)) if path.is_relative_to(config.repo_root) else str(path),
        config.run_timeout_seconds,
        control.hitl_mode,
        control.smart_pause_action,
        environment_identity=sources.environment_identity,
    )


__all__ = [
    "ExecutionPlan",
    "PlannedStage",
    "compile_execution_plan",
    "resolve_execution_plan",
    "resolve_plan_control_config",
]
