#!/usr/bin/env python3
"""LLM Manuscript Review orchestrator script.

This thin orchestrator coordinates the LLM review stage:
1. Checks Ollama availability and selects best model
2. Extracts text from combined manuscript PDF (full content, no truncation by default)
3. Generates executive summary of key findings
4. Generates writing quality review
5. Generates methodology and structure review
6. Generates improvement suggestions
7. Validates review quality and retries if needed
8. Saves all reviews to output/llm/ with detailed metrics

Stage 8 of the pipeline orchestration - uses local Ollama LLM for
manuscript analysis and review generation.

Output Files:
- executive_summary.md     # Key findings and contributions
- quality_review.md        # Writing clarity and style
- methodology_review.md    # Structure and methods assessment
- improvement_suggestions.md # Actionable recommendations
- review_metadata.json     # Model used, timestamp, config, detailed metrics
- combined_review.md       # All reviews in one document with TODO checklist

Environment Variables:
- LLM_MAX_INPUT_LENGTH: Maximum characters to send to LLM (default: 500000 = ~125K tokens)
                        Set to 0 for unlimited input size
- LLM_REVIEW_TIMEOUT: Timeout for each review generation (default: 300s)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.llm import (
    LLMClient,
    LLMConfig,
    GenerationOptions,
    is_ollama_running,
    ensure_ollama_ready,
    select_best_model,
    get_model_info,
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
)
from infrastructure.llm.templates import REVIEW_MIN_WORDS
from infrastructure.validation.pdf_validator import extract_text_from_pdf, PDFValidationError

# Set up logger for this module
logger = get_logger(__name__)

# Default maximum text length - 500K chars (~125K tokens)
# Most modern LLMs support 32K-128K tokens, so this is a safe default
# Set LLM_MAX_INPUT_LENGTH=0 for unlimited
DEFAULT_MAX_INPUT_LENGTH = 500000

# Default timeout for review generation (5 minutes per review)
DEFAULT_REVIEW_TIMEOUT = 300.0

# =============================================================================
# Manuscript Review System Prompt
# =============================================================================

MANUSCRIPT_REVIEW_SYSTEM_PROMPT = """You are an expert academic manuscript reviewer with extensive experience in peer review for top-tier journals. Your role is to provide thorough, constructive, and professional reviews of research manuscripts.

Key responsibilities:
1. Analyze the manuscript content carefully and completely
2. Provide specific, actionable feedback with references to the text
3. Maintain a professional, constructive tone
4. Focus exclusively on the manuscript content provided
5. Structure your responses clearly with the requested headers and sections

Guidelines:
- Always base your assessment on the actual manuscript text provided
- Do not reference external sources or unrelated materials
- Provide balanced feedback highlighting both strengths and areas for improvement
- Be specific - cite sections, passages, or elements when making observations
- Use markdown formatting for clear structure
- Complete all requested sections with substantive content

