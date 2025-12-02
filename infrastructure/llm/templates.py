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
# Note: improvement_suggestions uses a lower threshold (200) because models often
# produce focused, actionable output that may be shorter but still high-quality.
# The retry mechanism catches truly short responses.
REVIEW_MIN_WORDS = {
    "executive_summary": 250,
    "quality_review": 300,
    "methodology_review": 300,
    "improvement_suggestions": 200,  # Lower threshold for focused actionable output
}


class ManuscriptExecutiveSummary(ResearchTemplate):
    """Template for generating executive summary of a manuscript.
    
    Produces a structured executive summary with 5 key sections,
    targeting 400-600 words of substantive analysis.
    
    Uses manuscript-first structure with task instructions at end
    for better LLM attention to the actual content.
    """
    template_str = """=== MANUSCRIPT BEGIN ===

${text}

=== MANUSCRIPT END ===

TASK: Write an executive summary of the manuscript above.

REQUIREMENTS:
1. Your summary MUST reference specific content from the manuscript above
2. Write 400-600 words in academic prose
3. Use these section headers:
   ## Overview
   ## Key Contributions  
   ## Methodology Summary
   ## Principal Results
   ## Significance and Impact

4. Quote or paraphrase actual text from the manuscript
5. Do NOT invent details not present in the manuscript
6. Do NOT reference external sources not cited in the manuscript

Begin your executive summary now:"""


class ManuscriptQualityReview(ResearchTemplate):
    """Template for reviewing writing quality of a manuscript.
    
    Produces a detailed quality assessment with scoring rubric,
    targeting 500-700 words of critical analysis.
    
    Uses manuscript-first structure with task instructions at end
    for better LLM attention to the actual content.
    """
    template_str = """=== MANUSCRIPT BEGIN ===

${text}

=== MANUSCRIPT END ===

TASK: Provide a quality review of the manuscript above.

REQUIREMENTS:
1. Your review MUST reference specific content from the manuscript above
2. Write 500-700 words in academic prose
3. Use these section headers:
   ## Overall Quality Score
   ## Clarity Assessment
   ## Structure and Organization
   ## Technical Accuracy
   ## Readability
   ## Specific Issues Found
   ## Recommendations

4. For each section, include a score: **Score: X/5** (where X is 1-5)
5. When citing issues, quote actual text or describe specific sections
6. Base all scores on evidence from the manuscript
7. Do NOT invent details not present in the manuscript

Begin your quality review now:"""


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

REQUIREMENTS:
1. Your review MUST reference specific content from the manuscript above
2. Write 500-700 words in academic prose
3. Use these section headers:
   ## Methodology Overview
   ## Research Design Assessment
   ## Strengths
   ## Weaknesses
   ## Recommendations

4. Quote or paraphrase actual methodology from the manuscript
5. Base strengths and weaknesses on manuscript evidence only
6. Do NOT invent details not present in the manuscript
7. Do NOT reference external methodologies not mentioned in the manuscript

Begin your methodology review now:"""


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

REQUIREMENTS:
1. Your suggestions MUST reference specific content from the manuscript above
2. Write 500-800 words with detailed actionable recommendations
3. Use these section headers:
   ## Summary
   ## High Priority Improvements
   ## Medium Priority Improvements
   ## Low Priority Improvements
   ## Overall Recommendation

4. For each improvement, explain WHY it matters and HOW to address it
5. Reference specific sections by their actual titles from the manuscript
6. Base all suggestions on actual content found in the manuscript
7. Do NOT invent issues not present in the manuscript
8. Choose ONE recommendation: Accept with Minor Revisions, Accept with Major Revisions, or Revise and Resubmit

Begin your improvement suggestions now:"""


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
