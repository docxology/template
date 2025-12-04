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
- LLM_LONG_MAX_TOKENS: Maximum tokens per review response (default: 4096)
                       Configured via LLMConfig.long_max_tokens, can be overridden with env var
                       Priority: LLM_LONG_MAX_TOKENS env var > config default (4096)

CLI Usage:
- python3 scripts/06_llm_review.py                # Run both reviews and translations
- python3 scripts/06_llm_review.py --reviews-only # Run only English scientific reviews
- python3 scripts/06_llm_review.py --translations-only # Run only translations
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class ReviewMode(Enum):
    """Mode for LLM review execution."""
    ALL = "all"  # Run both reviews and translations
    REVIEWS_ONLY = "reviews_only"  # Run only English scientific reviews
    TRANSLATIONS_ONLY = "translations_only"  # Run only translations

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_progress, format_error_with_suggestions,
    format_duration, log_with_spinner, StreamingProgress, Spinner
)
from infrastructure.core.config_loader import get_translation_languages
from infrastructure.llm import (
    LLMClient,
    LLMConfig,
    GenerationOptions,
    is_ollama_running,
    ensure_ollama_ready,
    select_best_model,
    get_model_info,
    get_available_models,
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
    ManuscriptTranslationAbstract,
    detect_repetition,
    deduplicate_sections,
    is_off_topic,
    has_on_topic_signals,
    detect_conversational_phrases,
    check_format_compliance,
    check_model_loaded,
    preload_model,
)
from infrastructure.llm.templates import REVIEW_MIN_WORDS, TRANSLATION_LANGUAGES

# Try to import new prompt system
try:
    from infrastructure.llm.prompts.loader import get_default_loader
    from infrastructure.llm.prompts.composer import PromptComposer
    PROMPT_SYSTEM_AVAILABLE = True
except ImportError:
    PROMPT_SYSTEM_AVAILABLE = False
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