You are reviewing an academic research manuscript. Treat this as a formal peer review."""

# Off-topic detection patterns (indicates LLM confusion)
# These patterns must appear at START of response or be very specific
OFF_TOPIC_PATTERNS_START = [
    # Email/letter formats (must be at start)
    r"^Re:\s",                        # Email reply format
    r"^Dear\s",                       # Letter format
    r"^To:\s",                        # Email header format
    r"^Subject:\s",                   # Email subject line
    r"^From:\s",                      # Email from header
    # Casual greetings at start (inappropriate for formal review)
    r"^Hi\s",                         # Casual greeting
    r"^Hello\s",                      # Casual greeting
    r"^Hey\s",                        # Very casual greeting
    r"^Hello!",                       # Casual with exclamation
]

OFF_TOPIC_PATTERNS_ANYWHERE = [
    # AI assistant phrases that clearly indicate confusion
    r"Q&A forum",
    r"I'm happy to help you with",
    r"I'm not sure if I can help",
    r"this is a very good question",
    r"feel free to ask me",
    r"I don't have access to",
    r"I cannot access",
    r"As an AI assistant",
    r"as a language model",
    r"I am an AI",
    r"I'm an AI assistant",
    # Code blocks that dominate response (more than just examples)
    r"^```python\n",                  # Code block at very start
    r"import pandas as pd\nimport",   # Multi-import block
]

# Conversational AI phrases that indicate poor review quality (not off-topic, but problematic)
CONVERSATIONAL_PATTERNS = [
    r"based on the document you shared",
    r"based on the document you've shared",
    r"I'll give you a precise",
    r"I'll provide you",
    r"Let me know if",
    r"let me know your",
    r"I'd be happy to",
    r"I'll help you",
    r"if you'd like me to",
    r"tell me:",
    r"Need help\?",
    r"I'm here to",
    r"just say the word",
]

# Common emoji patterns found in LLM outputs
EMOJI_PATTERNS = [
    r"[\U0001F300-\U0001F9FF]",  # Miscellaneous symbols and pictographs
    r"[\U0001F600-\U0001F64F]",  # Emoticons
    r"[\U0001F680-\U0001F6FF]",  # Transport and map symbols
    r"[\U00002600-\U000027BF]",  # Misc symbols (sun, stars, etc.)
    r"[✓✅❌⚠️💡🔑🚀⚙️📚📊🎯🌟🛠️😊🔥🟠🟢]",  # Commonly used symbols
]

# Markdown table patterns (forbidden in review format)
TABLE_PATTERNS = [
    r"\|\s*[-:]+\s*\|",           # Table header separator: |---|---|
    r"^\s*\|[^|]+\|[^|]+\|",      # Table row with 2+ columns: | x | y |
]

# Hallucinated section reference patterns (references to non-existent sections)
HALLUCINATED_SECTION_PATTERNS = [
    r"section\s+1[0-9]\.\d",      # Section 10.x, 11.x, 12.x, etc. (unlikely to exist)
    r"section\s+\d+\.\d+\.\d+",   # Deep section references like 12.8.1
    r"p\.\s*\d{2,3}\b",           # Page references like "p. 44" (assumes specific pages)
    r"\(page\s+\d{2,}\)",         # (page XX) references
]

# Positive signals that indicate on-topic response (overrides off-topic detection)
ON_TOPIC_SIGNALS = [
    r"## overview",
    r"## key contributions",
    r"## methodology",
    r"## strengths",
    r"## weaknesses",
    r"## score",
    r"\*\*score:",
    r"## high priority",
    r"## recommendations",
    r"the manuscript",
    r"this research",
    r"the paper",
    r"the authors",
    r"the study",
]

def get_max_input_length() -> int:
    """Get configured maximum input length from environment.
    
    Returns:
        Maximum character count, or 0 for unlimited
    """
    env_value = os.environ.get("LLM_MAX_INPUT_LENGTH")
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            logger.warning(f"Invalid LLM_MAX_INPUT_LENGTH value: {env_value}, using default")
    return DEFAULT_MAX_INPUT_LENGTH


def get_review_timeout() -> float:
    """Get configured timeout for review generation.
    
    Returns:
        Timeout in seconds
    """
    env_value = os.environ.get("LLM_REVIEW_TIMEOUT")
    if env_value is not None:
        try:
            return float(env_value)
        except ValueError:
            logger.warning(f"Invalid LLM_REVIEW_TIMEOUT value: {env_value}, using default")
    return DEFAULT_REVIEW_TIMEOUT


def has_on_topic_signals(text: str) -> bool:
    """Check if response contains clear on-topic indicators.
    
    Args:
        text: Response text to check
        
    Returns:
        True if response has clear manuscript review signals
    """
    text_lower = text.lower()
    signals_found = 0
    for pattern in ON_TOPIC_SIGNALS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            signals_found += 1
    # If we find 2+ on-topic signals, it's clearly on-topic
    return signals_found >= 2


def detect_emojis(text: str) -> List[str]:
    """Detect emoji usage in response text.
    
    Args:
        text: Response text to check
        
    Returns:
        List of emojis found
    """
    emojis_found = []
    for pattern in EMOJI_PATTERNS:
        matches = re.findall(pattern, text)
        emojis_found.extend(matches)
    return emojis_found


def detect_tables(text: str) -> bool:
    """Detect markdown table usage in response text.
    
    Args:
        text: Response text to check
        
    Returns:
        True if markdown tables are found
    """
    for pattern in TABLE_PATTERNS:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def detect_conversational_phrases(text: str) -> List[str]:
    """Detect conversational AI phrases in response text.
    
    Args:
        text: Response text to check
        
    Returns:
        List of conversational phrases found
    """
    text_lower = text.lower()
    phrases_found = []
    for pattern in CONVERSATIONAL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Extract a snippet of the matched text for logging
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                phrases_found.append(match.group(0)[:50])
    return phrases_found


def detect_hallucinated_sections(text: str) -> List[str]:
    """Detect hallucinated section references in response text.
    
    Looks for references to sections that are unlikely to exist in typical
    manuscripts (e.g., Section 12.8.1, page 44).
    
    Args:
        text: Response text to check
        
    Returns:
        List of suspicious section references found
    """
    text_lower = text.lower()
    references_found = []
    for pattern in HALLUCINATED_SECTION_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        references_found.extend(matches)
    return references_found


def check_format_compliance(response: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Check response for format compliance issues.
    
    Detects:
    - Emoji usage (violates template instructions)
    - Markdown tables (violates template instructions)
    - Conversational AI phrases (unprofessional for review)
    - Hallucinated section references (indicates confusion)
    
    Args:
        response: The generated review text
        
    Returns:
        Tuple of (is_compliant, list of issues, details dict)
    """
    issues = []
    details: Dict[str, Any] = {
        "emojis_found": [],
        "has_tables": False,
        "conversational_phrases": [],
        "hallucinated_refs": [],
    }
    
    # Check for emojis
    emojis = detect_emojis(response)
    if emojis:
        details["emojis_found"] = emojis[:10]  # Limit to first 10
        issues.append(f"Contains {len(emojis)} emoji(s) - violates format requirements")
    
    # Check for tables
    if detect_tables(response):
        details["has_tables"] = True
        issues.append("Contains markdown tables - violates format requirements")
    
    # Check for conversational phrases
    phrases = detect_conversational_phrases(response)
    if phrases:
        details["conversational_phrases"] = phrases[:5]  # Limit to first 5
        issues.append(f"Contains conversational AI phrases: {phrases[0][:30]}...")
    
    # Check for hallucinated section references
    hall_refs = detect_hallucinated_sections(response)
    if hall_refs:
        details["hallucinated_refs"] = hall_refs[:5]  # Limit to first 5
        issues.append(f"Contains suspicious section references: {', '.join(hall_refs[:3])}")
    
    is_compliant = len(issues) == 0
    return is_compliant, issues, details


def is_off_topic(text: str) -> bool:
    """Check if response contains off-topic indicators.
    
    Uses a two-tier approach:
    1. Check for start-of-response patterns (strict)
    2. Check for anywhere patterns (must be strong signals)
    3. Override if clear on-topic signals are present
    
    Args:
        text: Response text to check
        
    Returns:
        True if response appears off-topic
    """
    # First check for on-topic signals - if present, not off-topic
    if has_on_topic_signals(text):
        return False
    
    text_lower = text.lower().strip()
    
    # Check start-of-response patterns
    for pattern in OFF_TOPIC_PATTERNS_START:
        if re.search(pattern, text_lower[:100], re.IGNORECASE | re.MULTILINE):
            return True
    
    # Check anywhere patterns (must be strong signals)
    for pattern in OFF_TOPIC_PATTERNS_ANYWHERE:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False


