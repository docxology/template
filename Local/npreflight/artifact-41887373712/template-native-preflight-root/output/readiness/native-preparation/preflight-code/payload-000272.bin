"""Pipeline checkpoint system for resume capability.

This module provides checkpoint functionality to save and restore pipeline state,
allowing the pipeline to resume from the last successful stage after interruption.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_text_confined, unlink_confined
from infrastructure.core.project_paths import find_repo_root, validate_project_name
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.fingerprints import paths_digest

logger = get_logger(__name__)
CHECKPOINT_SCHEMA_VERSION = 4


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""

    name: str
    exit_code: int
    duration: float
    timestamp: str = ""
    completed: bool = True
    status: str = "succeeded"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineCheckpoint:
    """Pipeline checkpoint state."""

    pipeline_start_time: float
    last_stage_completed: int
    stage_results: list[StageResult]
    total_stages: int
    checkpoint_time: float
    output_digest: str = ""
    schema_version: int = CHECKPOINT_SCHEMA_VERSION
    plan_digest: str = ""
    source_digest: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "pipeline_start_time": self.pipeline_start_time,
            "last_stage_completed": self.last_stage_completed,
            "stage_results": [asdict(sr) for sr in self.stage_results],
            "total_stages": self.total_stages,
            "checkpoint_time": self.checkpoint_time,
            "output_digest": self.output_digest,
            "schema_version": self.schema_version,
            "plan_digest": self.plan_digest,
            "source_digest": self.source_digest,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineCheckpoint":
        """Create a checkpoint only from fields safe for resume and reporting."""
        if not isinstance(data, dict):
            raise ValueError("checkpoint must be an object")
        if type(data.get("schema_version")) is not int or data["schema_version"] != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError("Unsupported checkpoint schema; preserve this file and start a fresh run")
        for name in ("last_stage_completed", "total_stages"):
            if type(data.get(name)) is not int:
                raise ValueError(f"checkpoint {name} must be an integer")
        for name in ("pipeline_start_time", "checkpoint_time"):
            _validate_nonnegative_number(data.get(name), name)
        digest = data.get("output_digest", "")
        if not isinstance(digest, str) or (
            digest and (len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest))
        ):
            raise ValueError("checkpoint output_digest must be a SHA-256 hex digest")
        for name in ("plan_digest", "source_digest"):
            value = data.get(name, "")
            if not isinstance(value, str) or (
                value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value))
            ):
                raise ValueError(f"checkpoint {name} must be a SHA-256 hex digest")
        if not isinstance(data.get("run_id", ""), str):
            raise ValueError("checkpoint run_id must be a string")
        raw_results = data.get("stage_results", [])
        if not isinstance(raw_results, list):
            raise ValueError("checkpoint stage_results must be a list")
        stage_results = []
        for raw in raw_results:
            if not isinstance(raw, dict):
                raise ValueError("checkpoint stage result must be an object")
            result = StageResult(**raw)
            if not isinstance(result.name, str) or not result.name:
                raise ValueError("checkpoint stage name must be a non-empty string")
            if type(result.exit_code) is not int or type(result.completed) is not bool:
                raise ValueError("checkpoint stage exit_code/completed have invalid types")
            _validate_nonnegative_number(result.duration, "stage duration")
            if not isinstance(result.timestamp, str) or not isinstance(result.status, str):
                raise ValueError("checkpoint stage timestamp/status must be strings")
            if not isinstance(result.context, dict):
                raise ValueError("checkpoint stage context must be an object")
            stage_results.append(result)
        return cls(
            pipeline_start_time=data["pipeline_start_time"],
            last_stage_completed=data["last_stage_completed"],
            stage_results=stage_results,
            total_stages=data["total_stages"],
            checkpoint_time=data["checkpoint_time"],
            output_digest=digest,
            plan_digest=data.get("plan_digest", ""),
            source_digest=data.get("source_digest", ""),
            run_id=data.get("run_id", ""),
        )


def _validate_nonnegative_number(value: Any, name: str) -> None:
    """Reject JSON booleans, nonnumbers, and nonfinite runtime measurements."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"checkpoint {name} must be a nonnegative finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"checkpoint {name} must be a nonnegative finite number")


