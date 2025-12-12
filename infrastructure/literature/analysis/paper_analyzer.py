"""Paper structure and content analysis.

Analyzes PDF structure, extracts metadata, and creates content profiles
for enhanced context in summarization and analysis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.analysis.domain_detector import DomainDetector, DomainDetectionResult
from infrastructure.literature.sources import SearchResult
from infrastructure.validation.pdf_validator import extract_text_from_pdf

logger = get_logger(__name__)


@dataclass
class PaperStructure:
    """Analysis of paper structure and organization."""
    has_abstract: bool
    has_introduction: bool
    has_methodology: bool
    has_results: bool
    has_discussion: bool
    has_conclusion: bool
    section_count: int
    section_titles: List[str]
    estimated_pages: int
    word_count: int
    character_count: int


@dataclass
class PaperContentProfile:
    """Comprehensive profile of paper content and characteristics."""
    citation_key: str
    title: str
    structure: PaperStructure
    domain_detection: DomainDetectionResult
    complexity_score: float
    has_equations: bool
    has_figures: bool
    has_tables: bool
    has_references: bool
    reference_count: Optional[int]
    keywords: List[str]
    topics: List[str]


class PaperAnalyzer:
    """Analyzes paper structure, content, and characteristics."""
    
    def __init__(self):
        """Initialize paper analyzer."""
        self.domain_detector = DomainDetector()
    
    def analyze_paper(
        self,
        pdf_path: Path,
        search_result: Optional[SearchResult] = None
    ) -> PaperContentProfile:
        """Perform comprehensive analysis of a paper.
        
        Args:
            pdf_path: Path to PDF file.
            search_result: Optional search result with metadata.
            
        Returns:
            PaperContentProfile with analysis results.
        """
        # Extract text
        try:
            text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            logger.warning(f"Failed to extract text from {pdf_path}: {e}")
            text = ""
        
        # Analyze structure
        structure = self._analyze_structure(text)
        
        # Detect domain
        domain_result = self.domain_detector.detect_domain(
            text=text,
            title=search_result.title if search_result else None,
            abstract=search_result.abstract if search_result else None
        )
        
        # Calculate complexity
        complexity = self._calculate_complexity(text, structure)
        
        # Detect content features
        has_equations = self._has_equations(text)
        has_figures = self._has_figures(text)
        has_tables = self._has_tables(text)
        has_references = self._has_references(text)
        reference_count = self._count_references(text) if has_references else None
        
        # Extract keywords and topics
        keywords = self._extract_keywords(text)
        topics = self._extract_topics(text)
        
        citation_key = pdf_path.stem
        title = search_result.title if search_result else citation_key
        
        return PaperContentProfile(
            citation_key=citation_key,
            title=title,
            structure=structure,
            domain_detection=domain_result,
            complexity_score=complexity,
            has_equations=has_equations,
            has_figures=has_figures,
            has_tables=has_tables,
            has_references=has_references,
            reference_count=reference_count,
            keywords=keywords,
            topics=topics
        )
    
    def _analyze_structure(self, text: str) -> PaperStructure:
        """Analyze paper structure and sections."""
        lines = text.split("\n")
        
        # Common section patterns
        section_patterns = {
            "abstract": [r"^\s*(?:Abstract|Summary)\s*$", r"^#+\s*(?:Abstract|Summary)"],
            "introduction": [r"^\s*(?:1\.?\s*)?Introduction\s*$", r"^#+\s*Introduction"],
            "methodology": [
                r"^\s*(?:2\.?\s*)?(?:Method|Methods|Methodology|Experimental\s+Setup)\s*$",
                r"^#+\s*(?:Method|Methods|Methodology)"
            ],
            "results": [
                r"^\s*(?:3\.?\s*)?(?:Results?|Findings?|Data)\s*$",
                r"^#+\s*(?:Results?|Findings?)"
            ],
            "discussion": [
                r"^\s*(?:4\.?\s*)?(?:Discussion|Analysis)\s*$",
                r"^#+\s*Discussion"
            ],
            "conclusion": [
                r"^\s*(?:5\.?\s*)?(?:Conclusion|Conclusions?|Summary)\s*$",
                r"^#+\s*(?:Conclusion|Conclusions?)"
            ]
        }
        
        section_titles = []
        section_flags = {
            "has_abstract": False,
            "has_introduction": False,
            "has_methodology": False,
            "has_results": False,
            "has_discussion": False,
            "has_conclusion": False
        }
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for section headers
            for section_name, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line_stripped, re.IGNORECASE):
                        section_titles.append(line_stripped)
                        section_flags[f"has_{section_name}"] = True
                        break
        
        # Estimate pages (assuming ~500 words per page)
        word_count = len(text.split())
        estimated_pages = max(1, word_count // 500)
        
        return PaperStructure(
            has_abstract=section_flags["has_abstract"],
            has_introduction=section_flags["has_introduction"],
            has_methodology=section_flags["has_methodology"],
            has_results=section_flags["has_results"],
            has_discussion=section_flags["has_discussion"],
            has_conclusion=section_flags["has_conclusion"],
            section_count=len(section_titles),
            section_titles=section_titles[:20],  # Limit to first 20
            estimated_pages=estimated_pages,
            word_count=word_count,
            character_count=len(text)
        )
    
    def _calculate_complexity(self, text: str, structure: PaperStructure) -> float:
        """Calculate complexity score (0.0 to 1.0)."""
        score = 0.0
        
        # Length factor
        if structure.word_count > 10000:
            score += 0.3
        elif structure.word_count > 5000:
            score += 0.2
        elif structure.word_count > 2000:
            score += 0.1
        
        # Structure factor
        if structure.section_count > 8:
            score += 0.2
        elif structure.section_count > 5:
            score += 0.1
        
        # Equation density
        equation_count = len(re.findall(r'\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)', text))
        if equation_count > 50:
            score += 0.2
        elif equation_count > 20:
            score += 0.1
        
        # Technical term density
        technical_terms = len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text))
        if technical_terms > 100:
            score += 0.3
        elif technical_terms > 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _has_equations(self, text: str) -> bool:
        """Check if paper contains equations."""
        # Look for LaTeX-style equations
        patterns = [
            r'\$.*?\$',  # Inline math
            r'\\\[.*?\\\]',  # Display math
            r'\\\(.*?\\\)',  # Inline math (alternative)
            r'\\begin\{equation\}',  # Equation environment
            r'\\begin\{align\}',  # Align environment
        ]
        return any(re.search(p, text) for p in patterns)
    
    def _has_figures(self, text: str) -> bool:
        """Check if paper mentions figures."""
        patterns = [
            r'\bFigure\s+\d+',
            r'\bFig\.\s+\d+',
            r'\bfig\.\s+\d+',
            r'\\begin\{figure\}'
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _has_tables(self, text: str) -> bool:
        """Check if paper mentions tables."""
        patterns = [
            r'\bTable\s+\d+',
            r'\bTab\.\s+\d+',
            r'\\begin\{table\}'
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _has_references(self, text: str) -> bool:
        """Check if paper has references section."""
        patterns = [
            r'^\s*(?:References?|Bibliography|Works\s+Cited)\s*$',
            r'^#+\s*(?:References?|Bibliography)',
            r'\\begin\{thebibliography\}',
            r'\\bibliography'
        ]
        return any(re.search(p, text, re.IGNORECASE | re.MULTILINE) for p in patterns)
    
    def _count_references(self, text: str) -> Optional[int]:
        """Count number of references."""
        # Look for reference patterns
        patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'\\cite\{[^}]+\}',  # \cite{key}
            r'\\bibitem',  # \bibitem entries
        ]
        
        max_ref = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Try to extract numbers
                numbers = []
                for match in matches:
                    if isinstance(match, str) and match.isdigit():
                        numbers.append(int(match))
                    elif isinstance(match, tuple):
                        numbers.extend([int(m) for m in match if str(m).isdigit()])
                
                if numbers:
                    max_ref = max(max_ref, max(numbers))
        
        return max_ref if max_ref > 0 else None
    
    def _extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """Extract keywords from text."""
        # Simple frequency-based extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Common stop words
        stop_words = {
            "this", "that", "these", "those", "with", "from", "have", "been",
            "were", "will", "would", "could", "should", "which", "their",
            "there", "where", "when", "what", "then", "than", "them", "they"
        }
        
        word_freq: Dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def _extract_topics(self, text: str, max_topics: int = 10) -> List[str]:
        """Extract topic phrases from text."""
        # Look for capitalized phrases (potential topics)
        topics = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', text)
        
        # Remove common false positives
        false_positives = {"Figure", "Table", "Section", "Chapter", "Page"}
        topics = [t for t in topics if t not in false_positives]
        
        # Count frequencies
        topic_freq: Dict[str, int] = {}
        for topic in topics:
            topic_freq[topic] = topic_freq.get(topic, 0) + 1
        
        sorted_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:max_topics]]

