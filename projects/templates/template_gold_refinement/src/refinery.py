"""Gold-refinery pipeline: ore → smelting → assaying → cupellation → certification.

Each stage has a name, a metallurgical operation, a manuscript-composition
analogy, an input purity, and an output purity. Purity increases monotonically
across stages. The refinery is the load-bearing pipeline — not a rhetorical
frame — because each stage maps to a real template-infrastructure operation.

Stages:
  1. ore          — raw draft prose, unrefined claims          (~37.5%, 9K)
  2. smelting     — remove dross: filler, unsupported claims   (~75%, 18K)
  3. assaying     — test claims against evidence                (~91.7%, 22K)
  4. cupellation  — cross-reference resolution, citation audit  (~99.0%, 24K)
  5. certification — full pipeline validation, nine-nines       (~99.9999999%)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

try:
    from .purity import (
        NINE_NINES_PURITY,
        KaratGrade,
        assert_monotone_increase,
        karat_for_purity,
    )
except ImportError:
    from purity import (  # type: ignore[no-redef]
        NINE_NINES_PURITY,
        KaratGrade,
        assert_monotone_increase,
        karat_for_purity,
    )


@dataclass(frozen=True)
class RefinementStage:
    """One stage of the gold-refinery pipeline."""

    name: str
    metallurgical_operation: str
    manuscript_operation: str
    input_purity: float
    output_purity: float
    order: int

    @property
    def karat_grade(self) -> KaratGrade:
        """Process karat grade."""
        return karat_for_purity(self.output_purity)

    @property
    def purity_gain(self) -> float:
        """Process purity gain."""
        return self.output_purity - self.input_purity

    @property
    def label(self) -> str:
        """Process label."""
        return f"{self.order}. {self.name} ({self.karat_grade.label})"


# The five canonical refinement stages
CANONICAL_STAGES: tuple[RefinementStage, ...] = (
    RefinementStage(
        name="ore",
        metallurgical_operation="Extract raw gold-bearing ore from the earth",
        manuscript_operation="Draft prose and raw claims from source material",
        input_purity=0.10,
        output_purity=0.375,
        order=1,
    ),
    RefinementStage(
        name="smelting",
        metallurgical_operation="Heat ore to separate gold from slag and dross",
        manuscript_operation="Remove filler, unsupported claims, and redundant prose",
        input_purity=0.375,
        output_purity=0.750,
        order=2,
    ),
    RefinementStage(
        name="assaying",
        metallurgical_operation="Test a sample to determine gold content and impurities",
        manuscript_operation="Validate every claim against evidence and citation",
        input_purity=0.750,
        output_purity=0.9167,
        order=3,
    ),
    RefinementStage(
        name="cupellation",
        metallurgical_operation="Refine by blowing air through molten lead-gold alloy",
        manuscript_operation="Resolve cross-references and audit citation integrity",
        input_purity=0.9167,
        output_purity=0.999,
        order=4,
    ),
    RefinementStage(
        name="certification",
        metallurgical_operation="Certify purity grade and stamp hallmark",
        manuscript_operation="Full pipeline validation, reproducibility, nine-nines",
        input_purity=0.999,
        output_purity=NINE_NINES_PURITY,
        order=5,
    ),
)


@dataclass(frozen=True)
class RefineryResult:
    """Result of running the refinery pipeline."""

    stages: tuple[RefinementStage, ...]
    final_purity: float
    final_karat: KaratGrade
    total_purity_gain: float

    @property
    def stage_count(self) -> int:
        """Process stage count."""
        return len(self.stages)

    @property
    def stage_labels(self) -> tuple[str, ...]:
        """Process stage labels."""
        return tuple(s.label for s in self.stages)

    @property
    def purity_sequence(self) -> tuple[float, ...]:
        """All purity values including input to first stage and output of each."""
        if not self.stages:
            return ()
        return (self.stages[0].input_purity,) + tuple(s.output_purity for s in self.stages)

    @property
    def is_nine_nines_certified(self) -> bool:
        """Check whether nine nines certified."""
        return bool(self.final_purity >= NINE_NINES_PURITY)


def run_refinery(stages: Sequence[RefinementStage] | None = None) -> RefineryResult:
    """Run the refinery pipeline and return the result.

    Validates monotone purity increase across all stages before returning.
    """
    pipeline = tuple(stages) if stages is not None else CANONICAL_STAGES
    if not pipeline:
        raise ValueError("Refinery pipeline must have at least one stage")

    purities = [pipeline[0].input_purity] + [s.output_purity for s in pipeline]
    assert_monotone_increase(purities)

    # Validate stage ordering
    for i, stage in enumerate(pipeline):
        if stage.order != i + 1:
            raise ValueError(f"Stage order mismatch: stage {i} has order {stage.order}, expected {i + 1}")

    final = pipeline[-1]
    total_gain = final.output_purity - pipeline[0].input_purity
    return RefineryResult(
        stages=pipeline,
        final_purity=final.output_purity,
        final_karat=karat_for_purity(final.output_purity),
        total_purity_gain=total_gain,
    )


def stage_by_name(name: str, stages: Sequence[RefinementStage] | None = None) -> RefinementStage:
    """Look up a stage by name (case-insensitive)."""
    pipeline = tuple(stages) if stages is not None else CANONICAL_STAGES
    lower = name.lower()
    for stage in pipeline:
        if stage.name.lower() == lower:
            return stage
    raise KeyError(f"No refinement stage named '{name}'")


def stage_by_order(order: int, stages: Sequence[RefinementStage] | None = None) -> RefinementStage:
    """Look up a stage by its 1-based order index."""
    pipeline = tuple(stages) if stages is not None else CANONICAL_STAGES
    for stage in pipeline:
        if stage.order == order:
            return stage
    raise KeyError(f"No refinement stage with order {order}")


__all__ = [
    "CANONICAL_STAGES",
    "RefinementStage",
    "RefineryResult",
    "run_refinery",
    "stage_by_name",
    "stage_by_order",
]
