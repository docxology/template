"""Advanced document quality analysis and metrics.

This module provides comprehensive quality analysis for research documents,
including readability metrics, structural analysis, and academic standards
compliance checking.

All functions follow the thin orchestrator pattern and are fully tested
with 100% coverage requirements.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter
import statistics

from pypdf import PdfReader


class QualityMetrics:
    """Container for document quality metrics."""

    def __init__(self):
        self.readability_score: float = 0.0
        self.academic_compliance: float = 0.0
        self.structural_integrity: float = 0.0
        self.formatting_quality: float = 0.0
        self.overall_score: float = 0.0
        self.issues: List[str] = []
        self.recommendations: List[str] = []


def extract_text_from_pdf_detailed(pdf_path: Path) -> Dict[str, Any]:
    """Extract detailed text information from PDF for quality analysis.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with detailed text analysis

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF cannot be read
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(str(pdf_path))
        pages_text = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages_text.append({
                'page_number': i + 1,
                'text': text,
                'word_count': len(text.split()) if text else 0,
                'line_count': len(text.split('\n')) if text else 0
            })

        total_words = sum(page['word_count'] for page in pages_text)
        total_lines = sum(page['line_count'] for page in pages_text)

        return {
            'total_pages': len(pages_text),
            'total_words': total_words,
            'total_lines': total_lines,
            'pages': pages_text,
            'avg_words_per_page': total_words / len(pages_text) if pages_text else 0,
            'avg_lines_per_page': total_lines / len(pages_text) if pages_text else 0
        }

    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def analyze_readability(text: str) -> Dict[str, float]:
    """Analyze text readability using multiple metrics.

    Args:
        text: Text content to analyze

    Returns:
        Dictionary with readability metrics
    """
    if not text:
        return {'flesch_score': 0.0, 'gunning_fog': 0.0, 'avg_sentence_length': 0.0}

    sentences = re.split(r'[.!?]+', text)
    words = re.findall(r'\b\w+\b', text)
    syllables = count_syllables(text)

    # Remove empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences or not words:
        return {'flesch_score': 0.0, 'gunning_fog': 0.0, 'avg_sentence_length': 0.0}

    avg_sentence_length = len(words) / len(sentences)
    avg_syllables_per_word = syllables / len(words) if words else 0

    # Simplified Flesch Reading Ease Score
    flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

    # Simplified Gunning Fog Index
    complex_words = sum(1 for word in words if count_syllables_word(word) >= 3)
    gunning_fog = 0.4 * ((len(words) / len(sentences)) + 100 * (complex_words / len(words)))

    return {
        'flesch_score': max(0, min(100, flesch_score)),
        'gunning_fog': max(0, gunning_fog),
        'avg_sentence_length': avg_sentence_length,
        'avg_syllables_per_word': avg_syllables_per_word
    }


def count_syllables(text: str) -> int:
    """Count syllables in text using a simple heuristic.

    Args:
        text: Text to analyze

    Returns:
        Estimated syllable count
    """
    text = text.lower()
    syllables = 0
    words = re.findall(r'\b\w+\b', text)

    for word in words:
        syllables += count_syllables_word(word)

    return syllables


def count_syllables_word(word: str) -> int:
    """Count syllables in a single word.

    Args:
        word: Word to analyze

    Returns:
        Syllable count
    """
    word = word.lower()

    # Handle special cases
    if len(word) <= 3:
        return 1

    # Remove common silent endings
    word = re.sub(r'e$', '', word)
    word = re.sub(r'es$', '', word)
    word = re.sub(r'ed$', '', word)

    # Count vowel groups
    vowels = 'aeiouy'
    syllables = 0
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllables += 1
        previous_was_vowel = is_vowel

    # Ensure at least one syllable
    return max(1, syllables)


