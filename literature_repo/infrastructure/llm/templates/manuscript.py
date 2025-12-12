"""Manuscript review templates for LLM operations."""
from __future__ import annotations

from typing import Any, Optional
from string import Template

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.templates.base import ResearchTemplate
from infrastructure.llm.templates.helpers import (
    format_requirements,
    token_budget_awareness,
    content_requirements,
    section_structure,
    validation_hints,
)

logger = get_logger(__name__)

# Try to import prompt composer system
try:
    from infrastructure.llm.prompts.composer import PromptComposer
    PROMPT_COMPOSER_AVAILABLE = True
except ImportError:
    PROMPT_COMPOSER_AVAILABLE = False
    logger.debug("Prompt composer not available, using template system")

# Minimum word counts for quality validation
# Note: improvement_suggestions uses a lower threshold (200) because models often
# produce focused, actionable output that may be shorter but still high-quality.
# The retry mechanism catches truly short responses.
REVIEW_MIN_WORDS = {
    "executive_summary": 250,
    "quality_review": 300,
    "methodology_review": 300,
    "improvement_suggestions": 200,  # Lower threshold for focused actionable output
    "translation": 400,  # English abstract + translation (~200 words each)
}

# Supported translation languages with full names for prompts
TRANSLATION_LANGUAGES = {
    "zh": "Chinese (Simplified)",
    "hi": "Hindi",
    "ru": "Russian",
}


# Minimum word counts for quality validation
# Note: improvement_suggestions uses a lower threshold (200) because models often
# produce focused, actionable output that may be shorter but still high-quality.
# The retry mechanism catches truly short responses.
REVIEW_MIN_WORDS = {
    "executive_summary": 250,
    "quality_review": 300,
    "methodology_review": 300,
    "improvement_suggestions": 200,  # Lower threshold for focused actionable output
    "translation": 400,  # English abstract + translation (~200 words each)
}

# Supported translation languages with full names for prompts
TRANSLATION_LANGUAGES = {
    "zh": "Chinese (Simplified)",
    "hi": "Hindi",
    "ru": "Russian",
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

${format_requirements}

${section_structure}

${token_budget_awareness}

${content_requirements}

${validation_hints}

Begin your executive summary now:"""
    
    def render(self, text: Optional[str] = None, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        """Render template with enhanced constraints.
        
        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop('text', None)
        
        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)
        if text is None:
            raise LLMTemplateError(
                "Missing template variable: text",
                context={"required": "text"}
            )
        
        # Try to use new prompt composer if available
        if PROMPT_COMPOSER_AVAILABLE:
            try:
                composer = PromptComposer()
                return composer.compose_template(
                    "manuscript_reviews.json#manuscript_executive_summary",
                    text=text,
                    max_tokens=max_tokens,
                    **kwargs
                )
            except Exception as e:
                logger.debug(f"Failed to use prompt composer, falling back: {e}")
        
        # Fallback implementation
        # Define required sections
        required_headers = [
            "## Overview",
            "## Key Contributions",
            "## Methodology Summary",
            "## Principal Results",
            "## Significance and Impact"
        ]
        
        section_descriptions = {
            "## Overview": "Brief introduction to the research topic and objectives (80-120 words)",
            "## Key Contributions": "Main advances and novel contributions (100-150 words)",
            "## Methodology Summary": "Approach and methods used (80-120 words)",
            "## Principal Results": "Key findings and outcomes (100-150 words)",
            "## Significance and Impact": "Importance and implications (80-120 words)"
        }
        
        # Calculate token budgets if max_tokens provided
        section_budgets = None
        if max_tokens:
            # Allocate ~20% per section (5 sections)
            tokens_per_section = max_tokens // 5
            section_budgets = {
                "Overview": tokens_per_section,
                "Key Contributions": tokens_per_section,
                "Methodology Summary": tokens_per_section,
                "Principal Results": tokens_per_section,
                "Significance and Impact": tokens_per_section
            }
        
        # Build constraint sections
        format_req = format_requirements(required_headers, markdown_format=True)
        section_struct = section_structure(required_headers, section_descriptions, required_order=True)
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets,
            word_targets={
                "Overview": (80, 120),
                "Key Contributions": (100, 150),
                "Methodology Summary": (80, 120),
                "Principal Results": (100, 150),
                "Significance and Impact": (80, 120)
            }
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True
        )
        validation = validation_hints(
            word_count_range=(400, 600),
            required_elements=["all 5 section headers", "specific manuscript references"],
            format_checks=["word count", "section presence", "content relevance"]
        )
        
        # Render base template
        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs
        )


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