class CheckpointManager:
    """Manages pipeline checkpoints for resume capability."""

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        project_name: str = "project",
        repo_root: Path | None = None,
        project_dir: Path | None = None,
        output_dir: Path | None = None,
    ):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Explicit directory for checkpoint files. Takes priority
                over all other arguments.
            project_name: Name of the project (default: "project").
            repo_root: Repository root path; inferred from __file__ if not provided.
            project_dir: Absolute path to the project directory. When given,
                checkpoint files are stored in ``project_dir/output/.checkpoints``
                and ``project_name``/``repo_root`` are only used as fallbacks.
            output_dir: Actual deliverables to fingerprint independently of the
                checkpoint storage namespace. Defaults to checkpoint_dir.parent.
        """
        if checkpoint_dir is None:
            if project_dir is not None:
                checkpoint_dir = project_dir / "output" / ".checkpoints"
            else:
                resolved_root = repo_root if repo_root is not None else find_repo_root()
                checkpoint_dir = (
                    resolved_root / "projects" / validate_project_name(project_name) / "output" / ".checkpoints"
                )

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_file = self.checkpoint_dir / "pipeline_checkpoint.json"
        self.output_dir = Path(output_dir) if output_dir is not None else self.checkpoint_dir.parent
        self.expected_plan_digest = ""
        self.expected_source_digest = ""
        self.run_id = ""

    def _ensure_checkpoint_dir(self) -> None:
        """Ensure checkpoint directory exists."""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        pipeline_start_time: float,
        last_stage_completed: int,
        stage_results: list[StageResult],
        total_stages: int,
    ) -> bool:
        """Save pipeline checkpoint.

        Args:
            pipeline_start_time: Pipeline start timestamp
            last_stage_completed: Last successfully completed stage number
            stage_results: List of stage results
            total_stages: Total number of stages

        Returns:
            True if checkpoint saved successfully, False if save failed.
            Callers should log a warning and continue — pipeline execution
            proceeds regardless, but resume will not be available.
        """
        try:
            checkpoint = PipelineCheckpoint(
                pipeline_start_time=pipeline_start_time,
                last_stage_completed=last_stage_completed,
                stage_results=stage_results,
                total_stages=total_stages,
                checkpoint_time=time.time(),
                output_digest=self._output_tree_digest(),
                plan_digest=self.expected_plan_digest,
                source_digest=self.expected_source_digest,
                run_id=self.run_id,
            )
            payload = json.dumps(checkpoint.to_dict(), indent=2, allow_nan=False)
            self._ensure_checkpoint_dir()
            atomic_write_text_confined(self.checkpoint_dir, self.checkpoint_file, payload + "\n", mode=0o600)
            logger.debug(f"Checkpoint saved: stage {last_stage_completed}/{total_stages}")
            return True
        except Exception as e:  # noqa: BLE001 — intentional: checkpoint save must not crash the pipeline regardless of failure mode
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            logger.warning("Checkpoint save failed - pipeline resume will not be available for this run")
            return False

    def load_checkpoint(self) -> PipelineCheckpoint | None:
        """Load pipeline checkpoint.

        Returns:
            PipelineCheckpoint if found and valid, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            data = json.loads(read_text_confined(self.checkpoint_dir.parent, self.checkpoint_file))
            checkpoint = PipelineCheckpoint.from_dict(data)
            logger.info(
                f"Loaded checkpoint: stage {checkpoint.last_stage_completed}/{checkpoint.total_stages}"  # noqa: E501
            )
            return checkpoint
        except Exception as e:  # noqa: BLE001 — intentional: corrupt/invalid checkpoint must degrade gracefully to fresh run
            logger.warning(f"Failed to load checkpoint: {e}", exc_info=True)
            logger.info("Invalid checkpoint preserved; resume is refused")
            return None

    def clear_checkpoint(self) -> None:
        """Clear saved checkpoint."""
        if self.checkpoint_file.exists():
            try:
                unlink_confined(self.checkpoint_dir.parent, self.checkpoint_file)
                logger.debug("Checkpoint cleared")
            except Exception as e:  # noqa: BLE001 — intentional: stale checkpoint file is non-fatal
                logger.warning(f"Failed to clear checkpoint: {e}")

    def checkpoint_exists(self) -> bool:
        """Check if checkpoint exists.

        Returns:
            True if checkpoint file exists and is valid
        """
        if not self.checkpoint_file.exists():
            return False

        try:
            checkpoint = self.load_checkpoint()
            return checkpoint is not None
        except Exception as e:  # noqa: BLE001 — intentional: corrupt/missing checkpoint must return False
            logger.debug(f"checkpoint_exists check failed (treating as no checkpoint): {type(e).__name__}: {e}")
            return False

    def _output_tree_digest(self) -> str:
        """SHA-256 of the output tree excluding checkpoints, logs, and internal metadata."""
        output_root = self.output_dir
        if not output_root.is_dir():
            return ""
        return paths_digest((output_root,), stable_output=True)

    def validate_checkpoint(self) -> tuple[bool, str | None]:
        """Validate checkpoint integrity and consistency.

        Returns:
            Tuple of (is_valid, error_message)
            is_valid: True if checkpoint is valid and can be used
            error_message: None if valid, error description if invalid
        """
        checkpoint, diagnostic = self.load_validated_checkpoint()
        return checkpoint is not None, diagnostic

    def load_validated_checkpoint(self) -> tuple[PipelineCheckpoint | None, str | None]:
        """Read one confined bounded snapshot and validate that exact observation."""
        if not self.checkpoint_file.exists():
            return (
                None,
                "Checkpoint file does not exist - no previous pipeline run to resume",
            )
        checkpoint = self.load_checkpoint()
        if checkpoint is None:
            return None, "Failed to load checkpoint (unsafe, corrupted or invalid format)"
        valid, diagnostic = self._validate_checkpoint_snapshot(checkpoint)
        return (checkpoint if valid else None), diagnostic

    def _validate_checkpoint_snapshot(self, checkpoint: PipelineCheckpoint) -> tuple[bool, str | None]:
        """Validate the already-confined observation without rereading its path."""
        try:
            # Validate checkpoint structure
            if checkpoint.last_stage_completed < 0:
                return (
                    False,
                    f"Invalid checkpoint: last_stage_completed ({checkpoint.last_stage_completed}) cannot be negative - checkpoint corrupted",  # noqa: E501
                )

            if checkpoint.total_stages <= 0:
                return (
                    False,
                    f"Invalid checkpoint: total_stages ({checkpoint.total_stages}) must be positive - checkpoint corrupted",  # noqa: E501
                )

            if checkpoint.last_stage_completed > checkpoint.total_stages:
                return (
                    False,
                    f"Invalid checkpoint: last_stage_completed ({checkpoint.last_stage_completed}) > total_stages ({checkpoint.total_stages}) - checkpoint corrupted",  # noqa: E501
                )

            # Validate stage results consistency
            if len(checkpoint.stage_results) != checkpoint.last_stage_completed:
                return (
                    False,
                    f"Checkpoint inconsistency: {len(checkpoint.stage_results)} stage results but last_stage_completed={checkpoint.last_stage_completed} - checkpoint corrupted",  # noqa: E501
                )

            # Only positively classified completion records can grant reuse.
            for i, result in enumerate(checkpoint.stage_results):
                valid_skip = result.status == "skipped" and result.context.get("receipt_validated") is True
                valid_status = (
                    result.status == "succeeded"
                    or valid_skip
                    or (result.status == "cached" and result.context.get("receipt_validated") is True)
                )
                if not valid_status or not result.completed or (result.exit_code != 0 and not valid_skip):
                    return (
                        False,
                        f"Stage {i} ({result.name}) did not complete successfully; refusing to skip it on resume",
                    )
                for key in ("receipt_validated", "hitl_pause", "in_process_completed"):
                    if type(result.context.get(key, False)) is not bool:
                        return False, f"Checkpoint stage {key} must be a boolean"
                if result.context.get("hitl_pause") is True and i != len(checkpoint.stage_results) - 1:
                    return False, "Checkpoint pause must be at the end of the completed prefix"
                if not isinstance(result.context.get("stage_key"), str) or not result.context["stage_key"]:
                    return False, "Checkpoint stage has no stable identity; start a fresh run"
                child_code = result.context.get("child_exit_code", result.exit_code)
                if child_code is not None and type(child_code) is not int:
                    return False, "Checkpoint child_exit_code must be an integer or null"
                attempts = result.context.get("attempt_count", 1)
                if type(attempts) is not int or attempts < 1:
                    return False, "Checkpoint attempt_count must be a positive integer"
                attempt_codes = result.context.get("attempt_exit_codes", [])
                if not isinstance(attempt_codes, (list, tuple)) or any(type(code) is not int for code in attempt_codes):
                    return False, "Checkpoint attempt_exit_codes must contain exact integers"
                if attempt_codes and (len(attempt_codes) != attempts or attempt_codes[-1] != child_code):
                    return False, "Checkpoint attempt history differs from original child outcome"
                in_process = result.context.get("in_process_completed", False)
                if in_process and (child_code is not None or attempt_codes):
                    return False, "Checkpoint in-process completion invents child evidence"
                if result.status == "succeeded" and child_code != 0 and not in_process:
                    return False, "Checkpoint succeeded stage has no successful child outcome"
                if valid_skip and (child_code != 2 or result.exit_code != 2):
                    return False, "Checkpoint skip has no original exit-2 receipt"
                for key in ("reason", "error_message"):
                    if not isinstance(result.context.get(key, ""), str):
                        return False, f"Checkpoint {key} must be a string"

            for field_name, expected in (
                ("plan_digest", self.expected_plan_digest),
                ("source_digest", self.expected_source_digest),
            ):
                recorded = getattr(checkpoint, field_name)
                if not expected or not recorded or not checkpoint.run_id:
                    return False, "Checkpoint has no current source/plan/run binding; start a fresh run"
                if recorded != expected:
                    return False, f"Checkpoint {field_name} differs from current execution contract; start a fresh run"
            if checkpoint.last_stage_completed > 0 and not checkpoint.output_digest:
                return False, "Checkpoint has no output identity; start a fresh run"
            if checkpoint.last_stage_completed > 0:
                current = self._output_tree_digest()
                if current != checkpoint.output_digest:
                    return (
                        False,
                        "Checkpoint output digest does not match the current output tree — refusing resume",
                    )

            return True, None

        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            return (
                False,
                f"Checkpoint validation failed: {e}; preserve diagnostics and start a fresh run",
            )
