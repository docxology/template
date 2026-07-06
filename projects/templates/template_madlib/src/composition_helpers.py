from __future__ import annotations

from collections.abc import Iterable

from .config import MethodStep, PipelinePhase


def _disabled_section_body(section: str) -> str:
    return "\n\n".join(
        [
            (f"This section is disabled by `madlib.section_conditions.{section}` in `manuscript/config.yaml`."),
            (
                "The placeholder still resolves so reviewers can distinguish an intentionally disabled section "
                "from a missing generation step."
            ),
        ]
    )


def _protocol_sentence(steps: tuple[MethodStep, ...]) -> str:
    return "; ".join(f"{step.name} produces `{step.output}`" for step in steps)


def _phase_sentence(phases: tuple[PipelinePhase, ...]) -> str:
    return "; ".join(f"{phase.name} maps `{phase.input_artifact}` to `{phase.output_artifact}`" for phase in phases)


def _sentence_list(items: tuple[str, ...]) -> str:
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _comma_join(items: Iterable[str]) -> str:
    values = tuple(items)
    return ", ".join(values) if values else "none"


def _figure_markdown(alt: str, filename: str, label: str) -> str:
    return f"![{alt}](../output/figures/{filename}){{#{label}}}"
