"""Literature analysis templates for LLM operations.

Contains multi-paper analysis templates: literature review synthesis,
science communication narratives, comparative analysis, research gap
identification, and citation network analysis.
"""

from __future__ import annotations

from infrastructure.llm.templates.base import ResearchTemplate


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
