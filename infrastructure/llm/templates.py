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

REQUIREMENTS:
1. First, write a technical abstract in English (200-400 words)
2. The abstract MUST reference specific content from the manuscript above
3. Include:
   - Research objective and motivation
   - Methodology overview
   - Key findings and results
   - Significance and implications

4. Use these section headers:
   ## English Abstract
   ## ${target_language} Translation

5. After the English abstract, provide a complete and accurate translation in ${target_language}
6. The translation must preserve technical terminology and scientific accuracy
7. Use formal academic tone in both languages
8. Do NOT add information not present in the manuscript
9. Do NOT provide transliteration - use native script for the target language

Begin with the English abstract, then provide the translation:"""


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
}

def get_template(name: str) -> ResearchTemplate:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise LLMTemplateError(f"Template not found: {name}")
    return TEMPLATES[name]()
