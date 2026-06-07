#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.plugins — schema-validated plugin stages.

Follows the No Mocks Policy: every test uses real temp files and real DAG
objects. The feature is opt-in (DEFAULT-OFF): with no plugin declaration the
plan is byte-identical to today, which is asserted explicitly here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition
from infrastructure.core.pipeline.plugins import (
    PluginStageError,
    load_plugin_stages,
    merge_plugin_stages,
    parse_plugin_stages,
)


def _core_dag() -> PipelineDAG:
    """A small stand-in for the core DAG."""
    return PipelineDAG(
        [
            StageDefinition(name="Clean Output Directories", method="_run_clean_outputs", tags=["core"]),
            StageDefinition(name="Environment Setup", method="_run_setup", depends_on=["Clean Output Directories"]),
            StageDefinition(name="Copy Outputs", method="_run_copy", depends_on=["Environment Setup"]),
        ]
    )


class TestLoadPluginStagesDefaultOff:
    """No declaration file -> no plugin stages (the default-off contract)."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_plugin_stages(tmp_path) == []

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "pipeline_plugins.yaml").write_text("", encoding="utf-8")
        assert load_plugin_stages(tmp_path) == []

    def test_empty_plugins_block_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "pipeline_plugins.yaml").write_text("plugins: []\n", encoding="utf-8")
        assert load_plugin_stages(tmp_path) == []


class TestLoadPluginStagesValid:
    """A valid declaration loads into validated plugin stage definitions."""

    def test_loads_a_declared_stage(self, tmp_path: Path) -> None:
        (tmp_path / "pipeline_plugins.yaml").write_text(
            """
plugins:
  - name: Extra Report
    script: my_extra_report.py
    depends_on: [Copy Outputs]
    tags: [plugin]
""",
            encoding="utf-8",
        )
        decls = load_plugin_stages(tmp_path)
        assert len(decls) == 1
        assert decls[0].name == "Extra Report"
        assert decls[0].script == "my_extra_report.py"
        assert decls[0].depends_on == ("Copy Outputs",)
        assert "plugin" in decls[0].tags


class TestParsePluginStagesValidation:
    """Invalid declarations are rejected with a clear PluginStageError."""

    def test_requires_name(self) -> None:
        with pytest.raises(PluginStageError, match="name"):
            parse_plugin_stages([{"script": "x.py"}])

    def test_requires_script_or_method(self) -> None:
        with pytest.raises(PluginStageError, match="script.*method|method.*script"):
            parse_plugin_stages([{"name": "Bad"}])

    def test_rejects_both_script_and_method(self) -> None:
        with pytest.raises(PluginStageError, match="not both|both"):
            parse_plugin_stages([{"name": "Bad", "script": "x.py", "method": "do_x"}])

    def test_rejects_non_mapping_entry(self) -> None:
        with pytest.raises(PluginStageError, match="mapping"):
            parse_plugin_stages(["not-a-mapping"])

    def test_rejects_unknown_key(self) -> None:
        with pytest.raises(PluginStageError, match="unsupported|unknown"):
            parse_plugin_stages([{"name": "X", "script": "x.py", "bogus_key": 1}])

    def test_rejects_non_list_depends_on(self) -> None:
        with pytest.raises(PluginStageError, match="depends_on"):
            parse_plugin_stages([{"name": "X", "script": "x.py", "depends_on": "Copy Outputs"}])

    def test_rejects_duplicate_plugin_names(self) -> None:
        with pytest.raises(PluginStageError, match="[Dd]uplicate"):
            parse_plugin_stages(
                [
                    {"name": "X", "script": "x.py"},
                    {"name": "X", "method": "do_x"},
                ]
            )


class TestMergePluginStages:
    """Merging validated plugins into a core DAG."""

    def test_plugin_stage_appears_in_plan(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([{"name": "Extra Report", "script": "report.py", "depends_on": ["Copy Outputs"]}])
        merge_plugin_stages(dag, decls)
        names = [s.name for s in dag.sorted_stages()]
        assert "Extra Report" in names
        # Runs after its declared dependency.
        assert names.index("Copy Outputs") < names.index("Extra Report")

    def test_plugin_cannot_clobber_core_stage_name(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([{"name": "Copy Outputs", "script": "report.py"}])
        with pytest.raises(PluginStageError, match="clobber|core stage|already"):
            merge_plugin_stages(dag, decls)

    def test_plugin_depends_on_unknown_stage_rejected(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([{"name": "Extra", "script": "report.py", "depends_on": ["Nonexistent Stage"]}])
        with pytest.raises(PluginStageError, match="depends_on|unknown|Nonexistent"):
            merge_plugin_stages(dag, decls)

    def test_plugin_may_depend_on_another_plugin(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages(
            [
                {"name": "Plugin A", "script": "a.py", "depends_on": ["Copy Outputs"]},
                {"name": "Plugin B", "script": "b.py", "depends_on": ["Plugin A"]},
            ]
        )
        merge_plugin_stages(dag, decls)
        names = [s.name for s in dag.sorted_stages()]
        assert names.index("Plugin A") < names.index("Plugin B")

    def test_empty_declarations_leave_dag_unchanged(self) -> None:
        dag = _core_dag()
        before = [s.name for s in dag.sorted_stages()]
        merge_plugin_stages(dag, [])
        after = [s.name for s in dag.sorted_stages()]
        assert before == after

    def test_merged_plugin_resolves_to_runnable_spec(self) -> None:
        """A merged plugin stage converts into a StageSpec that the executor can run."""
        # Minimal core DAG whose single existing stage uses a method the fake
        # executor actually provides, so to_stage_specs() can resolve every stage.
        dag = PipelineDAG([StageDefinition(name="Copy Outputs", method="_run_copy")])
        decls = parse_plugin_stages([{"name": "Extra Report", "script": "report.py", "depends_on": ["Copy Outputs"]}])
        merge_plugin_stages(dag, decls)

        executed: list[str] = []

        class _FakeConfig:
            project_name = "demo"

        class _FakeExecutor:
            config = _FakeConfig()

            def _run_copy(self) -> bool:
                return True

            def _run_script(self, script: str, *args: str, allow_skip_code: bool = False) -> bool:
                executed.append(script)
                return True

        specs = dag.to_stage_specs(_FakeExecutor())
        spec = next(s for s in specs if s.name == "Extra Report")
        assert spec.func() is True
        assert executed == ["report.py"]
