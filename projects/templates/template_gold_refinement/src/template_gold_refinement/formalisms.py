from __future__ import annotations

from dataclasses import asdict, dataclass
import re

_DISPLAY_CODE_TOKEN = re.compile(r"`[^`\n]*`|[A-Za-z_][A-Za-z0-9_./:#*-]*")
_DISPLAY_CAMELCASE = re.compile(r"[A-Z][a-z]+(?:[A-Z][A-Za-z0-9]+)+")
_DISPLAY_DOTTED_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]+\.(?:[A-Za-z_][A-Za-z0-9_]+\.)*[A-Za-z_][A-Za-z0-9_]+")


def format_table_code(value: str) -> str:
    """Mark code identifiers in declared display fields without changing data.

    Existing inline code is retained. Square-bracket indices remain outside
    the code span so Pandoc emits the anchor prefix as simple breakable texttt.
    This presentation pass adds only backticks, never rewrites source anchors.
    """
    if len(value) > 8192 or "\n" in value or "``" in value or value.count("`") % 2:
        return value
    plain = re.sub(r"`[^`\n]*`", "", value)
    # Refuse authored Markdown syntax rather than rewriting inside its delimiters.
    # Only a plain numeric provenance suffix is admitted outside existing code.
    plain = re.sub(r"(?<=[A-Za-z0-9_])\[[0-9]{1,6}\]", "", plain)
    if any(character in plain for character in r"\{}$<>|[]") or "**" in plain or "://" in plain:
        return value
    if re.search(r"(?<!\w)_[^\s]*_(?!\w)|(?:^|\s)[#!]", plain):
        return value
    for word in plain.split():
        if "*" in word and (
            word.count("*") != 1
            or "/" not in word
            or re.fullmatch(r"[A-Za-z0-9_./:#-]+\*[A-Za-z0-9_./:#*-]*", word) is None
        ):
            return value

    def replace(match: re.Match[str]) -> str:
        token = match[0]
        if token.startswith("`"):
            return token
        identifier = token.rstrip(".")
        if (
            "/" in identifier
            or "_" in identifier
            or ("::" in identifier and not identifier.endswith(":"))
            or _DISPLAY_DOTTED_IDENTIFIER.fullmatch(identifier)
            or _DISPLAY_CAMELCASE.fullmatch(identifier)
        ):
            return "`" + identifier + "`" + token[len(identifier) :]
        return token

    return _DISPLAY_CODE_TOKEN.sub(replace, value)


@dataclass(frozen=True)
class Formalism:
    """Data container for Formalism."""

    formalism_id: str
    title: str
    equation_label: str
    source: str
    statement: str
    formula: str
    interpretation: str

    def as_dict(self) -> dict[str, str]:
        """Process as dict."""
        return asdict(self)


FORMALISMS: tuple[Formalism, ...] = (
    Formalism(
        formalism_id="F1",
        title="Purity functional",
        equation_label="eq:purity_functional",
        source="src/template_gold_refinement/purity.py::format_purity",
        statement="Manuscript purity is treated as a bounded fraction mapped to a reader-facing grade.",
        formula=r"\pi(s) \in [0, 1], \qquad g(s) = \operatorname{karat}(\pi(s))",
        interpretation="The value is descriptive: it summarizes local validation state rather than external quality.",
    ),
    Formalism(
        formalism_id="F2",
        title="Monotone refinement",
        equation_label="eq:monotone_refinery",
        source="src/template_gold_refinement/purity.py::assert_monotone_increase",
        statement="A valid refinery run requires every stage to improve the previous purity state.",
        formula=r"\pi_0 < \pi_1 < \cdots < \pi_n",
        interpretation="The test suite rejects equal or decreasing stage outputs.",
    ),
    Formalism(
        formalism_id="F3",
        title="Token-selection digest",
        equation_label="eq:token_digest",
        source="src/template_gold_refinement/composition.py::_choose_value",
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
        source="src/template_gold_refinement/evidence.py::EvidenceRegistry.support_rate",
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
        formula=r"\mathbf{v} = (v_{tokens}, v_{figures}, v_{claims}, v_{render}, v_{references}, v_{security})",
        interpretation="A publication claim is only as strong as the weakest required gate.",
    ),
    Formalism(
        formalism_id="F6",
        title="Certification predicate",
        equation_label="eq:certification_predicate",
        source="src/template_gold_refinement/refinery.py::RefineryResult.is_nine_nines_certified",
        statement="Certification is a predicate over final purity and validation readiness.",
        formula=r"\operatorname{certified}(r) \iff \pi_{final}(r) \geq 0.999999999 \land gates(r)",
        interpretation="The predicate binds the nine-nines metaphor to the actual validation chain.",
    ),
    Formalism(
        formalism_id="F7",
        title="Adversarial assay",
        equation_label="eq:adversarial_assay",
        source="src/template_gold_refinement/security_assay.py::build_security_assay",
        statement="Certification requires an explicit adversarial and supply-chain scope, not only ordinary gate success.",
        formula=(
            r"\operatorname{certified}_{adv}(r) \iff \operatorname{certified}(r) "
            r"\land \forall a \in A_r:\ threat(a) \land standard(a) \land evidence(a) "
            r"\land validator(a) \land boundary(a)"
        ),
        interpretation="The adversarial assay defines scope and evidence requirements; it is not proof of compliance or live scan findings.",
    ),
)


def formalism_count() -> int:
    """Process formalism count."""
    return len(FORMALISMS)


def equation_labels() -> tuple[str, ...]:
    """Process equation labels."""
    return tuple(item.equation_label for item in FORMALISMS)


def formalism_table_rows() -> str:
    """Process formalism table rows."""
    return "\n".join(
        f"| {item.formalism_id} | {item.title} | [@{item.equation_label}] | `{item.source}` |" for item in FORMALISMS
    )


def formalism_equation_blocks() -> str:
    """Process formalism equation blocks."""
    blocks = []
    for item in FORMALISMS:
        blocks.append(
            f"**{item.formalism_id}: {item.title}.** {item.statement}\n\n"
            f"$$\n{item.formula}\n$$ {{#{item.equation_label}}}\n\n"
            f"{item.interpretation} Source: `{item.source}`."
        )
    return "\n\n".join(blocks)


def formalism_traceability_rows() -> str:
    """Process formalism traceability rows."""
    return "\n".join(
        f"| {item.formalism_id} | {item.equation_label} | {format_table_code(item.source)} | {item.statement} |"
        for item in FORMALISMS
    )


def formalism_records() -> list[dict[str, str]]:
    """Process formalism records."""
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
    "format_table_code",
]
