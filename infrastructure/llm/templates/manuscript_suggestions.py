"""Manuscript review templates: methodology review and improvement suggestions."""

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


class ManuscriptMethodologyReview(ResearchTemplate):
    """Template for reviewing methodology and structure of a manuscript.

    Produces a comprehensive methodology assessment with strengths/weaknesses,
    targeting 500-700 words of analytical feedback.

    Uses manuscript-first structure with task instructions at end
    for better LLM attention to the actual content.
    """

    template_str = """=== MANUSCRIPT BEGIN ===

${text}

=== MANUSCRIPT END ===

TASK: Provide a methodology review of the manuscript above.

${format_requirements}

${section_structure}

${token_budget_awareness}

${content_requirements}

${validation_hints}

Begin your methodology review now:"""

    def render(
        self,
        text: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render template with enhanced constraints.

        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop("text", None)

        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)  # noqa: E501
        if text is None:
            raise LLMTemplateError("Missing template variable: text", context={"required": "text"})

        required_headers = [
            "## Methodology Overview",
            "## Research Design Assessment",
            "## Strengths",
            "## Weaknesses",
            "## Recommendations",
        ]

        section_descriptions = {
            "## Methodology Overview": "Summarize the methodology used in the manuscript (100-150 words)",  # noqa: E501
            "## Research Design Assessment": "Evaluate the research design and approach (120-180 words)",  # noqa: E501
            "## Strengths": "Identify methodological strengths with evidence (100-150 words)",
            "## Weaknesses": "Identify methodological weaknesses with evidence (100-150 words)",
            "## Recommendations": "Provide specific improvement recommendations (80-120 words)",
        }

        section_budgets = None
        if max_tokens:
            tokens_per_section = max_tokens // 5
            section_budgets = {
                section.replace("## ", ""): tokens_per_section for section in required_headers
            }

        format_req = format_requirements(required_headers, markdown_format=True)
        section_struct = section_structure(
            required_headers, section_descriptions, required_order=True
        )
        token_budget = token_budget_awareness(
            total_tokens=max_tokens, section_budgets=section_budgets
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True,
        )
        validation = validation_hints(
            word_count_range=(500, 700),
            required_elements=[
                "all 5 section headers",
                "methodology references",
                "strengths and weaknesses",
            ],
            format_checks=["word count", "section presence", "content relevance"],
        )

        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs,
        )


class ManuscriptImprovementSuggestions(ResearchTemplate):
    """Template for generating improvement suggestions for a manuscript.

    Produces a prioritized list of actionable improvements,
    targeting 500-800 words of specific recommendations with detailed rationale.

    Uses manuscript-first structure with task instructions at end
    for better LLM attention to the actual content.
    """

    template_str = """=== MANUSCRIPT BEGIN ===

${text}

=== MANUSCRIPT END ===

TASK: Provide improvement suggestions for the manuscript above.

${format_requirements}

${section_structure}

${token_budget_awareness}

${content_requirements}

${validation_hints}

Begin your improvement suggestions now:"""

    def render(
        self,
        text: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render template with enhanced constraints.

        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop("text", None)

        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)  # noqa: E501
        if text is None:
            raise LLMTemplateError("Missing template variable: text", context={"required": "text"})

        required_headers = [
            "## Summary",
            "## High Priority Improvements",
            "## Medium Priority Improvements",
            "## Low Priority Improvements",
            "## Overall Recommendation",
        ]

        section_descriptions = {
            "## Summary": "Brief overview of key improvement areas (80-120 words)",
            "## High Priority Improvements": "Critical issues requiring immediate attention (150-200 words)",  # noqa: E501
            "## Medium Priority Improvements": "Important but not critical improvements (120-180 words)",  # noqa: E501
            "## Low Priority Improvements": "Minor enhancements and suggestions (100-150 words)",
            "## Overall Recommendation": "Final recommendation: Accept with Minor Revisions, Accept with Major Revisions, or Revise and Resubmit (80-120 words)",  # noqa: E501
        }

        section_requirements = {
            "All improvement sections": "Each improvement must include: WHAT (the issue), WHY (why it matters), HOW (how to address it)",  # noqa: E501
            "Overall Recommendation": "Must choose exactly ONE: 'Accept with Minor Revisions', 'Accept with Major Revisions', or 'Revise and Resubmit'",  # noqa: E501
        }

        section_budgets = None
        if max_tokens:
            # Allocate more tokens to high priority section
            tokens_per_section = max_tokens // 5
            section_budgets = {
                "Summary": tokens_per_section,
                "High Priority Improvements": int(tokens_per_section * 1.3),
                "Medium Priority Improvements": int(tokens_per_section * 1.1),
                "Low Priority Improvements": tokens_per_section,
                "Overall Recommendation": tokens_per_section,
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
            total_tokens=max_tokens, section_budgets=section_budgets
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True,
        )
        validation = validation_hints(
            word_count_range=(500, 800),
            required_elements=[
                "all 5 section headers",
                "WHAT/WHY/HOW for each improvement",
                "overall recommendation choice",
            ],
            format_checks=[
                "word count",
                "section presence",
                "actionability",
                "content relevance",
            ],
        )

        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs,
        )
