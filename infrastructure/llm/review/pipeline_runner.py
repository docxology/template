"""LLM Review Pipeline runner for orchestration."""

from __future__ import annotations

import time
from functools import partial
from pathlib import Path

from infrastructure.core.exceptions import PDFValidationError
from infrastructure.core.logging.utils import (
    get_logger,
    log_substep,
    log_success,
    log_progress,
)
from infrastructure.core.config.queries import get_translation_languages, get_review_types
from infrastructure.llm.templates.manuscript import TRANSLATION_LANGUAGES, ManuscriptQualityReview, ManuscriptMethodologyReview
from infrastructure.llm.review.io import (
    save_review_outputs,
    save_single_review,
    generate_review_summary,
)
from infrastructure.llm.review.metrics import SessionMetrics
from infrastructure.llm.core.config import get_max_input_length
from infrastructure.llm.review.generator import (
    select_and_start_ollama_model,
    create_review_client,
    extract_manuscript_text,
    generate_llm_executive_summary,
    generate_improvement_suggestions,
    generate_review_with_metrics,
    generate_translation,
    warmup_model,
)

logger = get_logger(__name__)

REVIEW_GENERATORS = {
    "executive_summary": generate_llm_executive_summary,
    "quality_review": partial(
        generate_review_with_metrics,
        review_type="quality_review",
        review_name="quality review",
        template_class=ManuscriptQualityReview,
        temperature=0.3,
        max_tokens=None,
    ),
    "methodology_review": partial(
        generate_review_with_metrics,
        review_type="methodology_review",
        review_name="methodology review",
        template_class=ManuscriptMethodologyReview,
        temperature=0.3,
        max_tokens=None,
    ),
    "improvement_suggestions": generate_improvement_suggestions,
}


class ReviewMode:
    """Mode for LLM review execution."""

    ALL = "all"  # Run both reviews and translations
    REVIEWS_ONLY = "reviews_only"  # Run only English scientific reviews
    TRANSLATIONS_ONLY = "translations_only"  # Run only translations


def run_llm_review_pipeline(
    mode: str = ReviewMode.ALL,
    project_name: str = "project",
    repo_root: Path | None = None,
    project_dir: Path | None = None,
) -> int:
    """Execute LLM manuscript review orchestration.

    Args:
        mode: Execution mode - ALL (both), REVIEWS_ONLY, or TRANSLATIONS_ONLY.
        project_name: Name of project directory.
        repo_root: Optional repository root path.
        project_dir: Absolute path to the project directory. When provided,
            overrides ``repo_root / 'projects' / project_name``.

    Returns:
        Exit code (0=success, 1=failure, 2=skipped)
    """
    if repo_root is None:
        repo_root = Path.cwd()

    _project_root = (
        project_dir if project_dir is not None else repo_root / "projects" / project_name
    )
    project_output = _project_root / "output"

    # Use project basename for file matching
    project_basename = Path(project_name).name
    pdf_dir = project_output / "pdf"
    project_specific_pdf = pdf_dir / f"{project_basename}_combined.pdf"

    pdf_path = project_specific_pdf  # Always use expected filename; extract_manuscript_text handles missing-file case

    output_dir = project_output / "llm"

    # Initialize session metrics
    max_input_length = get_max_input_length()
    session_metrics = SessionMetrics(max_input_length=max_input_length)

    try:
        # Step 1: Check Ollama availability
        available, model_name = select_and_start_ollama_model()

        if not available:
            logger.warning("\n⚠️  Skipping LLM review - Ollama not available")
            return 2

        session_metrics.model_name = model_name

        # Step 2: Extract manuscript text
        try:
            text, manuscript_metrics = extract_manuscript_text(pdf_path, max_input_length=max_input_length)
        except PDFValidationError as e:
            logger.error(f"Cannot generate reviews: manuscript PDF is invalid — {e}")
            return 2
        session_metrics.manuscript = manuscript_metrics

        if not text:
            logger.error("Cannot generate reviews without manuscript text")
            return 2

        # Step 3: Initialize LLM client
        log_substep("Initializing LLM client...")
        client = create_review_client(model_name)

        if not client.check_connection():
            logger.error("Failed to connect to Ollama")
            return 1

        log_success("LLM client initialized", logger)

        # Step 3.5: Warmup model
        warmup_success, tokens_per_sec = warmup_model(client, text[:1000], model_name)
        if not warmup_success:
            logger.error("Model warmup failed - cannot proceed with reviews")
            return 1
        session_metrics.warmup_tokens_per_sec = tokens_per_sec

        # Step 4: Generate reviews
        reviews = {}
        total_start = time.time()

        # English reviews
        if mode != ReviewMode.TRANSLATIONS_ONLY:
            logger.info("\n  Generating English scientific reviews...")
            review_types = get_review_types(repo_root, project_name) or ["executive_summary"]

            for i, review_type in enumerate(review_types, 1):
                log_progress(
                    i, len(review_types), f"Review: {review_type.replace('_', ' ').title()}", logger
                )

                generator = REVIEW_GENERATORS.get(review_type)
                if generator is None:
                    logger.warning(f"  Skipping unknown review type: {review_type}")
                    continue
                response, metrics = generator(client, text, model_name)

                reviews[review_type] = response
                session_metrics.reviews[review_type] = metrics
                save_single_review(review_type, response, output_dir, model_name, metrics)

        # Translations
        if mode != ReviewMode.REVIEWS_ONLY:
            translation_languages = get_translation_languages(repo_root, project_name)
            if translation_languages:
                logger.info(
                    f"\n  Generating translations for {len(translation_languages)} language(s)..."
                )

                for i, lang_code in enumerate(translation_languages, 1):
                    lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
                    log_progress(i, len(translation_languages), f"Translation: {lang_name}", logger)
                    response, metrics = generate_translation(client, text, lang_code, model_name)
                    review_name = f"translation_{lang_code}"
                    session_metrics.reviews[review_name] = metrics
                    if response is not None:
                        reviews[review_name] = response
                        save_single_review(review_name, response, output_dir, model_name, metrics)
            elif mode == ReviewMode.TRANSLATIONS_ONLY:
                logger.warning("\n⚠️  No translation languages configured")
                return 2

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
        return 0

    except Exception as e:
        logger.error(f"Unexpected error during LLM review pipeline: {e}", exc_info=True)
        return 1
