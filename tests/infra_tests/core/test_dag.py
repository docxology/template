"""Tests for infrastructure.core.pipeline.dag — declarative pipeline DAG engine.

Tests YAML parsing, tag-based filtering, topological sorting, and StageSpec conversion.
Follows No Mocks Policy — all tests use real data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.dag import (
    PipelineDAG,
    StageDefinition,
    opt_in_tags_from_mapping,
)


def _stage(name: str, **values: object) -> StageDefinition:
    if isinstance(values.get("script"), str) and "/" not in values["script"]:
        values["script"] = "scripts/" + values["script"]
    values.setdefault("key", name.lower().replace(" ", "_"))
    if "script" not in values and "method" not in values:
        values["method"] = "run_stage"
    return StageDefinition(name=name, **values)


class TestStageDefinition:
    """Test StageDefinition dataclass."""

    def test_defaults(self):
        sd = StageDefinition(name="Test Stage")
        assert sd.name == "Test Stage"
        assert sd.script is None
        assert sd.method is None
        assert sd.args == []
        assert sd.allow_skip is False
        assert sd.depends_on == []
        assert sd.tags == []

    def test_full_init(self):
        sd = StageDefinition(
            name="Stage",
            script="01_test.py",
            args=["--verbose"],
            allow_skip=True,
            depends_on=["Setup"],
            tags=["core", "tests"],
        )
        assert sd.script == "01_test.py"
        assert sd.allow_skip is True
        assert sd.depends_on == ["Setup"]
        assert sd.tags == ["core", "tests"]


class TestPipelineDAGFromYAML:
    """Test YAML loading."""

    def test_load_default_yaml(self):
        """Test loading the actual default pipeline.yaml."""
        # Resolve from test file location → repo root
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        yaml_path = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
        dag = PipelineDAG.from_yaml(yaml_path)
        stages = dag.sorted_stages()
        assert len(stages) >= 8  # At least the core stages
        assert stages[0].name == "Clean Output Directories"

    def test_load_from_tmp(self, tmp_path):
        """Test loading a custom YAML."""
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text("""
opt_in_tags: [experimental]
stages:
  - name: A
    key: a
    method: do_a
    tags: [core]
  - name: B
    key: b
    script: scripts/b.py
    depends_on: [A]
    tags: [core]
