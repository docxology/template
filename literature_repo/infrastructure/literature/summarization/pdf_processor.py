"""PDF text processing with section prioritization.

This module provides intelligent PDF text processing that prioritizes
critical sections (title, abstract, introduction, conclusion) when truncating
long papers to ensure key context is preserved for summarization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger
from infrastructure.validation.pdf_validator import extract_text_from_pdf

logger = get_logger(__name__)


@dataclass
class PrioritizedPDFText:
    """Result of prioritized PDF text extraction.
    
    Attributes:
        text: Processed PDF text with prioritized sections preserved.
        sections_found: Dictionary mapping section names to (start, end) character positions.
        sections_included: List of section names that were included in final text.
        sections_excluded: List of section names that were excluded due to truncation.
        original_length: Original PDF text length in characters.
        final_length: Final processed text length in characters.
        truncation_occurred: Whether truncation was applied.
    """
    text: str
    sections_found: Dict[str, Tuple[int, int]]
    sections_included: List[str]
    sections_excluded: List[str]
    original_length: int
    final_length: int
    truncation_occurred: bool


class PDFProcessor:
    """Processes PDF text with intelligent section prioritization.
    
    Identifies and preserves critical sections (title, abstract, introduction,
    conclusion) when truncating long papers for summarization.
    """
    
    # Section header patterns (case-insensitive, flexible matching)
    SECTION_PATTERNS = {
        'title': [
            r'^[A-Z][^.!?]{10,200}$',  # First line that looks like a title
        ],
        'abstract': [
            r'^\s*(?:Abstract|Summary|Synopsis)\s*$',
            r'^\s*ABSTRACT\s*$',
        ],
        'introduction': [
            r'^\s*(?:1\.?\s+)?Introduction\s*$',
            r'^\s*INTRODUCTION\s*$',
            r'^\s*(?:1\.?\s+)?Background\s*$',
        ],
        'conclusion': [
            r'^\s*(?:Conclusion|Conclusions|Discussion and Conclusion)\s*$',
            r'^\s*CONCLUSION\s*$',
            r'^\s*(?:Discussion|Summary and Discussion)\s*$',
        ],
    }
    
    # Priority order for sections (higher priority preserved first)
    SECTION_PRIORITY = ['title', 'abstract', 'introduction', 'conclusion']
    
    # Target sizes for prioritized sections (in characters)
    SECTION_TARGET_SIZES = {
        'title': 500,  # Usually very short
        'abstract': 2000,  # Typically 150-300 words
        'introduction': 5000,  # First 2000 words of introduction
        'conclusion': 3000,  # Last 2000 words of conclusion
    }
    
    def identify_sections(self, pdf_text: str) -> Dict[str, Tuple[int, int]]:
        """Identify key sections in PDF text.
        
        Args:
            pdf_text: Full PDF text content.
            
        Returns:
            Dictionary mapping section names to (start_char, end_char) positions.
            Sections found: 'title', 'abstract', 'introduction', 'conclusion'
        """
        sections: Dict[str, Tuple[int, int]] = {}
        lines = pdf_text.split('\n')
        
        # Find title (first substantial line, usually at the beginning)
        if not sections.get('title'):
            for i, line in enumerate(lines[:20]):  # Check first 20 lines
                line_stripped = line.strip()
                if (len(line_stripped) > 10 and 
                    len(line_stripped) < 200 and
                    not line_stripped.lower().startswith(('abstract', 'introduction', 'keywords', 'author'))):
                    # Likely title - take first substantial line
                    start = sum(len(l) + 1 for l in lines[:i])  # +1 for newline
                    end = start + len(line_stripped)
                    sections['title'] = (start, end)
                    break
        
        # Find abstract
        for pattern in self.SECTION_PATTERNS['abstract']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                # Abstract typically ends before Introduction or next major section
                next_section = re.search(
                    r'^\s*(?:1\.?\s+)?(?:Introduction|Background|Keywords|1\.)\s*$',
                    pdf_text[start:],
                    re.IGNORECASE | re.MULTILINE
                )
                if next_section:
                    end = start + next_section.start()
                else:
                    # Abstract ends ~2000 chars later or at next blank line section
                    end = min(start + 2000, len(pdf_text))
                    # Try to find natural end (double newline or Keywords)
                    natural_end = re.search(r'\n\n(?:Keywords|1\.|Introduction)', pdf_text[start:], re.IGNORECASE)
                    if natural_end:
                        end = start + natural_end.start()
                
                sections['abstract'] = (start, end)
                break
        
        # Find introduction
        for pattern in self.SECTION_PATTERNS['introduction']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                # Introduction typically 2000-5000 words, take first 5000 chars
                end = min(start + self.SECTION_TARGET_SIZES['introduction'], len(pdf_text))
                sections['introduction'] = (start, end)
                break
        
        # Find conclusion (search from end)
        for pattern in self.SECTION_PATTERNS['conclusion']:
            # Search backwards from end
            matches = list(re.finditer(pattern, pdf_text, re.IGNORECASE | re.MULTILINE))
            if matches:
                # Take the last match (most likely to be the conclusion)
                match = matches[-1]
                start = match.end()
                end = len(pdf_text)  # Conclusion goes to end
                # But limit to reasonable size
                if end - start > self.SECTION_TARGET_SIZES['conclusion']:
                    start = end - self.SECTION_TARGET_SIZES['conclusion']
                sections['conclusion'] = (start, end)
                break
        
        if sections:
            logger.debug(f"Identified {len(sections)} sections: {', '.join(sections.keys())}")
        else:
            logger.debug("No standard sections identified in PDF")
        return sections
    
    def smart_truncate(
        self,
        pdf_text: str,
        sections: Dict[str, Tuple[int, int]],
        max_chars: int
    ) -> Tuple[str, List[str], List[str]]:
        """Truncate PDF text while preserving prioritized sections.
        
        Args:
            pdf_text: Full PDF text.
            sections: Dictionary of identified sections with (start, end) positions.
            max_chars: Maximum characters for final text.
            
        Returns:
            Tuple of (truncated_text, sections_included, sections_excluded).
        """
        if len(pdf_text) <= max_chars:
            return pdf_text, list(sections.keys()), []
        
        # Build prioritized text by including sections in priority order
        included_sections: List[str] = []
        excluded_sections: List[str] = []
        result_parts: List[Tuple[int, int, str]] = []  # (start, end, section_name)
        remaining_chars = max_chars
        
        # First pass: include prioritized sections
        for section_name in self.SECTION_PRIORITY:
            if section_name in sections:
                start, end = sections[section_name]
                section_text = pdf_text[start:end]
                section_size = len(section_text)
                
                # Limit section to target size if needed
                if section_size > self.SECTION_TARGET_SIZES.get(section_name, section_size):
                    section_text = section_text[:self.SECTION_TARGET_SIZES[section_name]]
                    section_size = len(section_text)
                    end = start + section_size
                
                if section_size <= remaining_chars:
                    result_parts.append((start, end, section_name))
                    included_sections.append(section_name)
                    remaining_chars -= section_size
                else:
                    # Can't fit even prioritized section - take what we can
                    if remaining_chars > 100:  # Only if meaningful space left
                        section_text = section_text[:remaining_chars]
                        result_parts.append((start, start + remaining_chars, section_name))
                        included_sections.append(section_name)
                        remaining_chars = 0
                    excluded_sections.append(section_name)
        
        # Second pass: fill remaining space with middle content (proportional)
        if remaining_chars > 1000:  # Only if substantial space remains
            # Find gaps between included sections
            included_ranges = sorted([(start, end) for start, end, _ in result_parts])
            
            # Extract middle content (between prioritized sections)
            middle_parts = []
            last_end = 0
            
            for start, end in included_ranges:
                if start > last_end:
                    middle_text = pdf_text[last_end:start]
                    if len(middle_text.strip()) > 100:  # Only non-empty gaps
                        middle_parts.append((last_end, start, middle_text))
                last_end = max(last_end, end)
            
            # Add remaining text after last section
            if last_end < len(pdf_text):
                middle_text = pdf_text[last_end:]
                if len(middle_text.strip()) > 100:
                    middle_parts.append((last_end, len(pdf_text), middle_text))
            
            # Distribute remaining chars proportionally across middle parts
            if middle_parts:
                total_middle_chars = sum(len(text) for _, _, text in middle_parts)
                if total_middle_chars > 0:
                    for start, end, text in middle_parts:
                        proportion = len(text) / total_middle_chars
                        allocated = int(remaining_chars * proportion)
                        if allocated > 100:  # Only if meaningful
                            truncated_text = text[:allocated]
                            result_parts.append((start, start + allocated, 'middle'))
        
        # Sort parts by position and combine
        result_parts.sort(key=lambda x: x[0])
        result_text_parts = []
        last_end = 0
        
        for start, end, section_name in result_parts:
            if start > last_end:
                # Add gap marker if significant
                gap_size = start - last_end
                if gap_size > 50:
                    result_text_parts.append(f"\n[... {gap_size} characters of middle content omitted ...]\n")
            result_text_parts.append(pdf_text[start:end])
            last_end = max(last_end, end)
        
        final_text = ''.join(result_text_parts)
        
        # Ensure we don't exceed max_chars
        if len(final_text) > max_chars:
            final_text = final_text[:max_chars] + "\n\n[... truncated for summarization ...]"
        
        return final_text, included_sections, excluded_sections
    
    def extract_prioritized_text(
        self,
        pdf_path: Path,
        max_chars: int
    ) -> PrioritizedPDFText:
        """Extract and prioritize PDF text for summarization.
        
        Args:
            pdf_path: Path to PDF file.
            max_chars: Maximum characters to extract (0 for unlimited).
            
        Returns:
            PrioritizedPDFText with processed text and metadata.
        """
        # Extract full text
        pdf_text = extract_text_from_pdf(pdf_path)
        original_length = len(pdf_text)
        
        # If no limit or text fits, return as-is
        if max_chars <= 0 or original_length <= max_chars:
            sections = self.identify_sections(pdf_text)
            return PrioritizedPDFText(
                text=pdf_text,
                sections_found=sections,
                sections_included=list(sections.keys()),
                sections_excluded=[],
                original_length=original_length,
                final_length=original_length,
                truncation_occurred=False
            )
        
        # Identify sections
        sections = self.identify_sections(pdf_text)
        
        # Smart truncate with prioritization
        truncated_text, included, excluded = self.smart_truncate(
            pdf_text, sections, max_chars
        )
        
        truncation_pct = ((original_length - len(truncated_text)) / original_length * 100) if original_length > 0 else 0
        truncation_occurred = len(truncated_text) < original_length
        
        if truncation_occurred:
            logger.info(
                f"PDF text processed: {original_length:,} chars -> {len(truncated_text):,} chars "
                f"({truncation_pct:.1f}% removed). Sections included: {', '.join(included)}"
            )
            if excluded:
                logger.debug(f"Sections excluded due to truncation: {', '.join(excluded)}")
        else:
            logger.debug(
                f"PDF text processed: {original_length:,} chars (no truncation needed). "
                f"Sections included: {', '.join(included)}"
            )
        
        return PrioritizedPDFText(
            text=truncated_text,
            sections_found=sections,
            sections_included=included,
            sections_excluded=excluded,
            original_length=original_length,
            final_length=len(truncated_text),
            truncation_occurred=truncation_occurred
        )


