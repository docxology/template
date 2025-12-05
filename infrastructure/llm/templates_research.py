"""Research task templates for LLM operations."""
from __future__ import annotations

from infrastructure.llm.templates_base import ResearchTemplate


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

