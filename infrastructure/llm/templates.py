"""Prompt templates for research tasks."""
from __future__ import annotations

from typing import Dict, Any, Optional, List
from string import Template

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Try to import new prompt system (optional for backward compatibility)
try:
    from infrastructure.llm.prompts.composer import PromptComposer
    PROMPT_COMPOSER_AVAILABLE = True
except ImportError:
    PROMPT_COMPOSER_AVAILABLE = False
    logger.debug("Prompt composer not available, using legacy template system")


# =============================================================================
# Modular Prompt Constraint System
# =============================================================================

def format_requirements(
    required_headers: List[str],
    markdown_format: bool = True,
    section_requirements: Optional[Dict[str, str]] = None
) -> str:
    """Generate format requirements section for prompts.
    
    Args:
        required_headers: List of required markdown section headers (e.g., ["## Overview", "## Results"])
        markdown_format: Whether to use markdown formatting
        section_requirements: Optional dict mapping section names to specific requirements
        
    Returns:
        Formatted requirements string
    """
    lines = ["FORMAT REQUIREMENTS:"]
    
    if markdown_format:
        lines.append("1. Use markdown formatting with proper headers")
        lines.append("2. Include these exact section headers (in order):")
        for header in required_headers:
            lines.append(f"   {header}")
    
    if section_requirements:
        lines.append("3. Section-specific requirements:")
        for section, req in section_requirements.items():
            lines.append(f"   - {section}: {req}")
    
    return "\n".join(lines)


def token_budget_awareness(
    total_tokens: Optional[int] = None,
    section_budgets: Optional[Dict[str, int]] = None,
    word_targets: Optional[Dict[str, tuple]] = None
) -> str:
    """Generate token budget awareness hints for prompts.
    
    Args:
        total_tokens: Total token budget available
        section_budgets: Optional dict mapping section names to approximate token budgets
        word_targets: Optional dict mapping section names to (min, max) word counts
        
    Returns:
        Formatted token budget awareness string
    """
    lines = ["TOKEN BUDGET AWARENESS:"]
    
    if total_tokens:
        lines.append(f"1. Total response budget: approximately {total_tokens} tokens")
        lines.append("   (Plan your response to stay within this limit)")
    
    if section_budgets:
        lines.append("2. Approximate token budgets per section:")
        for section, budget in section_budgets.items():
            lines.append(f"   - {section}: ~{budget} tokens")
    
    if word_targets:
        lines.append("3. Word count targets per section:")
        for section, (min_words, max_words) in word_targets.items():
            lines.append(f"   - {section}: {min_words}-{max_words} words")
    
    return "\n".join(lines)


def content_requirements(
    no_hallucination: bool = True,
    cite_sources: bool = True,
    evidence_based: bool = True,
    no_meta_commentary: bool = True
) -> str:
    """Generate content quality requirements section.
    
    Args:
        no_hallucination: Require no invented details
        cite_sources: Require citation of sources
        evidence_based: Require evidence-based claims
        no_meta_commentary: Prohibit meta-commentary about being AI
        
    Returns:
        Formatted content requirements string
    """
    lines = ["CONTENT QUALITY REQUIREMENTS:"]
    
    if no_hallucination:
        lines.append("1. NO HALLUCINATION: Only discuss information explicitly present in the provided content")
        lines.append("   - Do NOT add external knowledge, assumptions, or invented details")
        lines.append("   - Do NOT reference sources not mentioned in the provided content")
    
    if cite_sources:
        lines.append("2. CITE SOURCES: Reference specific sections, passages, or elements from the content")
        lines.append("   - Quote or paraphrase actual text when making observations")
        lines.append("   - Use specific section titles or page references when available")
    
    if evidence_based:
        lines.append("3. EVIDENCE-BASED: Base all claims on evidence from the provided content")
        lines.append("   - Support observations with specific examples")
        lines.append("   - Explain reasoning with reference to actual content")
    
    if no_meta_commentary:
        lines.append("4. NO META-COMMENTARY: Do not mention being an AI, assistant, or that this is generated content")
        lines.append("   - Write as if you are a human expert reviewer")
        lines.append("   - Use professional, academic tone throughout")
    
    return "\n".join(lines)


def section_structure(
    sections: List[str],
    section_descriptions: Optional[Dict[str, str]] = None,
    required_order: bool = True
) -> str:
    """Generate section structure requirements.
    
    Args:
        sections: List of required section names/headers
        section_descriptions: Optional dict mapping section names to descriptions
        required_order: Whether sections must appear in the specified order
        
    Returns:
        Formatted section structure string
    """
    lines = ["SECTION STRUCTURE:"]
    
    if required_order:
        lines.append("1. Sections must appear in this exact order:")
    else:
        lines.append("1. Include all of these sections:")
    
    for i, section in enumerate(sections, 1):
        if section_descriptions and section in section_descriptions:
            lines.append(f"   {i}. {section}: {section_descriptions[section]}")
        else:
            lines.append(f"   {i}. {section}")
    
    return "\n".join(lines)


