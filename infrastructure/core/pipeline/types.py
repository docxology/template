"""Pipeline type definitions — dataclasses and named tuples.

Extracted from pipeline.py to reduce file size and allow
other modules to import types without pulling in the full
PipelineExecutor and its heavy dependency chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NamedTuple


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution.

    Attributes:
        project_name: Name of the project directory (e.g. 'code_project').
        repo_root: Absolute path to the repository root.
        projects_dir: Name of the active projects directory relative to repo_root.
            Default 'projects'. Set to 'projects_in_progress' to run a project
            that hasn't been promoted to the active pool yet.
        clean: Whether to clean outputs before running.
        skip_infra: Whether to skip infrastructure tests.
        skip_llm: Whether to skip LLM stages.
        resume: Whether to resume from the last checkpoint.
        total_stages: Total number of pipeline stages (for ETA display).
    """

    project_name: str
    repo_root: Path
    projects_dir: str = "projects"
    clean: bool = True
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
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
                           projects_dir='projects_in_progress')
            → /repo/projects_in_progress/myproj
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
