"""Pipeline checkpoint system for resume capability.

This module provides checkpoint functionality to save and restore pipeline state,
allowing the pipeline to resume from the last successful stage after interruption.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.project_paths import find_repo_root, validate_project_name
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""

    name: str
    exit_code: int
    duration: float
    timestamp: str = ""
    completed: bool = True
    status: str = ""
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

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "pipeline_start_time": self.pipeline_start_time,
            "last_stage_completed": self.last_stage_completed,
            "stage_results": [asdict(sr) for sr in self.stage_results],
            "total_stages": self.total_stages,
            "checkpoint_time": self.checkpoint_time,
            "output_digest": self.output_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineCheckpoint":
        """Create a checkpoint only from fields safe for resume and reporting."""
        if not isinstance(data, dict):
            raise ValueError("checkpoint must be an object")
        for name in ("last_stage_completed", "total_stages"):
            if type(data.get(name)) is not int:
                raise ValueError(f"checkpoint {name} must be an integer")
        for name in ("pipeline_start_time", "checkpoint_time"):
            _validate_nonnegative_number(data.get(name), name)
        digest = data.get("output_digest", "")
        if digest is None:
            digest = ""  # Optional in legacy checkpoint files.
        if not isinstance(digest, str) or (
            digest and (len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest))
        ):
            raise ValueError("checkpoint output_digest must be a SHA-256 hex digest")
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
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            checkpoint = PipelineCheckpoint.from_dict(data)
            logger.info(
                f"Loaded checkpoint: stage {checkpoint.last_stage_completed}/{checkpoint.total_stages}"  # noqa: E501
            )
            return checkpoint
        except Exception as e:  # noqa: BLE001 — intentional: corrupt/invalid checkpoint must degrade gracefully to fresh run
            logger.warning(f"Failed to load checkpoint: {e}", exc_info=True)
            logger.info("Invalid checkpoint file detected - starting fresh pipeline run")
            return None

    def clear_checkpoint(self) -> None:
        """Clear saved checkpoint."""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
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
        output_root = self.checkpoint_dir.parent
        if not output_root.is_dir():
            return ""
        digest = hashlib.sha256()
        files: list[Path] = []
        ignored_parts = {".checkpoints", ".pipeline", "logs", "__pycache__"}
        for path in output_root.rglob("*"):
            if not path.is_file():
                continue
            try:
                rel_parts = set(path.relative_to(output_root).parts)
                if rel_parts & ignored_parts:
                    continue
            except ValueError:
                continue
            files.append(path)
        for path in sorted(files, key=lambda item: item.as_posix()):
            rel = path.relative_to(output_root).as_posix()
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\n")
        return digest.hexdigest()

    def validate_checkpoint(self) -> tuple[bool, str | None]:
        """Validate checkpoint integrity and consistency.

        Returns:
            Tuple of (is_valid, error_message)
            is_valid: True if checkpoint is valid and can be used
            error_message: None if valid, error description if invalid
        """
        if not self.checkpoint_file.exists():
            return (
                False,
                "Checkpoint file does not exist - no previous pipeline run to resume",
            )

        try:
            checkpoint = self.load_checkpoint()
            if checkpoint is None:
                return False, "Failed to load checkpoint (corrupted or invalid format)"

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

            if checkpoint.last_stage_completed >= checkpoint.total_stages:
                return (
                    False,
                    f"Invalid checkpoint: last_stage_completed ({checkpoint.last_stage_completed}) >= total_stages ({checkpoint.total_stages}) - checkpoint corrupted",  # noqa: E501
                )

            # Validate stage results consistency
            if len(checkpoint.stage_results) != checkpoint.last_stage_completed:
                return (
                    False,
                    f"Checkpoint inconsistency: {len(checkpoint.stage_results)} stage results but last_stage_completed={checkpoint.last_stage_completed} - checkpoint corrupted",  # noqa: E501
                )

            # Check that all completed stages have exit_code 0
            for i, result in enumerate(checkpoint.stage_results):
                if not result.completed or result.exit_code != 0:
                    return (
                        False,
                        f"Stage {i} ({result.name}) did not complete successfully; refusing to skip it on resume",
                    )

            if checkpoint.last_stage_completed > 0 and checkpoint.output_digest:
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
                f"Checkpoint validation failed: {e} - checkpoint file may be corrupted, starting fresh pipeline run",  # noqa: E501
            )
