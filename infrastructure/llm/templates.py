"""Prompt templates for research tasks."""
from __future__ import annotations

from typing import Dict, Any, Optional
from string import Template

from infrastructure.core.exceptions import LLMTemplateError


class ResearchTemplate:
    """Base class for research templates."""
    
    template_str: str = ""
    
    def render(self, **kwargs: Any) -> str:
        """Render template with variables."""
        try:
            return Template(self.template_str).substitute(**kwargs)
        except KeyError as e:
            raise LLMTemplateError(
                f"Missing template variable: {e}",
                context={"required": str(e)}
            )


class SummarizeAbstract(ResearchTemplate):
    """Template for summarizing abstracts."""
    template_str = (
        "Please summarize the following abstract in 3-5 bullet points, "
        "highlighting the main contribution, methodology, and results:\n\n"
        "${text}"
    )


class LiteratureReview(ResearchTemplate):
    """Template for generating literature reviews."""
    template_str = (
        "Based on the following paper summaries, write a cohesive "
        "literature review paragraph:\n\n"
        "${summaries}"
    )


class CodeDocumentation(ResearchTemplate):
    """Template for documenting code."""
    template_str = (
        "Generate a Python docstring for the following code, "
        "including Args, Returns, and Raises sections:\n\n"
        "${code}"
    )


class DataInterpretation(ResearchTemplate):
    """Template for interpreting data."""
    template_str = (
        "Analyze the following data statistics and provide "
        "a scientific interpretation of the trends:\n\n"
        "${stats}"
    )


# =============================================================================
# Manuscript Review Templates
# =============================================================================

# Minimum word counts for quality validation
REVIEW_MIN_WORDS = {
    "executive_summary": 250,
    "quality_review": 300,
    "methodology_review": 300,
    "improvement_suggestions": 250,
}


class ManuscriptExecutiveSummary(ResearchTemplate):
    """Template for generating executive summary of a manuscript.
    
    Produces a structured executive summary with 5 key sections,
    targeting 400-600 words of substantive analysis.
    """
    template_str = """STRICT REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTION:

FORBIDDEN (DO NOT USE):
- NO emojis (no checkmarks, stars, rockets, light bulbs, etc.)
- NO markdown tables (no | column | separators |)
- NO conversational phrases ("I'll help you", "Let me know", "Based on your document")
- NO invented section numbers (do not reference "Section 12.8" or similar)
- NO fabricated statistics or benchmarks not in the manuscript
- NO external references not cited in the manuscript

REQUIRED FORMAT - Use ONLY these exact headers:

## Overview
## Key Contributions
## Methodology Summary
## Principal Results
## Significance and Impact

RULES:
1. Write 400-600 words total in plain academic prose
2. Use ONLY headers and bullet points for formatting
3. Reference ONLY content that appears in the manuscript
4. Quote or paraphrase actual text when possible
5. Do not invent or hallucinate details

---

Analyze this manuscript and provide your executive summary:

${text}"""


class ManuscriptQualityReview(ResearchTemplate):
    """Template for reviewing writing quality of a manuscript.
    
    Produces a detailed quality assessment with scoring rubric,
    targeting 500-700 words of critical analysis.
    """
    template_str = """STRICT REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTION:

FORBIDDEN (DO NOT USE):
- NO emojis (no checkmarks, stars, rockets, light bulbs, etc.)
- NO markdown tables (no | column | separators |)
- NO conversational phrases ("I'll help you", "Let me know", "Based on your document")
- NO invented section numbers (do not reference "Section 12.8" or similar)
- NO fabricated performance claims not in the manuscript

REQUIRED FORMAT - Use ONLY these exact headers:

## Overall Quality Score
## Clarity Assessment
## Structure and Organization
## Technical Accuracy
## Readability
## Consistency
## Specific Issues Found
## Recommendations

SCORING FORMAT:
For each assessment section, include: **Score: X/5** (where X is 1-5)

RULES:
1. Write 500-700 words total in plain academic prose
2. Reference ONLY content that appears in the manuscript
3. When citing issues, quote actual text or describe specific locations
4. Base all scores on evidence from the manuscript
5. Do not invent or hallucinate details

---

Analyze this manuscript and provide your quality review:

${text}"""


class ManuscriptMethodologyReview(ResearchTemplate):
    """Template for reviewing methodology and structure of a manuscript.
    
    Produces a comprehensive methodology assessment with strengths/weaknesses,
    targeting 500-700 words of analytical feedback.
    """
    template_str = """STRICT REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTION:

FORBIDDEN (DO NOT USE):
- NO emojis (no checkmarks, stars, rockets, light bulbs, etc.)
- NO markdown tables (no | column | separators |)
- NO conversational phrases ("I'll help you", "Let me know", "Based on your document")
- NO invented section numbers (do not reference "Section 12.8" or similar)
- NO fabricated benchmarks or performance claims not in the manuscript

REQUIRED FORMAT - Use ONLY these exact headers:

## Methodology Overview
## Research Design Assessment
## Strengths
## Weaknesses
## Recommendations

RULES:
1. Write 500-700 words total in plain academic prose
2. Use ONLY headers and bullet points for formatting
3. Reference ONLY methods and results described in the manuscript
4. Quote or paraphrase actual text when describing methodology
5. Base strengths and weaknesses on manuscript evidence only
6. Do not invent or hallucinate details

---

Analyze this manuscript and provide your methodology review:

${text}"""


class ManuscriptImprovementSuggestions(ResearchTemplate):
    """Template for generating improvement suggestions for a manuscript.
    
    Produces a prioritized list of actionable improvements,
    targeting 400-600 words of specific recommendations.
    """
    template_str = """STRICT REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTION:

FORBIDDEN (DO NOT USE):
- NO emojis (no checkmarks, stars, rockets, light bulbs, etc.)
- NO markdown tables (no | column | separators |)
- NO conversational phrases ("I'll help you", "Let me know", "Based on your document")
- NO invented section numbers (do not reference "Section 12.8" or similar)
- NO fabricated claims or external recommendations not based on manuscript

REQUIRED FORMAT - Use ONLY these exact headers:

## Summary
## High Priority Improvements
## Medium Priority Improvements
## Low Priority Improvements
## Overall Recommendation

RULES:
1. Write 400-600 words total in plain academic prose
2. Use ONLY headers and numbered/bulleted lists for formatting
3. Reference ONLY issues that exist in the manuscript
4. Describe specific locations using section titles from the manuscript
5. Base all suggestions on actual content found in the document
6. Do not invent or hallucinate details

RECOMMENDATION OPTIONS (choose ONE):
- Accept with Minor Revisions
- Accept with Major Revisions
- Revise and Resubmit

---

Analyze this manuscript and provide your improvement suggestions:

${text}"""


# Registry of available templates
TEMPLATES = {
    # Original templates
    "summarize_abstract": SummarizeAbstract,
    "literature_review": LiteratureReview,
    "code_doc": CodeDocumentation,
    "data_interpret": DataInterpretation,
    # Manuscript review templates
    "manuscript_executive_summary": ManuscriptExecutiveSummary,
    "manuscript_quality_review": ManuscriptQualityReview,
    "manuscript_methodology_review": ManuscriptMethodologyReview,
    "manuscript_improvement_suggestions": ManuscriptImprovementSuggestions,
}

def get_template(name: str) -> ResearchTemplate:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise LLMTemplateError(f"Template not found: {name}")
    return TEMPLATES[name]()
