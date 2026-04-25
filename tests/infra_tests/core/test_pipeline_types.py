"""Tests for infrastructure.core.pipeline.types module.

Tests PipelineConfig, PipelineStageResult, and StageSpec using real
data (No Mocks Policy).
"""

from __future__ import annotations

from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineStageResult,
    StageSpec,
)


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_project_dir_property(self, tmp_path):
        """project_dir resolves to repo_root/projects_dir/project_name."""
        config = PipelineConfig(project_name="myproj", repo_root=tmp_path)
        assert config.project_dir == tmp_path / "projects" / "myproj"

    def test_custom_projects_dir(self, tmp_path):
        """projects_dir override changes the resolved path."""
        config = PipelineConfig(
            project_name="myproj",
            repo_root=tmp_path,
            projects_dir="projects_in_progress",
        )
        assert config.project_dir == tmp_path / "projects_in_progress" / "myproj"

    def test_nested_project_name_resolves_under_projects_dir(self, tmp_path):
        """Qualified project names preserve program-directory layouts."""
        config = PipelineConfig(
            project_name="my_program/myproj",
            repo_root=tmp_path,
            projects_dir="projects",
        )
        assert config.project_dir == tmp_path / "projects" / "my_program" / "myproj"

    def test_default_values(self, tmp_path):
        """Default values are correct."""
        config = PipelineConfig(project_name="p", repo_root=tmp_path)
        assert config.projects_dir == "projects"
        assert config.clean is True
        assert config.skip_infra is False
        assert config.skip_llm is False
        assert config.resume is False
        assert config.total_stages == 10

    def test_override_defaults(self, tmp_path):
        """All defaults can be overridden."""
        config = PipelineConfig(
            project_name="p",
            repo_root=tmp_path,
            clean=False,
            skip_infra=True,
            skip_llm=True,
            resume=True,
            total_stages=5,
        )
        assert config.clean is False
        assert config.skip_infra is True
        assert config.skip_llm is True
        assert config.resume is True
        assert config.total_stages == 5

    def test_project_name_stored(self, tmp_path):
        """project_name is stored correctly."""
        config = PipelineConfig(project_name="code_project", repo_root=tmp_path)
        assert config.project_name == "code_project"

    def test_repo_root_stored(self, tmp_path):
        """repo_root is stored as-is."""
        config = PipelineConfig(project_name="p", repo_root=tmp_path)
        assert config.repo_root == tmp_path


class TestPipelineStageResult:
    """Tests for PipelineStageResult dataclass."""

    def test_is_skipped_false_on_success(self):
        """Successful stage is not skipped."""
        result = PipelineStageResult(
            stage_num=1, stage_name="test", success=True, duration=1.5
        )
        assert result.is_skipped is False

    def test_is_skipped_false_on_nonzero_exit(self):
        """Failed stage with nonzero exit code is not skipped."""
        result = PipelineStageResult(
            stage_num=1, stage_name="test", success=False, duration=0.5, exit_code=1
        )
        assert result.is_skipped is False

    def test_is_skipped_true_on_failure_with_zero_exit(self):
        """Failed stage with zero exit code is skipped."""
        result = PipelineStageResult(
            stage_num=1, stage_name="test", success=False, duration=0.0, exit_code=0
        )
        assert result.is_skipped is True

    def test_default_exit_code_zero(self):
        """Default exit_code is 0."""
        result = PipelineStageResult(
            stage_num=2, stage_name="render", success=True, duration=3.2
        )
        assert result.exit_code == 0

    def test_default_error_message_empty(self):
        """Default error_message is empty string."""
        result = PipelineStageResult(
            stage_num=1, stage_name="test", success=True, duration=1.0
        )
        assert result.error_message == ""

    def test_error_message_stored(self):
        """error_message is stored correctly."""
        result = PipelineStageResult(
            stage_num=1,
            stage_name="test",
            success=False,
            duration=0.1,
            error_message="Timeout exceeded",
        )
        assert result.error_message == "Timeout exceeded"

    def test_stage_fields_stored(self):
        """stage_num, stage_name, success, duration all stored correctly."""
        result = PipelineStageResult(
            stage_num=7, stage_name="validate", success=True, duration=4.5
        )
        assert result.stage_num == 7
        assert result.stage_name == "validate"
        assert result.success is True
        assert result.duration == 4.5


class TestStageSpec:
    """Tests for StageSpec NamedTuple."""

    def test_name_and_func_stored(self):
        """name and func fields are accessible."""
        func = lambda: True
        spec = StageSpec(name="my_stage", func=func)
        assert spec.name == "my_stage"
        assert spec.func is func

    def test_callable_func(self):
        """func field is callable."""
        spec = StageSpec(name="test", func=lambda: False)
        assert callable(spec.func)
        assert spec.func() is False

    def test_is_named_tuple(self):
        """StageSpec is a NamedTuple (supports indexing)."""
        func = lambda: True
        spec = StageSpec(name="stage", func=func)
        assert spec[0] == "stage"
        assert spec[1] is func
