"""Review generation utilities for manuscript review operations."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Default configuration values for review operations
DEFAULT_MAX_INPUT_LENGTH = 500000  # Characters
DEFAULT_REVIEW_MAX_TOKENS = 16384  # Increased for longer review outputs (matches long_max_tokens default)
DEFAULT_REVIEW_TIMEOUT = 600.0  # seconds


def get_manuscript_review_system_prompt() -> str:
    """Get the system prompt for manuscript reviews.
    
    Returns:
        System prompt string for manuscript review operations
    """
    return (
        "You are an expert scientific reviewer. "
        "Provide thorough, constructive, and scientifically rigorous reviews. "
        "Focus on methodology, clarity, and scientific contribution."
    )


def get_max_input_length() -> int:
    """Get maximum input length for manuscript review operations.
    
    Reads from LLM_MAX_INPUT_LENGTH environment variable if set,
    otherwise returns DEFAULT_MAX_INPUT_LENGTH.
    
    Returns:
        Maximum number of characters that can be processed (0 = unlimited)
    """
    env_limit = os.environ.get('LLM_MAX_INPUT_LENGTH')
    if env_limit:
        try:
            return int(env_limit)
        except ValueError:
            return DEFAULT_MAX_INPUT_LENGTH
    return DEFAULT_MAX_INPUT_LENGTH


def get_review_timeout() -> float:
    """Get timeout for review generation operations.
    
    Returns:
        Timeout in seconds
    """
    return DEFAULT_REVIEW_TIMEOUT


def get_review_max_tokens() -> tuple[int, str]:
    """Get maximum tokens for review generation.
    
    Reads from LLM_LONG_MAX_TOKENS environment variable if set,
    otherwise uses DEFAULT_REVIEW_MAX_TOKENS.
    
    Returns:
        Tuple of (max_tokens, source_description)
    """
    import os
    env_tokens = os.environ.get('LLM_LONG_MAX_TOKENS')
    if env_tokens:
        try:
            return (int(env_tokens), "LLM_LONG_MAX_TOKENS environment variable")
        except ValueError:
            pass
    
    # Also check LLM_REVIEW_MAX_TOKENS for review-specific override
    env_review_tokens = os.environ.get('LLM_REVIEW_MAX_TOKENS')
    if env_review_tokens:
        try:
            return (int(env_review_tokens), "LLM_REVIEW_MAX_TOKENS environment variable")
        except ValueError:
            pass
    
    return (DEFAULT_REVIEW_MAX_TOKENS, "default_config")


def validate_review_quality(
    review_text: str,
    review_type: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate that a review meets quality standards.
    
    Args:
        review_text: The review text to validate
        review_type: Type of review (executive_summary, quality_review, 
                    improvement_suggestions, methodology_review)
        model_name: Optional model name for logging/context
        
    Returns:
        Tuple of (is_valid, issues_list, details_dict)
    """
    from infrastructure.llm.validation.structure import (
        validate_section_completeness,
        extract_structured_sections,
    )
    from infrastructure.llm.validation.repetition import detect_repetition
    from infrastructure.llm.validation.format import (
        is_off_topic,
        detect_conversational_phrases,
    )
    
    issues: List[str] = []
    details: Dict[str, Any] = {
        "word_count": len(review_text.split()),
        "review_type": review_type or "default",
    }
    
    # Basic checks
    word_count = len(review_text.split()) if review_text else 0
    details["word_count"] = word_count
    
    if not review_text or len(review_text.strip()) < 50:
        issues.append("Review text too short or empty")
        # Still check word count and add word count issue
        if review_type == "executive_summary":
            issues.append(f"Too short: {word_count} words (minimum 250 words)")
        elif review_type == "quality_review" and word_count < 400:
            issues.append(f"Too short: {word_count} words (minimum 400 words)")
        elif review_type == "improvement_suggestions" and word_count < 200:
            issues.append(f"Too short: {word_count} words (minimum 200 words)")
        elif review_type == "methodology_review" and word_count < 400:
            issues.append(f"Too short: {word_count} words (minimum 400 words)")
        elif word_count > 0:
            issues.append(f"Too short: {word_count} words")
        return False, issues, details
    
    # Check for off-topic content
    if is_off_topic(review_text):
        issues.append("Response appears off-topic or conversational")
        details["off_topic"] = True
        return False, issues, details
    
    # Check for conversational phrases (format compliance)
    conversational = detect_conversational_phrases(review_text)
    if conversational:
        details["format_compliance"] = {
            "conversational_phrases": conversational,
            "format_warnings": len(conversational)
        }
    
    # Review type-specific validation
    if review_type == "executive_summary":
        # Executive summary: minimum 250 words, requires sections
        if word_count < 250:
            issues.append(f"Too short: {word_count} words (minimum 250 words)")
        
        # Check for required sections (flexible matching)
        required_sections = [
            "## Overview", "## Key Contributions", "## Methodology",
            "## Principal Results", "## Significance"
        ]
        alternatives = {
            "overview": ["summary", "introduction"],
            "key contributions": ["contributions", "main contributions"],
            "methodology": ["methods", "approach"],
            "principal results": ["results", "findings", "key results"],
            "significance": ["impact", "implications", "significance"]
        }
        
        sections = extract_structured_sections(review_text)
        details["sections_found"] = list(sections.keys())
        
        # Check if we have at least some structure
        # Be very lenient - if we have any sections or markdown headers, consider it structured
        has_any_headers = bool(re.search(r'^#{1,6}\s+', review_text, re.MULTILINE))
        
        if not sections and not has_any_headers:
            issues.append("Missing expected structure: no section headers found")
        elif sections:
            # We have sections - that's good enough for structure validation
            details["matched_sections"] = list(sections.keys())
        # If we have headers but no sections extracted, that's still okay (lenient)
    
    elif review_type == "quality_review":
        # Quality review: minimum 400 words, requires scores or assessment sections
        if word_count < 400:
            issues.append(f"Too short: {word_count} < 400 words")
        
        # Check for scores or assessment keywords
        score_patterns = [
            r'score:\s*\d+',
            r'rating:\s*\d+',
            r'\[\d+/\d+\]',
            r'\d+\s*out\s*of\s*\d+',
            r'rating\s*of\s*\d+',
        ]
        assessment_keywords = [
            'clarity', 'structure', 'readability', 'technical accuracy',
            'overall quality', 'assessment', 'evaluation'
        ]
        
        has_score = any(re.search(pattern, review_text, re.IGNORECASE) 
                       for pattern in score_patterns)
        has_assessment = any(keyword in review_text.lower() 
                            for keyword in assessment_keywords)
        
        if not has_score and not has_assessment:
            issues.append("Missing scoring or assessment sections")
        else:
            details["has_scoring"] = has_score
            details["has_assessment"] = has_assessment
    
    elif review_type == "improvement_suggestions":
        # Improvement suggestions: minimum 200 words, requires priority sections
        if word_count < 200:
            issues.append(f"Too short: {word_count} words (minimum 200 words)")
        
        # Check for priority sections
        priority_keywords = [
            'high priority', 'medium priority', 'low priority',
            'critical', 'immediate', 'moderate', 'nice to have',
            'urgent', 'important', 'optional'
        ]
        
        has_priorities = any(keyword in review_text.lower() 
                           for keyword in priority_keywords)
        
        if not has_priorities:
            # Check for section headers that might indicate priorities
            sections = extract_structured_sections(review_text)
            priority_sections = [s for s in sections.keys() 
                                if any(kw in s.lower() for kw in ['priority', 'critical', 'immediate'])]
            if not priority_sections:
                issues.append("Missing priority-based organization")
            else:
                details["priority_sections"] = priority_sections
        else:
            details["has_priorities"] = True
    
    elif review_type == "methodology_review":
        # Methodology review: minimum 400 words, at least one section
        if word_count < 400:
            issues.append(f"Too short: {word_count} < 400 words")
        
        # Check for at least one section
        sections = extract_structured_sections(review_text)
        if not sections:
            # Check for keywords that indicate structure
            structure_keywords = ['strengths', 'weaknesses', 'limitations', 'strong points']
            has_structure = any(kw in review_text.lower() for kw in structure_keywords)
            if not has_structure:
                issues.append("Missing expected structure: no sections or structure keywords found")
        else:
            details["sections_found"] = list(sections.keys())
    
    # Repetition detection
    has_repetition, duplicates, unique_ratio = detect_repetition(review_text)
    details["repetition"] = {
        "has_repetition": has_repetition,
        "unique_ratio": unique_ratio,
        "duplicates_found": len(duplicates),
    }
    
    if has_repetition and unique_ratio < 0.5:
        issues.append(f"Severe repetition detected (unique ratio: {unique_ratio:.1%})")
    
    is_valid = len(issues) == 0
    return is_valid, issues, details