def validate_review_quality(
    response: str,
    review_type: str,
    min_words: Optional[int] = None,
    model_name: str = "",
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate that a review response meets quality standards.
    
    Uses flexible matching that accepts multiple valid formats.
    Provides detailed validation info for logging.
    
    Checks (in order):
    1. Off-topic content detection
    2. Format compliance (emojis, tables, conversational phrases, hallucinations)
    3. Word count requirements
    4. Structure requirements (type-specific)
    
    Args:
        response: The generated review text
        review_type: Type of review (executive_summary, quality_review, etc.)
        min_words: Minimum word count (uses defaults if None)
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (is_valid, list of issues found, validation details dict)
    """
    issues = []
    details: Dict[str, Any] = {"sections_found": [], "scores_found": [], "format_compliance": {}}
    response_lower = response.lower()
    
    # Check for off-topic content FIRST (most critical - triggers immediate retry)
    if is_off_topic(response):
        issues.append("Response appears off-topic or confused")
        # Return immediately for off-topic - no point checking structure
        return False, issues, details
    
    # Check format compliance (emojis, tables, conversational phrases, hallucinations)
    is_format_compliant, format_issues, format_details = check_format_compliance(response)
    details["format_compliance"] = format_details
    
    # Format issues are warnings, not hard failures (small models often violate these)
    is_small_model = any(s in model_name.lower() for s in ["3b", "4b", "7b", "8b"])
    if not is_format_compliant:
        if is_small_model:
            # For small models, log format issues as warnings but don't fail
            details["format_warnings"] = format_issues
        else:
            # For larger models, format issues are more significant
            issues.extend(format_issues)
    
    # Get minimum word count - lower for smaller models
    is_small_model = any(s in model_name.lower() for s in ["3b", "4b", "7b", "8b"])
    default_min = REVIEW_MIN_WORDS.get(review_type, 200)
    if is_small_model:
        default_min = int(default_min * 0.8)  # 20% lower threshold for small models
    min_word_count = min_words or default_min
    
    # Check word count
    word_count = len(response.split())
    details["word_count"] = word_count
    details["min_required"] = min_word_count
    
    if word_count < min_word_count:
        issues.append(f"Too short: {word_count} words (minimum: {min_word_count})")
    
    # Check for expected structure (headers) with flexible matching
    if review_type == "executive_summary":
        # Accept multiple variations of section names
        header_variations = [
            (["overview", "summary", "introduction", "abstract"], "overview"),
            (["key contributions", "contributions", "main findings", "key findings", "highlights"], "contributions"),
            (["methodology", "methods", "approach", "method", "techniques"], "methodology"),
            (["results", "findings", "principal results", "outcomes", "key results"], "results"),
            (["significance", "impact", "implications", "importance", "takeaway"], "significance"),
        ]
        found_sections = []
        for variations, section_name in header_variations:
            if any(v in response_lower for v in variations):
                found_sections.append(section_name)
        
        details["sections_found"] = found_sections
        details["sections_required"] = 1  # Only require 1 section (very flexible)
        
        # Require at least 1 of 5 sections (very flexible for varied model outputs)
        if len(found_sections) < 1:
            issues.append(f"Missing expected structure (found: none of 5 expected sections)")
    
    elif review_type == "quality_review":
        # Flexible score detection - multiple patterns
        score_patterns = [
            (r'\*\*score:\s*(\d)/5\*\*', "**Score: X/5**"),
            (r'score:\s*(\d)/5', "Score: X/5"),
            (r'\*\*(\d)/5\*\*', "**X/5**"),
            (r'score\s*:\s*(\d)', "Score: X"),
            (r'rating\s*:\s*(\d)', "Rating: X"),
            (r'\[(\d)/5\]', "[X/5]"),
            (r'(\d)\s*out\s*of\s*5', "X out of 5"),
            (r'(\d)/5', "X/5"),
        ]
        
        scores_found = []
        for pattern, pattern_name in score_patterns:
            matches = re.findall(pattern, response_lower)
            if matches:
                scores_found.extend([(m, pattern_name) for m in matches])
        
        details["scores_found"] = scores_found
        
        # Also check for qualitative assessment sections
        has_assessment = any([
            "clarity" in response_lower,
            "structure" in response_lower,
            "readability" in response_lower,
            "technical accuracy" in response_lower,
            "overall quality" in response_lower,
        ])
        details["has_assessment"] = has_assessment
        
        # Accept if either scores OR assessment sections present
        if not scores_found and not has_assessment:
            issues.append("Missing scoring or quality assessment")
    
    elif review_type == "methodology_review":
        # Flexible methodology review detection
        methodology_sections = [
            (["strengths", "strong points", "advantages", "positives", "pros"], "strengths"),
            (["weaknesses", "limitations", "concerns", "issues", "weak points", "cons", "gaps"], "weaknesses"),
            (["suggestions", "recommendations", "improvements", "future work"], "recommendations"),
        ]
        found_sections = []
        for variations, section_name in methodology_sections:
            if any(v in response_lower for v in variations):
                found_sections.append(section_name)
        
        details["sections_found"] = found_sections
        
        # Also check for methodology-related content
        has_methodology_content = any([
            "research design" in response_lower,
            "methodology" in response_lower,
            "approach" in response_lower,
            "methods" in response_lower,
            "experimental" in response_lower,
        ])
        details["has_methodology_content"] = has_methodology_content
        
        # Require at least 1 section OR methodology content
        if len(found_sections) < 1 and not has_methodology_content:
            issues.append(f"Missing expected sections (found: {found_sections or 'none'})")
    
    elif review_type == "improvement_suggestions":
        # Flexible priority detection
        priority_variations = [
            (["high priority", "critical", "urgent", "must fix", "immediate", "major"], "high"),
            (["medium priority", "moderate", "should address", "important", "significant"], "medium"),
            (["low priority", "minor", "nice to have", "optional", "consider", "cosmetic"], "low"),
        ]
        found_priorities = []
        for variations, priority_name in priority_variations:
            if any(v in response_lower for v in variations):
                found_priorities.append(priority_name)
        
        details["priorities_found"] = found_priorities
        
        # Also check for recommendation content
        has_recommendations = any([
            "recommendation" in response_lower,
            "suggest" in response_lower,
            "improve" in response_lower,
            "fix" in response_lower,
            "address" in response_lower,
        ])
        details["has_recommendations"] = has_recommendations
        
        # Require at least 1 priority OR recommendation content
        if len(found_priorities) < 1 and not has_recommendations:
            issues.append(f"Missing priority sections or recommendations")
    
    is_valid = len(issues) == 0
    return is_valid, issues, details


def create_review_client(model_name: str) -> LLMClient:
    """Create an LLMClient configured for manuscript review.
    
    Args:
        model_name: Name of the model to use
        
    Returns:
        Configured LLMClient instance
    """
    config = LLMConfig.from_env()
    config.default_model = model_name
    config.timeout = get_review_timeout()
    config.system_prompt = MANUSCRIPT_REVIEW_SYSTEM_PROMPT
    config.auto_inject_system_prompt = True
    config.long_max_tokens = 4096  # Increase for comprehensive reviews
    
    return LLMClient(config)


@dataclass
class ReviewMetrics:
    """Metrics for a single review generation."""
    input_chars: int = 0
    input_words: int = 0
    input_tokens_est: int = 0  # Estimated tokens (~4 chars/token)
    output_chars: int = 0
    output_words: int = 0
    output_tokens_est: int = 0
    generation_time_seconds: float = 0.0
    preview: str = ""  # First 150 chars of response


@dataclass
class ManuscriptMetrics:
    """Metrics for the manuscript input."""
    total_chars: int = 0
    total_words: int = 0
    total_tokens_est: int = 0
    truncated: bool = False
    truncated_chars: int = 0  # Chars after truncation (if any)


@dataclass
class SessionMetrics:
    """Complete metrics for the review session."""
    manuscript: ManuscriptMetrics = field(default_factory=ManuscriptMetrics)
    reviews: Dict[str, ReviewMetrics] = field(default_factory=dict)
    total_generation_time: float = 0.0
    model_name: str = ""
    max_input_length: int = 0


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (approximately 4 characters per token).
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def log_stage(message: str) -> None:
    """Log a stage start message."""
    logger.info(f"\n  {message}")


def check_ollama_availability() -> Tuple[bool, Optional[str]]:
    """Check if Ollama is running and select best model.
    
    Returns:
        Tuple of (is_available, model_name)
    """
    log_stage("Checking Ollama availability...")
    
    if not is_ollama_running():
        logger.warning("Ollama server is not running")
        logger.info("  To start Ollama: ollama serve")
        logger.info("  To install a model: ollama pull llama3")
        return False, None
    
    log_success("Ollama server is running", logger)
    
    # Select best available model
    model = select_best_model()
    if not model:
        logger.warning("No Ollama models available")
        logger.info("  Install a model with: ollama pull llama3")
        return False, None
    
    # Get model info for logging
    model_info = get_model_info(model)
    if model_info:
        size_gb = model_info.get("size", 0) / (1024**3)
        logger.info(f"  Selected model: {model} ({size_gb:.1f} GB)")
    else:
        logger.info(f"  Selected model: {model}")
    
    return True, model


def extract_manuscript_text(pdf_path: Path) -> Tuple[Optional[str], ManuscriptMetrics]:
    """Extract text from combined manuscript PDF.
    
    Args:
        pdf_path: Path to combined PDF
        
    Returns:
        Tuple of (extracted text or None, manuscript metrics)
    """
    log_stage(f"Extracting text from manuscript: {pdf_path.name}")
    
    metrics = ManuscriptMetrics()
    
    if not pdf_path.exists():
        logger.error(f"Manuscript PDF not found: {pdf_path}")
        return None, metrics
    
    try:
        text = extract_text_from_pdf(pdf_path)
        
        # Calculate metrics for full text
        metrics.total_chars = len(text)
        metrics.total_words = len(text.split())
        metrics.total_tokens_est = estimate_tokens(text)
        
        logger.info(f"  Extracted: {metrics.total_chars:,} chars ({metrics.total_words:,} words, ~{metrics.total_tokens_est:,} tokens)")
        
        # Check if truncation is needed
        max_length = get_max_input_length()
        
        if max_length > 0 and len(text) > max_length:
            metrics.truncated = True
            metrics.truncated_chars = max_length
            
            logger.warning(f"  Truncating from {metrics.total_chars:,} to {max_length:,} characters")
            logger.info(f"  Set LLM_MAX_INPUT_LENGTH=0 for unlimited, or increase the limit")
            
            text = text[:max_length] + "\n\n[... truncated for LLM context limit ...]"
        else:
            metrics.truncated = False
            metrics.truncated_chars = metrics.total_chars
            logger.info(f"  Sending full manuscript to LLM (no truncation)")
        
        return text, metrics
        
    except PDFValidationError as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return None, metrics


def generate_review_with_metrics(
    client: LLMClient,
    text: str,
    review_type: str,
    review_name: str,
    template_class: type,
    model_name: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    max_retries: int = 1,
) -> Tuple[str, ReviewMetrics]:
    """Generate a review with detailed metrics and quality validation.
    
    Resets client context before each review to prevent pollution.
    Validates response quality and retries if needed.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        review_type: Type key for validation (e.g., 'executive_summary')
        review_name: Human-readable name for logging
        template_class: Template class to use for the prompt
        model_name: Model name for model-specific adjustments
        temperature: Generation temperature
        max_tokens: Maximum tokens for response
        max_retries: Number of retry attempts for low-quality responses (reduced default)
        
    Returns:
        Tuple of (response content, metrics)
    """
    log_stage(f"Generating {review_name}...")
    
    metrics = ReviewMetrics(
        input_chars=len(text),
        input_words=len(text.split()),
        input_tokens_est=estimate_tokens(text),
    )
    
    # Reset context to prevent pollution from previous reviews
    client.reset()
    
    # Render the template with manuscript text
    template = template_class()
    prompt = template.render(text=text)
    
    # Adjust temperature for smaller models (they need slightly more randomness)
    is_small_model = any(s in model_name.lower() for s in ["3b", "4b", "7b", "8b"])
    adjusted_temp = temperature + 0.1 if is_small_model else temperature
    
    options = GenerationOptions(
        temperature=adjusted_temp,
        max_tokens=max_tokens,
    )
    
    start_time = time.time()
    best_response = ""
    best_issues: List[str] = []
    best_details: Dict[str, Any] = {}
    
    for attempt in range(max_retries + 1):
        try:
            current_prompt = prompt
            
            if attempt > 0:
                logger.debug(f"    Retry {attempt}/{max_retries} (temp={adjusted_temp:.2f})")
                client.reset()  # Reset context for retry
                # Slightly increase temperature on retries
                adjusted_temp = min(temperature + 0.15 * attempt, 0.8)
                options = GenerationOptions(
                    temperature=adjusted_temp,
                    max_tokens=max_tokens,
                )
            
            # Use query() directly - templates already contain detailed instructions
            response = client.query(current_prompt, options=options)
            
            # Validate response quality with model-specific thresholds
            is_valid, issues, details = validate_review_quality(
                response, review_type, model_name=model_name
            )
            
            # Keep track of best response (by word count)
            if len(response.split()) > len(best_response.split()):
                best_response = response
                best_issues = issues
                best_details = details
            
            if is_valid:
                # Response is good - log format compliance at INFO if there are warnings
                format_warnings = details.get("format_warnings", [])
                if format_warnings:
                    logger.info(f"    Format warnings (non-blocking): {', '.join(format_warnings[:2])}")
                break
            else:
                # Log validation issues at INFO for visibility
                if attempt < max_retries:
                    logger.info(f"    Validation issues: {', '.join(issues[:2])} - retrying")
                    continue
                else:
                    # Use best response - log why we're accepting it
                    logger.info(f"    Accepting response with issues: {', '.join(best_issues[:2])}")
                    response = best_response
                    
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"    Generation error: {e}")
                continue
            else:
                metrics.generation_time_seconds = time.time() - start_time
                logger.error(f"Failed to generate {review_name}: {e}")
                error_response = f"*Error generating {review_name}: {e}*"
                metrics.output_chars = len(error_response)
                metrics.output_words = len(error_response.split())
                return error_response, metrics
    
    # Calculate output metrics
    metrics.generation_time_seconds = time.time() - start_time
    metrics.output_chars = len(response)
    metrics.output_words = len(response.split())
    metrics.output_tokens_est = estimate_tokens(response)
    metrics.preview = response[:150].replace('\n', ' ') + "..." if len(response) > 150 else response
    
    # Log success with metrics
    log_success(f"{review_name} generated", logger)
    logger.info(f"    Output: {metrics.output_chars:,} chars ({metrics.output_words:,} words) in {metrics.generation_time_seconds:.1f}s")
    
    # Log format compliance summary at INFO level
    if best_details:
        format_info = best_details.get("format_compliance", {})
        issues_summary = []
        
        if format_info.get("emojis_found"):
            issues_summary.append(f"{len(format_info['emojis_found'])} emoji(s)")
        if format_info.get("has_tables"):
            issues_summary.append("tables")
        if format_info.get("hallucinated_refs"):
            issues_summary.append(f"{len(format_info['hallucinated_refs'])} suspicious ref(s)")
        if format_info.get("conversational_phrases"):
            issues_summary.append("conversational phrases")
        
        if issues_summary:
            logger.info(f"    Format notes: {', '.join(issues_summary)}")
    
    return response, metrics


def generate_executive_summary(
    client: LLMClient, text: str, model_name: str = ""
) -> Tuple[str, ReviewMetrics]:
    """Generate executive summary of manuscript.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (executive summary markdown, metrics)
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="executive_summary",
        review_name="executive summary",
        template_class=ManuscriptExecutiveSummary,
        model_name=model_name,
        temperature=0.3,
        max_tokens=4096,
    )