""")
        dag = PipelineDAG.from_yaml(yaml_file)
        assert len(dag.stages) == 2
        assert dag.opt_in_tags == frozenset({"experimental"})

    def test_from_dict_reads_opt_in_tags(self):
        dag = PipelineDAG.from_dict(
            {
                "opt_in_tags": ["ebook", "docxplus"],
                "stages": [{"name": "A", "key": "a", "method": "do_a", "tags": ["core"]}],
            }
        )
        assert dag.opt_in_tags == frozenset({"ebook", "docxplus"})
        assert opt_in_tags_from_mapping({"opt_in_tags": ["ebook"]}) == frozenset({"ebook"})

    def test_invalid_yaml_raises(self, tmp_path):
        """Test that missing stages key raises ValueError."""
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text("foo: bar\n")
        with pytest.raises(ValueError, match="stages"):
            PipelineDAG.from_yaml(yaml_file)


class TestPipelineDAGFromDict:
    """Test dict construction."""

    def test_from_dict_basic(self):
        data = {
            "stages": [
                {"name": "A", "key": "a", "method": "do_a", "tags": ["core"]},
                {"name": "B", "key": "b", "script": "scripts/b.py", "depends_on": ["A"], "tags": ["core"]},
            ]
        }
        dag = PipelineDAG.from_dict(data)
        assert len(dag.stages) == 2

    def test_from_dict_empty(self):
        dag = PipelineDAG.from_dict({"stages": []})
        assert len(dag.stages) == 0


class TestPipelineDAGValidation:
    """Test validation of stage definitions."""

    def test_duplicate_names_raise(self):
        with pytest.raises(ValueError, match="Duplicate"):
            PipelineDAG(
                [
                    _stage(name="A"),
                    _stage(name="A"),
                ]
            )


class TestPipelineDAGFiltering:
    """Test tag-based and stage name filtering."""

    def _make_dag(self):
        return PipelineDAG(
            [
                _stage(name="Clean", method="clean", tags=["core", "clean"]),
                _stage(name="Setup", method="setup", tags=["core"]),
                _stage(name="Tests", script="test.py", tags=["core", "tests"]),
                _stage(name="LLM Review", script="llm.py", tags=["llm"]),
            ]
        )

    def test_exclude_tags(self):
        dag = self._make_dag()
        dag.filter_tags(exclude={"llm"})
        names = [s.name for s in dag.stages]
        assert "LLM Review" not in names
        assert "Clean" in names

    def test_include_only_tags(self):
        dag = self._make_dag()
        dag.filter_tags(include_only={"tests"})
        names = [s.name for s in dag.stages]
        assert names == ["Tests"]

    def test_remove_stage(self):
        dag = self._make_dag()
        dag.remove_stage("Clean")
        names = [s.name for s in dag.stages]
        assert "Clean" not in names
        assert len(names) == 3


class TestPipelineDAGSorting:
    """Test topological sorting."""

    def test_linear_order_preserved(self):
        dag = PipelineDAG(
            [
                _stage(name="A"),
                _stage(name="B", depends_on=["A"]),
                _stage(name="C", depends_on=["B"]),
            ]
        )
        sorted_ = dag.sorted_stages()
        assert [s.name for s in sorted_] == ["A", "B", "C"]

    def test_diamond_dependency(self):
        dag = PipelineDAG(
            [
                _stage(name="A"),
                _stage(name="B", depends_on=["A"]),
                _stage(name="C", depends_on=["A"]),
                _stage(name="D", depends_on=["B", "C"]),
            ]
        )
        sorted_ = dag.sorted_stages()
        names = [s.name for s in sorted_]
        assert names.index("A") < names.index("B")
        assert names.index("A") < names.index("C")
        assert names.index("B") < names.index("D")
        assert names.index("C") < names.index("D")

    def test_cycle_detected(self):
        dag = PipelineDAG(
            [
                _stage(name="A", depends_on=["C"]),
                _stage(name="B", depends_on=["A"]),
                _stage(name="C", depends_on=["B"]),
            ]
        )
        with pytest.raises(ValueError, match="Cycle"):
            dag.sorted_stages()

    def test_unknown_source_dependency_rejected(self):
        with pytest.raises(ValueError, match="unknown stage 'X'"):
            PipelineDAG([_stage("A"), _stage("C", depends_on=["X"])])

    def test_dropped_dependency_edges_recorded(self):
        dag = PipelineDAG([_stage("A"), _stage("B", depends_on=["A"])])
        dag.remove_stage("A")
        dag.sorted_stages()
        assert dag.dropped_dependency_edges == [("B", "A")]

    def test_no_dropped_edges_when_all_present(self):
        """Negative control: a fully-resolved DAG records zero dropped edges."""
        dag = PipelineDAG(
            [
                _stage(name="A"),
                _stage(name="B", depends_on=["A"]),
                _stage(name="C", depends_on=["B"]),
            ]
        )
        dag.sorted_stages()
        assert dag.dropped_dependency_edges == []

    def test_filtering_out_a_dependency_warns_and_records(self, caplog):
        """Filtering out a stage another stage depends on is observable."""
        import logging

        dag = PipelineDAG(
            [
                _stage(name="A", tags=["prep"]),
                _stage(name="B", depends_on=["A"], tags=["core"]),
            ]
        )
        dag.filter_tags(exclude={"prep"})  # drops A; B still depends on it
        with caplog.at_level(logging.WARNING, logger="infrastructure.core.pipeline.dag"):
            dag.sorted_stages()
        assert dag.dropped_dependency_edges == [("B", "A")]
        assert any("dropped" in m and "B->A" in m for m in caplog.messages)

    def test_sort_preserves_original_order_for_independent_stages(self):
        """Independent stages should preserve their declaration order."""
        dag = PipelineDAG(
            [
                _stage(name="C"),
                _stage(name="A"),
                _stage(name="B"),
            ]
        )
        sorted_ = dag.sorted_stages()
        assert [s.name for s in sorted_] == ["C", "A", "B"]


def test_from_yaml_missing_stage_name_raises_valueerror_with_source(tmp_path):
    """A stage entry without 'name' raises ValueError naming the source."""
    yaml_file = tmp_path / "pipeline.yaml"
    yaml_file.write_text(
        "stages:\n  - script: scripts/run.py\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="pipeline.yaml"):
        PipelineDAG.from_yaml(yaml_file)


def test_from_dict_rejects_non_mapping_stage_entries():
    """from_dict applies the same per-entry validation as from_yaml."""
    with pytest.raises(ValueError, match="mapping"):
        PipelineDAG.from_dict({"stages": ["not-a-mapping"]})


def test_from_dict_rejects_missing_stage_name():
    """from_dict fails closed on a stage entry without a name."""
    with pytest.raises(ValueError, match="name"):
        PipelineDAG.from_dict({"stages": [{"script": "scripts/run.py"}]})


@pytest.mark.parametrize("value", [None, "stages", {}, 3])
def test_stages_container_requires_list(value):
    with pytest.raises(ValueError, match="stages.*list"):
        PipelineDAG.from_dict({"stages": value})


@pytest.mark.parametrize(
    "field,value,diagnostic",
    [
        ("key", None, "key"),
        ("key", "Bad Key", "key"),
        ("script", "runner.py", "repository-relative"),
        ("script", "../runner.py", "repository-relative"),
        ("script", 9, "script"),
        ("method", "run stages", "identifier"),
        ("allow_skip", "false", "boolean"),
        ("args", "--verbose", "list"),
        ("tags", "core", "list"),
        ("depends_on", "Setup", "list"),
        ("unknown", True, "unsupported"),
        ("contract", {"retry_policy": -1}, "retry_policy"),
        ("contract", {"retry_policy": True}, "retry_policy"),
        ("contract", {"retry_policy": "2"}, "retry_policy"),
        ("contract", {"output_artifacts": "output/"}, "list"),
        ("hooks", {"timeout_seconds": 0}, "timeout_seconds"),
        ("hooks", {"timeout_seconds": True}, "timeout_seconds"),
        ("hooks", {"timeout_seconds": 1.5}, "timeout_seconds"),
        ("hooks", {"run_in_ci": "false"}, "boolean"),
        ("hooks", {"pre_stage": [[]]}, "empty"),
    ],
)
def test_yaml_and_dict_reject_invalid_stage_types(tmp_path, field, value, diagnostic):
    import yaml

    entry = {"name": "Stage", "key": "stage", "method": "run_stage"}
    if field == "script":
        entry.pop("method")
    entry[field] = value
    data = {"stages": [entry]}
    path = tmp_path / "pipeline.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    for load in (lambda: PipelineDAG.from_dict(data), lambda: PipelineDAG.from_yaml(path)):
        with pytest.raises(ValueError, match=diagnostic):
            load()


def test_direct_dag_construction_cannot_bypass_flag_or_key_checks():
    with pytest.raises(ValueError, match="boolean"):
        PipelineDAG([StageDefinition(name="Stage", key="stage", method="run_stage", allow_skip="false")])
    with pytest.raises(ValueError, match="key"):
        PipelineDAG([StageDefinition(name="Stage", method="run_stage")])


def test_duplicate_stable_keys_rejected():
    with pytest.raises(ValueError, match="Duplicate stage keys"):
        PipelineDAG([_stage("First", key="same"), _stage("Second", key="same")])


def test_from_dict_rejects_missing_stages_key():
    """from_dict requires the top-level 'stages' key like from_yaml."""
    with pytest.raises(ValueError, match="stages"):
        PipelineDAG.from_dict({})