def create_review_client():
    """Create an LLM client configured for review operations.
    
    Returns:
        LLMClient instance configured for reviews
    """
    from infrastructure.llm import LLMClient, LLMConfig
    
    config = LLMConfig(
        max_tokens=DEFAULT_REVIEW_MAX_TOKENS,
        timeout=DEFAULT_REVIEW_TIMEOUT,
    )
    return LLMClient(config)


def check_ollama_availability() -> bool:
    """Check if Ollama is available for review operations.
    
    Returns:
        True if Ollama is available
    """
    from infrastructure.llm.utils.ollama import is_ollama_running
    return is_ollama_running()


def warmup_model(model_name: str) -> bool:
    """Warm up a model by sending a test query.
    
    Args:
        model_name: Name of the model to warm up
        
    Returns:
        True if warmup successful
    """
    try:
        from infrastructure.llm import LLMClient
        client = LLMClient()
        client.query("test", model=model_name)
        return True
    except Exception:
        return False


def extract_manuscript_text(pdf_path: str) -> str:
    """Extract text from a PDF manuscript.
    
    Attempts to extract text using available PDF parsing libraries.
    Supports PyPDF2, pdfplumber, and pypdf as optional dependencies.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        FileNotFoundError: If PDF file does not exist
        ValueError: If no PDF parsing library is available
        
    Example:
        >>> text = extract_manuscript_text("manuscript.pdf")
        >>> print(f"Extracted {len(text)} characters")
    """
    from pathlib import Path
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Try pdfplumber first (best quality)
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}, trying alternatives...")
    
    # Try pypdf (newer PyPDF2)
    try:
        import pypdf
        text_parts = []
        with open(pdf_file, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}, trying PyPDF2...")
    
    # Try PyPDF2 (legacy)
    try:
        import PyPDF2
        text_parts = []
        with open(pdf_file, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")
    
    # No PDF library available
    raise ValueError(
        "No PDF parsing library available. Install one of: pdfplumber, pypdf, or PyPDF2. "
        "Example: pip install pdfplumber"
    )


def generate_review_with_metrics(
    manuscript_text: str,
    review_type: str,
    model: str | None = None
) -> tuple[str, dict]:
    """Generate a review with metrics.
    
    Generates a review of the specified type and collects comprehensive metrics
    including generation time, token estimates, and output statistics.
    
    Args:
        manuscript_text: Text of the manuscript
        review_type: Type of review to generate (executive_summary, quality_review,
                    methodology_review, improvement_suggestions)
        model: Model name to use (optional)
        
    Returns:
        Tuple of (review_text, metrics_dict) where metrics_dict contains:
        - tokens_used: Estimated tokens used
        - time_seconds: Generation time in seconds
        - input_chars: Input text length
        - output_chars: Output text length
        - output_words: Output word count
        
    Example:
        >>> review, metrics = generate_review_with_metrics(
        ...     manuscript_text, "executive_summary", model="llama3"
        ... )
        >>> print(f"Generated {metrics['output_words']} words in {metrics['time_seconds']:.2f}s")
    """
    import time as time_module
    from infrastructure.llm import LLMClient
    from infrastructure.llm.review.metrics import ReviewMetrics, estimate_tokens
    
    start_time = time_module.time()
    
    # Truncate manuscript if needed
    max_length = get_max_input_length()
    if len(manuscript_text) > max_length:
        manuscript_text = manuscript_text[:max_length]
        logger.warning(f"Manuscript truncated to {max_length} characters")
    
    # Generate review based on type
    if review_type == "executive_summary":
        review_text = generate_executive_summary(manuscript_text, model=model)
    elif review_type == "quality_review":
        review_text = generate_quality_review(manuscript_text, model=model)
    elif review_type == "methodology_review":
        review_text = generate_methodology_review(manuscript_text, model=model)
    elif review_type == "improvement_suggestions":
        review_text = generate_improvement_suggestions(manuscript_text, model=model)
    else:
        # Fallback: generic review
        client = LLMClient()
        review_text = client.query(
            f"Provide a comprehensive {review_type} review of this manuscript:\n\n{manuscript_text[:10000]}",
            model=model
        )
    
    generation_time = time_module.time() - start_time
    
    # Calculate metrics
    metrics = ReviewMetrics(
        input_chars=len(manuscript_text),
        input_words=len(manuscript_text.split()),
        input_tokens_est=estimate_tokens(manuscript_text),
        output_chars=len(review_text),
        output_words=len(review_text.split()),
        output_tokens_est=estimate_tokens(review_text),
        generation_time_seconds=generation_time,
        preview=review_text[:150] if review_text else "",
    )
    
    # Convert to dict for return
    metrics_dict = {
        "tokens_used": metrics.output_tokens_est,
        "time_seconds": metrics.generation_time_seconds,
        "input_chars": metrics.input_chars,
        "input_words": metrics.input_words,
        "input_tokens_est": metrics.input_tokens_est,
        "output_chars": metrics.output_chars,
        "output_words": metrics.output_words,
        "output_tokens_est": metrics.output_tokens_est,
    }
    
    return review_text, metrics_dict


def generate_executive_summary(manuscript_text: str, model: str | None = None) -> str:
    """Generate an executive summary of the manuscript.
    
    Uses the ManuscriptExecutiveSummary template to create a prompt and queries
    the LLM to generate a comprehensive executive summary.
    
    Args:
        manuscript_text: Text of the manuscript
        model: Model name to use (optional)
        
    Returns:
        Executive summary text generated by the LLM
        
    Example:
        >>> summary = generate_executive_summary(manuscript_text, model="llama3")
        >>> print(f"Summary length: {len(summary)} characters")
    """
    from infrastructure.llm import LLMClient
    from infrastructure.llm.templates import ManuscriptExecutiveSummary
    
    template = ManuscriptExecutiveSummary()
    prompt = template.render(text=manuscript_text[:50000])
    
    client = LLMClient()
    return client.query(prompt, model=model)


def generate_quality_review(manuscript_text: str, model: str | None = None) -> str:
    """Generate a quality review of the manuscript.
    
    Uses the ManuscriptQualityReview template to create a prompt and queries
    the LLM to generate a comprehensive quality assessment.
    
    Args:
        manuscript_text: Text of the manuscript
        model: Model name to use (optional)
        
    Returns:
        Quality review text generated by the LLM
        
    Example:
        >>> review = generate_quality_review(manuscript_text, model="llama3")
        >>> print(f"Review length: {len(review)} characters")
    """
    from infrastructure.llm import LLMClient
    from infrastructure.llm.templates import ManuscriptQualityReview
    
    template = ManuscriptQualityReview()
    prompt = template.render(text=manuscript_text[:50000])
    
    client = LLMClient()
    return client.query(prompt, model=model)


def generate_methodology_review(manuscript_text: str, model: str | None = None) -> str:
    """Generate a methodology review of the manuscript.
    
    Uses the ManuscriptMethodologyReview template to create a prompt and queries
    the LLM to generate a comprehensive methodology assessment.
    
    Args:
        manuscript_text: Text of the manuscript
        model: Model name to use (optional)
        
    Returns:
        Methodology review text generated by the LLM
        
    Example:
        >>> review = generate_methodology_review(manuscript_text, model="llama3")
        >>> print(f"Review length: {len(review)} characters")
    """
    from infrastructure.llm import LLMClient
    from infrastructure.llm.templates import ManuscriptMethodologyReview
    
    template = ManuscriptMethodologyReview()
    prompt = template.render(text=manuscript_text[:50000])
    
    client = LLMClient()
    return client.query(prompt, model=model)


def generate_improvement_suggestions(manuscript_text: str, model: str | None = None) -> str:
    """Generate improvement suggestions for the manuscript.
    
    Uses the ManuscriptImprovementSuggestions template to create a prompt and queries
    the LLM to generate actionable improvement recommendations.
    
    Args:
        manuscript_text: Text of the manuscript
        model: Model name to use (optional)
        
    Returns:
        Improvement suggestions text generated by the LLM
        
    Example:
        >>> suggestions = generate_improvement_suggestions(manuscript_text, model="llama3")
        >>> print(f"Suggestions length: {len(suggestions)} characters")
    """
    from infrastructure.llm import LLMClient
    from infrastructure.llm.templates import ManuscriptImprovementSuggestions
    
    template = ManuscriptImprovementSuggestions()
    prompt = template.render(text=manuscript_text[:50000])
    
    client = LLMClient()
    return client.query(prompt, model=model)


def generate_translation(
    text: str,
    target_language: str,
    model: str | None = None
) -> str:
    """Generate a translation of text to target language.
    
    Uses the ManuscriptTranslationAbstract template to create a prompt and queries
    the LLM to generate a translation of the provided text.
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., "zh", "hi", "ru")
        model: Model name to use (optional)
        
    Returns:
        Translated text generated by the LLM
        
    Example:
        >>> translation = generate_translation("Hello world", "zh", model="llama3")
        >>> print(f"Translation: {translation}")
    """
    from infrastructure.llm import LLMClient
    from infrastructure.llm.templates import ManuscriptTranslationAbstract
    
    template = ManuscriptTranslationAbstract()
    prompt = template.render(text=text, target_language=target_language)
    
    client = LLMClient()
    return client.query(prompt, model=model)