def generate_quality_review(
    client: LLMClient, text: str, model_name: str = ""
) -> Tuple[str, ReviewMetrics]:
    """Generate writing quality review.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (quality review markdown, metrics)
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="quality_review",
        review_name="quality review",
        template_class=ManuscriptQualityReview,
        model_name=model_name,
        temperature=0.3,
        max_tokens=4096,
    )


def generate_methodology_review(
    client: LLMClient, text: str, model_name: str = ""
) -> Tuple[str, ReviewMetrics]:
    """Generate methodology and structure review.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (methodology review markdown, metrics)
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="methodology_review",
        review_name="methodology review",
        template_class=ManuscriptMethodologyReview,
        model_name=model_name,
        temperature=0.3,
        max_tokens=4096,
    )


def generate_improvement_suggestions(
    client: LLMClient, text: str, model_name: str = ""
) -> Tuple[str, ReviewMetrics]:
    """Generate actionable improvement suggestions.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (improvement suggestions markdown, metrics)
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="improvement_suggestions",
        review_name="improvement suggestions",
        template_class=ManuscriptImprovementSuggestions,
        model_name=model_name,
        temperature=0.4,
        max_tokens=4096,
    )


def extract_action_items(reviews: Dict[str, str]) -> str:
    """Extract actionable items from reviews into a TODO checklist.
    
    Args:
        reviews: Dictionary of review name -> content
        
    Returns:
        Markdown formatted TODO checklist
    """
    todos = []
    
    # Extract from improvement suggestions
    suggestions = reviews.get("improvement_suggestions", "")
    
    # Look for checklist items (already formatted as [ ])
    for line in suggestions.split("\n"):
        if "[ ]" in line:
            # Already formatted as checklist
            item = line.strip()
            if item.startswith("- "):
                item = item[2:]
            todos.append(item)
    
    # Look for high priority items
    in_high_priority = False
    for line in suggestions.split("\n"):
        if "high priority" in line.lower():
            in_high_priority = True
            continue
        elif "medium priority" in line.lower() or "low priority" in line.lower():
            in_high_priority = False
        
        if in_high_priority and line.strip().startswith(("- **", "- *", "1.", "2.", "3.", "4.", "5.")):
            # Extract the issue/recommendation
            item = line.strip()
            if item.startswith("- "):
                item = item[2:]
            if item.startswith(("**Issue**:", "*Issue*:", "**Recommendation**:", "*Recommendation*:")):
                item = item.split(":", 1)[1].strip()
            if len(item) > 10 and item not in todos:
                todos.append(f"[ ] {item[:100]}..." if len(item) > 100 else f"[ ] {item}")
    
    # Extract from quality review - low scores
    quality = reviews.get("quality_review", "")
    for line in quality.split("\n"):
        if "score:" in line.lower() and any(s in line for s in ["1", "2"]):
            # Low score found - next few lines might have the issue
            continue
    
    if not todos:
        todos = [
            "[ ] Review executive summary for accuracy",
            "[ ] Address issues in quality review",
            "[ ] Consider methodology suggestions",
            "[ ] Prioritize high-priority improvements",
        ]
    
    return "\n".join(todos[:10])  # Limit to 10 items


def calculate_format_compliance_summary(reviews: Dict[str, str]) -> str:
    """Calculate format compliance summary across all reviews.
    
    Args:
        reviews: Dictionary of review name -> content
        
    Returns:
        Markdown formatted format compliance summary
    """
    total_reviews = len(reviews)
    issues_by_category = {
        "emojis": 0,
        "tables": 0,
        "conversational": 0,
        "hallucinated_refs": 0,
    }
    
    for name, content in reviews.items():
        emojis = detect_emojis(content)
        if emojis:
            issues_by_category["emojis"] += 1
        
        if detect_tables(content):
            issues_by_category["tables"] += 1
        
        phrases = detect_conversational_phrases(content)
        if phrases:
            issues_by_category["conversational"] += 1
        
        refs = detect_hallucinated_sections(content)
        if refs:
            issues_by_category["hallucinated_refs"] += 1
    
    # Calculate compliance percentage
    total_checks = total_reviews * 4  # 4 categories per review
    total_issues = sum(issues_by_category.values())
    compliance_rate = ((total_checks - total_issues) / total_checks) * 100 if total_checks > 0 else 100
    
    # Build summary
    summary_parts = [f"**Format Compliance:** {compliance_rate:.0f}%"]
    
    issue_notes = []
    if issues_by_category["emojis"]:
        issue_notes.append(f"{issues_by_category['emojis']} review(s) with emojis")
    if issues_by_category["tables"]:
        issue_notes.append(f"{issues_by_category['tables']} review(s) with tables")
    if issues_by_category["conversational"]:
        issue_notes.append(f"{issues_by_category['conversational']} review(s) with conversational phrases")
    if issues_by_category["hallucinated_refs"]:
        issue_notes.append(f"{issues_by_category['hallucinated_refs']} review(s) with suspicious references")
    
    if issue_notes:
        summary_parts.append(f"*Notes: {'; '.join(issue_notes)}*")
    else:
        summary_parts.append("*All reviews comply with format requirements*")
    
    return "\n".join(summary_parts)


def calculate_quality_summary(reviews: Dict[str, str]) -> str:
    """Calculate overall quality summary from reviews.
    
    Args:
        reviews: Dictionary of review name -> content
        
    Returns:
        Markdown formatted quality summary
    """
    # Check if quality review has scores
    quality = reviews.get("quality_review", "")
    scores = []
    
    # Extract scores (Score: [1-5] pattern)
    score_pattern = r'\*\*Score:\s*(\d)\*\*|\bScore:\s*(\d)\b'
    matches = re.findall(score_pattern, quality)
    for match in matches:
        score = match[0] or match[1]
        if score:
            scores.append(int(score))
    
    if scores:
        avg_score = sum(scores) / len(scores)
        return f"**Average Quality Score:** {avg_score:.1f}/5 ({len(scores)} criteria evaluated)"
    else:
        return "*Quality scores not available*"


def save_review_outputs(
    reviews: Dict[str, str],
    output_dir: Path,
    model_name: str,
    pdf_path: Path,
    session_metrics: SessionMetrics,
) -> bool:
    """Save all review outputs to markdown files with detailed metrics.
    
    Args:
        reviews: Dictionary of review name -> content
        output_dir: Output directory path
        model_name: Name of LLM model used
        pdf_path: Path to source manuscript PDF
        session_metrics: Complete session metrics
        
    Returns:
        True if all files saved successfully
    """
    log_stage("Saving review outputs...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success = True
    timestamp = datetime.now().isoformat()
    date_str = timestamp[:10]
    
    # Save individual reviews
    for name, content in reviews.items():
        filepath = output_dir / f"{name}.md"
        try:
            metrics = session_metrics.reviews.get(name, ReviewMetrics())
            header = f"""# {name.replace('_', ' ').title()}

