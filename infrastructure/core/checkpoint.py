"""Pipeline checkpoint system for resume capability.

This module provides checkpoint functionality to save and restore pipeline state,
allowing the pipeline to resume from the last successful stage after interruption.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""

    name: str
    exit_code: int
    duration: float
    timestamp: str
    completed: bool = True


@dataclass
class PipelineCheckpoint:
    """Pipeline checkpoint state."""

    pipeline_start_time: float
    last_stage_completed: int
    stage_results: list[StageResult]
    total_stages: int
    checkpoint_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "pipeline_start_time": self.pipeline_start_time,
            "last_stage_completed": self.last_stage_completed,
            "stage_results": [asdict(sr) for sr in self.stage_results],
            "total_stages": self.total_stages,
            "checkpoint_time": self.checkpoint_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineCheckpoint":
        """Create checkpoint from dictionary."""
        stage_results = [StageResult(**sr) for sr in data.get("stage_results", [])]
        return cls(
            pipeline_start_time=data["pipeline_start_time"],
            last_stage_completed=data["last_stage_completed"],
            stage_results=stage_results,
            total_stages=data["total_stages"],
            checkpoint_time=data["checkpoint_time"],
        )


class CheckpointManager:
    """Manages pipeline checkpoints for resume capability."""

    def __init__(
        self, checkpoint_dir: Optional[Path] = None, project_name: str = "project"
    ):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files (default: projects/{project_name}/output/.checkpoints)
            project_name: Name of the project (default: "project")
        """
        if checkpoint_dir is None:
            # Default to projects/{project_name}/output/.checkpoints
            repo_root = Path(__file__).parent.parent.parent
            checkpoint_dir = (
                repo_root / "projects" / project_name / "output" / ".checkpoints"
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
    ) -> None:
        """Save pipeline checkpoint.

        Args:
            pipeline_start_time: Pipeline start timestamp
            last_stage_completed: Last successfully completed stage number
            stage_results: List of stage results
            total_stages: Total number of stages
        """
        checkpoint = PipelineCheckpoint(
            pipeline_start_time=pipeline_start_time,
            last_stage_completed=last_stage_completed,
            stage_results=stage_results,
            total_stages=total_stages,
            checkpoint_time=time.time(),
        )

        try:
            # Ensure checkpoint directory exists
            self._ensure_checkpoint_dir()
            with open(self.checkpoint_file, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)
            logger.debug(
                f"Checkpoint saved: stage {last_stage_completed}/{total_stages}"
            )
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
            logger.info(
                "Checkpoint save failed - pipeline resume will not be available for this run"
            )

    def load_checkpoint(self) -> Optional[PipelineCheckpoint]:
        """Load pipeline checkpoint.

        Returns:
            PipelineCheckpoint if found and valid, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, "r") as f:
                data = json.load(f)
            checkpoint = PipelineCheckpoint.from_dict(data)
            logger.info(
                f"Loaded checkpoint: stage {checkpoint.last_stage_completed}/{checkpoint.total_stages}"
            )
            return checkpoint
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            logger.info(
                "Invalid checkpoint file detected - starting fresh pipeline run"
            )
            return None

    def clear_checkpoint(self) -> None:
        """Clear saved checkpoint."""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.debug("Checkpoint cleared")
            except Exception as e:
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
        except Exception:
            return False

    def validate_checkpoint(self) -> Tuple[bool, Optional[str]]:
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
                    f"Invalid checkpoint: last_stage_completed ({checkpoint.last_stage_completed}) cannot be negative - checkpoint corrupted",
                )

            if checkpoint.total_stages <= 0:
                return (
                    False,
                    f"Invalid checkpoint: total_stages ({checkpoint.total_stages}) must be positive - checkpoint corrupted",
                )

            if checkpoint.last_stage_completed >= checkpoint.total_stages:
                return (
                    False,
                    f"Invalid checkpoint: last_stage_completed ({checkpoint.last_stage_completed}) >= total_stages ({checkpoint.total_stages}) - checkpoint corrupted",
                )

            # Validate stage results consistency
            if len(checkpoint.stage_results) != checkpoint.last_stage_completed:
                return (
                    False,
                    f"Checkpoint inconsistency: {len(checkpoint.stage_results)} stage results but last_stage_completed={checkpoint.last_stage_completed} - checkpoint corrupted",
                )

            # Check that all completed stages have exit_code 0
            for i, result in enumerate(checkpoint.stage_results):
                if result.exit_code != 0 and result.completed:
                    return (
                        False,
                        f"Stage {i} ({result.name}) marked completed but has non-zero exit code",
                    )

            return True, None

        except Exception as e:
            return (
                False,
                f"Checkpoint validation failed: {e} - checkpoint file may be corrupted, starting fresh pipeline run",
            )
