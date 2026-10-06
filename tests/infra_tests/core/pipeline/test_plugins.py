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


def _entry(name: str, **values: object) -> dict[str, object]:
    if isinstance(values.get("script"), str) and "/" not in values["script"]:
        values["script"] = "scripts/" + values["script"]
    return {
        "name": name,
        "key": name.lower().replace(" ", "_"),
        "contract": {
            "output_artifacts": ["output/report.json"],
            "definition_of_done": "Writes a validated report.",
            "failure_code": "REPORT_FAILED",
        },
        **values,
    }


def _core_dag() -> PipelineDAG:
    """A small stand-in for the core DAG."""
    return PipelineDAG(
        [
            StageDefinition(name="Clean Output Directories", key="clean", method="_run_clean_outputs", tags=["core"]),
            StageDefinition(
                name="Environment Setup", key="setup", method="_run_setup", depends_on=["Clean Output Directories"]
            ),
            StageDefinition(name="Copy Outputs", key="copy", method="_run_copy", depends_on=["Environment Setup"]),
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
    key: extra_report
    script: scripts/my_extra_report.py
    contract:
      output_artifacts: [output/report.json]
      definition_of_done: Writes a validated report.
      failure_code: REPORT_FAILED
    depends_on: [Copy Outputs]
    tags: [plugin]
""",
            encoding="utf-8",
        )
        decls = load_plugin_stages(tmp_path)
        assert len(decls) == 1
        assert decls[0].name == "Extra Report"
        assert decls[0].script == "scripts/my_extra_report.py"
        assert decls[0].depends_on == ("Copy Outputs",)
        assert "plugin" in decls[0].tags


class TestParsePluginStagesValidation:
    """Invalid declarations are rejected with a clear PluginStageError."""

    def test_requires_name(self) -> None:
        with pytest.raises(PluginStageError, match="name"):
            parse_plugin_stages([{"script": "x.py"}])

    def test_requires_script_or_method(self) -> None:
        with pytest.raises(PluginStageError, match="script.*method|method.*script"):
            parse_plugin_stages([_entry("Bad")])

    def test_rejects_both_script_and_method(self) -> None:
        with pytest.raises(PluginStageError, match="not both|both"):
            parse_plugin_stages([_entry("Bad", script="x.py", method="do_x")])

    def test_rejects_non_mapping_entry(self) -> None:
        with pytest.raises(PluginStageError, match="mapping"):
            parse_plugin_stages(["not-a-mapping"])

    def test_rejects_unknown_key(self) -> None:
        with pytest.raises(PluginStageError, match="unsupported|unknown"):
            parse_plugin_stages([_entry("X", script="x.py", bogus_key=1)])

    def test_rejects_non_list_depends_on(self) -> None:
        with pytest.raises(PluginStageError, match="depends_on"):
            parse_plugin_stages([_entry("X", script="x.py", depends_on="Copy Outputs")])

    def test_rejects_duplicate_plugin_names(self) -> None:
        with pytest.raises(PluginStageError, match="[Dd]uplicate"):
            parse_plugin_stages(
                [
                    _entry("X", script="x.py"),
                    _entry("X", method="do_x"),
                ]
            )


class TestMergePluginStages:
    """Merging validated plugins into a core DAG."""

    def test_plugin_stage_appears_in_plan(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([_entry("Extra Report", script="report.py", depends_on=["Copy Outputs"])])
        merge_plugin_stages(dag, decls)
        names = [s.name for s in dag.sorted_stages()]
        assert "Extra Report" in names
        # Runs after its declared dependency.
        assert names.index("Copy Outputs") < names.index("Extra Report")

    def test_plugin_cannot_clobber_core_stage_name(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([_entry("Copy Outputs", script="report.py")])
        with pytest.raises(PluginStageError, match="clobber|core stage|already"):
            merge_plugin_stages(dag, decls)

    def test_plugin_depends_on_unknown_stage_rejected(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages([_entry("Extra", script="report.py", depends_on=["Nonexistent Stage"])])
        with pytest.raises(PluginStageError, match="depends_on|unknown|Nonexistent"):
            merge_plugin_stages(dag, decls)

    def test_plugin_may_depend_on_another_plugin(self) -> None:
        dag = _core_dag()
        decls = parse_plugin_stages(
            [
                _entry("Plugin A", script="a.py", depends_on=["Copy Outputs"]),
                _entry("Plugin B", script="b.py", depends_on=["Plugin A"]),
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

    def test_merged_plugin_resolves_to_runnable_spec(self, tmp_path: Path) -> None:
        from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor

        project = tmp_path / "projects" / "demo"
        project.mkdir(parents=True)
        script = tmp_path / "scripts" / "report.py"
        script.parent.mkdir()
        script.write_text(
            # Stage outputs belong under output/; writing into project source
            # is refused by consumed-source custody after the child exits.
            "from pathlib import Path\nPath('projects/demo/output').mkdir(exist_ok=True)\n"
            "Path('projects/demo/output/report.txt').write_text('real child')\n",
            encoding="utf-8",
        )
        dag = PipelineDAG([StageDefinition(name="Clean", key="clean", method="_run_clean_outputs")])
        declarations = parse_plugin_stages([_entry("Extra Report", script="scripts/report.py", depends_on=["Clean"])])
        merge_plugin_stages(dag, declarations)
        executor = PipelineExecutor(PipelineConfig(project_name="demo", repo_root=tmp_path))
        spec = next(stage for stage in dag.to_stage_specs(executor) if stage.key == "extra_report")
        assert bool(spec.func())
        assert (project / "output" / "report.txt").read_text(encoding="utf-8") == "real child"
        assert spec.contract == declarations[0].contract


@pytest.mark.parametrize("field", ["key", "contract"])
def test_plugin_requires_explicit_identity_and_contract(field: str) -> None:
    entry = _entry("Report", script="scripts/report.py")
    entry.pop(field)
    with pytest.raises(PluginStageError, match=field):
        parse_plugin_stages([entry])


def test_plugin_contract_and_hooks_survive_merge() -> None:
    dag = _core_dag()
    declarations = parse_plugin_stages(
        [_entry("Report", script="scripts/report.py", hooks={"timeout_seconds": 7, "run_in_ci": True})]
    )
    merge_plugin_stages(dag, declarations)
    report = next(stage for stage in dag.stages if stage.key == "report")
    assert report.contract == declarations[0].contract
    assert report.hooks.timeout_seconds == 7
    assert report.hooks.run_in_ci is True


def test_failed_plugin_merge_does_not_change_live_dag() -> None:
    dag = _core_dag()
    before = list(dag.stages)
    declarations = parse_plugin_stages([_entry("Report", script="scripts/report.py", depends_on=["Unknown"])])
    with pytest.raises(PluginStageError, match="Unknown"):
        merge_plugin_stages(dag, declarations)
    assert dag.stages == before


def test_plugin_cannot_reuse_core_stable_key() -> None:
    dag = _core_dag()
    declarations = parse_plugin_stages([_entry("New Display Name", key="copy", script="scripts/report.py")])
    with pytest.raises(PluginStageError, match="clobber"):
        merge_plugin_stages(dag, declarations)
