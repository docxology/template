#!/usr/bin/env python3
"""LLM Manuscript Review orchestrator script.

This thin orchestrator coordinates the LLM review stage:
1. Checks Ollama availability and selects best model
2. Extracts text from combined manuscript PDF (full content, no truncation by default)
3. Generates configured review types (default: executive_summary only)
4. Generates translations to configured languages (if enabled)
5. Validates review quality and retries if needed
6. Saves all reviews to output/llm/ with detailed metrics

Stage 8 of the pipeline orchestration - uses local Ollama LLM for
manuscript analysis and review generation.

Review Types (configurable via config.yaml):
- executive_summary: Key findings and contributions (default)
- quality_review: Writing clarity and style
- methodology_review: Structure and methods assessment
- improvement_suggestions: Actionable recommendations

Configuration (projects/{name}/manuscript/config.yaml):
```yaml
llm:
  reviews:
    enabled: true
    types:
      - executive_summary  # Default: single review
      # - quality_review
      # - methodology_review
      # - improvement_suggestions
  translations:
    enabled: true
    languages:
      - zh  # Default: single translation
      # - hi
      # - ru
```

Output Files:
- executive_summary.md     # Key findings and contributions (if enabled)
- quality_review.md        # Writing clarity and style (if enabled)
- methodology_review.md    # Structure and methods assessment (if enabled)
- improvement_suggestions.md # Actionable recommendations (if enabled)
- translation_{lang}.md   # Translations for each configured language
- review_metadata.json     # Model used, timestamp, config, detailed metrics
- combined_review.md       # All reviews in one document with TODO checklist

Environment Variables:
- LLM_MAX_INPUT_LENGTH: Maximum characters to send to LLM (default: 500000 = ~125K tokens)
                        Set to 0 for unlimited input size
- LLM_REVIEW_TIMEOUT: Timeout for each review generation (default: 300s)
- LLM_LONG_MAX_TOKENS: Maximum tokens per review response (default: 16384)
                       Configured via LLMConfig.long_max_tokens, can be overridden with env var
                       Priority: LLM_LONG_MAX_TOKENS env var > config default (16384)
- LLM_CONTEXT_WINDOW: Context window size (default: 262144 for 256K models like ministral-3:3b)

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
import subprocess
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
from infrastructure.core.exceptions import LLMConnectionError, LLMTemplateError
from infrastructure.core.config_loader import get_translation_languages, get_review_types
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import LLMConfig, GenerationOptions
from infrastructure.llm.utils.ollama import (
    is_ollama_running,
    ensure_ollama_ready,
    select_best_model,
    get_model_info,
    get_available_models,
    check_model_loaded,
    preload_model,
)
from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor
from infrastructure.llm.templates.manuscript import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
    ManuscriptTranslationAbstract,
    REVIEW_MIN_WORDS,
    TRANSLATION_LANGUAGES,
)
from infrastructure.llm.validation.repetition import (
    detect_repetition,
    deduplicate_sections,
)
from infrastructure.llm.validation.format import (
    is_off_topic,
    check_format_compliance,
)
from infrastructure.llm.review.io import (
    save_review_outputs,
    save_single_review,
    generate_review_summary,
)

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


def log_timeout_info(timeout: float, operation: str) -> None:
    """Log timeout configuration with warnings.

    Args:
        timeout: Timeout in seconds
        operation: Description of the operation
    """
    logger.info(f"    Timeout: {timeout:.0f}s per {operation}")
    if timeout < 60:
        logger.warning(f"    ⚠️  Low timeout ({timeout:.0f}s) - may cause failures for slow models")
        logger.info(f"    Consider: export LLM_REVIEW_TIMEOUT=300 (5 minutes) for better reliability")


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
    
    # Check word count with 5% tolerance for edge cases
    word_count = len(response.split())
    details["word_count"] = word_count
    details["min_required"] = min_word_count
    
    # Allow 5% tolerance to handle edge cases (e.g., 316 words when minimum is 320)
    tolerance = max(1, int(min_word_count * 0.05))  # At least 1 word tolerance
    effective_min = min_word_count - tolerance
    
    if word_count < effective_min:
        issues.append(f"Too short: {word_count} words (minimum: {min_word_count}, effective: {effective_min} with tolerance)")
    
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

    Attempts to start Ollama automatically if not running (unless disabled).
    Includes retry logic with exponential backoff for robustness.

    Returns:
        Tuple of (is_available, model_name)
    """
    log_stage("Checking Ollama availability...")

    # Check if auto-start is enabled (default: True)
    auto_start = os.environ.get("OLLAMA_AUTO_START", "true").lower() == "true"

    # First check if Ollama is installed
    try:
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True,
            timeout=2.0
        )
        if result.returncode != 0:
            logger.error("❌ Ollama command not found. Install Ollama: https://ollama.ai")
            logger.info("  macOS: brew install ollama")
            logger.info("  Linux: curl -fsSL https://ollama.ai/install.sh | sh")
            logger.info("  Windows: Download from https://ollama.ai/download")
            return False, None
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("❌ Unable to check if Ollama is installed")
        logger.info("  Install Ollama from: https://ollama.ai")
        return False, None

    # Step 1: Check if Ollama server is responding, auto-start if needed
    logger.info("    Checking Ollama server status...")

    # Retry logic with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        if attempt > 0:
            wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
            logger.info(f"    Retry {attempt}/{max_retries - 1} in {wait_time}s...")
            time.sleep(wait_time)

        if not is_ollama_running():
            if auto_start:
                logger.info("    Ollama not running, attempting to start automatically...")
                if ensure_ollama_ready(auto_start=True):
                    log_success("Ollama server started and ready", logger)
                    break  # Success, exit retry loop
                else:
                    if attempt == max_retries - 1:  # Last attempt failed
                        logger.warning("❌ Failed to start Ollama server automatically after retries")
                        logger.info("  To start manually:")
                        logger.info("    1. Open a terminal: ollama serve")
                        logger.info("    2. Or start Ollama app if installed")
                        logger.info("  To disable auto-start: export OLLAMA_AUTO_START=false")
                        logger.info("  To install a model: ollama pull llama3-gradient")
                        return False, None
                    else:
                        logger.warning(f"    Attempt {attempt + 1} failed, retrying...")
                        continue
            else:
                logger.warning("❌ Ollama server is not running")
                logger.info("  Auto-start is disabled (OLLAMA_AUTO_START=false)")
                logger.info("  To start Ollama:")
                logger.info("    1. Open a terminal: ollama serve")
                logger.info("    2. Or start Ollama app if installed")
                logger.info("  To enable auto-start: export OLLAMA_AUTO_START=true")
                logger.info("  To install a model: ollama pull llama3-gradient")
                return False, None
        else:
            log_success("Ollama server is running", logger)
            break  # Server is running, exit retry loop
    
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

    # Log timeout configuration for warmup
    warmup_timeout = get_review_timeout()
    logger.info(f"    Timeout: {warmup_timeout:.0f}s for warmup and performance test")

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

        # Track preload time for warnings
        preload_start = time.time()

        # Use improved spinner utility
        with log_with_spinner(
            f"Loading {model_name} into GPU memory...",
            logger,
            final_message=None  # We'll log success separately
        ):
            preload_success, preload_error = preload_model(model_name)

        preload_elapsed = time.time() - preload_start

        if preload_success:
            logger.info(f"    ✓ Model loaded successfully in {preload_elapsed:.1f}s")
            if preload_elapsed > 120:  # Warn if loading took more than 2 minutes
                logger.warning(f"    ⚠️ Model loading took {preload_elapsed:.1f}s (>2 minutes)")
                logger.info(f"    Consider using a smaller model for faster startup")
        else:
            error_msg = f": {preload_error}" if preload_error else ""
            logger.warning(f"    ⚠️ Preload returned error{error_msg}, continuing anyway...")
            logger.info(f"    (Model may still work - Ollama will load on first query)")
    
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

                # Start heartbeat monitor for long operations
                config = LLMConfig.from_env()
                heartbeat_monitor = StreamHeartbeatMonitor(
                    operation_name=review_name,
                    timeout_seconds=get_review_timeout(),
                    heartbeat_interval=config.heartbeat_interval,
                    stall_threshold=config.stall_threshold,
                    early_warning_threshold=config.early_warning_threshold,
                    logger=logger
                )
                heartbeat_monitor.set_estimated_total(estimated_total_tokens)
                heartbeat_monitor.start_monitoring()

                try:
                    for chunk in client.stream_query(current_prompt, options=options):
                        response_chunks.append(chunk)
                        tokens_generated += len(chunk.split())  # Rough token estimate
                        progress.set(tokens_generated)
                        heartbeat_monitor.update_token_received()  # Update heartbeat

                finally:
                    # Stop heartbeat monitor
                    heartbeat_monitor.stop_monitoring()
                
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

    # Get timeout configuration and log warnings
    timeout = get_review_timeout()
    log_timeout_info(timeout, f"translation ({target_language})")

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
        # Use streaming for better progress visibility with improved progress indicator
        try:
            # Create streaming progress tracker
            progress = StreamingProgress(
                total=max_tokens,
                message=f"Generating translation ({target_language})",
                update_interval=0.5
            )

            # Start heartbeat monitor for long operations
            config = LLMConfig.from_env()
            heartbeat_monitor = StreamHeartbeatMonitor(
                operation_name=f"translation ({target_language})",
                timeout_seconds=timeout,
                heartbeat_interval=config.heartbeat_interval,
                stall_threshold=config.stall_threshold,
                early_warning_threshold=config.early_warning_threshold,
                logger=logger
            )
            heartbeat_monitor.set_estimated_total(max_tokens)
            heartbeat_monitor.start_monitoring()

            response_chunks = []
            tokens_generated = 0

            try:
                for chunk in client.stream_query(prompt, options=options):
                    response_chunks.append(chunk)
                    tokens_generated += len(chunk.split())  # Rough token estimate
                    progress.set(tokens_generated)
                    heartbeat_monitor.update_token_received()  # Update heartbeat

                # Finish progress display
                total_time = time.time() - heartbeat_monitor.start_time
                final_tokens_per_sec = tokens_generated / total_time if total_time > 0 else 0
                progress.finish(f"    Generated {tokens_generated:,} tokens in {total_time:.1f}s ({final_tokens_per_sec:.1f} tokens/sec)")

            finally:
                # Stop heartbeat monitor
                heartbeat_monitor.stop_monitoring()

            response = "".join(response_chunks)

        except Exception as stream_error:
            # Fallback to non-streaming if streaming fails
            logger.warning(f"    Streaming failed, using non-streaming: {stream_error}")
            response = client.query(prompt, options=options)

        # Validate response quality
        is_valid, issues, details = validate_review_quality(
            response, "translation", model_name=model_name
        )

        if not is_valid:
            logger.info(f"    Validation issues: {', '.join(issues[:2])}")

    except LLMConnectionError as e:
        metrics.generation_time_seconds = time.time() - start_time
        logger.error(f"Connection failed during translation ({target_language}): {e}")

        # Provide specific guidance for connection issues
        if "timeout" in str(e).lower():
            logger.error("  This appears to be a timeout issue:")
            logger.error(f"  - Current timeout: {get_review_timeout():.0f}s")
            logger.error("  - Try increasing: export LLM_REVIEW_TIMEOUT=300")
            logger.error("  - Or use faster model: smaller models load faster")
        elif "connection" in str(e).lower():
            logger.error("  This appears to be a connection issue:")
            logger.error("  - Check Ollama: ollama ps")
            logger.error("  - Restart if needed: ollama serve")

        error_response = f"*Connection error generating translation to {target_language}: {e}*"
        metrics.output_chars = len(error_response)
        metrics.output_words = len(error_response.split())
        return error_response, metrics

    except LLMTemplateError as e:
        metrics.generation_time_seconds = time.time() - start_time
        logger.error(f"Template error during translation ({target_language}): {e}")
        logger.error("  This may indicate an issue with the translation prompt")
        error_response = f"*Template error generating translation to {target_language}: {e}*"
        metrics.output_chars = len(error_response)
        metrics.output_words = len(error_response.split())
        return error_response, metrics

    except Exception as e:
        metrics.generation_time_seconds = time.time() - start_time

        # Check if we have partial response from streaming
        partial_response = ""
        if 'response_chunks' in locals() and response_chunks:
            partial_response = "".join(response_chunks)
            if len(partial_response.strip()) > 50:  # Only log if meaningful content
                logger.warning(f"Partial response received ({len(partial_response)} chars)")
                logger.debug(f"Partial content: {partial_response[:200]}...")

        logger.error(f"Failed to generate translation ({target_language}): {e}")

        # Provide actionable suggestions based on error type
        error_str = str(e).lower()
        if "timeout" in error_str:
            logger.error("  Suggestion: Increase timeout for translations:")
            logger.error("    export LLM_REVIEW_TIMEOUT=300  # 5 minutes")
        elif "memory" in error_str or "gpu" in error_str.lower():
            logger.error("  Suggestion: Model may be too large for available memory")
            logger.error("    Try: ollama pull gemma2:2b  # Smaller model")
        elif "context" in error_str:
            logger.error("  Suggestion: Manuscript may be too long for model context")
            logger.error("    Try: export LLM_MAX_INPUT_LENGTH=250000  # Reduce input size")
        else:
            logger.error("  Suggestion: Check Ollama status and model availability")
            logger.error("    ollama ps && ollama list")

        if partial_response:
            error_response = f"*Error generating translation to {target_language}: {e}*\n\n*Partial response saved:*\n{partial_response[:500]}{'...' if len(partial_response) > 500 else ''}"
        else:
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


