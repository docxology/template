"""Parser for extracting structured metadata from markdown summaries.

Parses markdown summary files to extract structured information including
key findings, methods, results, and other metadata in JSON format.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from datetime import datetime

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class SummaryMetadata:
    """Structured metadata extracted from a summary."""
    citation_key: str
    title: str
    authors: List[str]
    year: Optional[int]
    source: str
    venue: Optional[str]
    doi: Optional[str]
    pdf_path: Optional[str]
    generated_date: Optional[str]
    
    # Extracted content sections
    overview: Optional[str] = None
    key_contributions: Optional[str] = None
    methodology: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    discussion: Optional[str] = None
    
    # Statistics
    input_words: Optional[int] = None
    input_chars: Optional[int] = None
    output_words: Optional[int] = None
    compression_ratio: Optional[float] = None
    generation_time: Optional[float] = None
    quality_score: Optional[float] = None
    attempts: Optional[int] = None
    
    # Keywords and concepts (extracted from content)
    keywords: List[str] = None
    concepts: List[str] = None
    
    def __post_init__(self):
        """Initialize default values for lists."""
        if self.keywords is None:
            self.keywords = []
        if self.concepts is None:
            self.concepts = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class SummaryParser:
    """Parser for extracting structured data from markdown summaries."""
    
    # Section header patterns
    SECTION_PATTERNS = {
        "overview": [
            r"^###?\s+(?:Overview|Summary|Introduction|Abstract)",
            r"^##\s+(?:Overview|Summary|Introduction|Abstract)"
        ],
        "key_contributions": [
            r"^###?\s+(?:Key\s+Contributions?|Contributions?|Findings?|Main\s+Results?)",
            r"^##\s+(?:Key\s+Contributions?|Contributions?|Findings?)"
        ],
        "methodology": [
            r"^###?\s+(?:Methodology|Methods?|Approach|Experimental\s+Setup)",
            r"^##\s+(?:Methodology|Methods?|Approach)"
        ],
        "results": [
            r"^###?\s+(?:Results?|Data|Findings?|Outcomes?)",
            r"^##\s+(?:Results?|Data|Findings?)"
        ],
        "limitations": [
            r"^###?\s+(?:Limitations?|Future\s+Work|Discussion|Challenges?)",
            r"^##\s+(?:Limitations?|Future\s+Work|Discussion)"
        ],
        "discussion": [
            r"^###?\s+(?:Discussion|Conclusion|Implications?)",
            r"^##\s+(?:Discussion|Conclusion)"
        ]
    }
    
    def parse_summary_file(self, summary_path: Path) -> SummaryMetadata:
        """Parse a markdown summary file and extract structured metadata.
        
        Args:
            summary_path: Path to markdown summary file.
            
        Returns:
            SummaryMetadata with extracted information.
        """
        content = summary_path.read_text(encoding="utf-8")
        return self.parse_summary_content(content, citation_key=summary_path.stem.replace("_summary", ""))
    
    def parse_summary_content(self, content: str, citation_key: Optional[str] = None) -> SummaryMetadata:
        """Parse summary content string and extract metadata.
        
        Args:
            content: Markdown summary content.
            citation_key: Optional citation key (extracted from filename if not provided).
            
        Returns:
            SummaryMetadata with extracted information.
        """
        lines = content.split("\n")
        
        # Extract header metadata
        metadata = self._extract_header_metadata(lines, citation_key)
        
        # Extract sections
        sections = self._extract_sections(lines)
        metadata.overview = sections.get("overview")
        metadata.key_contributions = sections.get("key_contributions")
        metadata.methodology = sections.get("methodology")
        metadata.results = sections.get("results")
        metadata.limitations = sections.get("limitations")
        metadata.discussion = sections.get("discussion")
        
        # Extract statistics
        stats = self._extract_statistics(content)
        metadata.input_words = stats.get("input_words")
        metadata.input_chars = stats.get("input_chars")
        metadata.output_words = stats.get("output_words")
        metadata.compression_ratio = stats.get("compression_ratio")
        metadata.generation_time = stats.get("generation_time")
        metadata.quality_score = stats.get("quality_score")
        metadata.attempts = stats.get("attempts")
        
        # Extract keywords and concepts
        all_text = " ".join([s for s in sections.values() if s])
        metadata.keywords = self._extract_keywords(all_text)
        metadata.concepts = self._extract_concepts(all_text)
        
        return metadata
    
    def _extract_header_metadata(self, lines: List[str], citation_key: Optional[str]) -> SummaryMetadata:
        """Extract metadata from header section."""
        metadata = SummaryMetadata(
            citation_key=citation_key or "unknown",
            title="",
            authors=[],
            year=None,
            source="unknown",
            venue=None,
            doi=None,
            pdf_path=None,
            generated_date=None
        )
        
        in_header = True
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if i > 0:  # Second separator ends header
                    break
                continue
            
            if not in_header:
                continue
            
            # Parse metadata fields
            if line.startswith("# "):
                metadata.title = line[2:].strip()
            elif line.startswith("**Authors:**"):
                authors_str = line.replace("**Authors:**", "").strip()
                metadata.authors = [a.strip() for a in authors_str.split(",") if a.strip()]
            elif line.startswith("**Year:**"):
                year_str = line.replace("**Year:**", "").strip()
                try:
                    metadata.year = int(year_str) if year_str != "Unknown" else None
                except ValueError:
                    pass
            elif line.startswith("**Source:**"):
                metadata.source = line.replace("**Source:**", "").strip()
            elif line.startswith("**Venue:**"):
                venue_str = line.replace("**Venue:**", "").strip()
                metadata.venue = venue_str if venue_str != "N/A" else None
            elif line.startswith("**DOI:**"):
                doi_str = line.replace("**DOI:**", "").strip()
                metadata.doi = doi_str if doi_str != "N/A" else None
            elif line.startswith("**PDF:**"):
                pdf_match = re.search(r'\[.*?\]\((.*?)\)', line)
                if pdf_match:
                    metadata.pdf_path = pdf_match.group(1)
            elif line.startswith("**Generated:**"):
                metadata.generated_date = line.replace("**Generated:**", "").strip()
        
        return metadata
    
    def _extract_sections(self, lines: List[str]) -> Dict[str, str]:
        """Extract content sections from markdown."""
        sections: Dict[str, str] = {}
        current_section: Optional[str] = None
        current_content: List[str] = []
        
        in_summary = False
        for line in lines:
            # Skip header section
            if line.strip() == "---":
                if not in_summary:
                    in_summary = True
                    continue
                else:
                    # End of summary section
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content).strip()
                    break
            
            if not in_summary:
                continue
            
            # Check for section headers
            section_found = False
            for section_name, patterns in self.SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        # Save previous section
                        if current_section and current_content:
                            sections[current_section] = "\n".join(current_content).strip()
                        
                        # Start new section
                        current_section = section_name
                        current_content = []
                        section_found = True
                        break
                if section_found:
                    break
            
            # Add content to current section
            if current_section and not section_found:
                # Skip empty lines at start of section
                if line.strip() or current_content:
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    def _extract_statistics(self, content: str) -> Dict[str, Any]:
        """Extract statistics from summary statistics section."""
        stats = {}
        
        # Look for statistics section
        stats_match = re.search(r"Summary Statistics:.*?(?=\n\n|\Z)", content, re.DOTALL)
        if not stats_match:
            return stats
        
        stats_text = stats_match.group(0)
        
        # Extract individual statistics
        patterns = {
            "input_words": r"Input:\s*(\d+(?:,\d+)?)\s+words",
            "input_chars": r"Input:.*?\((\d+(?:,\d+)?)\s+chars\)",
            "output_words": r"Output:\s*(\d+(?:,\d+)?)\s+words",
            "compression_ratio": r"Compression:\s*([\d.]+)x",
            "generation_time": r"Generation:\s*([\d.]+)s",
            "quality_score": r"Quality Score:\s*([\d.]+)/",
            "attempts": r"Attempts:\s*(\d+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, stats_text)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    if key in ("compression_ratio", "generation_time", "quality_score"):
                        stats[key] = float(value_str)
                    else:
                        stats[key] = int(value_str)
                except ValueError:
                    pass
        
        return stats
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple frequency analysis."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can", "this",
            "that", "these", "those", "it", "its", "they", "them", "their"
        }
        
        # Extract words (3+ characters, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Count frequencies
        word_freq: Dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def _extract_concepts(self, text: str, max_concepts: int = 15) -> List[str]:
        """Extract key concepts (phrases) from text."""
        # Look for capitalized phrases (potential concepts)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        
        # Also look for quoted terms
        quoted = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted)
        
        # Remove duplicates and limit
        unique_concepts = list(dict.fromkeys(concepts))  # Preserves order
        return unique_concepts[:max_concepts]
    
    def export_metadata(self, metadata: SummaryMetadata, output_path: Path) -> None:
        """Export metadata to JSON file.
        
        Args:
            metadata: SummaryMetadata to export.
            output_path: Path to output JSON file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
    
    def batch_parse_summaries(self, summaries_dir: Path) -> List[SummaryMetadata]:
        """Parse all summaries in a directory.
        
        Args:
            summaries_dir: Directory containing summary markdown files.
            
        Returns:
            List of SummaryMetadata for all parsed summaries.
        """
        summaries = []
        for summary_file in summaries_dir.glob("*_summary.md"):
            try:
                metadata = self.parse_summary_file(summary_file)
                summaries.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to parse {summary_file}: {e}")
        
        return summaries
    
    def export_batch_metadata(self, summaries_dir: Path, output_path: Path) -> None:
        """Parse all summaries and export metadata to JSON.
        
        Args:
            summaries_dir: Directory containing summary markdown files.
            output_path: Path to output JSON file.
        """
        summaries = self.batch_parse_summaries(summaries_dir)
        metadata_list = [s.to_dict() for s in summaries]
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "total_summaries": len(summaries),
                "summaries": metadata_list
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported metadata for {len(summaries)} summaries to {output_path}")

