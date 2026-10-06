"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from infrastructure.core.runtime.checkpoint import CheckpointManager
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.errors import (
    PIPELINE_STAGE_FAILED,
)
from infrastructure.core.pipeline.resume import PipelineResumeMixin
from infrastructure.core.pipeline.stages import PipelineStageMixin
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    PipelineStageResult,
    StageSpec,
)
from infrastructure.core.pipeline._stage_execution import execute_stage
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
from infrastructure.core.telemetry import TelemetryCollector
from infrastructure.core.pipeline.observability import (
    setup_log_file_handler,
    close_log_file_handler,
    initialize_telemetry,
    write_pause_recommendations_report,
    write_run_lessons_report,
)
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.plan import ExecutionPlan, resolve_execution_plan, resolve_plan_control_config
from infrastructure.core.pipeline.plan_custody import configuration_control_identity
from infrastructure.core.pipeline.execution_custody import execution_guard_result
from infrastructure.core.pipeline.artifact_contracts import (
    InputSnapshot,
    capture_inputs,
    contract_failure,
    validate_completion,
    InputContractError,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from infrastructure.core.pipeline.dag import PipelineDAG
    from infrastructure.core.pipeline.plugins import PluginStageDeclaration


class PipelineExecutor(PipelineStageMixin, PipelineResumeMixin):
    """Execute research project pipeline stages with owned log handlers.

    Construction acquires handlers. Execution releases them in a finally block.
    Preview-only and direct-stage callers must call ``close()`` when finished;
    closing repeatedly is safe and leaves unrelated logger handlers untouched.
    """

    def __init__(self, config: PipelineConfig) -> None:
        """Initialize pipeline executor.

        Sets up per-project log file that captures all pipeline execution logs
        (Python + subprocess output). Log file is located at:
        projects/{project_name}/output/logs/pipeline.log

        Note: construction performs lightweight file I/O — it creates the log directory
        (``mkdir -p``), opens the log file handler, and reads ``pipeline.yaml`` to
        configure telemetry reporters.  These operations are intentional: the executor
        cannot function without its log file, and the YAML load is a simple path probe
        (existence check + YAML parse) on a small config file.  They are not deferred
        because there is no meaningful "lazy" moment for a log handler — it must be
        ready before the first stage runs.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.control_config = self._resolve_control_config()
        from copy import deepcopy

        self._initial_control_config = self.control_config
        self._initial_control_snapshot = deepcopy(self.control_config)
        self.checkpoint_manager = CheckpointManager(
            project_name=config.project_name,
            repo_root=config.repo_root,
            project_dir=config.project_dir,
            checkpoint_dir=config.runtime_output_dir / ".checkpoints",
            output_dir=config.project_dir / "output",
        )

        # Log file: projects/{project_name}/output/logs/pipeline.log
        # Recreated by _setup_log_file_handler after clean stage deletes it.
        self.log_file = config.runtime_output_dir / "logs" / "pipeline.log"
        self._log_handler: logging.FileHandler | None = None
        self._module_log_handler: logging.FileHandler | None = None
        self._module_log_level: int | None = None

        # Dispose owned logging if telemetry initialization refuses configuration.
        self._telemetry: TelemetryCollector | None = None
        try:
            self._setup_log_file_handler()
            initialize_telemetry(self)
        except BaseException:
            self.close()
            raise

        # Incremental (content-hash) skip manifest. Stays ``None`` unless the
        # opt-in feature is enabled and a run loads it. DEFAULT-OFF.
        from infrastructure.core.pipeline.incremental import HashManifest

        self._incremental_manifest: HashManifest | None = None
        self._artifact_manifest_sealed = False
        self._artifact_manifest_boundary_keys: frozenset[str] = frozenset()
        self._artifact_manifest_boundary_names: frozenset[str] = frozenset()
        self.run_id = uuid.uuid4().hex
        self.execution_plan: ExecutionPlan | None = None
        self._plan_digest = ""
        self._active_stage_key = ""
        self._last_child_outcome: StageOutcome | None = None
        self._run_deadline = 0.0
        self._remaining_run_seconds = config.run_timeout_seconds
        self._stage_deadline = 0.0
        self._preview_plan: ExecutionPlan | None = None
        self._preview_selection: tuple[object, ...] | None = None
        self._active_stage_admission: dict[str, object] | None = None

    def _explicit_plan_control(self) -> PipelineControlConfig | None:
        """Retain deliberate caller overrides; cached YAML is never authority."""
        if (
            self.control_config is not self._initial_control_config
            or self.control_config != self._initial_control_snapshot
        ):
            return self.control_config
        return None

    def run_result(self, results: list[PipelineStageResult]) -> RunResult:
        """Judge completion against the compiled expected stage set."""
        expected = self.execution_plan.expected_stage_keys if self.execution_plan else ()
        return RunResult.from_results(results, expected)

    def _setup_log_file_handler(self) -> None:
        """Restore logging after output cleanup."""
        setup_log_file_handler(self)

    def close(self) -> None:
        """Release owned log handlers; repeated calls preserve unrelated handlers."""
        close_log_file_handler(self)

    def _resolve_pipeline_yaml(self) -> Path:
        """Return the pipeline YAML path to use: project-specific if it exists, else default."""
        return resolve_pipeline_source(
            self.config.repo_root,
            self.config.project_dir,
            explicit_path=self.config.pipeline_path,
            purpose=PipelinePurpose.EXECUTION,
        ).path

    def _default_pipeline_yaml(self) -> Path:
        """Return the repository DAG, or the identical installed package data."""
        return resolve_pipeline_source(
            self.config.repo_root,
            purpose=PipelinePurpose.EXECUTION,
        ).path

    def _project_pipeline_yaml(self) -> Path:
        return Path(self.config.project_dir) / "pipeline.yaml"

    def _resolve_control_config(self) -> PipelineControlConfig:
        """Resolve advisory control config from YAML plus explicit config."""
        return resolve_plan_control_config(self.config)

    # -- Stage list construction ---------------------------------------------

    def _build_stage_list(self, skip_clean: bool) -> list[StageSpec]:
        """Build canonical stage list by loading the declarative pipeline DAG.

        Resolution order:
        1. ``projects/{name}/pipeline.yaml`` (project-specific override)
        2. repository ``infrastructure/core/pipeline/pipeline.yaml``
        3. the same ``pipeline.yaml`` installed as package data

        Mode and explicit clean/verification selection leave the YAML source unchanged.
        """
        self.execution_plan = resolve_execution_plan(self, skip_clean=skip_clean)
        self._plan_digest = self.execution_plan.digest
        self.checkpoint_manager.expected_plan_digest = self._plan_digest
        self.checkpoint_manager.expected_source_digest = self.execution_plan.source_identity
        self.checkpoint_manager.run_id = self.run_id
        specs = self.execution_plan.bind(self)
        self.config.total_stages = len(specs)
        self._artifact_manifest_boundary_keys = frozenset(
            stage.key for stage in self.execution_plan.stages if stage.validation_boundary
        )
        self._artifact_manifest_boundary_names = frozenset(
            stage.name for stage in self.execution_plan.stages if stage.validation_boundary
        )
        return specs

    def preview_stage_names(self, *, skip_clean: bool | None = None) -> tuple[str, ...]:
        """Return the exact filtered project/plugin execution order without running it."""
        effective_skip_clean = not self.config.clean if skip_clean is None else skip_clean
        specs = self._build_stage_list(skip_clean=effective_skip_clean)
        self._preview_plan = self.execution_plan
        self._preview_selection = self._preview_identity(effective_skip_clean)
        return tuple(stage.name for stage in specs)

    def _preview_identity(self, skip_clean: bool) -> tuple[object, ...]:
        return (skip_clean, configuration_control_identity(self.config, self._explicit_plan_control()))

    # -- Plugin-stage integration (DEFAULT-OFF) ------------------------------

    def _load_plugin_stages(self) -> list[PluginStageDeclaration]:
        """Load validated plugin declarations for this project (``[]`` if none)."""
        from infrastructure.core.pipeline.plugins import load_plugin_stages

        return load_plugin_stages(self.config.project_dir)

    def _merge_plugin_stages_into_dag(self, dag: PipelineDAG) -> None:
        """Merge declared plugin stages into the DAG (no-op when none declared)."""
        from infrastructure.core.pipeline.plugins import merge_plugin_stages

        merge_plugin_stages(dag, self._load_plugin_stages())

    # -- Pipeline execution --------------------------------------------------

    def execute_pipeline(self) -> list[PipelineStageResult]:
        """Execute the core or live contract selected by config.mode."""
        try:
            selection = self._preview_identity(not self.config.clean)
            if self._preview_plan is not None and self._preview_selection == selection:
                return self.execute_plan(self._preview_plan)
            self._build_stage_list(skip_clean=not self.config.clean)
            assert self.execution_plan is not None
            return self.execute_plan(self.execution_plan)
        finally:
            self.close()

    def execute_plan(
        self, plan: ExecutionPlan, *, deadline_monotonic: float | None = None
    ) -> list[PipelineStageResult]:
        """Execute a resolved plan within its budget and any supervising deadline."""
        from infrastructure.core.pipeline.execution_session import execute_resolved_plan

        try:
            if self._log_handler is None:
                self._setup_log_file_handler()
            return execute_resolved_plan(self, plan, deadline_monotonic=deadline_monotonic)
        finally:
            self.close()

    def _run_stage_and_checkpoint(
        self,
        stage_num: int,
        stage_spec: StageSpec,
        results: list[PipelineStageResult],
        pipeline_start: float,
    ) -> PipelineStageResult:
        """Execute or validate reuse, then record the source-bound result."""
        self._remaining_run_seconds = (
            self._run_deadline - time.monotonic() if self._run_deadline else self.config.run_timeout_seconds
        )
        guard = execution_guard_result(
            config=self.config,
            plan=self.execution_plan,
            deadline=self._run_deadline,
            stage_num=stage_num,
            stage_name=stage_spec.name,
            stage_key=stage_spec.key or stage_spec.name,
        )
        if guard is not None:
            results.append(guard)
            return guard
        try:
            snapshot = capture_inputs(self.config, stage_spec.contract)
        except (OSError, ValueError) as exc:
            result = contract_failure(stage_num, stage_spec, InputContractError(str(exc)))
            results.append(result)
            return result
        self._prepare_artifact_manifest_for_stage(stage_spec, results)
        skipped = self._maybe_skip_stage_incremental(stage_num, stage_spec)
        if skipped is not None:
            guard = validate_completion(self.config, stage_spec, skipped, snapshot)
            if guard is not None:
                results.append(guard)
                return guard
            results.append(skipped)
            return skipped

        result = self._execute_stage(
            stage_num,
            stage_spec.name,
            stage_spec.func,
            pipeline_start,
            stage_spec=stage_spec,
            input_snapshot=snapshot,
        )
        guard = (
            execution_guard_result(
                config=self.config,
                plan=self.execution_plan,
                deadline=self._run_deadline,
                stage_num=stage_num,
                stage_name=stage_spec.name,
                stage_key=stage_spec.key or stage_spec.name,
                completion=True,
            )
            if result.stage_completed and (result.success or result.hitl_pause)
            else None
        )
        guard = guard or validate_completion(self.config, stage_spec, result, snapshot)
        if guard is not None:
            result.success = False
            result.exit_code = guard.exit_code
            result.error_message = guard.error_message
            result.hitl_pause = False
            result.stage_completed = False
            result.outcome = (
                replace(result.outcome, status=guard.outcome.status, diagnostic=guard.error_message)
                if result.outcome is not None and guard.outcome is not None
                else guard.outcome
            )
        results.append(result)
        if not result.success:
            logger.error(PIPELINE_STAGE_FAILED.format(stage_num=stage_num, stage_name=stage_spec.name))
        if result.stage_completed and (result.success or result.hitl_pause):
            self._record_incremental_hash(stage_spec)
            if not self._artifact_manifest_sealed:
                self._write_artifact_manifest(stage_num, stage_spec)
            self._write_snapshot(stage_num, stage_spec)
            self._save_checkpoint(pipeline_start, stage_num, results)
        return result

    # -- Incremental (content-hash) stage skipping (DEFAULT-OFF) -------------

    def _incremental_enabled(self) -> bool:
        return bool(getattr(self.config, "incremental", None) and self.config.incremental.enabled)

    def _maybe_skip_stage_incremental(self, stage_num: int, stage_spec: StageSpec) -> PipelineStageResult | None:
        """Return a skip result when the stage can be skipped, else ``None``.

        No-op (returns ``None``) when incremental mode is disabled — the default.
        """
        if not self._incremental_enabled() or self._incremental_manifest is None:
            return None
        if self.execution_plan and (
            self.execution_plan.hitl_mode != "full-auto" or self.execution_plan.smart_pause_action == "pause"
        ):
            return None
        if self.execution_plan and any(
            stage.key == stage_spec.key and not stage.cacheable for stage in self.execution_plan.stages
        ):
            return None
        from infrastructure.core.pipeline.incremental import should_skip_stage

        decision = should_skip_stage(
            config=self.config.incremental,
            manifest=self._incremental_manifest,
            repo_root=self.config.repo_root,
            project_dir=self.config.project_dir,
            stage_name=stage_spec.key or stage_spec.name,
            contract=stage_spec.contract,
            execution_identity=self._plan_digest,
            mode=self.config.mode,
            stage_script=next(
                (stage.script for stage in self.execution_plan.stages if stage.key == stage_spec.key), None
            )
            if self.execution_plan is not None
            else None,
        )
        if not decision.skip:
            return None
        logger.info(f"⏭ Stage {stage_num} skipped (unchanged inputs): {stage_spec.name}")
        return PipelineStageResult(
            stage_num=stage_num,
            stage_name=stage_spec.name,
            success=True,
            duration=0.0,
            lessons=(f"incremental skip: {stage_spec.name} inputs unchanged",),
            stage_key=stage_spec.key or stage_spec.name,
            outcome=StageOutcome(
                stage_spec.key or stage_spec.name,
                StageStatus.CACHED,
                child_exit_code=None,
                reason="current_content_and_outputs",
                receipt_validated=True,
            ),
        )

    def _record_incremental_hash(self, stage_spec: StageSpec) -> None:
        """Record the stage's input/output hashes (no-op when feature disabled)."""
        if not self._incremental_enabled() or self._incremental_manifest is None:
            return
        if stage_spec.contract.mutable_artifacts:
            return
        if self.execution_plan and any(
            stage.key == stage_spec.key and not stage.cacheable for stage in self.execution_plan.stages
        ):
            return
        from infrastructure.core.pipeline.incremental import record_stage_hash, save_hash_manifest

        try:
            # Pass empty upstream hashes: transitive invalidation flows through
            # declared-input file content (see should_skip_stage), and this keeps
            # the recorded input hash symmetric with the skip-check computation.
            record_stage_hash(
                manifest=self._incremental_manifest,
                repo_root=self.config.repo_root,
                project_dir=self.config.project_dir,
                stage_name=stage_spec.key or stage_spec.name,
                contract=stage_spec.contract,
                upstream_output_hashes={},
                execution_identity=self._plan_digest,
                mode=self.config.mode,
            )
            save_hash_manifest(self.config.runtime_output_dir, self._incremental_manifest)
        except OSError as exc:
            logger.warning(f"Failed to record incremental hash: {exc}")

    def _load_incremental_manifest(self) -> None:
        """Load the hash manifest for this run (no-op when feature disabled)."""
        self._incremental_manifest = None
        if not self._incremental_enabled():
            return
        from infrastructure.core.pipeline.incremental import load_hash_manifest

        self._incremental_manifest = load_hash_manifest(self.config.runtime_output_dir)

    def _execute_pipeline(self, stages: list[StageSpec]) -> list[PipelineStageResult]:
        """Execute pipeline stages."""
        self._current_stage_count = len(stages)
        self._artifact_manifest_sealed = False
        results: list[PipelineStageResult] = []
        pipeline_start = time.time()
        self._load_incremental_manifest()

        for stage_num, stage_spec in enumerate(stages, 1):
            result = self._run_stage_and_checkpoint(stage_num, stage_spec, results, pipeline_start)
            if not result.success or result.hitl_pause:
                break

        self._finalize_pipeline_run(pipeline_start, results)
        return results

    def _finalize_pipeline_run(self, pipeline_start: float, results: list[PipelineStageResult]) -> None:
        """Shared post-run finalization for fresh and resumed pipeline paths."""
        if self._telemetry is not None:
            total_duration = time.time() - pipeline_start
            self._telemetry.finalize(total_duration=total_duration)
        write_pause_recommendations_report(self)
        write_run_lessons_report(self, results)
        if (
            results
            and not (results[-1].stage_completed and (results[-1].success or results[-1].hitl_pause))
            and (self.config.resume or not results[-1].hitl_pause)
        ):
            # Successful new stages already save their checkpoints. A refused
            # continuation must preserve prior evidence, including its output
            # identity, rather than bless changes from an unsuccessful attempt.
            # A fresh pause before any execution still needs a bound checkpoint.
            return
        completed: list[PipelineStageResult] = []
        for result in results:
            if not result.stage_completed or not (result.success or result.hitl_pause):
                break
            completed.append(result)
        if completed or any(result.hitl_pause for result in results):
            self._save_checkpoint(pipeline_start, len(completed), completed)

    def _write_artifact_manifest(self, stage_num: int, stage_spec: StageSpec) -> None:
        """Persist stage and aggregate artifact manifests."""
        try:
            from infrastructure.core.pipeline.artifacts import (
                aggregate_artifact_manifests,
                output_inventory_mode_for_project,
                write_stage_artifact_manifest,
            )

            write_stage_artifact_manifest(
                repo_root=self.config.repo_root,
                project_dir=self.config.project_dir,
                stage_num=stage_num,
                stage_name=stage_spec.name,
                contract=stage_spec.contract,
                record_output_dir=self.config.runtime_output_dir if self.config.shared_infrastructure else None,
            )
            aggregate_artifact_manifests(
                self.config.runtime_output_dir,
                inventory_output_dir=self.config.project_dir / "output" if self.config.shared_infrastructure else None,
                inventory_mode=output_inventory_mode_for_project(
                    self.config.repo_root,
                    self.config.project_dir,
                ),
            )
        except (OSError, ValueError) as exc:
            logger.warning(f"Failed to write artifact manifest: {exc}")

    def _prepare_artifact_manifest_for_stage(
        self,
        stage_spec: StageSpec,
        results: list[PipelineStageResult],
    ) -> None:
        """Seal the aggregate immediately before canonical output validation.

        Stage 04 binds its validation report and rendered-provenance receipt to
        the aggregate manifest inside the stage subprocess. Re-aggregating
        afterward would replace stage metadata and invalidate that commitment.
        Once validation is reached, later runtime-only stages therefore keep
        writing snapshots/checkpoints but never rewrite the aggregate.

        The completed-result check restores the same sealed state when a run is
        resumed after validation.
        """
        if self._artifact_manifest_sealed:
            return
        crossed_boundary = any(
            result.success
            and result.stage_completed
            and (
                result.stage_key in self._artifact_manifest_boundary_keys
                if result.stage_key
                else result.stage_name in self._artifact_manifest_boundary_names
            )
            for result in results
        )
        if crossed_boundary:
            self._artifact_manifest_sealed = True
            return
        at_boundary = (
            stage_spec.key == "validate" or stage_spec.key in self._artifact_manifest_boundary_keys
            if stage_spec.key
            else stage_spec.name in self._artifact_manifest_boundary_names
        )
        if not at_boundary:
            return

        # Seal first: a failed aggregate refresh must not fall through to a
        # post-validation rewrite of an older manifest.
        self._artifact_manifest_sealed = True
        try:
            from infrastructure.core.pipeline.artifacts import (
                aggregate_artifact_manifests,
                output_inventory_mode_for_project,
            )

            aggregate_artifact_manifests(
                self.config.runtime_output_dir,
                inventory_output_dir=self.config.project_dir / "output" if self.config.shared_infrastructure else None,
                inventory_mode=output_inventory_mode_for_project(
                    self.config.repo_root,
                    self.config.project_dir,
                ),
            )
        except (OSError, ValueError) as exc:
            logger.warning(f"Failed to finalize artifact manifest before validation: {exc}")

    def _write_snapshot(self, stage_num: int, stage_spec: StageSpec) -> None:
        """Persist a stage output snapshot."""
        try:
            from infrastructure.core.pipeline.snapshot import create_snapshot

            create_snapshot(
                self.config.project_dir / "output",
                stage_num=stage_num,
                stage_name=stage_spec.name,
                record_output_dir=self.config.runtime_output_dir if self.config.shared_infrastructure else None,
            )
        except OSError as exc:
            logger.warning(f"Failed to write pipeline snapshot: {exc}")

    def _execute_stage(
        self,
        stage_num: int,
        stage_name: str,
        stage_func: Callable[[], bool | StageOutcome],
        pipeline_start: float | None = None,
        *,
        stage_spec: StageSpec | None = None,
        input_snapshot: InputSnapshot | None = None,
    ) -> PipelineStageResult:
        """Execute single pipeline stage with timing and error handling."""
        return execute_stage(
            self,
            stage_num,
            stage_name,
            stage_func,
            pipeline_start,
            stage_spec=stage_spec,
            input_snapshot=input_snapshot,
        )