${format_requirements}

${section_structure}

${token_budget_awareness}

${content_requirements}

${validation_hints}

Begin your quality review now:"""
    
    def render(self, text: Optional[str] = None, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        """Render template with enhanced constraints.
        
        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop('text', None)
        
        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)
        if text is None:
            raise LLMTemplateError(
                "Missing template variable: text",
                context={"required": "text"}
            )
        
        required_headers = [
            "## Overall Quality Score",
            "## Clarity Assessment",
            "## Structure and Organization",
            "## Technical Accuracy",
            "## Readability",
            "## Specific Issues Found",
            "## Recommendations"
        ]
        
        section_descriptions = {
            "## Overall Quality Score": "Provide overall score (1-5) with brief justification (50-80 words)",
            "## Clarity Assessment": "Evaluate writing clarity with score and specific examples (80-120 words)",
            "## Structure and Organization": "Assess organization with score and structural observations (80-120 words)",
            "## Technical Accuracy": "Review technical correctness with score and evidence (80-120 words)",
            "## Readability": "Evaluate readability with score and specific issues (60-100 words)",
            "## Specific Issues Found": "List concrete issues with manuscript references (100-150 words)",
            "## Recommendations": "Provide actionable recommendations (80-120 words)"
        }
        
        section_requirements = {
            "Overall Quality Score": "Must include: **Score: X/5** format where X is 1-5",
            "All scoring sections": "Each section with 'Assessment' or 'Accuracy' must include **Score: X/5**",
            "Specific Issues Found": "Must quote or reference specific manuscript sections",
            "Recommendations": "Must be actionable and specific to manuscript content"
        }
        
        section_budgets = None
        if max_tokens:
            tokens_per_section = max_tokens // 7
            section_budgets = {section.replace("## ", ""): tokens_per_section for section in required_headers}
        
        format_req = format_requirements(required_headers, markdown_format=True, section_requirements=section_requirements)
        section_struct = section_structure(required_headers, section_descriptions, required_order=True)
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True
        )
        validation = validation_hints(
            word_count_range=(500, 700),
            required_elements=["all 7 section headers", "scores in **Score: X/5** format", "specific manuscript references"],
            format_checks=["word count", "section presence", "score format", "content relevance"]
        )
        
        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs
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
    
    def render(self, text: Optional[str] = None, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        """Render template with enhanced constraints.
        
        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop('text', None)
        
        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)
        if text is None:
            raise LLMTemplateError(
                "Missing template variable: text",
                context={"required": "text"}
            )
        
        required_headers = [
            "## Methodology Overview",
            "## Research Design Assessment",
            "## Strengths",
            "## Weaknesses",
            "## Recommendations"
        ]
        
        section_descriptions = {
            "## Methodology Overview": "Summarize the methodology used in the manuscript (100-150 words)",
            "## Research Design Assessment": "Evaluate the research design and approach (120-180 words)",
            "## Strengths": "Identify methodological strengths with evidence (100-150 words)",
            "## Weaknesses": "Identify methodological weaknesses with evidence (100-150 words)",
            "## Recommendations": "Provide specific improvement recommendations (80-120 words)"
        }
        
        section_budgets = None
        if max_tokens:
            tokens_per_section = max_tokens // 5
            section_budgets = {section.replace("## ", ""): tokens_per_section for section in required_headers}
        
        format_req = format_requirements(required_headers, markdown_format=True)
        section_struct = section_structure(required_headers, section_descriptions, required_order=True)
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True
        )
        validation = validation_hints(
            word_count_range=(500, 700),
            required_elements=["all 5 section headers", "methodology references", "strengths and weaknesses"],
            format_checks=["word count", "section presence", "content relevance"]
        )
        
        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs
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
    
    def render(self, text: Optional[str] = None, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        """Render template with enhanced constraints.
        
        Args:
            text: Manuscript text (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text can be passed here too)
        """
        # Extract from kwargs if not provided as positional arg
        if text is None:
            text = kwargs.pop('text', None)
        
        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)
        if text is None:
            raise LLMTemplateError(
                "Missing template variable: text",
                context={"required": "text"}
            )
        
        required_headers = [
            "## Summary",
            "## High Priority Improvements",
            "## Medium Priority Improvements",
            "## Low Priority Improvements",
            "## Overall Recommendation"
        ]
        
        section_descriptions = {
            "## Summary": "Brief overview of key improvement areas (80-120 words)",
            "## High Priority Improvements": "Critical issues requiring immediate attention (150-200 words)",
            "## Medium Priority Improvements": "Important but not critical improvements (120-180 words)",
            "## Low Priority Improvements": "Minor enhancements and suggestions (100-150 words)",
            "## Overall Recommendation": "Final recommendation: Accept with Minor Revisions, Accept with Major Revisions, or Revise and Resubmit (80-120 words)"
        }
        
        section_requirements = {
            "All improvement sections": "Each improvement must include: WHAT (the issue), WHY (why it matters), HOW (how to address it)",
            "Overall Recommendation": "Must choose exactly ONE: 'Accept with Minor Revisions', 'Accept with Major Revisions', or 'Revise and Resubmit'"
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
                "Overall Recommendation": tokens_per_section
            }
        
        format_req = format_requirements(required_headers, markdown_format=True, section_requirements=section_requirements)
        section_struct = section_structure(required_headers, section_descriptions, required_order=True)
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True
        )
        validation = validation_hints(
            word_count_range=(500, 800),
            required_elements=["all 5 section headers", "WHAT/WHY/HOW for each improvement", "overall recommendation choice"],
            format_checks=["word count", "section presence", "actionability", "content relevance"]
        )
        
        base_template = Template(self.template_str)
        return base_template.substitute(
            text=text,
            format_requirements=format_req,
            section_structure=section_struct,
            token_budget_awareness=token_budget,
            content_requirements=content_req,
            validation_hints=validation,
            **kwargs
        )


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
    
    def render(self, text: Optional[str] = None, target_language: Optional[str] = None, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        """Render template with enhanced constraints.
        
        Args:
            text: Manuscript text (required)
            target_language: Target language name (required)
            max_tokens: Optional token budget for response
            **kwargs: Additional template variables (text and target_language can be passed here too)
        """
        # Extract from kwargs if not provided as positional args
        if text is None:
            text = kwargs.pop('text', None)
        if target_language is None:
            target_language = kwargs.pop('target_language', None)
        
        # Check required arguments and raise LLMTemplateError if missing (matches base class behavior)
        if text is None:
            raise LLMTemplateError(
                "Missing template variable: text",
                context={"required": "text"}
            )
        if target_language is None:
            raise LLMTemplateError(
                "Missing template variable: target_language",
                context={"required": "target_language"}
            )
        required_headers = [
            "## English Abstract",
            f"## {target_language} Translation"
        ]
        
        section_descriptions = {
            "## English Abstract": "Technical abstract in English (200-400 words) covering: research objective, methodology, key findings, significance",
            f"## {target_language} Translation": f"Complete and accurate translation in {target_language}, preserving technical terminology and scientific accuracy"
        }
        
        section_requirements = {
            "English Abstract": "Must include: research objective and motivation, methodology overview, key findings and results, significance and implications",
            f"{target_language} Translation": "Must be complete translation (not summary), preserve technical terms, use native script (not transliteration), maintain formal academic tone"
        }
        
        section_budgets = None
        if max_tokens:
            # Split roughly 50/50 between English and translation
            section_budgets = {
                "English Abstract": max_tokens // 2,
                f"{target_language} Translation": max_tokens // 2
            }
        
        format_req = format_requirements(required_headers, markdown_format=True, section_requirements=section_requirements)
        section_struct = section_structure(required_headers, section_descriptions, required_order=True)
        token_budget = token_budget_awareness(
            total_tokens=max_tokens,
            section_budgets=section_budgets,
            word_targets={
                "English Abstract": (200, 400),
                f"{target_language} Translation": (200, 400)  # Approximate word count
            }
        )
        content_req = content_requirements(
            no_hallucination=True,
            cite_sources=True,
            evidence_based=True,
            no_meta_commentary=True
        )
        validation = validation_hints(
            word_count_range=(400, 800),  # Total: ~200-400 English + ~200-400 translation
            required_elements=["English abstract section", f"{target_language} translation section", "technical terminology preservation"],
            format_checks=["word count", "section presence", "translation completeness", "content relevance"]
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
            **kwargs
        )