*Generated by LLM ({model_name}) on {date_str}*
*Output: {metrics.output_chars:,} chars ({metrics.output_words:,} words) in {metrics.generation_time_seconds:.1f}s*

---

"""
            filepath.write_text(header + content)
            logger.debug(f"  Saved: {filepath.name}")
        except Exception as e:
            logger.error(f"Failed to save {name}: {e}")
            success = False
    
    # Extract action items for TODO checklist
    action_items = extract_action_items(reviews)
    quality_summary = calculate_quality_summary(reviews)
    format_compliance_summary = calculate_format_compliance_summary(reviews)
    
    # Save combined review with enhanced structure
    combined_path = output_dir / "combined_review.md"
    try:
        # Build metrics summary for combined review
        metrics_summary = f"""## Generation Metrics

**Input Manuscript:**
- Characters: {session_metrics.manuscript.total_chars:,}
- Words: {session_metrics.manuscript.total_words:,}
- Estimated tokens: ~{session_metrics.manuscript.total_tokens_est:,}
- Truncated: {'Yes' if session_metrics.manuscript.truncated else 'No'}

**Reviews Generated:**
"""
        for name, metrics in session_metrics.reviews.items():
            metrics_summary += f"- {name.replace('_', ' ').title()}: {metrics.output_chars:,} chars ({metrics.output_words:,} words) in {metrics.generation_time_seconds:.1f}s\n"
        
        metrics_summary += f"\n**Total Generation Time:** {session_metrics.total_generation_time:.1f}s\n"
        
        combined_content = f"""# LLM Manuscript Review

