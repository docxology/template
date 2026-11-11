"""Pipeline logging, telemetry initialization, and advisory reports."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import (
    get_logger,
    log_pipeline_stage_with_eta,
)
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor

logger = get_logger(__name__)


class _ExcludeObservability(logging.Filter):
    """The module's direct sink already records these messages once."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name != __name__


def close_log_file_handler(self: PipelineExecutor) -> None:
    """Detach and close only the handlers owned by this executor."""
    owned = (
        (logging.getLogger(), self._log_handler),
        (logger, self._module_log_handler),
    )
    self._log_handler = None
    self._module_log_handler = None
    for owner, handler in owned:
        if handler is None:
            continue
        owner.removeHandler(handler)
        try:
            handler.close()
        except OSError as exc:
            logger.warning("Failed to close owned pipeline log handler: %s", exc)
    if self._module_log_level is not None:
        logger.setLevel(self._module_log_level)
        self._module_log_level = None


def setup_log_file_handler(self: PipelineExecutor) -> None:
    """Attach owned sinks without reconfiguring unrelated logger handlers.

    A direct module sink preserves ordinary CLI progress when propagation is
    disabled. The owned root sink excludes that module to avoid duplicate
    records under pytest. Cleanup detaches both sinks before closing them.
    """
    close_log_file_handler(self)
    self.log_file.parent.mkdir(parents=True, exist_ok=True)
    self._module_log_level = logger.level
    try:
        self._module_log_handler = logging.FileHandler(self.log_file)
        self._module_log_handler.setLevel(logging.DEBUG)
        self._module_log_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        logger.addHandler(self._module_log_handler)
        logger.setLevel(logging.DEBUG)
        self._log_handler = logging.FileHandler(self.log_file)
        self._log_handler.setLevel(logging.DEBUG)
        self._log_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
        self._log_handler.addFilter(_ExcludeObservability())
        logging.getLogger().addHandler(self._log_handler)
    except BaseException:
        close_log_file_handler(self)
        raise
    logger.debug("Set up log file handler: %s", self.log_file)


def initialize_telemetry(self: PipelineExecutor) -> None:
    """Initialize the telemetry collector from pipeline YAML config."""
    from infrastructure.core.pipeline.dag import load_telemetry_config

    yaml_path = self._resolve_pipeline_yaml()

    telem_config = TelemetryConfig()  # defaults
    if yaml_path.exists():
        loaded = load_telemetry_config(yaml_path)
        if loaded is not None:
            telem_config = loaded

    output_dir = self.config.runtime_output_dir
    self._telemetry = TelemetryCollector(
        config=telem_config,
        project_name=self.config.project_name,
        output_dir=output_dir,
    )
    self._telemetry.capture_system_info()


def write_pause_recommendations_report(self: PipelineExecutor) -> None:
    """Persist advisory SmartPause recommendations."""
    try:
        from infrastructure.core.pipeline.smart_pause import (
            compute_pause_recommendations,
            write_pause_recommendations,
        )

        output_dir = self.config.runtime_output_dir
        write_pause_recommendations(output_dir, compute_pause_recommendations(output_dir))
    except OSError as exc:
        logger.warning(f"Failed to write pause recommendations: {exc}")


def write_run_lessons_report(self: PipelineExecutor, results: list[PipelineStageResult]) -> None:
    """Persist explicit run lessons when possible."""
    try:
        from infrastructure.reporting.run_lessons import collect_run_lessons, write_run_lessons

        output_dir = self.config.runtime_output_dir
        lessons = collect_run_lessons(results, project_output_dir=output_dir)
        write_run_lessons(output_dir, lessons)
    except OSError as exc:
        logger.warning(f"Failed to write run lessons report: {exc}")


def record_stage_telemetry(
    executor: PipelineExecutor,
    *,
    stage_name: str,
    stage_num: int,
    success: bool,
    exit_code: int = 0,
    error_message: str = "",
) -> None:
    """Process record stage telemetry."""
    if executor._telemetry is None:
        return
    executor._telemetry.end_stage(
        stage_name,
        stage_num,
        success=success,
        exit_code=exit_code,
        error_message=error_message,
    )


def log_stage_start(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    pipeline_start: float | None,
) -> None:
    """Process log stage start."""
    if pipeline_start is not None:
        log_pipeline_stage_with_eta(
            stage_num,
            executor.config.total_stages,
            stage_name,
            pipeline_start,
            logger,
        )
    else:
        logger.info(f"Stage {stage_num}: {stage_name}")