def analyze_academic_standards(text: str) -> Dict[str, Any]:
    """Analyze compliance with academic writing standards.

    Args:
        text: Document text to analyze

    Returns:
        Dictionary with academic compliance metrics
    """
    issues = []
    recommendations = []

    # Check for academic writing patterns
    has_abstract = bool(re.search(r'\babstract\b', text.lower()))
    has_introduction = bool(re.search(r'\bintroduction\b', text.lower()))
    has_methodology = bool(re.search(r'\bmethodology\b|\bmethods\b', text.lower()))
    has_results = bool(re.search(r'\bresults?\b', text.lower()))
    has_discussion = bool(re.search(r'\bdiscussion\b', text.lower()))
    has_conclusion = bool(re.search(r'\bconclusion\b', text.lower()))

    # Check for citations
    citation_count = len(re.findall(r'\[\d+\]|\(\d+\)|\\cite\{[^}]+\}', text))

    # Check for equations
    equation_count = len(re.findall(r'\\begin\{equation\}|\\begin\{align\}|\\begin\{gather\}', text))

    # Check for figures and tables
    figure_count = len(re.findall(r'\\begin\{figure\}|\\includegraphics', text))
    table_count = len(re.findall(r'\\begin\{table\}', text))

    # Academic structure score
    structure_score = 0
    if has_abstract: structure_score += 15
    if has_introduction: structure_score += 10
    if has_methodology: structure_score += 15
    if has_results: structure_score += 15
    if has_discussion: structure_score += 15
    if has_conclusion: structure_score += 15
    if citation_count > 0: structure_score += 10
    if equation_count > 0: structure_score += 5

    # Recommendations
    if not has_abstract:
        recommendations.append("Consider adding an abstract section")
    if citation_count < 5:
        recommendations.append("Consider adding more citations for academic rigor")
    if equation_count == 0:
        recommendations.append("Consider adding mathematical formulations if applicable")
    if figure_count == 0 and table_count == 0:
        recommendations.append("Consider adding figures or tables for better presentation")

    return {
        'structure_score': min(100, structure_score),
        'has_abstract': has_abstract,
        'has_introduction': has_introduction,
        'has_methodology': has_methodology,
        'has_results': has_results,
        'has_discussion': has_discussion,
        'has_conclusion': has_conclusion,
        'citation_count': citation_count,
        'equation_count': equation_count,
        'figure_count': figure_count,
        'table_count': table_count,
        'recommendations': recommendations
    }


def analyze_structural_integrity(text: str) -> Dict[str, Any]:
    """Analyze document structural integrity.

    Args:
        text: Document text to analyze

    Returns:
        Dictionary with structural analysis
    """
    issues = []

    # Check for section consistency
    sections = re.findall(r'\\section\{([^}]+)\}', text)
    subsections = re.findall(r'\\subsection\{([^}]+)\}', text)

    # Check for proper LaTeX structure
    has_title = bool(re.search(r'\\title\{', text))
    has_author = bool(re.search(r'\\author\{', text))
    has_date = bool(re.search(r'\\date\{', text))
    has_maketitle = bool(re.search(r'\\maketitle', text))

    # Check for table of contents
    has_toc = bool(re.search(r'\\tableofcontents', text))

    # Check for proper bibliography
    has_bibliography = bool(re.search(r'\\bibliography\{', text))

    # Structural integrity score
    structure_score = 0
    if has_title: structure_score += 10
    if has_author: structure_score += 10
    if has_date: structure_score += 10
    if has_maketitle: structure_score += 10
    if has_toc: structure_score += 15
    if has_bibliography: structure_score += 15
    if len(sections) >= 3: structure_score += 15
    if len(subsections) >= 2: structure_score += 15

    # Issues detection
    if not has_title:
        issues.append("Missing document title")
    if not has_author:
        issues.append("Missing document author")
    if not has_maketitle:
        issues.append("Missing \\maketitle command")
    if not has_toc:
        issues.append("Missing table of contents")
    if not has_bibliography:
        issues.append("Missing bibliography")

    return {
        'structural_score': min(100, structure_score),
        'section_count': len(sections),
        'subsection_count': len(subsections),
        'has_title': has_title,
        'has_author': has_author,
        'has_date': has_date,
        'has_maketitle': has_maketitle,
        'has_toc': has_toc,
        'has_bibliography': has_bibliography,
        'issues': issues
    }