def main(mode: ReviewMode = ReviewMode.ALL, project_name: str = "project") -> int:
    """Execute LLM manuscript review orchestration.

    Args:
        mode: Execution mode - ALL (both), REVIEWS_ONLY, or TRANSLATIONS_ONLY
        project_name: Name of project in projects/ directory

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
    project_output = repo_root / "projects" / project_name / "output"

    # Try project-specific filename first, then fallback to generic for backward compatibility
    # Use project basename for file matching (handles nested projects like "cognitive_integrity/cogsec_multiagent_1_theory")
    project_basename = Path(project_name).name
    pdf_dir = project_output / "pdf"
    project_specific_pdf = pdf_dir / f"{project_basename}_combined.pdf"
    generic_pdf = pdf_dir / "project_combined.pdf"

    if project_specific_pdf.exists():
        pdf_path = project_specific_pdf
    elif generic_pdf.exists():
        pdf_path = generic_pdf
        logger.warning(f"Using legacy PDF filename: {generic_pdf.name}. Consider upgrading to project-specific naming.")
    else:
        pdf_path = project_specific_pdf  # Use expected filename in error message

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
            logger.warning("  Skipping LLM review - manuscript text extraction failed")
            logger.info("  Install pypdf for PDF text extraction: pip install pypdf")
            return 2  # Graceful skip, not failure
        
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
            review_types = get_review_types(repo_root, project_name)
            
            # Default to single review if none configured
            if not review_types:
                review_types = ['executive_summary']
                logger.info("  Using default: executive_summary (no review config found)")
            
            for i, review_type in enumerate(review_types, 1):
                log_progress(i, len(review_types), f"Review: {review_type.replace('_', ' ').title()}", logger)
                
                if review_type == "executive_summary":
                    response, metrics = generate_executive_summary(client, text, model_name)
                elif review_type == "quality_review":
                    response, metrics = generate_quality_review(client, text, model_name)
                elif review_type == "methodology_review":
                    response, metrics = generate_methodology_review(client, text, model_name)
                elif review_type == "improvement_suggestions":
                    response, metrics = generate_improvement_suggestions(client, text, model_name)
                else:
                    logger.warning(f"  Skipping unknown review type: {review_type}")
                    continue
                
                reviews[review_type] = response
                session_metrics.reviews[review_type] = metrics
                save_single_review(review_type, response, output_dir, model_name, metrics)
        
        # Step 4b: Generate translations (if not reviews-only)
        if mode != ReviewMode.REVIEWS_ONLY:
            translation_languages = get_translation_languages(repo_root, project_name)
            if translation_languages:
                logger.info(f"\n  Generating translations for {len(translation_languages)} language(s)...")

                # Estimate time per translation based on warmup performance
                if session_metrics.warmup_tokens_per_sec > 0:
                    max_tokens, _ = get_review_max_tokens()
                    estimated_tokens_per_translation = max_tokens
                    estimated_seconds_per_translation = estimated_tokens_per_translation / session_metrics.warmup_tokens_per_sec
                    logger.info(f"    Estimated time per translation: ~{estimated_seconds_per_translation:.0f} seconds")
                    logger.info(f"    Total estimated time: ~{(estimated_seconds_per_translation * len(translation_languages)):.0f} seconds")

                # Get timeout for warnings
                translation_timeout = get_review_timeout()
                if translation_timeout < 120:
                    logger.warning(f"    ⚠️  Low timeout ({translation_timeout:.0f}s) may cause translation failures")
                    logger.info(f"    Consider: export LLM_REVIEW_TIMEOUT=300 for translations")

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
                logger.info(f"  Configure translations in projects/{project_name}/manuscript/config.yaml:")
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
    
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
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

    exit(main(mode, args.project))