*Generated by {model_name} on {date_str}*
*Source: {pdf_path.name}*

---

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Action Items](#action-items-checklist) | Prioritized TODO list |
| [Executive Summary](#executive-summary) | Key findings overview |
| [Quality Review](#quality-review) | Writing quality assessment |
| [Methodology Review](#methodology-review) | Methods evaluation |
| [Improvement Suggestions](#improvement-suggestions) | Detailed recommendations |
| [Generation Metrics](#generation-metrics) | Review statistics |

---

## Quality Overview

{quality_summary}

{format_compliance_summary}

---

## Action Items Checklist

The following items are extracted from the review for easy tracking:

{action_items}

---

{metrics_summary}

---

# Executive Summary

{reviews.get('executive_summary', '*Not generated*')}

---

# Quality Review

{reviews.get('quality_review', '*Not generated*')}

---

# Methodology Review

{reviews.get('methodology_review', '*Not generated*')}

---

# Improvement Suggestions

{reviews.get('improvement_suggestions', '*Not generated*')}

---

## Review Metadata

- **Model:** {model_name}
- **Generated:** {timestamp}
- **Source:** {pdf_path.name}
- **Total Words Generated:** {sum(m.output_words for m in session_metrics.reviews.values()):,}

---

*End of LLM Manuscript Review*
"""
        combined_path.write_text(combined_content)
        logger.debug(f"  Saved: {combined_path.name}")
    except Exception as e:
        logger.error(f"Failed to save combined review: {e}")
        success = False
    
    # Save metadata with comprehensive metrics
    metadata_path = output_dir / "review_metadata.json"
    try:
        # Convert metrics to serializable format
        reviews_metrics_dict = {
            name: {
                "input_chars": m.input_chars,
                "input_words": m.input_words,
                "input_tokens_est": m.input_tokens_est,
                "output_chars": m.output_chars,
                "output_words": m.output_words,
                "output_tokens_est": m.output_tokens_est,
                "generation_time_seconds": round(m.generation_time_seconds, 2),
            }
            for name, m in session_metrics.reviews.items()
        }
        
        # Calculate format compliance per review
        format_compliance_per_review = {}
        for name, content in reviews.items():
            is_compliant, issues, details = check_format_compliance(content)
            format_compliance_per_review[name] = {
                "compliant": is_compliant,
                "issues": issues,
                "emojis_found": len(details.get("emojis_found", [])),
                "has_tables": details.get("has_tables", False),
                "conversational_phrases": len(details.get("conversational_phrases", [])),
                "hallucinated_refs": len(details.get("hallucinated_refs", [])),
            }
        
        # Calculate overall compliance rate
        total_reviews = len(reviews)
        compliant_reviews = sum(1 for r in format_compliance_per_review.values() if r["compliant"])
        compliance_rate = (compliant_reviews / total_reviews * 100) if total_reviews > 0 else 100
        
        metadata = {
            "model": model_name,
            "timestamp": timestamp,
            "source_pdf": str(pdf_path),
            "reviews_generated": list(reviews.keys()),
            "max_input_length": get_max_input_length(),
            "manuscript_metrics": {
                "total_chars": session_metrics.manuscript.total_chars,
                "total_words": session_metrics.manuscript.total_words,
                "total_tokens_est": session_metrics.manuscript.total_tokens_est,
                "truncated": session_metrics.manuscript.truncated,
                "truncated_chars": session_metrics.manuscript.truncated_chars,
            },
            "review_metrics": reviews_metrics_dict,
            "format_compliance": {
                "overall_rate": round(compliance_rate, 1),
                "compliant_reviews": compliant_reviews,
                "total_reviews": total_reviews,
                "per_review": format_compliance_per_review,
            },
            "total_generation_time_seconds": round(session_metrics.total_generation_time, 2),
            "config": {
                "temperature_summary": 0.3,
                "temperature_review": 0.3,
                "temperature_suggestions": 0.4,
                "max_tokens": 4096,
                "timeout_seconds": get_review_timeout(),
                "system_prompt": "manuscript_review",
            }
        }
        metadata_path.write_text(json.dumps(metadata, indent=2))
        logger.debug(f"  Saved: {metadata_path.name}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        success = False
    
    if success:
        log_success(f"All reviews saved to {output_dir}", logger)
    
    return success


def generate_review_summary(
    reviews: Dict[str, str],
    output_dir: Path,
    session_metrics: SessionMetrics,
) -> None:
    """Generate comprehensive summary of LLM review results.
    
    Args:
        reviews: Dictionary of generated reviews
        output_dir: Output directory path
        session_metrics: Complete session metrics
    """
    logger.info("\n" + "="*60)
    logger.info("LLM Manuscript Review Summary")
    logger.info("="*60)
    
    # Input manuscript metrics
    m = session_metrics.manuscript
    logger.info(f"\nInput manuscript:")
    logger.info(f"  {m.total_chars:,} chars ({m.total_words:,} words, ~{m.total_tokens_est:,} tokens)")
    if m.truncated:
        logger.info(f"  Truncated to {m.truncated_chars:,} chars")
    else:
        logger.info(f"  Full text sent to LLM (no truncation)")
    
    logger.info(f"\nOutput directory: {output_dir}")
    
    # Per-review metrics
    logger.info(f"\nReviews generated:")
    total_output_chars = 0
    total_output_words = 0
    
    for name, content in reviews.items():
        metrics = session_metrics.reviews.get(name, ReviewMetrics())
        total_output_chars += metrics.output_chars
        total_output_words += metrics.output_words
        logger.info(
            f"  • {name.replace('_', ' ').title()}: "
            f"{metrics.output_chars:,} chars ({metrics.output_words:,} words) "
            f"in {metrics.generation_time_seconds:.1f}s"
        )
    
    # Totals
    logger.info(f"\nTotal output: {total_output_chars:,} chars ({total_output_words:,} words)")
    logger.info(f"Total generation time: {session_metrics.total_generation_time:.1f}s")
    
    # File sizes
    logger.info(f"\nFiles created:")
    for filepath in sorted(output_dir.glob("*")):
        size_kb = filepath.stat().st_size / 1024
        logger.info(f"  • {filepath.name}: {size_kb:.1f} KB")
    
    logger.info("")


def main() -> int:
    """Execute LLM manuscript review orchestration.
    
    Returns:
        Exit code (0=success, 1=failure, 2=skipped)
    """
    log_header("STAGE 08: LLM Manuscript Review")
    
    repo_root = Path(__file__).parent.parent
    project_output = repo_root / "project" / "output"
    pdf_path = project_output / "pdf" / "project_combined.pdf"
    output_dir = project_output / "llm"
    
    # Initialize session metrics
    session_metrics = SessionMetrics(max_input_length=get_max_input_length())
    
    try:
        # Step 1: Check Ollama availability
        available, model_name = check_ollama_availability()
        
        if not available:
            logger.warning("\n⚠️  Skipping LLM review - Ollama not available")
            logger.info("  The pipeline will continue without LLM reviews.")
            logger.info("  To enable: start Ollama and install a model")
            return 2  # Skip code, not failure
        
        session_metrics.model_name = model_name
        
        # Step 2: Extract manuscript text
        text, manuscript_metrics = extract_manuscript_text(pdf_path)
        session_metrics.manuscript = manuscript_metrics
        
        if not text:
            logger.error("Cannot generate reviews without manuscript text")
            return 1
        
        # Step 3: Initialize LLM client with manuscript review configuration
        log_stage("Initializing LLM client...")
        client = create_review_client(model_name)
        
        if not client.check_connection():
            logger.error("Failed to connect to Ollama")
            return 1
        
        log_success("LLM client initialized", logger)
        logger.info(f"    Timeout: {get_review_timeout():.0f}s per review")
        logger.info(f"    Max tokens: 4096 per review")
        
        # Step 4: Generate reviews with metrics
        reviews = {}
        total_start = time.time()
        
        response, metrics = generate_executive_summary(client, text, model_name)
        reviews["executive_summary"] = response
        session_metrics.reviews["executive_summary"] = metrics
        
        response, metrics = generate_quality_review(client, text, model_name)
        reviews["quality_review"] = response
        session_metrics.reviews["quality_review"] = metrics
        
        response, metrics = generate_methodology_review(client, text, model_name)
        reviews["methodology_review"] = response
        session_metrics.reviews["methodology_review"] = metrics
        
        response, metrics = generate_improvement_suggestions(client, text, model_name)
        reviews["improvement_suggestions"] = response
        session_metrics.reviews["improvement_suggestions"] = metrics
        
        session_metrics.total_generation_time = time.time() - total_start
        
        # Step 5: Save outputs
        if not save_review_outputs(reviews, output_dir, model_name, pdf_path, session_metrics):
            logger.error("Failed to save some review outputs")
            return 1
        
        # Step 6: Generate summary
        generate_review_summary(reviews, output_dir, session_metrics)
        
        log_success("\n✅ LLM manuscript review complete!", logger)
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during LLM review: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
