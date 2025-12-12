"""Context extraction for paper summarization.

This module extracts and structures key sections from PDFs to provide
focused context for summarization, improving accuracy and relevance.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.summarization.models import SummarizationContext

logger = get_logger(__name__)


@dataclass
class PaperStructure:
    """Structure of a paper with identified sections.
    
    Attributes:
        title: Paper title.
        abstract: Abstract text.
        introduction: Introduction section.
        conclusion: Conclusion section.
        methods: Methodology section (optional).
        results: Results section (optional).
        discussion: Discussion section (optional).
    """
    title: str
    abstract: str
    introduction: str
    conclusion: str
    methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None


class ContextExtractor:
    """Extracts structured context from PDF text for summarization.
    
    Identifies key sections, extracts key terms, and creates structured
    context objects to improve summarization quality.
    """
    
    # Section header patterns (case-insensitive, flexible matching)
    SECTION_PATTERNS = {
        'abstract': [
            r'^\s*(?:Abstract|Summary|Synopsis)\s*$',
            r'^\s*ABSTRACT\s*$',
        ],
        'introduction': [
            r'^\s*(?:1\.?\s+)?Introduction\s*$',
            r'^\s*INTRODUCTION\s*$',
            r'^\s*(?:1\.?\s+)?Background\s*$',
        ],
        'methods': [
            r'^\s*(?:2\.?\s+)?(?:Method|Methods|Methodology|Approach)\s*$',
            r'^\s*METHODS?\s*$',
            r'^\s*METHODOLOGY\s*$',
        ],
        'results': [
            r'^\s*(?:3\.?\s+)?(?:Results?|Findings?|Outcomes?)\s*$',
            r'^\s*RESULTS?\s*$',
        ],
        'discussion': [
            r'^\s*(?:4\.?\s+)?(?:Discussion|Analysis)\s*$',
            r'^\s*DISCUSSION\s*$',
        ],
        'conclusion': [
            r'^\s*(?:Conclusion|Conclusions|Discussion and Conclusion)\s*$',
            r'^\s*CONCLUSION\s*$',
            r'^\s*(?:Discussion|Summary and Discussion)\s*$',
        ],
    }
    
    # Stop words for key term extraction
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'paper', 'presents', 'proposes', 'investigates',
        'studies', 'examines', 'analyzes', 'discusses', 'using', 'based',
        'through', 'within', 'between', 'during', 'while', 'where', 'when',
        'what', 'how', 'why', 'about', 'their', 'there', 'which', 'common',
        'very', 'more', 'most', 'some', 'many', 'such', 'only', 'also',
    }
    
    # Common terms to exclude from key terms
    COMMON_TERMS = {
        'that', 'with', 'from', 'this', 'which', 'their', 'there', 'these',
        'those', 'would', 'could', 'should', 'might', 'about', 'using',
        'based', 'through', 'within', 'between', 'during', 'while', 'where',
        'when', 'what', 'how', 'why',
    }
    
    def extract_paper_structure(self, pdf_text: str) -> PaperStructure:
        """Identify all sections in PDF text.
        
        Args:
            pdf_text: Full PDF text content.
            
        Returns:
            PaperStructure with identified sections.
        """
        lines = pdf_text.split('\n')
        
        # Find title (first substantial line, usually at the beginning)
        title = ""
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            line_stripped = line.strip()
            if (len(line_stripped) > 10 and 
                len(line_stripped) < 200 and
                not line_stripped.lower().startswith(('abstract', 'introduction', 'keywords', 'author'))):
                title = line_stripped
                break
        
        # Find abstract
        abstract = ""
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
                    end = min(start + 2000, len(pdf_text))
                    natural_end = re.search(r'\n\n(?:Keywords|1\.|Introduction)', pdf_text[start:], re.IGNORECASE)
                    if natural_end:
                        end = start + natural_end.start()
                
                abstract = pdf_text[start:end].strip()
                break
        
        # Find introduction
        introduction = ""
        for pattern in self.SECTION_PATTERNS['introduction']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                # Take first 3000 chars of introduction
                end = min(start + 3000, len(pdf_text))
                introduction = pdf_text[start:end].strip()
                break
        
        # Find methods
        methods = None
        for pattern in self.SECTION_PATTERNS['methods']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                # Methods typically 2000-5000 chars
                next_section = re.search(
                    r'^\s*(?:3\.?\s+)?(?:Results?|Findings?|Discussion)\s*$',
                    pdf_text[start:],
                    re.IGNORECASE | re.MULTILINE
                )
                if next_section:
                    end = start + next_section.start()
                else:
                    end = min(start + 5000, len(pdf_text))
                methods = pdf_text[start:end].strip()
                break
        
        # Find results
        results = None
        for pattern in self.SECTION_PATTERNS['results']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                next_section = re.search(
                    r'^\s*(?:4\.?\s+)?(?:Discussion|Conclusion)\s*$',
                    pdf_text[start:],
                    re.IGNORECASE | re.MULTILINE
                )
                if next_section:
                    end = start + next_section.start()
                else:
                    end = min(start + 5000, len(pdf_text))
                results = pdf_text[start:end].strip()
                break
        
        # Find discussion
        discussion = None
        for pattern in self.SECTION_PATTERNS['discussion']:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start = match.end()
                next_section = re.search(
                    r'^\s*(?:Conclusion|References?|Bibliography)\s*$',
                    pdf_text[start:],
                    re.IGNORECASE | re.MULTILINE
                )
                if next_section:
                    end = start + next_section.start()
                else:
                    end = min(start + 5000, len(pdf_text))
                discussion = pdf_text[start:end].strip()
                break
        
        # Find conclusion (search from end)
        conclusion = ""
        for pattern in self.SECTION_PATTERNS['conclusion']:
            matches = list(re.finditer(pattern, pdf_text, re.IGNORECASE | re.MULTILINE))
            if matches:
                match = matches[-1]  # Take last match
                start = match.end()
                end = len(pdf_text)
                # Limit to last 3000 chars
                if end - start > 3000:
                    start = end - 3000
                conclusion = pdf_text[start:end].strip()
                break
        
        return PaperStructure(
            title=title,
            abstract=abstract,
            introduction=introduction,
            conclusion=conclusion,
            methods=methods,
            results=results,
            discussion=discussion
        )
    
    def extract_key_terms(self, pdf_text: str, title: str) -> List[str]:
        """Extract actual key terms from title and abstract.
        
        Args:
            pdf_text: Full PDF text.
            title: Paper title.
            
        Returns:
            List of key terms (4+ characters, not stop words).
        """
        # Extract key terms from title (4+ char words, not stop words)
        title_lower = title.lower()
        title_terms = [
            w for w in re.findall(r'\b[a-zA-Z]{4,}\b', title_lower)
            if w not in self.STOP_WORDS and w not in self.COMMON_TERMS
        ]
        
        # Extract key terms from abstract (first 2000 chars)
        abstract_text = pdf_text[:2000].lower()
        abstract_terms = [
            w for w in re.findall(r'\b[a-zA-Z]{4,}\b', abstract_text)
            if w not in self.STOP_WORDS and w not in self.COMMON_TERMS
        ]
        
        # Count frequency and take top terms
        term_counts = Counter(abstract_terms)
        top_abstract_terms = [term for term, count in term_counts.most_common(10)]
        
        # Combine (prioritize title terms)
        all_terms = list(set(title_terms + top_abstract_terms))[:15]
        
        logger.debug(f"Extracted {len(all_terms)} key terms: {', '.join(all_terms[:10])}")
        
        return all_terms
    
    def extract_equations(self, pdf_text: str) -> List[str]:
        """Extract mathematical equations from PDF text.
        
        Args:
            pdf_text: Full PDF text.
            
        Returns:
            List of equation strings (simplified extraction).
        """
        # Simple pattern matching for equations
        # Look for patterns like: = ... =, or ( ... ), or [ ... ]
        equation_patterns = [
            r'=\s*[^=\n]{10,100}=',  # Equations with = signs
            r'\([^)]{20,100}\)',  # Parenthesized expressions
            r'\[[^\]]{20,100}\]',  # Bracketed expressions
        ]
        
        equations = []
        for pattern in equation_patterns:
            matches = re.findall(pattern, pdf_text)
            equations.extend(matches[:5])  # Limit to 5 per pattern
        
        return equations[:10]  # Total limit of 10 equations
    
    def create_summarization_context(
        self,
        pdf_text: str,
        title: str,
        max_chars: Optional[int] = None
    ) -> SummarizationContext:
        """Create structured context object for summarization.
        
        Args:
            pdf_text: Full PDF text (will be stored as-is in full_text field).
            title: Paper title.
            max_chars: Optional maximum characters for context (for truncation).
                      NOTE: This does NOT truncate full_text - full_text always contains complete PDF.
            
        Returns:
            SummarizationContext with structured information.
        """
        # Extract paper structure
        structure = self.extract_paper_structure(pdf_text)
        
        # Extract key terms
        key_terms = self.extract_key_terms(pdf_text, title if title else structure.title)
        
        # Extract equations
        equations = self.extract_equations(pdf_text)
        
        # Use provided title or extracted title
        final_title = title if title else structure.title
        
        # IMPORTANT: full_text always contains the COMPLETE PDF text (no truncation)
        # This ensures the LLM has access to all content for extracting claims, methods, quotes
        complete_pdf_text = pdf_text
        
        # Create context
        context = SummarizationContext(
            title=final_title,
            abstract=structure.abstract,
            introduction=structure.introduction,
            conclusion=structure.conclusion,
            key_terms=key_terms,
            equations=equations,
            methods=structure.methods,
            results=structure.results,
            discussion=structure.discussion,
            full_text=complete_pdf_text  # Always complete, never truncated
        )
        
        # Log context creation with detailed breakdown
        context_parts = []
        if final_title:
            context_parts.append(f"title={len(final_title)} chars")
        if structure.abstract:
            context_parts.append(f"abstract={len(structure.abstract)} chars")
        if structure.introduction:
            context_parts.append(f"intro={len(structure.introduction)} chars")
        if structure.conclusion:
            context_parts.append(f"conclusion={len(structure.conclusion)} chars")
        if structure.methods:
            context_parts.append(f"methods={len(structure.methods)} chars")
        if structure.results:
            context_parts.append(f"results={len(structure.results)} chars")
        if structure.discussion:
            context_parts.append(f"discussion={len(structure.discussion)} chars")
        if key_terms:
            context_parts.append(f"key_terms={len(key_terms)}")
        if equations:
            context_parts.append(f"equations={len(equations)}")
        context_parts.append(f"full_text={len(complete_pdf_text)} chars (COMPLETE)")
        
        logger.info(f"Created context: {', '.join(context_parts)}")
        
        return context
