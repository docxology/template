"""YAML-owned opt-in tags drive default and core-only stage filtering.

No mocks: real pipeline.yaml plus synthetic project-local YAML trees.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.dag import PipelineDAG, opt_in_tags_from_mapping
from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.stage_vocabulary import (
    all_stage_names,
    core_only_stage_names,
    core_stage_names,
    default_run_stage_count,
)
from infrastructure.orchestration.menu import MENU_OPTIONS


_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_YAML = _REPO_ROOT / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"


def _project_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    return repo_root


def test_opt_in_tags_from_mapping_reads_yaml_list() -> None:
    tags = opt_in_tags_from_mapping(
        {"opt_in_tags": ["ebook", "docxplus"], "stages": []},
    )
    assert tags == frozenset({"ebook", "docxplus"})


def test_opt_in_tags_from_mapping_empty_when_absent() -> None:
    assert opt_in_tags_from_mapping({"stages": []}) == frozenset()
    assert opt_in_tags_from_mapping(None) == frozenset()


def test_default_yaml_declares_docxplus_as_opt_in() -> None:
    dag = PipelineDAG.from_yaml(_DEFAULT_YAML)
    assert "docxplus" in dag.opt_in_tags
    names = [stage.name for stage in dag.sorted_stages()]
    assert "docxplus Export" in names


def test_preview_excludes_docxplus_from_default_full_and_core_only(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    full = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    core = PipelineExecutor(
        PipelineConfig(project_name="p", repo_root=repo_root, skip_llm=True),
    )

    full_names = full.preview_stage_names(include_llm=True)
    core_names = core.preview_stage_names(include_llm=False)

    assert "docxplus Export" not in full_names
    assert "docxplus Export" not in core_names
    assert "docxplus Export" in all_stage_names()
    assert "LLM Scientific Review" in full_names
    assert "LLM Scientific Review" not in core_names


def test_synthetic_opt_in_tag_is_omitted_from_preview(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    project_yaml = repo_root / "projects" / "p" / "pipeline.yaml"
    project_yaml.write_text(
        """
opt_in_tags: [experimental]
stages:
  - name: Clean Output Directories
    method: _run_clean_outputs
    tags: [core, clean]
  - name: Environment Setup
    method: run_project_tests
    depends_on: [Clean Output Directories]
    tags: [core]
  - name: Experimental Export
    method: run_project_tests
    depends_on: [Environment Setup]
    tags: [core, experimental]
""",
        encoding="utf-8",
    )
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    names = executor.preview_stage_names(include_llm=True)
    assert "Environment Setup" in names
    assert "Experimental Export" not in names


def test_executor_total_stages_matches_preview(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    full = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    core = PipelineExecutor(
        PipelineConfig(project_name="p", repo_root=repo_root, skip_llm=True),
    )
    full_names = full.preview_stage_names(include_llm=True)
    core_names = core.preview_stage_names(include_llm=False)
    assert full.config.total_stages == len(full_names)
    assert core.config.total_stages == len(core_names)
    assert full.config.total_stages == default_run_stage_count(include_llm=True)
    assert core.config.total_stages == default_run_stage_count(include_llm=False)


def test_vocabulary_and_menu_counts_follow_yaml() -> None:
    default_full = len(core_stage_names())
    core_only = len(core_only_stage_names())
    assert default_full > core_only
    assert "docxplus Export" not in core_stage_names()
    assert "docxplus Export" not in core_only_stage_names()

    descriptions = {key: desc for key, _label, desc in MENU_OPTIONS}
    assert f"{core_only} stages" in descriptions["8"]
    assert f"{default_full} stages" in descriptions["9"]
