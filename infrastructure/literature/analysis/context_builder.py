"""Context builder for enhanced LLM prompts.

Builds rich context for LLM operations by combining paper analysis,
domain detection, related papers, and metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.analysis.domain_detector import DomainDetectionResult
from infrastructure.literature.library.index import LibraryEntry
from infrastructure.literature.analysis.paper_analyzer import PaperContentProfile
from infrastructure.literature.sources import SearchResult

logger = get_logger(__name__)


@dataclass
class PaperContext:
    """Rich context for a paper to enhance LLM prompts."""
    citation_key: str
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: Optional[str]
    
    # Analysis results
    domain: str
    domain_confidence: float
    paper_type: str
    complexity_score: float
    
    # Structure information
    has_equations: bool
    has_figures: bool
    has_tables: bool
    section_count: int
    
    # Content characteristics
    keywords: List[str]
    topics: List[str]
    estimated_pages: int
    word_count: int
    
    # Related papers context
    related_papers: List[Dict[str, str]]
    
    # Domain-specific instructions
    domain_instructions: str


class ContextBuilder:
    """Builds rich context for LLM operations."""
    
    def __init__(self):
        """Initialize context builder."""
        from infrastructure.literature.analysis.paper_analyzer import PaperAnalyzer
        from infrastructure.literature.analysis.domain_detector import DomainDetector
        
        self.paper_analyzer = PaperAnalyzer()
        self.domain_detector = DomainDetector()
    
    def build_context(
        self,
        pdf_path: Path,
        search_result: SearchResult,
        library_entries: Optional[List[LibraryEntry]] = None,
        max_related: int = 5
    ) -> PaperContext:
        """Build comprehensive context for a paper.
        
        Args:
            pdf_path: Path to PDF file.
            search_result: Search result with metadata.
            library_entries: Optional library entries for finding related papers.
            max_related: Maximum number of related papers to include.
            
        Returns:
            PaperContext with rich context information.
        """
        # Analyze paper
        profile = self.paper_analyzer.analyze_paper(pdf_path, search_result)
        
        # Find related papers
        related_papers = []
        if library_entries:
            related_papers = self._find_related_papers(
                profile,
                library_entries,
                max_related
            )
        
        # Get domain-specific instructions
        domain_instructions = self.domain_detector.get_domain_specific_instructions(
            profile.domain_detection.domain
        )
        
        return PaperContext(
            citation_key=profile.citation_key,
            title=profile.title,
            authors=search_result.authors,
            year=search_result.year,
            abstract=search_result.abstract,
            domain=profile.domain_detection.domain.value,
            domain_confidence=profile.domain_detection.confidence,
            paper_type=profile.domain_detection.paper_type.value,
            complexity_score=profile.complexity_score,
            has_equations=profile.has_equations,
            has_figures=profile.has_figures,
            has_tables=profile.has_tables,
            section_count=profile.structure.section_count,
            keywords=profile.keywords,
            topics=profile.topics,
            estimated_pages=profile.structure.estimated_pages,
            word_count=profile.structure.word_count,
            related_papers=related_papers,
            domain_instructions=domain_instructions
        )
    
    def _find_related_papers(
        self,
        profile: PaperContentProfile,
        library_entries: List[LibraryEntry],
        max_related: int
    ) -> List[Dict[str, str]]:
        """Find related papers based on domain, keywords, and topics.
        
        Args:
            profile: Paper content profile.
            library_entries: Library entries to search.
            max_related: Maximum number of related papers.
            
        Returns:
            List of related paper dictionaries with title and citation_key.
        """
        related = []
        
        # Score papers by similarity
        scored_papers: List[Tuple[LibraryEntry, float]] = []
        
        for entry in library_entries:
            if entry.citation_key == profile.citation_key:
                continue  # Skip self
            
            score = 0.0
            
            # Domain match
            # (We'd need domain detection for each entry, simplified here)
            
            # Keyword overlap
            if entry.abstract:
                entry_keywords = set(entry.abstract.lower().split())
                profile_keywords = set(k.lower() for k in profile.keywords)
                overlap = len(entry_keywords & profile_keywords)
                score += overlap * 0.1
            
            # Year proximity (prefer recent related work)
            if entry.year and profile.domain_detection:
                # Simplified: prefer papers within 5 years
                # (Would need year from profile, simplified here)
                pass
            
            if score > 0:
                scored_papers.append((entry, score))
        
        # Sort by score and take top N
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        for entry, _ in scored_papers[:max_related]:
            related.append({
                "citation_key": entry.citation_key,
                "title": entry.title,
                "year": str(entry.year) if entry.year else "Unknown"
            })
        
        return related
    
    def format_context_for_prompt(self, context: PaperContext) -> str:
        """Format context as a string for inclusion in prompts.
        
        Args:
            context: PaperContext to format.
            
        Returns:
            Formatted context string.
        """
        lines = [
            f"=== PAPER CONTEXT ===",
            f"Title: {context.title}",
            f"Authors: {', '.join(context.authors)}",
            f"Year: {context.year or 'Unknown'}",
            f"",
            f"Domain: {context.domain} (confidence: {context.domain_confidence:.2f})",
            f"Paper Type: {context.paper_type}",
            f"Complexity: {context.complexity_score:.2f}",
            f"",
            f"Structure:",
            f"  - Sections: {context.section_count}",
            f"  - Estimated pages: {context.estimated_pages}",
            f"  - Word count: {context.word_count:,}",
            f"  - Has equations: {context.has_equations}",
            f"  - Has figures: {context.has_figures}",
            f"  - Has tables: {context.has_tables}",
            f"",
        ]
        
        if context.keywords:
            lines.append(f"Keywords: {', '.join(context.keywords[:10])}")
        
        if context.topics:
            lines.append(f"Topics: {', '.join(context.topics[:5])}")
        
        if context.related_papers:
            lines.append(f"")
            lines.append(f"Related Papers ({len(context.related_papers)}):")
            for paper in context.related_papers[:3]:  # Show top 3
                lines.append(f"  - {paper['title'][:60]}... ({paper['year']})")
        
        lines.append(f"")
        lines.append(f"=== END CONTEXT ===")
        
        return "\n".join(lines)