def validation_hints(
    word_count_range: Optional[tuple] = None,
    required_elements: Optional[List[str]] = None,
    format_checks: Optional[List[str]] = None
) -> str:
    """Generate validation hints that inform the model what will be checked.
    
    Args:
        word_count_range: Optional (min, max) word count tuple
        required_elements: Optional list of required elements (e.g., ["scores", "headers"])
        format_checks: Optional list of format checks that will be performed
        
    Returns:
        Formatted validation hints string
    """
    lines = ["VALIDATION HINTS (what will be checked):"]
    
    if word_count_range:
        min_words, max_words = word_count_range
        lines.append(f"1. Word count: Must be between {min_words} and {max_words} words")
    
    if required_elements:
        lines.append("2. Required elements:")
        for element in required_elements:
            lines.append(f"   - {element}")
    
    if format_checks:
        lines.append("3. Format compliance checks:")
        for check in format_checks:
            lines.append(f"   - {check}")
    
    return "\n".join(lines)


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


class PaperSummarization(ResearchTemplate):
    """Template for comprehensive paper summarization.

    Generates a detailed summary of a research paper focusing on
    relevance, comprehensiveness, and specificity rather than rigid structure.
    Emphasizes extracting key information accurately and substantively.
    """
    template_str = """=== PAPER CONTENT ===

Title: ${title}
Authors: ${authors}
Year: ${year}
Source: ${source}

PAPER TEXT:
${text}

=== END PAPER CONTENT ===

CRITICAL INSTRUCTIONS:
You are summarizing a scientific research paper. You MUST follow ALL rules below:

1. ONLY use information that appears in the paper text above. Do NOT add external knowledge, assumptions, or invented details.

2. Provide a comprehensive summary that covers the key aspects of the paper. Use section headers that make sense for the content, such as:
   - Overview/Summary (what the paper is about)
   - Key Contributions/Findings (main results and advances)
   - Methodology/Approach (how the research was conducted)
   - Results/Data (what was found or measured)
   - Limitations/Discussion (weaknesses and future work)

3. Word count: Aim for 400-700 words of substantive, detailed content. Focus on quality over quantity.

4. CONTENT FOCUS:
   - Emphasize relevance: Explain why this research matters and how it connects to broader scientific questions
   - Be comprehensive: Cover all major aspects mentioned in the paper without leaving out important details
   - Prioritize specificity: Use concrete details, numbers, methods, measurements, and findings from the paper
   - Extract key information accurately: Focus on what the paper actually says and demonstrates

5. DOMAIN-SPECIFIC EMPHASIS:
   - For PHYSICS papers: Highlight specific equations, experimental parameters, energy scales, detection methods, and statistical significance
   - For COMPUTER SCIENCE papers: Detail algorithms, complexity analysis, dataset characteristics, performance metrics, and comparisons
   - For BIOLOGY papers: Include species, sample sizes, statistical methods, biological mechanisms, and experimental conditions
   - For MATHEMATICS papers: Cover theorems, proofs, mathematical objects, computational complexity, and theoretical implications

6. QUALITY STANDARDS:
   - Be substantive: Provide detailed analysis rather than surface-level descriptions
   - Explain significance: Discuss why methods, results, and contributions matter
   - Maintain coherence: Ensure different sections complement rather than repeat each other
   - Use evidence: Support claims with specific details from the paper

7. ACCURACY REQUIREMENTS:
   - NO HALLUCINATION: Only discuss what the paper explicitly states
   - NO REPETITION: Avoid repeating the same information in multiple places
   - NO META-COMMENTARY: Do not mention being an AI or that this is a summary
   - SCIENTIFIC TONE: Use formal, academic language throughout

8. FLEXIBLE STRUCTURE: Use the section headers that best fit the paper's content. You may use fewer or more sections as appropriate, or even combine related information.

Begin your summary now:"""


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
        # Extract from kwargs if not provided as positional arg (for backward compatibility)
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
                logger.debug(f"Failed to use prompt composer, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
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
        # Extract from kwargs if not provided as positional arg (for backward compatibility)
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
        # Extract from kwargs if not provided as positional arg (for backward compatibility)
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
        # Extract from kwargs if not provided as positional arg (for backward compatibility)
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
        # Extract from kwargs if not provided as positional args (for backward compatibility)
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


# Literature Analysis Templates
# =============================================================================

class LiteratureReviewSynthesis(ResearchTemplate):
    """Template for synthesizing multiple paper summaries into a cohesive literature review.

    Generates a structured literature review that identifies themes, compares approaches,
    and highlights key findings across multiple papers.
    """
    template_str = """=== PAPER SUMMARIES ===

${summaries}

=== END PAPER SUMMARIES ===

TASK: Write a cohesive literature review paragraph that synthesizes these ${num_papers} papers.

REQUIREMENTS:
1. Focus on the ${focus} aspects of these papers
2. Identify common themes, approaches, and findings
3. Compare and contrast different methods or results
4. Highlight gaps or areas needing further research
5. Write in academic prose (300-500 words)
6. Reference specific papers by their titles
7. Do NOT invent details not present in the summaries
8. Structure as a flowing narrative, not bullet points

Begin your literature review synthesis:"""


class ScienceCommunicationNarrative(ResearchTemplate):
    """Template for creating accessible science communication narratives from research papers.

    Transforms technical research findings into engaging, understandable narratives
    for different audiences (general public, students, etc.).
    """
    template_str = """=== RESEARCH PAPERS ===

${papers}

=== END RESEARCH PAPERS ===

TASK: Create a science communication narrative that explains the key findings from these ${num_papers} research papers.

AUDIENCE: ${audience}
STYLE: ${narrative_style}

REQUIREMENTS:
1. Explain the scientific concepts in accessible language
2. Connect the research to real-world implications
3. Use storytelling techniques appropriate to the chosen style
4. Maintain scientific accuracy while being engaging
5. Include concrete examples from the papers
6. Write 600-800 words suitable for the target audience
7. Do NOT oversimplify to the point of inaccuracy
8. Make the science relatable and interesting

Begin your science communication narrative:"""


class ComparativeAnalysis(ResearchTemplate):
    """Template for comparative analysis across multiple research papers.

    Provides structured comparison of methods, results, datasets, or other aspects
    across multiple papers in the same research area.
    """
    template_str = """=== PAPERS FOR COMPARISON ===

${papers}

=== END PAPERS ===

TASK: Perform a comparative analysis of these ${num_papers} papers focusing on their ${aspect}.

REQUIREMENTS:
1. Compare how the papers approach the ${aspect}
2. Identify similarities and differences
3. Evaluate strengths and weaknesses of each approach
4. Discuss implications of different approaches
5. Write 500-700 words in analytical academic style
6. Use specific examples from each paper
7. Structure with clear sections (Introduction, Comparison, Analysis, Conclusions)
8. Base all analysis on information in the provided papers

Begin your comparative analysis:"""


class ResearchGapIdentification(ResearchTemplate):
    """Template for identifying research gaps from literature analysis.

    Analyzes a set of papers to identify unanswered questions, methodological gaps,
    and areas needing further research.
    """
    template_str = """=== LITERATURE FOR GAP ANALYSIS ===

${papers}

=== END LITERATURE ===

TASK: Analyze these ${num_papers} papers to identify research gaps in the ${domain} domain.

REQUIREMENTS:
1. Identify unanswered questions or unexplored areas
2. Find methodological gaps or limitations
3. Spot inconsistencies or contradictory findings
4. Suggest directions for future research
5. Write 400-600 words with specific recommendations
6. Reference specific papers and their findings
7. Prioritize gaps that are important and feasible to address
8. Structure with sections (Current State, Identified Gaps, Recommendations)

Begin your research gap analysis:"""


class CitationNetworkAnalysis(ResearchTemplate):
    """Template for analyzing citation relationships and networks between papers.

    Examines how papers reference and build upon each other, identifying
    key works, research trajectories, and intellectual connections.
    """
    template_str = """=== PAPERS FOR NETWORK ANALYSIS ===

${papers}

=== END PAPERS ===

TASK: Analyze the citation network and intellectual connections between these ${num_papers} papers.

REQUIREMENTS:
1. Identify how papers build upon or contradict each other
2. Find common methodologies, datasets, or theoretical frameworks
3. Trace research trajectories or evolution of ideas
4. Identify key foundational papers or influential works
5. Write 500-700 words with clear analysis structure
6. Reference specific connections between papers
7. Discuss implications for the research field
8. Use network concepts (hubs, clusters, bridges) where appropriate

Begin your citation network analysis:"""


# Registry of available templates
TEMPLATES = {
    # Original templates
    "summarize_abstract": SummarizeAbstract,
    "literature_review": LiteratureReview,
    "code_doc": CodeDocumentation,
    "data_interpret": DataInterpretation,
    "paper_summarization": PaperSummarization,
    # Manuscript review templates
    "manuscript_executive_summary": ManuscriptExecutiveSummary,
    "manuscript_quality_review": ManuscriptQualityReview,
    "manuscript_methodology_review": ManuscriptMethodologyReview,
    "manuscript_improvement_suggestions": ManuscriptImprovementSuggestions,
    "manuscript_translation_abstract": ManuscriptTranslationAbstract,
    # Literature analysis templates
    "literature_review_synthesis": LiteratureReviewSynthesis,
    "science_communication_narrative": ScienceCommunicationNarrative,
    "comparative_analysis": ComparativeAnalysis,
    "research_gap_identification": ResearchGapIdentification,
    "citation_network_analysis": CitationNetworkAnalysis,
}

def get_template(name: str) -> ResearchTemplate:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise LLMTemplateError(f"Template not found: {name}")
    return TEMPLATES[name]()
