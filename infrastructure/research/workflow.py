"""Research workflow stages and orchestration.

This module defines a lightweight, stage-based research workflow with
seven canonical stages from SCOPE through WRITE.  It is designed to be
used as a planning and tracking aid, not as an execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(str, Enum):
    """Execution status of a research stage."""

    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"
    skipped = "skipped"
    blocked = "blocked"


@dataclass(frozen=True)
class ResearchStage:
    """A single stage in a research workflow.

    Attributes:
        name: Stage identifier, e.g. ``"scope"``.
        label: Human-readable label.
        description: What this stage accomplishes.
        inputs: Expected input artefact types.
        outputs: Expected output artefact types.
        gate: Acceptance condition for the stage to be considered complete.
        status: Current execution status.
        order: Ordinal position (0-indexed) within the workflow.
    """

    name: str
    label: str
    description: str
    inputs: tuple[str, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)
    gate: str = ""
    status: StageStatus = StageStatus.pending
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stage to a JSON-safe dictionary."""
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "gate": self.gate,
            "status": self.status.value,
            "order": self.order,
        }


# ---------------------------------------------------------------------------
# Built-in stage definitions
# ---------------------------------------------------------------------------

_STAGE_DEFS: list[dict[str, Any]] = [
    {
        "name": "scope",
        "label": "Scope",
        "description": (
            "Define the research question, success criteria, and scope boundaries. "
            "Produce a domain profile and experiment plan skeleton."
        ),
        "inputs": (),
        "outputs": ("domain_profile.yaml", "experiment_plan.yaml"),
        "gate": "domain_profile.yaml and experiment_plan.yaml exist and are valid",
        "order": 0,
    },
    {
        "name": "survey",
        "label": "Survey",
        "description": (
            "Conduct a systematic literature survey across relevant databases. Collect and normalise Paper records."
        ),
        "inputs": ("domain_profile.yaml",),
        "outputs": ("output/literature/corpus.json",),
        "gate": "literature corpus non-empty; at least 5 unique sources",
        "order": 1,
    },
    {
        "name": "hypothesise",
        "label": "Hypothesise",
        "description": ("Distil survey findings into testable hypotheses or claims. Populate the idea ledger."),
        "inputs": ("output/literature/corpus.json",),
        "outputs": ("output/data/idea_ledger.json",),
        "gate": "idea_ledger.json contains at least one hypothesis",
        "order": 2,
    },
    {
        "name": "experiment",
        "label": "Experiment",
        "description": (
            "Execute or plan the experiments described in the experiment plan. Record runs in the provenance DAG."
        ),
        "inputs": ("experiment_plan.yaml", "output/data/idea_ledger.json"),
        "outputs": ("output/data/run_ledger.json", "output/provenance/dag.json"),
        "gate": "run_ledger.json contains at least one completed run",
        "order": 3,
    },
    {
        "name": "validate",
        "label": "Validate",
        "description": (
            "Check experiment results against the success criteria. Produce an evidence registry and validation report."
        ),
        "inputs": ("output/data/run_ledger.json",),
        "outputs": ("output/reports/validation_report.json",),
        "gate": "validation report shows all required checks passing",
        "order": 4,
    },
    {
        "name": "review",
        "label": "Review",
        "description": (
            "Human or agent review of findings; record review decisions. Gate the pipeline before manuscript writing."
        ),
        "inputs": ("output/reports/validation_report.json",),
        "outputs": ("output/data/review_decisions.json",),
        "gate": "all required review gates approved",
        "order": 5,
    },
    {
        "name": "write",
        "label": "Write",
        "description": (
            "Author or update the manuscript with validated findings. Produce the final research output artefacts."
        ),
        "inputs": ("output/data/review_decisions.json",),
        "outputs": ("manuscript/", "output/artifacts/"),
        "gate": "manuscript compiles; all required artefacts present",
        "order": 6,
    },
]


class ResearchWorkflow:
    """Seven-stage research workflow plan.

    The workflow is immutable once constructed.  Use :meth:`stage` to query
    individual stages and :meth:`describe` for a human-readable overview.

    Usage::

        workflow = ResearchWorkflow()
        print(workflow.describe())
        s = workflow.stage("experiment")
        print(s.gate)
    """

    STAGE_NAMES = ("scope", "survey", "hypothesise", "experiment", "validate", "review", "write")

    def __init__(self, stages: list[ResearchStage] | None = None) -> None:
        """Initialize the workflow, defaulting to the built-in seven stages."""
        if stages is not None:
            self._stages = {s.name: s for s in stages}
        else:
            self._stages = {
                d["name"]: ResearchStage(
                    name=d["name"],
                    label=d["label"],
                    description=d["description"],
                    inputs=tuple(d.get("inputs", ())),
                    outputs=tuple(d.get("outputs", ())),
                    gate=d.get("gate", ""),
                    order=d["order"],
                )
                for d in _STAGE_DEFS
            }

    def stage(self, name: str) -> ResearchStage:
        """Return the :class:`ResearchStage` named *name*.

        Args:
            name: Stage identifier.

        Raises:
            KeyError: When *name* is not a known stage.
        """
        try:
            return self._stages[name]
        except KeyError:
            valid = ", ".join(sorted(self._stages))
            raise KeyError(f"Unknown stage '{name}'. Valid stages: {valid}") from None

    def all_stages(self) -> list[ResearchStage]:
        """Return all stages ordered by their ``order`` attribute."""
        return sorted(self._stages.values(), key=lambda s: s.order)

    def describe(self) -> str:
        """Return a human-readable multi-line description of the workflow."""
        lines: list[str] = ["Research Workflow", "=" * 40]
        for s in self.all_stages():
            lines.append(f"\n[{s.order}] {s.label.upper()} ({s.name})")
            lines.append(f"    {s.description}")
            if s.inputs:
                lines.append(f"    Inputs:  {', '.join(s.inputs)}")
            if s.outputs:
                lines.append(f"    Outputs: {', '.join(s.outputs)}")
            if s.gate:
                lines.append(f"    Gate:    {s.gate}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe mapping."""
        return {"stages": [s.to_dict() for s in self.all_stages()]}

    def __len__(self) -> int:
        return len(self._stages)

    def __repr__(self) -> str:
        return f"ResearchWorkflow(stages={list(self._stages)})"


__all__ = [
    "ResearchStage",
    "ResearchWorkflow",
    "StageStatus",
]
