"""Advanced LLM operations for literature analysis.

This module provides multi-paper LLM operations including literature reviews,
science communication narratives, comparative analysis, research gap identification,
and citation network analysis.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from infrastructure.core.logging_utils import get_logger, log_success
from infrastructure.literature.library.index import LibraryEntry

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient

logger = get_logger(__name__)


@dataclass
class LLMOperationResult:
    """Result of an LLM operation.

    Attributes:
        operation_type: Type of operation performed.
        papers_used: Number of papers included in the operation.
        citation_keys: List of citation keys of papers used.
        output_text: Generated output text.
        output_path: Path where output was saved (if saved).
        generation_time: Time taken for LLM generation.
        tokens_estimated: Estimated token count.
        metadata: Additional metadata about the operation.
    """
    operation_type: str
    papers_used: int
    citation_keys: List[str]
    output_text: str
    output_path: Optional[Path] = None
    generation_time: float = 0.0
    tokens_estimated: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LiteratureLLMOperations:
    """Advanced LLM operations for multi-paper literature analysis.

    Provides methods for synthesizing information across multiple papers:
    - Literature reviews
    - Science communication narratives
    - Comparative analysis
    - Research gap identification
    - Citation network analysis
    """

    def __init__(self, llm_client: "LLMClient"):
        """Initialize LLM operations with an LLM client.

        Args:
            llm_client: Configured LLM client for text generation.
        """
        self.llm_client = llm_client

    def generate_literature_review(
        self,
        papers: List[LibraryEntry],
        focus: str = "general",
        max_papers: int = 10
    ) -> LLMOperationResult:
        """Generate a literature review synthesizing multiple papers.

        Args:
            papers: List of papers to include in the review.
            focus: Focus area for the review (e.g., "methodology", "results", "theory").
            max_papers: Maximum number of papers to include.

        Returns:
            LLMOperationResult with the generated literature review.
        """
        start_time = time.time()
        selected_papers = papers[:max_papers]  # Limit number of papers
        citation_keys = [p.citation_key for p in selected_papers]

        logger.info(f"Generating literature review for {len(selected_papers)} papers (focus: {focus})")

        # Collect summaries or abstracts for each paper
        paper_summaries = []
        for paper in selected_papers:
            # Try to load summary first
            summary_path = Path("data/summaries") / f"{paper.citation_key}_summary.md"
            if summary_path.exists():
                try:
                    content = summary_path.read_text()
                    # Extract just the summary content (skip metadata)
                    lines = content.split('\n')
                    summary_start = -1
                    for i, line in enumerate(lines):
                        if line.startswith('---') and summary_start == -1:
                            summary_start = i + 1
                            break
                    if summary_start > 0 and summary_start < len(lines):
                        summary_text = '\n'.join(lines[summary_start:]).strip()
                    else:
                        summary_text = content
                    paper_summaries.append(f"**{paper.title}**\n{summary_text}")
                except Exception as e:
                    logger.warning(f"Could not read summary for {paper.citation_key}: {e}")
                    paper_summaries.append(f"**{paper.title}**\n{paper.abstract or 'No summary available'}")
            else:
                paper_summaries.append(f"**{paper.title}**\n{paper.abstract or 'No abstract available'}")

        # Create the prompt
        from infrastructure.llm.templates.research import LiteratureReviewSynthesis
        template = LiteratureReviewSynthesis()
        summaries_text = '\n\n---\n\n'.join(paper_summaries)

        prompt = template.render(
            summaries=summaries_text,
            focus=focus,
            num_papers=len(selected_papers)
        )

        # Generate the review
        response = self.llm_client.query(prompt)

        generation_time = time.time() - start_time
        tokens_estimated = len(response.split()) * 1.3  # Rough estimate

        return LLMOperationResult(
            operation_type="literature_review",
            papers_used=len(selected_papers),
            citation_keys=citation_keys,
            output_text=response,
            generation_time=generation_time,
            tokens_estimated=int(tokens_estimated),
            metadata={"focus": focus, "max_papers": max_papers}
        )

    def generate_science_communication(
        self,
        papers: List[LibraryEntry],
        audience: str = "general_public",
        narrative_style: str = "storytelling"
    ) -> LLMOperationResult:
        """Generate a science communication narrative from multiple papers.

        Args:
            papers: List of papers to include.
            audience: Target audience ("general_public", "students", "researchers").
            narrative_style: Narrative style ("storytelling", "explanation", "timeline").

        Returns:
            LLMOperationResult with the generated narrative.
        """
        start_time = time.time()
        citation_keys = [p.citation_key for p in papers]

        logger.info(f"Generating science communication for {len(papers)} papers (audience: {audience}, style: {narrative_style})")

        # Collect key information from papers
        paper_info = []
        for paper in papers:
            summary_path = Path("data/summaries") / f"{paper.citation_key}_summary.md"
            if summary_path.exists():
                try:
                    content = summary_path.read_text()
                    # Extract key findings (look for "Key Contributions" or similar)
                    lines = content.split('\n')
                    key_findings = []
                    in_findings = False
                    for line in lines:
                        if any(phrase in line.lower() for phrase in ["key contributions", "main results", "findings"]):
                            in_findings = True
                        elif in_findings and line.startswith('###'):
                            break  # Next section
                        elif in_findings and line.strip():
                            key_findings.append(line)

                    summary = '\n'.join(key_findings) if key_findings else content[:500]
                except Exception:
                    summary = paper.abstract or "No summary available"
            else:
                summary = paper.abstract or "No abstract available"

            paper_info.append(f"**{paper.title}** ({paper.year or 'n/d'})\n{summary}")

        # Create the prompt
        from infrastructure.llm.templates.research import ScienceCommunicationNarrative
        template = ScienceCommunicationNarrative()
        papers_text = '\n\n---\n\n'.join(paper_info)

        prompt = template.render(
            papers=papers_text,
            audience=audience,
            narrative_style=narrative_style,
            num_papers=len(papers)
        )

        # Generate the narrative
        response = self.llm_client.query(prompt)

        generation_time = time.time() - start_time
        tokens_estimated = len(response.split()) * 1.3

        return LLMOperationResult(
            operation_type="science_communication",
            papers_used=len(papers),
            citation_keys=citation_keys,
            output_text=response,
            generation_time=generation_time,
            tokens_estimated=int(tokens_estimated),
            metadata={"audience": audience, "narrative_style": narrative_style}
        )

    def generate_comparative_analysis(
        self,
        papers: List[LibraryEntry],
        aspect: str = "methods"
    ) -> LLMOperationResult:
        """Generate comparative analysis across multiple papers.

        Args:
            papers: List of papers to compare.
            aspect: Aspect to compare ("methods", "results", "datasets", "performance").

        Returns:
            LLMOperationResult with the comparative analysis.
        """
        start_time = time.time()
        citation_keys = [p.citation_key for p in papers]

        logger.info(f"Generating comparative analysis for {len(papers)} papers (aspect: {aspect})")

        # Collect relevant information for comparison
        paper_comparisons = []
        for paper in papers:
            summary_path = Path("data/summaries") / f"{paper.citation_key}_summary.md"
            if summary_path.exists():
                try:
                    content = summary_path.read_text()
                    paper_comparisons.append(f"**{paper.title}** ({paper.year or 'n/d'})\n{content}")
                except Exception:
                    paper_comparisons.append(f"**{paper.title}**\n{paper.abstract or 'No summary available'}")
            else:
                paper_comparisons.append(f"**{paper.title}**\n{paper.abstract or 'No abstract available'}")

        # Create the prompt
        from infrastructure.llm.templates.research import ComparativeAnalysis
        template = ComparativeAnalysis()
        papers_text = '\n\n---\n\n'.join(paper_comparisons)

        prompt = template.render(
            papers=papers_text,
            aspect=aspect,
            num_papers=len(papers)
        )

        # Generate the analysis
        response = self.llm_client.query(prompt)

        generation_time = time.time() - start_time
        tokens_estimated = len(response.split()) * 1.3

        return LLMOperationResult(
            operation_type="comparative_analysis",
            papers_used=len(papers),
            citation_keys=citation_keys,
            output_text=response,
            generation_time=generation_time,
            tokens_estimated=int(tokens_estimated),
            metadata={"aspect": aspect}
        )

    def identify_research_gaps(
        self,
        papers: List[LibraryEntry],
        domain: str = "general"
    ) -> LLMOperationResult:
        """Identify research gaps from literature analysis.

        Args:
            papers: List of papers to analyze for gaps.
            domain: Research domain for context.

        Returns:
            LLMOperationResult with identified research gaps.
        """
        start_time = time.time()
        citation_keys = [p.citation_key for p in papers]

        logger.info(f"Identifying research gaps in {len(papers)} papers (domain: {domain})")

        # Collect paper summaries and methodologies
        paper_gaps = []
        for paper in papers:
            summary_path = Path("data/summaries") / f"{paper.citation_key}_summary.md"
            if summary_path.exists():
                try:
                    content = summary_path.read_text()
                    paper_gaps.append(f"**{paper.title}** ({paper.year or 'n/d'})\n{content}")
                except Exception:
                    paper_gaps.append(f"**{paper.title}**\n{paper.abstract or 'No summary available'}")
            else:
                paper_gaps.append(f"**{paper.title}**\n{paper.abstract or 'No abstract available'}")

        # Create the prompt
        from infrastructure.llm.templates.research import ResearchGapIdentification
        template = ResearchGapIdentification()
        papers_text = '\n\n---\n\n'.join(paper_gaps)

        prompt = template.render(
            papers=papers_text,
            domain=domain,
            num_papers=len(papers)
        )

        # Generate gap analysis
        response = self.llm_client.query(prompt)

        generation_time = time.time() - start_time
        tokens_estimated = len(response.split()) * 1.3

        return LLMOperationResult(
            operation_type="research_gaps",
            papers_used=len(papers),
            citation_keys=citation_keys,
            output_text=response,
            generation_time=generation_time,
            tokens_estimated=int(tokens_estimated),
            metadata={"domain": domain}
        )

    def analyze_citation_network(self, papers: List[LibraryEntry]) -> LLMOperationResult:
        """Analyze citation relationships and networks between papers.

        Args:
            papers: List of papers to analyze.

        Returns:
            LLMOperationResult with citation network analysis.
        """
        start_time = time.time()
        citation_keys = [p.citation_key for p in papers]

        logger.info(f"Analyzing citation network for {len(papers)} papers")

        # For now, we don't have actual citation data, so we'll do a simpler analysis
        # In a real implementation, this would analyze citation relationships

        paper_networks = []
        for paper in papers:
            summary_path = Path("data/summaries") / f"{paper.citation_key}_summary.md"
            if summary_path.exists():
                try:
                    content = summary_path.read_text()
                    paper_networks.append(f"**{paper.title}** ({paper.year or 'n/d'})\n{content}")
                except Exception:
                    paper_networks.append(f"**{paper.title}**\n{paper.abstract or 'No summary available'}")
            else:
                paper_networks.append(f"**{paper.title}**\n{paper.abstract or 'No abstract available'}")

        # Create the prompt
        from infrastructure.llm.templates.research import CitationNetworkAnalysis
        template = CitationNetworkAnalysis()
        papers_text = '\n\n---\n\n'.join(paper_networks)

        prompt = template.render(
            papers=papers_text,
            num_papers=len(papers)
        )

        # Generate network analysis
        response = self.llm_client.query(prompt)

        generation_time = time.time() - start_time
        tokens_estimated = len(response.split()) * 1.3

        return LLMOperationResult(
            operation_type="citation_network",
            papers_used=len(papers),
            citation_keys=citation_keys,
            output_text=response,
            generation_time=generation_time,
            tokens_estimated=int(tokens_estimated),
            metadata={}
        )

    def save_result(self, result: LLMOperationResult, output_dir: Path) -> Path:
        """Save LLM operation result to a markdown file.

        Args:
            result: Operation result to save.
            output_dir: Directory to save the result.

        Returns:
            Path to the saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename based on operation type and timestamp
        timestamp = int(time.time())
        filename = f"{result.operation_type}_{timestamp}.md"
        output_path = output_dir / filename

        # Build content
        content = f"""# {result.operation_type.replace('_', ' ').title()}

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Papers Used:** {result.papers_used}
**Citation Keys:** {', '.join(result.citation_keys)}
**Generation Time:** {result.generation_time:.1f}s
**Estimated Tokens:** {result.tokens_estimated}

## Metadata

- **Operation Type:** {result.operation_type}
- **Papers Analyzed:** {result.papers_used}
"""

        # Add operation-specific metadata
        if result.metadata:
            content += "\n### Operation Parameters\n\n"
            for key, value in result.metadata.items():
                content += f"- **{key}:** {value}\n"

        content += "\n---\n\n"
        content += result.output_text

        # Save file
        output_path.write_text(content)
        result.output_path = output_path

        logger.info(f"Saved {result.operation_type} result to {output_path}")
        log_success(f"Saved: {filename}")
        return output_path










