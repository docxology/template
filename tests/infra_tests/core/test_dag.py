"""Tests for infrastructure.core.pipeline.dag — declarative pipeline DAG engine.

Tests YAML parsing, tag-based filtering, topological sorting, and StageSpec conversion.
Follows No Mocks Policy — all tests use real data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition


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
stages:
  - name: A
    method: do_a
    tags: [core]
  - name: B
    script: b.py
    depends_on: [A]
    tags: [core]
""")
        dag = PipelineDAG.from_yaml(yaml_file)
        assert len(dag.stages) == 2

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
                {"name": "A", "method": "do_a", "tags": ["core"]},
                {"name": "B", "script": "b.py", "depends_on": ["A"], "tags": ["core"]},
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
            PipelineDAG([
                StageDefinition(name="A"),
                StageDefinition(name="A"),
            ])


class TestPipelineDAGFiltering:
    """Test tag-based and stage name filtering."""

    def _make_dag(self):
        return PipelineDAG([
            StageDefinition(name="Clean", method="clean", tags=["core", "clean"]),
            StageDefinition(name="Setup", method="setup", tags=["core"]),
            StageDefinition(name="Tests", script="test.py", tags=["core", "tests"]),
            StageDefinition(name="LLM Review", script="llm.py", tags=["llm"]),
        ])

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
        dag = PipelineDAG([
            StageDefinition(name="A"),
            StageDefinition(name="B", depends_on=["A"]),
            StageDefinition(name="C", depends_on=["B"]),
        ])
        sorted_ = dag.sorted_stages()
        assert [s.name for s in sorted_] == ["A", "B", "C"]

    def test_diamond_dependency(self):
        dag = PipelineDAG([
            StageDefinition(name="A"),
            StageDefinition(name="B", depends_on=["A"]),
            StageDefinition(name="C", depends_on=["A"]),
            StageDefinition(name="D", depends_on=["B", "C"]),
        ])
        sorted_ = dag.sorted_stages()
        names = [s.name for s in sorted_]
        assert names.index("A") < names.index("B")
        assert names.index("A") < names.index("C")
        assert names.index("B") < names.index("D")
        assert names.index("C") < names.index("D")

    def test_cycle_detected(self):
        dag = PipelineDAG([
            StageDefinition(name="A", depends_on=["C"]),
            StageDefinition(name="B", depends_on=["A"]),
            StageDefinition(name="C", depends_on=["B"]),
        ])
        with pytest.raises(ValueError, match="Cycle"):
            dag.sorted_stages()

    def test_filtered_deps_ignored(self):
        """Dependencies that have been filtered out should not block sorting."""
        dag = PipelineDAG([
            StageDefinition(name="A"),
            StageDefinition(name="B", depends_on=["A"]),
            StageDefinition(name="C", depends_on=["X"]),  # X does not exist
        ])
        sorted_ = dag.sorted_stages()
        assert len(sorted_) == 3

    def test_sort_preserves_original_order_for_independent_stages(self):
        """Independent stages should preserve their declaration order."""
        dag = PipelineDAG([
            StageDefinition(name="C"),
            StageDefinition(name="A"),
            StageDefinition(name="B"),
        ])
        sorted_ = dag.sorted_stages()
        assert [s.name for s in sorted_] == ["C", "A", "B"]
