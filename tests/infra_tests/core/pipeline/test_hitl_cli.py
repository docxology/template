"""Canonical HITL command identity and invalid-invocation boundaries."""

from pathlib import Path

import pytest

from infrastructure.core.pipeline.hitl_cli import PipelineArgs, handle_hitl_command
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


@pytest.mark.parametrize(
    "options",
    [
        {"hitl_command": "respond"},
        {"hitl_command": "validate-response"},
        {"hitl_command": "guide", "message": "Guidance"},
        {"hitl_command": "guide", "hitl_stage": 1},
        {"hitl_command": "guide", "hitl_stage": 0, "message": "Guidance"},
        {"hitl_command": "unknown"},
    ],
)
def test_hitl_missing_options_are_invocation_errors(tmp_path: Path, options: dict) -> None:
    scaffold_pipeline(tmp_path)
    assert handle_hitl_command(PipelineArgs("demo", **options), tmp_path) == 2
    assert not (tmp_path / "projects/demo/output/hitl/decisions.jsonl").exists()


def test_hitl_bare_public_name_uses_canonical_output(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("templates/demo",))
    code = handle_hitl_command(
        PipelineArgs("demo", hitl_command="guide", hitl_stage=1, message="Review the measured result."), tmp_path
    )
    assert code == 0
    assert (tmp_path / "projects/templates/demo/output/hitl/guidance/stage-01.md").is_file()
    assert not (tmp_path / "projects/demo").exists()


def test_hitl_traversal_is_rejected_before_state_write(tmp_path: Path) -> None:
    assert (
        handle_hitl_command(
            PipelineArgs("../outside", hitl_command="guide", hitl_stage=1, message="Guidance"), tmp_path
        )
        == 2
    )
    assert not (tmp_path / "outside").exists()
