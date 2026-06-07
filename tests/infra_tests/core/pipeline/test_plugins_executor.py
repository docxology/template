#!/usr/bin/env python3
"""Executor integration tests for plugin stages (PLUGIN-STAGES-1).

Proves three things with real temp project trees (No Mocks):
1. A fixture plugin stage declared in projects/{name}/pipeline_plugins.yaml
   appears in the executor's built stage list and runs in the DAG.
2. An invalid plugin declaration is rejected with a clear error.
3. DEFAULT-OFF: with no plugin declaration the built stage list is identical
   to the list built without the feature present at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.plugins import PluginStageError


def _make_project_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    return repo_root


class TestExecutorPluginMerge:
    def test_plugin_stage_runs_in_built_plan(self, tmp_path: Path) -> None:
        repo_root = _make_project_repo(tmp_path)
        project_dir = repo_root / "projects" / "p"
        (project_dir / "pipeline_plugins.yaml").write_text(
            """
plugins:
  - name: Fixture Plugin Stage
    method: run_project_tests
    depends_on: [Copy Outputs]
    tags: [plugin]
""",
            encoding="utf-8",
        )

        executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
        specs = executor._build_stage_list(include_llm=False, skip_clean=False)
        names = [s.name for s in specs]

        assert "Fixture Plugin Stage" in names
        # Plugin runs after its declared dependency.
        assert names.index("Copy Outputs") < names.index("Fixture Plugin Stage")
        # The merged plugin resolves to a runnable callable.
        spec = next(s for s in specs if s.name == "Fixture Plugin Stage")
        assert callable(spec.func)

    def test_invalid_plugin_rejected(self, tmp_path: Path) -> None:
        repo_root = _make_project_repo(tmp_path)
        project_dir = repo_root / "projects" / "p"
        # Clobbers a core stage name -> must be rejected.
        (project_dir / "pipeline_plugins.yaml").write_text(
            """
plugins:
  - name: Copy Outputs
    script: evil.py
""",
            encoding="utf-8",
        )

        executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
        with pytest.raises(PluginStageError):
            executor._build_stage_list(include_llm=False, skip_clean=False)

    def test_invalid_plugin_missing_runner_rejected(self, tmp_path: Path) -> None:
        repo_root = _make_project_repo(tmp_path)
        project_dir = repo_root / "projects" / "p"
        (project_dir / "pipeline_plugins.yaml").write_text(
            """
plugins:
  - name: No Runner Stage
""",
            encoding="utf-8",
        )
        executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
        with pytest.raises(PluginStageError):
            executor._build_stage_list(include_llm=False, skip_clean=False)


class TestExecutorDefaultOff:
    def test_no_plugin_file_means_unchanged_plan(self, tmp_path: Path) -> None:
        """DEFAULT-OFF: absent plugin file -> plan identical to baseline."""
        repo_root = _make_project_repo(tmp_path)
        executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))

        baseline = [s.name for s in executor._build_stage_list(include_llm=False, skip_clean=False)]

        # Add the plugin file then remove it: confirms presence is the only switch.
        plugin_file = repo_root / "projects" / "p" / "pipeline_plugins.yaml"
        plugin_file.write_text("plugins: []\n", encoding="utf-8")
        with_empty = [s.name for s in executor._build_stage_list(include_llm=False, skip_clean=False)]

        plugin_file.unlink()
        after = [s.name for s in executor._build_stage_list(include_llm=False, skip_clean=False)]

        assert baseline == after
        # An empty plugins block is also a no-op.
        assert with_empty == baseline