def analyze_formatting_quality(text: str) -> Dict[str, Any]:
    """Analyze document formatting quality.

    Args:
        text: Document text to analyze

    Returns:
        Dictionary with formatting analysis
    """
    issues = []
    recommendations = []

    # Check for consistent formatting patterns
    heading_levels = len(re.findall(r'\\section\{|\\subsection\{|\\subsubsection\{', text))

    # Check for proper math formatting
    math_environments = len(re.findall(r'\\begin\{equation\}|\\begin\{align\}|\\begin\{gather\}', text))
    inline_math = len(re.findall(r'\$[^$]+\$', text))

    # Check for proper figure formatting
    figure_captions = len(re.findall(r'\\caption\{', text))

    # Check for consistent spacing
    excessive_spaces = len(re.findall(r'\s{3,}', text))
    excessive_newlines = len(re.findall(r'\n{3,}', text))

    # Formatting score
    formatting_score = 0
    if heading_levels > 0: formatting_score += 20
    if math_environments > 0: formatting_score += 20
    if inline_math > 0: formatting_score += 10
    if figure_captions > 0: formatting_score += 15
    if excessive_spaces == 0: formatting_score += 10
    if excessive_newlines == 0: formatting_score += 10
    if heading_levels >= 3: formatting_score += 15

    # Issues and recommendations
    if excessive_spaces > 0:
        issues.append(f"Found {excessive_spaces} instances of excessive whitespace")
        recommendations.append("Use consistent spacing throughout the document")

    if excessive_newlines > 0:
        issues.append(f"Found {excessive_newlines} instances of excessive newlines")
        recommendations.append("Use consistent line breaks throughout the document")

    if math_environments == 0 and inline_math == 0:
        recommendations.append("Consider adding mathematical formulations if applicable")

    return {
        'formatting_score': min(100, formatting_score),
        'heading_levels': heading_levels,
        'math_environments': math_environments,
        'inline_math': inline_math,
        'figure_captions': figure_captions,
        'excessive_spaces': excessive_spaces,
        'excessive_newlines': excessive_newlines,
        'issues': issues,
        'recommendations': recommendations
    }


def calculate_overall_quality_score(metrics: QualityMetrics) -> float:
    """Calculate overall quality score from individual metrics.

    Args:
        metrics: QualityMetrics object with individual scores

    Returns:
        Overall quality score (0-100)
    """
    # Weighted average of different quality aspects
    weights = {
        'readability': 0.25,
        'academic': 0.30,
        'structural': 0.25,
        'formatting': 0.20
    }

    overall = (
        metrics.readability_score * weights['readability'] +
        metrics.academic_compliance * weights['academic'] +
        metrics.structural_integrity * weights['structural'] +
        metrics.formatting_quality * weights['formatting']
    )

    return min(100, max(0, overall))


def analyze_document_quality(pdf_path: Path, text: Optional[str] = None) -> QualityMetrics:
    """Perform comprehensive quality analysis of a research document.

    Args:
        pdf_path: Path to PDF file to analyze
        text: Optional pre-extracted text (for efficiency)

    Returns:
        QualityMetrics object with comprehensive analysis

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF cannot be analyzed
    """
    # Extract text if not provided
    if text is None:
        try:
            text_info = extract_text_from_pdf_detailed(pdf_path)
            text = '\n'.join(page['text'] for page in text_info['pages'])
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}")

    if not text:
        raise ValueError("No text content found in PDF")

    # Perform individual analyses
    readability = analyze_readability(text)
    academic = analyze_academic_standards(text)
    structural = analyze_structural_integrity(text)
    formatting = analyze_formatting_quality(text)

    # Create metrics object
    metrics = QualityMetrics()
    metrics.readability_score = readability['flesch_score']
    metrics.academic_compliance = academic['structure_score']
    metrics.structural_integrity = structural['structural_score']
    metrics.formatting_quality = formatting['formatting_score']
    metrics.issues = structural['issues'] + formatting['issues']
    metrics.recommendations = academic['recommendations'] + formatting['recommendations']
    metrics.overall_score = calculate_overall_quality_score(metrics)

    return metrics


def generate_quality_report(metrics: QualityMetrics) -> str:
    """Generate a human-readable quality report.

    Args:
        metrics: QualityMetrics object with analysis results

    Returns:
        Formatted quality report string
    """
    report = []
    report.append("=" * 60)
    report.append("📊 DOCUMENT QUALITY ANALYSIS REPORT")
    report.append("=" * 60)
    report.append(f"Overall Quality Score: {metrics.overall_score:.1f}/100")
    report.append("")

    report.append("📈 Individual Scores:")
    report.append(f"  • Readability: {metrics.readability_score:.1f}/100")
    report.append(f"  • Academic Compliance: {metrics.academic_compliance:.1f}/100")
    report.append(f"  • Structural Integrity: {metrics.structural_integrity:.1f}/100")
    report.append(f"  • Formatting Quality: {metrics.formatting_quality:.1f}/100")
    report.append("")

    if metrics.issues:
        report.append("⚠️  Issues Found:")
        for issue in metrics.issues:
            report.append(f"  • {issue}")
        report.append("")

    if metrics.recommendations:
        report.append("💡 Recommendations:")
        for rec in metrics.recommendations:
            report.append(f"  • {rec}")
        report.append("")

    # Quality interpretation
    if metrics.overall_score >= 90:
        report.append("🎉 Excellent quality - ready for publication!")
    elif metrics.overall_score >= 75:
        report.append("✅ Good quality - minor improvements recommended.")
    elif metrics.overall_score >= 60:
        report.append("⚠️  Fair quality - significant improvements needed.")
    else:
        report.append("❌ Poor quality - major revisions required.")

    report.append("=" * 60)

    return '\n'.join(report)


