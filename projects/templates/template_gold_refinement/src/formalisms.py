from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Formalism:
    formalism_id: str
    title: str
    equation_label: str
    source: str
    statement: str
    formula: str
    interpretation: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


FORMALISMS: tuple[Formalism, ...] = (
    Formalism(
        formalism_id="F1",
        title="Purity functional",
        equation_label="eq:purity_functional",
        source="src/purity.py::format_purity",
        statement="Manuscript purity is treated as a bounded fraction mapped to a reader-facing grade.",
        formula=r"\pi(s) \in [0, 1], \qquad g(s) = \operatorname{karat}(\pi(s))",
        interpretation="The value is descriptive: it summarizes local validation state rather than external quality.",
    ),
    Formalism(
        formalism_id="F2",
        title="Monotone refinement",
        equation_label="eq:monotone_refinery",
        source="src/refinery.py::assert_monotone_increase",
        statement="A valid refinery run requires every stage to improve the previous purity state.",
        formula=r"\pi_0 < \pi_1 < \cdots < \pi_n",
        interpretation="The test suite rejects equal or decreasing stage outputs.",
    ),
    Formalism(
        formalism_id="F3",
        title="Token-selection digest",
        equation_label="eq:token_digest",
        source="src/composition.py::_choose_value",
        statement="Every mega-madlib token is selected from config-owned inventory by a deterministic digest.",
        formula=(
            r"i = \operatorname{int}(\operatorname{SHA256}(seed \Vert slot \Vert category "
            r"\Vert ordinal \Vert inventory)_{0:12}, 16) \bmod \lvert inventory \rvert"
        ),
        interpretation="Changing the seed or inventory changes the plan; replaying both reproduces it.",
    ),
    Formalism(
        formalism_id="F4",
        title="Claim-support fraction",
        equation_label="eq:claim_support",
        source="src/evidence.py::EvidenceRegistry.support_rate",
        statement="Contribution claims are assayed by counting supported local evidence pointers.",
        formula=r"\sigma = \frac{\lvert\{c \in C : supported(c)\}\rvert}{\lvert C \rvert}",
        interpretation="The numerator and denominator come from the project-local claim-support registry.",
    ),
    Formalism(
        formalism_id="F5",
        title="Integrity vector",
        equation_label="eq:integrity_vector",
        source="manuscript/config.yaml#gold_refinement.audit_rules",
        statement="Scientific integrity is represented as a vector of gate outcomes rather than one scalar badge.",
        formula=r"\mathbf{v} = (v_{tokens}, v_{figures}, v_{claims}, v_{render}, v_{references})",
        interpretation="A publication claim is only as strong as the weakest required gate.",
    ),
    Formalism(
        formalism_id="F6",
        title="Certification predicate",
        equation_label="eq:certification_predicate",
        source="src/refinery.py::RefineryResult.is_nine_nines_certified",
        statement="Certification is a predicate over final purity and validation readiness.",
        formula=r"\operatorname{certified}(r) \iff \pi_{final}(r) \geq 0.999999999 \land gates(r)",
        interpretation="The predicate binds the nine-nines metaphor to the actual validation chain.",
    ),
)


def formalism_count() -> int:
    return len(FORMALISMS)


def equation_labels() -> tuple[str, ...]:
    return tuple(item.equation_label for item in FORMALISMS)


def formalism_table_rows() -> str:
    return "\n".join(
        f"| {item.formalism_id} | {item.title} | [@{item.equation_label}] | `{item.source}` |" for item in FORMALISMS
    )


def formalism_equation_blocks() -> str:
    blocks = []
    for item in FORMALISMS:
        blocks.append(
            f"**{item.formalism_id}: {item.title}.** {item.statement}\n\n"
            f"$$\n{item.formula}\n$$ {{#{item.equation_label}}}\n\n"
            f"{item.interpretation} Source: `{item.source}`."
        )
    return "\n\n".join(blocks)


def formalism_traceability_rows() -> str:
    return "\n".join(
        f"| {item.formalism_id} | {item.equation_label} | {item.source} | {item.statement} |" for item in FORMALISMS
    )


def formalism_records() -> list[dict[str, str]]:
    return [item.as_dict() for item in FORMALISMS]


__all__ = [
    "FORMALISMS",
    "Formalism",
    "equation_labels",
    "formalism_count",
    "formalism_equation_blocks",
    "formalism_records",
    "formalism_table_rows",
    "formalism_traceability_rows",
]
