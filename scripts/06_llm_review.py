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
import sys
import time
from enum import Enum
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_progress
)
from infrastructure.core.config_loader import get_translation_languages
from infrastructure.llm.review_metrics import SessionMetrics
from infrastructure.llm.review_generator import (
    get_max_input_length,
    get_review_timeout,
    get_review_max_tokens,
    check_ollama_availability,
    extract_manuscript_text,
    create_review_client,
    warmup_model,
    generate_executive_summary,
    generate_quality_review,
    generate_methodology_review,
    generate_improvement_suggestions,
    generate_translation,
)
from infrastructure.llm.review_io import (
    save_review_outputs,
    save_single_review,
    generate_review_summary,
)
from infrastructure.llm.templates import TRANSLATION_LANGUAGES

# Set up logger for this module
logger = get_logger(__name__)


class ReviewMode(Enum):
    """Mode for LLM review execution."""
    ALL = "all"  # Run both reviews and translations
    REVIEWS_ONLY = "reviews_only"  # Run only English scientific reviews
    TRANSLATIONS_ONLY = "translations_only"  # Run only translations


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
        logger.info("\n  Initializing LLM client...")
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
