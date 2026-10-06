"""The operating menu uses the effective DAG's stable identities."""

from pathlib import Path

from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.stage_registry import MENU_KEY_TO_STAGE, known_stage_keys


def test_menu_selects_declared_stages_without_aggregate_aliases() -> None:
    keys = known_stage_keys()
    assert set(MENU_KEY_TO_STAGE.values()).issubset(keys)
    assert MENU_KEY_TO_STAGE["1"] == "project_tests"
    assert "tests" not in keys
    assert "executive_report" not in keys
    assert "clean" in keys


def test_public_stage_inventory_comes_from_the_declared_dag() -> None:
    path = Path(__file__).resolve().parents[4] / "infrastructure/core/pipeline/pipeline.yaml"
    dag = PipelineDAG.from_yaml(path)
    assert known_stage_keys() == frozenset(stage.key for stage in dag.stages)