def check_document_accessibility(pdf_path: Path) -> Dict[str, Any]:
    """Check document accessibility features.

    Args:
        pdf_path: Path to PDF file to check

    Returns:
        Dictionary with accessibility analysis
    """
    try:
        reader = PdfReader(str(pdf_path))

        accessibility_features = {
            'has_bookmarks': len(reader.outline) > 0,
            'has_metadata': reader.metadata is not None,
            'total_pages': len(reader.pages),
            'page_labels': []
        }

        # Check for page labels (basic accessibility)
        for i, page in enumerate(reader.pages):
            try:
                # Try to extract basic text structure
                text = page.extract_text()
                accessibility_features['page_labels'].append({
                    'page': i + 1,
                    'has_text': bool(text.strip()),
                    'text_length': len(text)
                })
            except:
                accessibility_features['page_labels'].append({
                    'page': i + 1,
                    'has_text': False,
                    'text_length': 0
                })

        return accessibility_features

    except Exception as e:
        return {
            'error': str(e),
            'has_bookmarks': False,
            'has_metadata': False,
            'total_pages': 0,
            'page_labels': []
        }


def validate_research_document_completeness(text: str) -> Dict[str, Any]:
    """Validate that a research document contains all expected sections.

    Args:
        text: Document text to analyze

    Returns:
        Dictionary with completeness analysis
    """
    text_lower = text.lower()

    # Define expected sections for different document types
    research_sections = {
        'abstract': ['abstract', 'summary'],
        'introduction': ['introduction', 'background', 'motivation'],
        'related_work': ['related work', 'literature review', 'previous work'],
        'methodology': ['methodology', 'methods', 'approach', 'algorithm'],
        'experiments': ['experiments', 'evaluation', 'results', 'validation'],
        'discussion': ['discussion', 'analysis', 'interpretation'],
        'conclusion': ['conclusion', 'future work', 'conclusions'],
        'references': ['references', 'bibliography', 'citations']
    }

    found_sections = {}
    missing_sections = []

    for section, keywords in research_sections.items():
        found = any(keyword in text_lower for keyword in keywords)
        found_sections[section] = found
        if not found:
            missing_sections.append(section)

    completeness_score = (len(research_sections) - len(missing_sections)) / len(research_sections) * 100

    return {
        'completeness_score': completeness_score,
        'found_sections': found_sections,
        'missing_sections': missing_sections,
        'total_expected': len(research_sections),
        'sections_found': len(research_sections) - len(missing_sections)
    }


def analyze_document_metrics(text: str) -> Dict[str, Any]:
    """Analyze various document metrics for quality assessment.

    Args:
        text: Document text to analyze

    Returns:
        Dictionary with comprehensive document metrics
    """
    words = re.findall(r'\b\w+\b', text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Basic metrics
    word_count = len(words)
    sentence_count = len(sentences)
    paragraph_count = len(re.findall(r'\n\s*\n', text)) + 1

    # Advanced metrics
    avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
    avg_sentences_per_paragraph = sentence_count / paragraph_count if paragraph_count > 0 else 0

    # Vocabulary diversity
    unique_words = len(set(words))
    vocabulary_richness = unique_words / word_count if word_count > 0 else 0

    # Common academic words
    academic_words = [
        'methodology', 'algorithm', 'analysis', 'evaluation', 'experiment',
        'hypothesis', 'theory', 'framework', 'model', 'approach',
        'implementation', 'validation', 'conclusion', 'discussion', 'results'
    ]

    academic_word_count = sum(1 for word in words if word.lower() in academic_words)

    return {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'paragraph_count': paragraph_count,
        'avg_words_per_sentence': avg_words_per_sentence,
        'avg_sentences_per_paragraph': avg_sentences_per_paragraph,
        'vocabulary_richness': vocabulary_richness,
        'unique_words': unique_words,
        'academic_word_count': academic_word_count,
        'academic_density': academic_word_count / word_count if word_count > 0 else 0
    }
