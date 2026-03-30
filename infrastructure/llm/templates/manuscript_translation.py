"""Manuscript translation template for abstract generation and translation."""

from __future__ import annotations

from string import Template
from typing import Any

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.templates.base import ResearchTemplate
from infrastructure.llm.templates.helpers import (
    content_requirements,
    format_requirements,
    section_structure,
    token_budget_awareness,
    validation_hints,
)

# Supported translation languages with full names for prompts
TRANSLATION_LANGUAGES = {
    "zh": "Chinese (Simplified)",
    "hi": "Hindi",
    "ru": "Russian",
    "de": "German",
}


class ManuscriptTranslationAbstract(ResearchTemplate):
    """Template for generating a technical abstract and translating to target language.

    Produces a medium-length technical abstract (~200-400 words in English),
    then translates it to the specified target language.

    Uses manuscript-first structure with task instructions at end
    for better LLM attention to the actual content.
    """

    template_str = """=== MANUSCRIPT BEGIN ===

${text}

=== MANUSCRIPT END ===

TASK: Write a technical abstract summary of the manuscript, then translate it to ${target_language}.

${format_requirements}

${section_structure}

${token_budget_awareness}

${content_requirements}

${validation_hints}

Begin with the English abstract, then provide the translation:"""

    def render(
        self,
        text: str | None = None,
        target_language: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render template with enhanced constraints.

        Note: This signature has 4 positional params (vs. 3 in sibling classes) because
        translation requires a target_language that other review templates do not need.

        Args:
            text: Manuscript text (required)
            target_language: Target language name (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text and target_language can be passed here too)
        """
        # Extract from kwargs if not provided as positional args
        if text is None:
            text = kwargs.pop("text", None)
        if target_language is None:
            target_language = kwargs.pop("target_language", None)

        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)  # noqa: E501
        if text is None:
            raise LLMTemplateError("Missing template variable: text", context={"required": "text"})
        if target_language is None:
            raise LLMTemplateError(
                "Missing template variable: target_language",
                context={"required": "target_language"},
            )
        required_headers = ["## English Abstract", f"## {target_language} Translation"]

        section_descriptions = {
            "## English Abstract": "Technical abstract in English (200-400 words) covering: research objective, methodology, key findings, significance",  # noqa: E501
            f"## {target_language} Translation": f"Complete and accurate translation in {target_language}, preserving technical terminology and scientific accuracy",  # noqa: E501
        }

        section_requirements = {
            "English Abstract": "Must include: research objective and motivation, methodology overview, key findings and results, significance and implications",  # noqa: E501
            f"{target_language} Translation": "Must be complete translation (not summary), preserve technical terms, use native script (not transliteration), maintain formal academic tone",  # noqa: E501
        }

        section_budgets = None
        if max_tokens:
            # Split roughly 50/50 between English and translation
            section_budgets = {
                "English Abstract": max_tokens // 2,
                f"{target_language} Translation": max_tokens // 2,
            }

        format_req = format_requirements(
            required_headers,
            markdown_format=True,
            section_requirements=section_requirements,
        )
        section_struct = section_structure(
            required_headers, section_descriptions, required_order=True
        )
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets,
            word_targets={
                "English Abstract": (200, 400),
                f"{target_language} Translation": (200, 400),  # Approximate word count
            },
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True,
        )
        validation = validation_hints(
            word_count_range=(
                400,
                800,
            ),  # Total: ~200-400 English + ~200-400 translation
            required_elements=[
                "English abstract section",
                f"{target_language} translation section",
                "technical terminology preservation",
            ],
            format_checks=[
                "word count",
                "section presence",
                "translation completeness",
                "content relevance",
            ],
        )

        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            target_language=target_language,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs,
        )
