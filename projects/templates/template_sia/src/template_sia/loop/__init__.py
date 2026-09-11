"""Self-improvement loop cluster: the project adapter for the shared SIA
harness, typed settings from ``manuscript/config.yaml``, the fail-closed
approval contract for live forks, and the deterministic reference target
agent for ``tasks/mini_classify``."""

from .approval import (
    APPROVAL_SCHEMA,
    ApprovalContract,
    validate_approval_contract,
)
from .loop import (
    SiaLoopResult,
    build_run_config,
    fixtures_dir,
    run_sia_loop_project,
)
from .loop_config import (
    ApprovalMode,
    SiaLoopSettings,
    load_paper_title,
    load_sia_settings,
)
from .reference_agent import (
    main,
    majority_label,
    run_agent,
    write_predictions,
)

__all__ = [
    "APPROVAL_SCHEMA",
    "ApprovalContract",
    "validate_approval_contract",
    "SiaLoopResult",
    "build_run_config",
    "fixtures_dir",
    "run_sia_loop_project",
    "ApprovalMode",
    "SiaLoopSettings",
    "load_paper_title",
    "load_sia_settings",
    "main",
    "majority_label",
    "run_agent",
    "write_predictions",
]
