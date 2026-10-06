"""Menu choices and public stable keys from the canonical DAG."""

from pathlib import Path
from typing import Final

from infrastructure.core.pipeline.dag import PipelineDAG

MENU_KEY_TO_STAGE: Final[dict[str, str]] = {
    "0": "setup",
    "1": "project_tests",
    "2": "analysis",
    "3": "render_pdf",
    "4": "validate",
    "5": "copy",
    "6": "llm_reviews",
    "7": "llm_translations",
}


def known_stage_keys() -> frozenset[str]:
    """Return declared keys, including executable builtins and opt-in stages."""
    dag = PipelineDAG.from_yaml(Path(__file__).with_name("pipeline.yaml"))
    return frozenset(stage.key for stage in dag.stages if stage.key is not None)


__all__ = ["MENU_KEY_TO_STAGE", "known_stage_keys"]