def get_manuscript_review_system_prompt() -> str:
    """Get manuscript review system prompt from infrastructure.
    
    Tries to load from new prompt system, falls back to hardcoded prompt.
    
    Returns:
        System prompt string
    """
    if PROMPT_SYSTEM_AVAILABLE:
        try:
            loader = get_default_loader()
            return loader.get_system_prompt("manuscript_review")
        except Exception as e:
            logger.debug(f"Could not load system prompt from prompt system: {e}")
    
    # Fallback to hardcoded prompt
    return """You are an expert academic manuscript reviewer with extensive experience in peer review for top-tier journals. Your role is to provide thorough, constructive, and professional reviews of research manuscripts.

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

# NOTE: Off-topic detection, conversational phrases, and on-topic signal patterns
# are now defined in infrastructure/llm/validation.py and imported above.
# The validation functions (is_off_topic, check_format_compliance, etc.) are also
# imported from there to follow the thin orchestrator pattern.

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


def get_review_max_tokens() -> Tuple[int, str]:
    """Get configured maximum tokens for review generation with source logging.
    
    Returns:
        Tuple of (max_tokens value, configuration source description)
    """
    config = LLMConfig.from_env()
    max_tokens = config.long_max_tokens
    
    # Determine configuration source
    if os.environ.get("LLM_LONG_MAX_TOKENS"):
        source = f"environment variable LLM_LONG_MAX_TOKENS={max_tokens}"
    else:
        source = f"config default long_max_tokens={max_tokens}"
    
    return max_tokens, source


def validate_review_quality(
    response: str,
    review_type: str,
    min_words: Optional[int] = None,
    model_name: str = "",
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate that a review response meets quality standards.
    
    Uses structure-only validation for general-purpose use.
    Emojis and tables are allowed.
    
    Checks (in order):
    1. Off-topic content detection (critical - triggers retry)
    2. Word count requirements (structural)
    3. Structure requirements (type-specific headers)
    
    Args:
        response: The generated review text
        review_type: Type of review (executive_summary, quality_review, etc.)
        min_words: Minimum word count (uses defaults if None)
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (is_valid, list of issues found, validation details dict)
    """
    issues = []
    details: Dict[str, Any] = {"sections_found": [], "scores_found": [], "format_compliance": {}, "repetition": {}}
    response_lower = response.lower()
    
    # Check for off-topic content FIRST (most critical - triggers immediate retry)
    if is_off_topic(response):
        issues.append("Response appears off-topic or confused")
        # Return immediately for off-topic - no point checking structure
        return False, issues, details
    
    # Check for repetition SECOND (also critical - triggers retry or cleanup)
    has_repetition, duplicates, unique_ratio = detect_repetition(response)
    details["repetition"] = {
        "has_repetition": has_repetition,
        "unique_ratio": unique_ratio,
        "duplicates_found": len(duplicates),
    }
    
    # Flag excessive repetition as a hard failure (unique ratio < 50%)
    if unique_ratio < 0.5:
        issues.append(f"Excessive repetition detected: {unique_ratio:.0%} unique content")
        # Return immediately for severe repetition
        return False, issues, details
    elif has_repetition:
        # Moderate repetition is a warning, not a failure
        details["repetition_warning"] = f"Some repeated content detected ({len(duplicates)} duplicates)"
        logger.debug(f"Repetition warning: {unique_ratio:.0%} unique content")
    
    # Check format compliance (now just conversational phrases - warning only)
    is_format_compliant, format_issues, format_details = check_format_compliance(response)
    details["format_compliance"] = format_details
    
    # Format issues are always warnings now, never hard failures
    if not is_format_compliant:
        details["format_warnings"] = format_issues
    
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
    
    elif review_type == "translation":
        # Check for English abstract section
        has_english = any([
            "english abstract" in response_lower,
            "## english" in response_lower,
            "abstract" in response_lower and "english" in response_lower,
        ])
        details["has_english_section"] = has_english
        
        # Check for translation section (any language keyword)
        translation_keywords = ["translation", "chinese", "hindi", "russian", "中文", "हिंदी", "русский"]
        has_translation = any(kw in response_lower for kw in translation_keywords)
        details["has_translation_section"] = has_translation
        
        # Both sections required
        if not has_english:
            issues.append("Missing English abstract section")
        if not has_translation:
            issues.append("Missing translation section")
    
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
    config.system_prompt = get_manuscript_review_system_prompt()
    config.auto_inject_system_prompt = True
    # long_max_tokens is now read from environment or config default
    
    # Log configuration source
    max_tokens, source = get_review_max_tokens()
    logger.debug(f"Review max_tokens configuration: {source}")
    
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
    warmup_tokens_per_sec: float = 0.0  # Performance from warmup step


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
    
    Provides detailed status messages about Ollama server and model availability.
    
    Returns:
        Tuple of (is_available, model_name)
    """
    log_stage("Checking Ollama availability...")
    
    # Step 1: Check if Ollama server is responding
    logger.info("    Pinging Ollama server at localhost:11434...")
    
    if not is_ollama_running():
        logger.warning("❌ Ollama server is not running")
        logger.info("  To start Ollama:")
        logger.info("    1. Open a terminal: ollama serve")
        logger.info("    2. Or start Ollama app if installed")
        logger.info("  To install a model: ollama pull llama3-gradient")
        return False, None
    
    log_success("Ollama server is running", logger)
    
    # Step 2: List available models
    logger.info("    Discovering available models...")
    available_models = get_available_models()
    if not available_models:
        logger.warning("❌ No Ollama models available")
        logger.info("  Install a model with: ollama pull llama3-gradient")
        logger.info("  Recommended models for manuscript review:")
        logger.info("    - llama3-gradient (4.7GB, 256K context, reliable)")
        logger.info("    - llama3.1:latest (4.7GB, 128K context)")
        return False, None
    
    # Log available models
    model_names = [m.get("name", "unknown") for m in available_models]
    logger.info(f"    Found {len(model_names)} model(s): {', '.join(model_names[:5])}")
    if len(model_names) > 5:
        logger.info(f"    ... and {len(model_names) - 5} more")
    
    # Step 3: Select best model
    logger.info("    Selecting best model for manuscript review...")
    model = select_best_model()
    if not model:
        logger.warning("❌ Could not select a suitable model")
        return False, None
    
    # Get detailed model info
    model_info = get_model_info(model)
    if model_info:
        size_bytes = model_info.get("size", 0)
        size_gb = size_bytes / (1024**3)
        
        # Extract parameter count from model name if available
        param_info = ""
        for size_hint in ["3b", "4b", "7b", "8b", "13b", "14b", "34b", "70b"]:
            if size_hint in model.lower():
                param_info = f", {size_hint.upper()} params"
                break
        
        logger.info(f"  Selected model: {model} ({size_gb:.1f} GB{param_info})")
        
        # Estimate context window from model name
        context_info = "32K context"
        if "qwen3" in model.lower() or "gradient" in model.lower():
            context_info = "128K+ context"
        elif "llama3.1" in model.lower():
            context_info = "128K context"
        logger.info(f"  Context window: ~{context_info}")
    else:
        logger.info(f"  Selected model: {model}")
    
    return True, model



def warmup_model(client: LLMClient, text_preview: str, model_name: str) -> Tuple[bool, float]:
    """Warmup the model with a tiny prompt to ensure it's loaded.
    
    This sends a small request before the main reviews to:
    1. Load the model into GPU memory (if not already loaded)
    2. Measure tokens/second performance
    3. Provide immediate feedback that the model is responsive
    4. Estimate total review time
    
    Uses streaming to provide real-time feedback during potentially slow model loading.
    
    Args:
        client: LLMClient instance
        text_preview: First ~500 chars of manuscript for context
        model_name: Model name for logging
        
    Returns:
        Tuple of (success, tokens_per_second)
    """
    log_stage("Warming up model...")
    
    # Check if model might already be loaded using Ollama's /api/ps
    logger.info(f"    Checking loaded models via Ollama API...")
    model_preloaded, loaded_model = check_model_loaded(model_name)
    
    need_preload = False
    if model_preloaded:
        logger.info(f"    ✓ Model {model_name} is already loaded in GPU memory")
        logger.info(f"    Warmup should be fast (~1-5 seconds)")
    elif loaded_model and "cache expired" in str(loaded_model):
        logger.info(f"    ⚠️ Model cache has expired - needs to reload")
        need_preload = True
    elif loaded_model:
        logger.info(f"    ⚠️ Different model loaded: {loaded_model}")
        logger.info(f"    Will switch to {model_name}")
        need_preload = True
    else:
        logger.info(f"    ⏳ No model currently loaded in GPU memory")
        need_preload = True
    
    # If model needs loading, preload it with progress indicator
    if need_preload:
        logger.info(f"    ⏳ Loading {model_name} into GPU memory...")
        logger.info(f"    (This may take 30-120 seconds depending on model size)")
        
        # Use improved spinner utility
        with log_with_spinner(
            f"Loading {model_name} into GPU memory...",
            logger,
            final_message=None  # We'll log success separately
        ):
            preload_success = preload_model(model_name)
        
        if preload_success:
            logger.info(f"    ✓ Model loaded successfully")
        else:
            logger.warning(f"    ⚠️ Preload returned error, continuing anyway...")
    
    # Now generate a short test response to measure performance
    logger.info(f"    Generating test response...")
    logger.info(f"    (Waiting for model - may take 30-60s if not fully loaded)")
    
    prompt = f"In exactly one sentence, what is the main topic of this text?\n\n{text_preview[:500]}"
    
    start_time = time.time()
    response_chunks = []
    first_token_time = None
    
    # Use improved spinner for waiting period
    spinner = Spinner("Waiting for first token...", delay=0.1)
    spinner.start()
    
    try:
        # Use streaming to get real-time feedback
        for chunk in client.stream_short(prompt):
            if first_token_time is None:
                first_token_time = time.time()
                time_to_first = first_token_time - start_time
                
                # Stop spinner
                spinner.stop()
                
                logger.info(f"    ✓ First token in {time_to_first:.1f}s - generating response...")
            
            response_chunks.append(chunk)
        
        elapsed = time.time() - start_time
        response = "".join(response_chunks)
        
        # Calculate performance metrics
        if first_token_time:
            generation_time = elapsed - (first_token_time - start_time)
            output_tokens = len(response.split()) * 1.3  # words × 1.3 ≈ tokens
            tokens_per_sec = output_tokens / generation_time if generation_time > 0 else 0
        else:
            tokens_per_sec = 0
        
        log_success(f"Warmup complete ({elapsed:.1f}s)", logger)
        
        # Show truncated response for confirmation
        response_preview = response[:80].replace('\n', ' ')
        if len(response) > 80:
            response_preview += "..."
        logger.info(f"    Response: {response_preview}")
        logger.info(f"    Performance: ~{tokens_per_sec:.1f} tokens/sec")
        
        # Estimate time for full reviews (4 reviews × configured max tokens each)
        if tokens_per_sec > 0:
            max_tokens, _ = get_review_max_tokens()
            estimated_total_tokens = 4 * max_tokens
            estimated_minutes = (estimated_total_tokens / tokens_per_sec) / 60
            logger.info(f"    Estimated review time: ~{estimated_minutes:.1f} minutes")
        else:
            logger.info(f"    ⚠️ Could not estimate review time (slow response)")
        
        return True, tokens_per_sec
        
    except Exception as e:
        # Stop spinner first
        spinner.stop()
        
        elapsed = time.time() - start_time
        logger.error(f"Model warmup failed after {elapsed:.1f}s: {e}")
        
        # Provide helpful troubleshooting info
        if elapsed > 120:
            logger.error("    ⚠️ Model loading timed out - the model may be too large for available memory")
            logger.error("    Try: ollama pull llama3-gradient")
        elif "connection" in str(e).lower():
            logger.error("    ⚠️ Connection to Ollama lost during warmup")
            logger.error("    Check: ollama ps")
        
        return False, 0.0


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
        logger.error(format_error_with_suggestions(e))
        return None, metrics


def generate_review_with_metrics(
    client: LLMClient,
    text: str,
    review_type: str,
    review_name: str,
    template_class: type,
    model_name: str = "",
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
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
        max_tokens: Maximum tokens for response (uses client config if None)
        max_retries: Number of retry attempts for low-quality responses (reduced default)
        
    Returns:
        Tuple of (response content, metrics)
    """
    log_stage(f"Generating {review_name}...")
    
    # Use configured max_tokens if not provided
    if max_tokens is None:
        max_tokens, _ = get_review_max_tokens()
    
    metrics = ReviewMetrics(
        input_chars=len(text),
        input_words=len(text.split()),
        input_tokens_est=estimate_tokens(text),
    )
    
    # Reset context to prevent pollution from previous reviews
    client.reset()
    
    # Render the template with manuscript text and token budget
    template = template_class()
    prompt = template.render(text=text, max_tokens=max_tokens)
    
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
    
    # Track if we had off-topic issues for reinforced prompting
    had_off_topic = False
    
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
                
                # If previous attempt was off-topic, add reinforced instructions
                if had_off_topic:
                    if PROMPT_SYSTEM_AVAILABLE:
                        try:
                            composer = PromptComposer()
                            retry_prompt = composer.add_retry_prompt(prompt, retry_type="off_topic")
                            current_prompt = retry_prompt
                        except Exception as e:
                            logger.debug(f"Could not use prompt composer for retry: {e}")
                            # Fallback to hardcoded
                            current_prompt = (
                                "IMPORTANT: You must review the ACTUAL manuscript text provided below. "
                                "Do NOT generate hypothetical content, generic book descriptions, or "
                                "unrelated topics. Your review must reference specific content from "
                                "the manuscript.\n\n" + prompt
                            )
                    else:
                        # Fallback to hardcoded
                        current_prompt = (
                            "IMPORTANT: You must review the ACTUAL manuscript text provided below. "
                            "Do NOT generate hypothetical content, generic book descriptions, or "
                            "unrelated topics. Your review must reference specific content from "
                            "the manuscript.\n\n" + prompt
                        )
                    logger.debug("    Added reinforced prompt for off-topic retry")
            
            # Use streaming query for progress tracking
            response_chunks = []
            tokens_generated = 0
            first_token_time = None
            start_gen_time = time.time()
            
            # Estimate total tokens needed (rough estimate: ~4 chars per token)
            estimated_total_tokens = max_tokens
            
            # Use streaming for better progress visibility with improved progress indicator
            try:
                # Create streaming progress tracker
                progress = StreamingProgress(
                    total=estimated_total_tokens,
                    message=f"Generating {review_name}",
                    update_interval=0.5
                )
                
                for chunk in client.stream_query(current_prompt, options=options):
                    if first_token_time is None:
                        first_token_time = time.time()
                        time_to_first = first_token_time - start_gen_time
                        logger.info(f"    ✓ First token in {time_to_first:.1f}s - generating...")
                    
                    response_chunks.append(chunk)
                    tokens_generated += len(chunk.split())  # Rough token estimate
                    progress.set(tokens_generated)
                
                # Finish progress display
                total_time = time.time() - start_gen_time
                final_tokens_per_sec = tokens_generated / total_time if total_time > 0 else 0
                progress.finish(f"    Generated {tokens_generated:,} tokens in {total_time:.1f}s ({final_tokens_per_sec:.1f} tokens/sec)")
                
                response = "".join(response_chunks)
                
            except Exception as stream_error:
                # Fallback to non-streaming if streaming fails
                logger.warning(f"    Streaming failed, using non-streaming: {stream_error}")
                response = client.query(current_prompt, options=options)
            
            # Validate response quality with model-specific thresholds
            is_valid, issues, details = validate_review_quality(
                response, review_type, model_name=model_name
            )
            
            # Track if this attempt was off-topic
            had_off_topic = any("off-topic" in issue.lower() for issue in issues)
            
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
    
    # Post-processing: clean up any remaining repetitive content with safety checks
    original_length = len(response)

    # Only apply deduplication if severe repetition is detected
    has_rep, _, unique_ratio = detect_repetition(response, similarity_threshold=0.8)
    if has_rep and unique_ratio < 0.3:  # Only for severe repetition cases
        # Use conservative deduplication to avoid removing valid content
        response = deduplicate_sections(
            response,
            max_repetitions=2,
            mode="conservative",
            similarity_threshold=0.9,  # Very strict similarity requirement
            min_content_preservation=0.8  # Preserve at least 80% of content
        )

        reduction_ratio = len(response) / original_length
        if reduction_ratio < 0.95:  # Only log significant changes
            logger.info(
                f"    Cleaned severe repetition: {original_length} → {len(response)} chars "
                f"({reduction_ratio:.1%} preserved)"
            )

        # Safety check: never remove more than 30% of content
        if reduction_ratio < 0.7:
            logger.warning(
                f"    Deduplication removed too much content ({reduction_ratio:.1%}). "
                f"Restoring original response."
            )
            response = best_response  # Restore the original response
    
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
        if format_info.get("conversational_phrases"):
            logger.info(f"    Format notes: conversational phrases detected")
        # Log repetition warnings if any
        rep_warning = best_details.get("repetition_warning")
        if rep_warning:
            logger.info(f"    Repetition notes: {rep_warning}")
    
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
        max_tokens=None,  # Uses configured value from client
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
        max_tokens=None,  # Uses configured value from client
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
        max_tokens=None,  # Uses configured value from client
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
        max_tokens=None,  # Uses configured value from client
    )


