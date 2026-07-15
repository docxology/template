"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.runtime.checkpoint import CheckpointManager
from infrastructure.core.logging.utils import (
    get_logger,
    setup_logger,
    setup_root_log_file_handler,
)
from infrastructure.core.errors import (
    PIPELINE_STAGE_FAILED,
)
from infrastructure.core.pipeline.resume import PipelineResumeMixin
from infrastructure.core.pipeline.stages import PipelineStageMixin
from infrastructure.core.pipeline.control import load_pipeline_control_config, merge_control_configs
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    PipelineStageResult,
    StageSpec,
)
from infrastructure.core.pipeline._stage_execution import execute_stage
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

logger = get_logger(__name__)

if TYPE_CHECKING:
    from infrastructure.core.pipeline.dag import PipelineDAG
    from infrastructure.core.pipeline.plugins import PluginStageDeclaration


class PipelineExecutor(PipelineStageMixin, PipelineResumeMixin):
    """Execute research project pipeline stages."""

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
        self.checkpoint_manager = CheckpointManager(project_name=config.project_name, repo_root=config.repo_root)

        # Log file: projects/{project_name}/output/logs/pipeline.log
        # Recreated by _setup_log_file_handler after clean stage deletes it.
        self.log_file = config.project_dir / "output" / "logs" / "pipeline.log"
        self._log_handler: logging.FileHandler | None = None
        self._setup_log_file_handler()

        # Telemetry collector (lazy: reads pipeline.yaml for enabled reporters)
        self._telemetry: TelemetryCollector | None = None
        self._init_telemetry()

        # Incremental (content-hash) skip manifest. Stays ``None`` unless the
        # opt-in feature is enabled and a run loads it. DEFAULT-OFF.
        from infrastructure.core.pipeline.incremental import HashManifest

        self._incremental_manifest: HashManifest | None = None

    def _setup_log_file_handler(self) -> None:
        """Set up or recreate the log file handler.

        Called during init and after the clean stage (which may delete the log file).
        Delegates root-logger file handler management to logging_utils.
        """
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        setup_logger(__name__, log_file=self.log_file)

        if self._log_handler is not None:
            try:
                self._log_handler.close()
            except OSError as e:
                logger.warning(f"Failed to close log handler: {e}")

        self._log_handler = setup_root_log_file_handler(self.log_file)
        logger.debug(f"Set up log file handler: {self.log_file}")

    def _resolve_pipeline_yaml(self) -> Path:
        """Return the pipeline YAML path to use: project-specific if it exists, else default."""
        project_yaml = Path(self.config.project_dir) / "pipeline.yaml"
        return project_yaml if project_yaml.exists() else self._default_pipeline_yaml()

    def _default_pipeline_yaml(self) -> Path:
        """Return the repository DAG, or the identical installed package data."""
        repository_yaml = Path(self.config.repo_root) / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
        return repository_yaml if repository_yaml.exists() else Path(__file__).with_name("pipeline.yaml")

    def _project_pipeline_yaml(self) -> Path:
        return Path(self.config.project_dir) / "pipeline.yaml"

    def _resolve_control_config(self) -> PipelineControlConfig:
        """Resolve advisory control config from YAML plus explicit config."""
        default_yaml = self._default_pipeline_yaml()
        project_yaml = self._project_pipeline_yaml()
        loaded = load_pipeline_control_config(
            default_yaml if default_yaml.exists() else None,
            project_yaml=project_yaml if project_yaml.exists() else None,
            cli_hitl_mode=self.config.hitl_mode,
        )
        if self.config.control != type(self.config.control)():
            loaded = merge_control_configs(loaded, self.config.control)
        return loaded

    def _init_telemetry(self) -> None:
        """Initialize the telemetry collector from pipeline YAML config."""
        from infrastructure.core.pipeline.dag import load_telemetry_config

        yaml_path = self._resolve_pipeline_yaml()

        telem_config = TelemetryConfig()  # defaults
        if yaml_path.exists():
            loaded = load_telemetry_config(yaml_path)
            if loaded is not None:
                telem_config = loaded

        output_dir = self.config.project_dir / "output"
        self._telemetry = TelemetryCollector(
            config=telem_config,
            project_name=self.config.project_name,
            output_dir=output_dir,
        )
        self._telemetry.capture_system_info()

    # -- Stage list construction ---------------------------------------------

    def _build_stage_list(self, include_llm: bool, skip_clean: bool) -> list[StageSpec]:
        """Build canonical stage list by loading the declarative pipeline DAG.

        Resolution order:
        1. ``projects/{name}/pipeline.yaml`` (project-specific override)
        2. repository ``infrastructure/core/pipeline/pipeline.yaml``
        3. the same ``pipeline.yaml`` installed as package data

        Tag-based filtering applies ``skip_clean``, ``skip_infra``, and ``skip_llm``
        flags without modifying the YAML source.
        """
        from infrastructure.core.pipeline.dag import PipelineDAG

        # Resolve YAML path: project-specific → repository/package default.
        resolved = self._resolve_pipeline_yaml()
        if resolved == self.config.project_dir / "pipeline.yaml":
            logger.info("Using project-specific pipeline: %s", resolved)
        else:
            logger.debug("Using default pipeline: %s", resolved)

        dag = PipelineDAG.from_yaml(resolved)
        exclude_tags: set[str] = {"ebook", "metadata", "bundle", "archival", "science", "provenance"}
        if not include_llm or self.config.skip_llm:
            exclude_tags.add("llm")
        if skip_clean:
            dag.remove_stage("Clean Output Directories")
        if self.config.skip_infra:
            dag.remove_stage("Infrastructure Tests")
        dag.filter_tags(exclude=exclude_tags)

        self._merge_plugin_stages_into_dag(dag)
        return dag.to_stage_specs(self)

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

    def execute_full_pipeline(self) -> list[PipelineStageResult]:
        """Execute complete pipeline (tests -> analysis -> PDF -> validate -> copy -> LLM)."""
        logger.info(f"Executing full pipeline for project '{self.config.project_name}'")
        return self._run_pipeline(include_llm=True)

    def execute_core_pipeline(self) -> list[PipelineStageResult]:
        """Execute core pipeline (tests -> analysis -> PDF -> validate -> copy)."""
        logger.info(f"Executing core pipeline for project '{self.config.project_name}'")
        return self._run_pipeline(include_llm=False)

    def _run_pipeline(self, include_llm: bool) -> list[PipelineStageResult]:
        """Shared implementation for execute_full_pipeline and execute_core_pipeline.

        The whole run is held under a per-project output lock so a concurrent
        pipeline/test run on the same project cannot clean or rewrite ``output/``
        mid-flight (the cause of random-location "artifact missing" gate
        failures). The lock is cross-process re-entrant: the test stage spawned
        as a subprocess inherits the holder's environment marker and treats its
        own acquisition as a no-op, so it never deadlocks against this run.
        """
        with project_output_lock(self.config.project_dir):
            if self.config.resume:
                return self._resume_pipeline()
            skip_clean = not self.config.clean
            return self._execute_pipeline(self._build_stage_list(include_llm=include_llm, skip_clean=skip_clean))

    def _run_stage_and_checkpoint(
        self,
        stage_num: int,
        stage_spec: StageSpec,
        results: list[PipelineStageResult],
        pipeline_start: float,
    ) -> PipelineStageResult:
        """Execute a stage, append to results, and checkpoint on success.

        When incremental mode is opt-in enabled, a stage whose declared inputs
        are unchanged and whose declared outputs are present is SKIPPED. With the
        feature disabled (the default) this path is never entered and behavior is
        byte-identical to before.
        """
        skipped = self._maybe_skip_stage_incremental(stage_num, stage_spec)
        if skipped is not None:
            results.append(skipped)
            return skipped

        result = self._execute_stage(
            stage_num,
            stage_spec.name,
            stage_spec.func,
            pipeline_start,
            stage_spec=stage_spec,
        )
        results.append(result)
        if not result.success:
            logger.error(PIPELINE_STAGE_FAILED.format(stage_num=stage_num, stage_name=stage_spec.name))
        elif result.stage_completed:
            self._record_incremental_hash(stage_spec)
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
        from infrastructure.core.pipeline.incremental import should_skip_stage

        decision = should_skip_stage(
            config=self.config.incremental,
            manifest=self._incremental_manifest,
            repo_root=self.config.repo_root,
            project_dir=self.config.project_dir,
            stage_name=stage_spec.name,
            contract=stage_spec.contract,
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
        )

    def _record_incremental_hash(self, stage_spec: StageSpec) -> None:
        """Record the stage's input/output hashes (no-op when feature disabled)."""
        if not self._incremental_enabled() or self._incremental_manifest is None:
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
                stage_name=stage_spec.name,
                contract=stage_spec.contract,
                upstream_output_hashes={},
            )
            save_hash_manifest(self.config.project_dir / "output", self._incremental_manifest)
        except OSError as exc:
            logger.warning(f"Failed to record incremental hash: {exc}")

    def _load_incremental_manifest(self) -> None:
        """Load the hash manifest for this run (no-op when feature disabled)."""
        self._incremental_manifest = None
        if not self._incremental_enabled():
            return
        from infrastructure.core.pipeline.incremental import load_hash_manifest

        self._incremental_manifest = load_hash_manifest(self.config.project_dir / "output")

    def _execute_pipeline(self, stages: list[StageSpec]) -> list[PipelineStageResult]:
        """Execute pipeline stages."""
        self._current_stage_count = len(stages)
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
        self._write_pause_recommendations_report()
        self._write_run_lessons_report(results)

    def _write_pause_recommendations_report(self) -> None:
        """Persist advisory SmartPause recommendations."""
        try:
            from infrastructure.core.pipeline.smart_pause import (
                compute_pause_recommendations,
                write_pause_recommendations,
            )

            output_dir = self.config.project_dir / "output"
            write_pause_recommendations(output_dir, compute_pause_recommendations(output_dir))
        except OSError as exc:
            logger.warning(f"Failed to write pause recommendations: {exc}")

    def _write_run_lessons_report(self, results: list[PipelineStageResult]) -> None:
        """Persist explicit run lessons when possible."""
        try:
            from infrastructure.reporting.run_lessons import collect_run_lessons, write_run_lessons

            output_dir = self.config.project_dir / "output"
            lessons = collect_run_lessons(results, project_output_dir=output_dir)
            write_run_lessons(output_dir, lessons)
        except OSError as exc:
            logger.warning(f"Failed to write run lessons report: {exc}")

    def _write_artifact_manifest(self, stage_num: int, stage_spec: StageSpec) -> None:
        """Persist stage and aggregate artifact manifests."""
        try:
            from infrastructure.core.pipeline.artifacts import (
                aggregate_artifact_manifests,
                write_stage_artifact_manifest,
            )

            write_stage_artifact_manifest(
                repo_root=self.config.repo_root,
                project_dir=self.config.project_dir,
                stage_num=stage_num,
                stage_name=stage_spec.name,
                contract=stage_spec.contract,
            )
            aggregate_artifact_manifests(self.config.project_dir / "output")
        except (OSError, ValueError) as exc:
            logger.warning(f"Failed to write artifact manifest: {exc}")

    def _write_snapshot(self, stage_num: int, stage_spec: StageSpec) -> None:
        """Persist a stage output snapshot."""
        try:
            from infrastructure.core.pipeline.snapshot import create_snapshot

            create_snapshot(self.config.project_dir / "output", stage_num=stage_num, stage_name=stage_spec.name)
        except OSError as exc:
            logger.warning(f"Failed to write pipeline snapshot: {exc}")

    def _execute_stage(
        self,
        stage_num: int,
        stage_name: str,
        stage_func: Callable[[], bool],
        pipeline_start: float | None = None,
        *,
        stage_spec: StageSpec | None = None,
    ) -> PipelineStageResult:
        """Execute single pipeline stage with timing and error handling."""
        return execute_stage(
            self,
            stage_num,
            stage_name,
            stage_func,
            pipeline_start,
            stage_spec=stage_spec,
        )
