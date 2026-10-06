"""YAML-owned opt-in tags drive default and core-only stage filtering.

No mocks: real pipeline.yaml plus synthetic project-local YAML trees.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from infrastructure.core.pipeline.dag import PipelineDAG, opt_in_tags_from_mapping
from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.stage_vocabulary import (
    all_stage_names,
    core_stage_names,
    live_stage_names,
    default_run_stage_count,
)
from infrastructure.orchestration.menu import MENU_OPTIONS


_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_YAML = _REPO_ROOT / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"


def _project_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    # Resolved plans admit only existing canonical stage targets.
    shutil.copytree(
        Path(__file__).parents[4] / "scripts" / "pipeline",
        repo_root / "scripts" / "pipeline",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
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
    full = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root, mode="live"))
    core = PipelineExecutor(
        PipelineConfig(project_name="p", repo_root=repo_root, mode="core"),
    )

    full_names = full.preview_stage_names()
    core_names = core.preview_stage_names()

    assert "docxplus Export" not in full_names
    assert "docxplus Export" not in core_names
    assert "docxplus Export" in all_stage_names()
    assert "LLM Manuscript Review" in full_names
    assert "LLM Manuscript Review" not in core_names


def test_synthetic_opt_in_tag_is_omitted_from_preview(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    project_yaml = repo_root / "projects" / "p" / "pipeline.yaml"
    project_yaml.write_text(
        """
opt_in_tags: [experimental]
stages:
  - name: Clean Output Directories
    key: clean
    method: _run_clean_outputs
    tags: [core, clean]
  - name: Environment Setup
    key: setup
    method: run_project_tests
    depends_on: [Clean Output Directories]
    tags: [core]
  - name: Experimental Export
    key: experimental_export
    method: run_project_tests
    depends_on: [Environment Setup]
    tags: [core, experimental]
""",
        encoding="utf-8",
    )
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root, mode="live"))
    names = executor.preview_stage_names()
    assert "Environment Setup" in names
    assert "Experimental Export" not in names


def test_executor_total_stages_matches_preview(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    full = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root, mode="live"))
    core = PipelineExecutor(
        PipelineConfig(project_name="p", repo_root=repo_root, mode="core"),
    )
    full_names = full.preview_stage_names()
    core_names = core.preview_stage_names()
    assert full.config.total_stages == len(full_names)
    assert core.config.total_stages == len(core_names)
    assert full.config.total_stages == default_run_stage_count(mode="live")
    assert core.config.total_stages == default_run_stage_count(mode="core")


def test_plain_live_tag_vocabulary_matches_compiled_selection(tmp_path: Path) -> None:
    repo_root = _project_repo(tmp_path)
    declaration = repo_root / "projects/p/pipeline.yaml"
    declaration.write_text(
        "opt_in_tags: [publication]\nstages:\n"
        "  - {name: Core, key: core, method: run_project_tests, tags: [core]}\n"
        "  - {name: Local Live, key: local_live, method: run_project_tests, tags: [live]}\n"
        "  - {name: Model, key: model, method: run_project_tests, tags: [llm]}\n"
        "  - {name: Paid, key: paid, method: run_project_tests, tags: [paid]}\n"
        "  - {name: Publish, key: publish, method: run_project_tests, tags: [publication]}\n"
    )
    core = PipelineExecutor(PipelineConfig("p", repo_root, mode="core"))
    live = PipelineExecutor(PipelineConfig("p", repo_root, mode="live"))
    assert core.preview_stage_names() == core_stage_names(yaml_path=declaration) == ("Core",)
    assert live.preview_stage_names() == live_stage_names(yaml_path=declaration) == ("Core", "Local Live", "Model")


def test_paid_plugin_remains_opt_in_when_custom_dag_omits_paid_tag(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.plan import compile_execution_plan

    repo_root = _project_repo(tmp_path)
    project = repo_root / "projects/p"
    declaration = project / "pipeline.yaml"
    declaration.write_text(
        "opt_in_tags: []\nstages:\n"
        "  - {name: Core, key: core, method: run_project_tests, tags: [core]}\n"
        "  - {name: Paid Declaration, key: paid_declaration, method: run_project_tests, tags: [paid]}\n"
    )
    (project / "pipeline_plugins.yaml").write_text(
        "plugins:\n"
        "  - name: Paid Plugin\n    key: paid_plugin\n    method: run_project_tests\n    tags: [paid]\n"
        "    contract: {output_artifacts: [output/report.json], definition_of_done: Writes a report, failure_code: REPORT_FAILED}\n"
    )
    for mode in ("core", "live"):
        plan = compile_execution_plan(PipelineConfig("p", repo_root, mode=mode))
        assert plan.expected_stage_keys == ("core",)
        assert not any("paid" in stage.tags for stage in plan.stages)
    assert core_stage_names(yaml_path=declaration) == live_stage_names(yaml_path=declaration) == ("Core",)


def test_vocabulary_and_menu_counts_follow_yaml() -> None:
    default_full = len(live_stage_names())
    core_only = len(core_stage_names())
    assert default_full > core_only
    assert "docxplus Export" not in live_stage_names()
    assert "docxplus Export" not in core_stage_names()

    descriptions = {key: desc for key, _label, desc in MENU_OPTIONS}
    assert "local stages" in descriptions["8"]
    assert "live stages" in descriptions["9"]