def generate_translation(
    client: LLMClient,
    text: str,
    language_code: str,
    model_name: str = "",
) -> Tuple[str, ReviewMetrics]:
    """Generate technical abstract translation to target language.
    
    Creates a medium-length technical abstract in English (~200-400 words),
    then translates it to the specified target language.
    
    Args:
        client: LLMClient instance
        text: Manuscript text
        language_code: Target language code (e.g., 'zh', 'hi', 'ru')
        model_name: Model name for model-specific adjustments
        
    Returns:
        Tuple of (translation markdown, metrics)
    """
    # Get full language name for the prompt
    target_language = TRANSLATION_LANGUAGES.get(language_code, language_code)
    
    log_stage(f"Generating translation ({target_language})...")
    
    metrics = ReviewMetrics(
        input_chars=len(text),
        input_words=len(text.split()),
        input_tokens_est=estimate_tokens(text),
    )
    
    # Reset context to prevent pollution from previous reviews
    client.reset()
    
    # Use configured max_tokens
    max_tokens, _ = get_review_max_tokens()
    
    # Render the template with manuscript text, target language, and token budget
    template = ManuscriptTranslationAbstract()
    prompt = template.render(text=text, target_language=target_language, max_tokens=max_tokens)
    
    # Adjust temperature for smaller models
    is_small_model = any(s in model_name.lower() for s in ["3b", "4b", "7b", "8b"])
    temperature = 0.4 if is_small_model else 0.3
    
    options = GenerationOptions(
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    start_time = time.time()
    
    try:
        response = client.query(prompt, options=options)
        
        # Validate response quality
        is_valid, issues, details = validate_review_quality(
            response, "translation", model_name=model_name
        )
        
        if not is_valid:
            logger.info(f"    Validation issues: {', '.join(issues[:2])}")
        
    except Exception as e:
        metrics.generation_time_seconds = time.time() - start_time
        logger.error(f"Failed to generate translation ({target_language}): {e}")
        error_response = f"*Error generating translation to {target_language}: {e}*"
        metrics.output_chars = len(error_response)
        metrics.output_words = len(error_response.split())
        return error_response, metrics
    
    # Calculate output metrics
    metrics.generation_time_seconds = time.time() - start_time
    metrics.output_chars = len(response)
    metrics.output_words = len(response.split())
    metrics.output_tokens_est = estimate_tokens(response)
    metrics.preview = response[:150].replace('\n', ' ') + "..." if len(response) > 150 else response
    
    log_success(f"translation ({target_language}) generated", logger)
    logger.info(f"    Output: {metrics.output_chars:,} chars ({metrics.output_words:,} words) in {metrics.generation_time_seconds:.1f}s")
    
    return response, metrics


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
    
    Simplified version - only checks for conversational phrases.
    Emojis and tables are allowed.
    
    Args:
        reviews: Dictionary of review name -> content
        
    Returns:
        Markdown formatted format compliance summary
    """
    total_reviews = len(reviews)
    conversational_count = 0
    
    for name, content in reviews.items():
        phrases = detect_conversational_phrases(content)
        if phrases:
            conversational_count += 1
    
    # Calculate compliance percentage (only conversational phrases matter now)
    compliance_rate = ((total_reviews - conversational_count) / total_reviews) * 100 if total_reviews > 0 else 100
    
    # Build summary
    summary_parts = [f"**Format Compliance:** {compliance_rate:.0f}%"]
    
    if conversational_count > 0:
        summary_parts.append(f"*Notes: {conversational_count} review(s) with conversational phrases*")
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
            # Log with full absolute path and word count
            full_path = filepath.resolve()
            if name.startswith("translation_"):
                lang_code = name.replace("translation_", "")
                lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
                logger.info(f"  Saved translation ({lang_name}): {full_path} ({metrics.output_words:,} words)")
            else:
                logger.info(f"  Saved: {full_path} ({metrics.output_words:,} words)")
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
        
        # Build navigation table with optional translation links
        nav_rows = [
            "| [Action Items](#action-items-checklist) | Prioritized TODO list |",
            "| [Executive Summary](#executive-summary) | Key findings overview |",
            "| [Quality Review](#quality-review) | Writing quality assessment |",
            "| [Methodology Review](#methodology-review) | Methods evaluation |",
            "| [Improvement Suggestions](#improvement-suggestions) | Detailed recommendations |",
        ]
        
        # Add translation links if translations were generated
        translation_keys = [k for k in reviews.keys() if k.startswith("translation_")]
        for trans_key in translation_keys:
            lang_code = trans_key.replace("translation_", "")
            lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
            nav_rows.append(f"| [Translation ({lang_name})](#translation-{lang_code}) | Technical abstract in {lang_name} |")
        
        nav_rows.append("| [Generation Metrics](#generation-metrics) | Review statistics |")
        nav_table = "\n".join(nav_rows)
        
        # Build translations section if any translations were generated
        translations_section = ""
        if translation_keys:
            translations_section = "\n---\n\n# Translations\n\n"
            for trans_key in translation_keys:
                lang_code = trans_key.replace("translation_", "")
                lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
                translations_section += f"""## Translation ({lang_name}) {{#translation-{lang_code}}}

{reviews.get(trans_key, '*Not generated*')}

---

"""
        
        combined_content = f"""# LLM Manuscript Review

*Generated by {model_name} on {date_str}*
*Source: {pdf_path.name}*

---

## Quick Navigation

| Section | Description |
|---------|-------------|
{nav_table}

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
{translations_section}
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
        logger.info(f"  Saved combined review: {combined_path}")
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
                "conversational_phrases": len(details.get("conversational_phrases", [])),
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
                "max_tokens": get_review_max_tokens()[0],
                "max_tokens_source": get_review_max_tokens()[1],
                "timeout_seconds": get_review_timeout(),
                "system_prompt": "manuscript_review",
            }
        }
        metadata_path.write_text(json.dumps(metadata, indent=2))
        logger.info(f"  Saved metadata: {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        success = False
    
    if success:
        log_success(f"All reviews saved to {output_dir}", logger)
    
    return success


def save_single_review(
    review_name: str,
    content: str,
    output_dir: Path,
    model_name: str,
    metrics: ReviewMetrics,
) -> Path:
    """Save a single review immediately after generation.
    
    This function saves a review file as soon as it's generated, rather than
    waiting for all reviews to complete. This provides incremental progress
    and allows partial results to be available even if the process is interrupted.
    
    Args:
        review_name: Name of the review (e.g., 'executive_summary', 'translation_zh')
        content: Review content text
        output_dir: Output directory path
        model_name: Name of LLM model used
        metrics: Review generation metrics
        
    Returns:
        Path to saved file
    """
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filepath
    filepath = output_dir / f"{review_name}.md"
    
    # Create header with metadata
    timestamp = datetime.now().isoformat()
    date_str = timestamp[:10]
    header = f"""# {review_name.replace('_', ' ').title()}

*Generated by LLM ({model_name}) on {date_str}*
*Output: {metrics.output_chars:,} chars ({metrics.output_words:,} words) in {metrics.generation_time_seconds:.1f}s*

---

"""
    
    # Write file
    try:
        filepath.write_text(header + content)
        
        # Log with full absolute path and word count
        full_path = filepath.resolve()
        
        # Special handling for translations
        if review_name.startswith("translation_"):
            lang_code = review_name.replace("translation_", "")
            lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
            logger.info(f"✅ Saved: {full_path} ({metrics.output_words:,} words) - Translation ({lang_name})")
        else:
            logger.info(f"✅ Saved: {full_path} ({metrics.output_words:,} words)")
        
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to save {review_name}: {e}")
        raise


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
    
    # File sizes with full paths
    logger.info(f"\nFiles created:")
    translation_files = []
    other_files = []
    for filepath in sorted(output_dir.glob("*")):
        if filepath.name.startswith("translation_"):
            translation_files.append(filepath)
        else:
            other_files.append(filepath)
    
    # Log translation files with language names, full paths, and word counts
    if translation_files:
        logger.info(f"\n  Translation files:")
        for filepath in translation_files:
            full_path = filepath.resolve()
            size_kb = filepath.stat().st_size / 1024
            lang_code = filepath.stem.replace("translation_", "")
            lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
            # Get word count from metrics if available
            review_name = filepath.stem
            metrics = session_metrics.reviews.get(review_name, ReviewMetrics())
            word_count = metrics.output_words if metrics.output_words > 0 else "N/A"
            if word_count != "N/A":
                logger.info(f"    • {full_path} ({lang_name}): {size_kb:.1f} KB, {word_count:,} words")
            else:
                logger.info(f"    • {full_path} ({lang_name}): {size_kb:.1f} KB")
    
    # Log other files with full paths and word counts
    if other_files:
        logger.info(f"\n  Other files:")
        for filepath in other_files:
            full_path = filepath.resolve()
            size_kb = filepath.stat().st_size / 1024
            # Get word count from metrics if available
            review_name = filepath.stem
            metrics = session_metrics.reviews.get(review_name, ReviewMetrics())
            word_count = metrics.output_words if metrics.output_words > 0 else "N/A"
            if word_count != "N/A":
                logger.info(f"    • {full_path}: {size_kb:.1f} KB, {word_count:,} words")
            else:
                logger.info(f"    • {full_path}: {size_kb:.1f} KB")
    
    logger.info("")


def main(mode: ReviewMode = ReviewMode.ALL) -> int:
    """Execute LLM manuscript review orchestration.
    
    Args:
        mode: Execution mode - ALL (both), REVIEWS_ONLY, or TRANSLATIONS_ONLY
    
    Returns:
        Exit code (0=success, 1=failure, 2=skipped)
    """
    # Log appropriate header based on mode
    if mode == ReviewMode.REVIEWS_ONLY:
        log_header("Stage 8/9: LLM Scientific Review (English)")
    elif mode == ReviewMode.TRANSLATIONS_ONLY:
        log_header("Stage 9/9: LLM Translations")
    else:
        log_header("Stage 8/9: LLM Manuscript Review")
    
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
        max_tokens, source = get_review_max_tokens()
        logger.info(f"    Max tokens: {max_tokens} per review (configured from: {source})")
        
        # Step 3.5: Warmup model before heavy processing
        warmup_success, tokens_per_sec = warmup_model(client, text[:1000], model_name)
        if not warmup_success:
            logger.error("Model warmup failed - cannot proceed with reviews")
            return 1
        session_metrics.warmup_tokens_per_sec = tokens_per_sec
        
        # Step 4: Generate reviews with metrics
        reviews = {}
        total_start = time.time()
        
        # Step 4a: Generate English scientific reviews (if not translations-only)
        if mode != ReviewMode.TRANSLATIONS_ONLY:
            logger.info("\n  Generating English scientific reviews...")
            review_types = ["executive_summary", "quality_review", "methodology_review", "improvement_suggestions"]
            
            for i, review_type in enumerate(review_types, 1):
                log_progress(i, len(review_types), f"Review: {review_type.replace('_', ' ').title()}", logger)
                
                if review_type == "executive_summary":
                    response, metrics = generate_executive_summary(client, text, model_name)
                elif review_type == "quality_review":
                    response, metrics = generate_quality_review(client, text, model_name)
                elif review_type == "methodology_review":
                    response, metrics = generate_methodology_review(client, text, model_name)
                else:  # improvement_suggestions
                    response, metrics = generate_improvement_suggestions(client, text, model_name)
                
                reviews[review_type] = response
                session_metrics.reviews[review_type] = metrics
                save_single_review(review_type, response, output_dir, model_name, metrics)
        
        # Step 4b: Generate translations (if not reviews-only)
        if mode != ReviewMode.REVIEWS_ONLY:
            translation_languages = get_translation_languages(repo_root)
            if translation_languages:
                logger.info(f"\n  Generating translations for {len(translation_languages)} language(s)...")
                for i, lang_code in enumerate(translation_languages, 1):
                    lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
                    log_progress(i, len(translation_languages), f"Translation: {lang_name}", logger)
                    response, metrics = generate_translation(client, text, lang_code, model_name)
                    review_name = f"translation_{lang_code}"
                    reviews[review_name] = response
                    session_metrics.reviews[review_name] = metrics
                    save_single_review(review_name, response, output_dir, model_name, metrics)
            elif mode == ReviewMode.TRANSLATIONS_ONLY:
                logger.warning("\n⚠️  No translation languages configured")
                logger.info("  Configure translations in project/manuscript/config.yaml:")
                logger.info("    llm:")
                logger.info("      translations:")
                logger.info("        enabled: true")
                logger.info("        languages: [zh, hi, ru]")
                return 2  # Skip - nothing to do
        
        # Check if any reviews were generated
        if not reviews:
            logger.warning("\n⚠️  No reviews or translations were generated")
            return 2
        
        session_metrics.total_generation_time = time.time() - total_start
        
        # Step 5: Save outputs
        if not save_review_outputs(reviews, output_dir, model_name, pdf_path, session_metrics):
            logger.error("Failed to save some review outputs")
            return 1
        
        # Step 6: Generate summary
        generate_review_summary(reviews, output_dir, session_metrics)
        
        # Log appropriate completion message
        if mode == ReviewMode.REVIEWS_ONLY:
            log_success("\n✅ LLM scientific review complete!", logger)
        elif mode == ReviewMode.TRANSLATIONS_ONLY:
            log_success("\n✅ LLM translations complete!", logger)
        else:
            log_success("\n✅ LLM manuscript review complete!", logger)
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during LLM review: {e}", exc_info=True)
        return 1


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="LLM Manuscript Review - Generate AI-powered reviews and translations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/06_llm_review.py                    # Run both reviews and translations
  python3 scripts/06_llm_review.py --reviews-only     # Run only English scientific reviews
  python3 scripts/06_llm_review.py --translations-only # Run only translations

Requires Ollama to be running with at least one model installed.
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--reviews-only",
        action="store_true",
        help="Run only English scientific reviews (executive summary, quality, methodology, improvements)"
    )
    mode_group.add_argument(
        "--translations-only",
        action="store_true",
        help="Run only translations to configured languages"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Determine mode from arguments
    if args.reviews_only:
        mode = ReviewMode.REVIEWS_ONLY
    elif args.translations_only:
        mode = ReviewMode.TRANSLATIONS_ONLY
    else:
        mode = ReviewMode.ALL
    
    exit(main(mode))
