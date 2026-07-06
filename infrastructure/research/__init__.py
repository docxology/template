"""Research workflow module.

Provides a seven-stage research workflow plan (SCOPE → SURVEY → HYPOTHESISE
→ EXPERIMENT → VALIDATE → REVIEW → WRITE) and associated configuration.

Quick start::

    from infrastructure.research import ResearchWorkflow

    wf = ResearchWorkflow()
    print(wf.describe())
    stage = wf.stage("experiment")
    print(stage.gate)
"""

from __future__ import annotations

from infrastructure.research.config import ResearchWorkflowConfig, load_research_workflow_config
from infrastructure.research.workflow import ResearchStage, ResearchWorkflow, StageStatus

__all__ = [
    "ResearchStage",
    "ResearchWorkflow",
    "StageStatus",
    "ResearchWorkflowConfig",
    "load_research_workflow_config",
]
