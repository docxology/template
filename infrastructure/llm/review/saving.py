"""File I/O operations for saving and summarizing LLM review outputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.llm.review.formatting import (
    _build_combined_review_content,
    _build_review_header,
    _build_review_metadata,
)
from infrastructure.llm.review.metrics import ReviewMetrics, SessionMetrics
from infrastructure.llm.templates import TRANSLATION_LANGUAGES

logger = get_logger(__name__)


def save_review_outputs(
    reviews: dict[str, str],
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
    logger.info("Saving review outputs...")

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
            header = _build_review_header(name, model_name, date_str, metrics)
            _tmp = filepath.with_suffix(filepath.suffix + ".tmp")
            try:
                _tmp.write_text(header + content)
                _tmp.replace(filepath)
            except Exception:
                _tmp.unlink(missing_ok=True)
                raise
            # Log with full absolute path and word count
            full_path = filepath.resolve()
            if name.startswith("translation_"):
                lang_code = name.replace("translation_", "")
                lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
                logger.info(
                    f"  Saved translation ({lang_name}): {full_path} ({metrics.output_words:,} words)"  # noqa: E501
                )
            else:
                logger.info(f"  Saved: {full_path} ({metrics.output_words:,} words)")
        except OSError as e:
            logger.error(f"Failed to save {name}: {e}", exc_info=True)
            success = False

    # Save combined review
    combined_path = output_dir / "combined_review.md"
    try:
        combined_content = _build_combined_review_content(
            reviews, model_name, pdf_path, session_metrics, timestamp, date_str,
        )
        _tmp = combined_path.with_suffix(combined_path.suffix + ".tmp")
        try:
            _tmp.write_text(combined_content)
            _tmp.replace(combined_path)
        except Exception:
            _tmp.unlink(missing_ok=True)
            raise
        logger.info(f"  Saved combined review: {combined_path}")
    except OSError as e:
        logger.error(f"Failed to save combined review: {e}", exc_info=True)
        success = False

    # Save metadata
    metadata_path = output_dir / "review_metadata.json"
    try:
        metadata = _build_review_metadata(
            reviews, model_name, pdf_path, session_metrics, timestamp,
        )
        _tmp = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
        try:
            _tmp.write_text(json.dumps(metadata, indent=2))
            _tmp.replace(metadata_path)
        except Exception:
            _tmp.unlink(missing_ok=True)
            raise
        logger.info(f"  Saved metadata: {metadata_path}")
    except (OSError, ValueError) as e:
        logger.error(f"Failed to save metadata: {e}", exc_info=True)
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
    header = _build_review_header(review_name, model_name, date_str, metrics)

    # Write file
    try:
        _tmp = filepath.with_suffix(filepath.suffix + ".tmp")
        try:
            _tmp.write_text(header + content)
            _tmp.replace(filepath)
        except Exception:
            _tmp.unlink(missing_ok=True)
            raise

        # Log with full absolute path and word count
        full_path = filepath.resolve()

        # Special handling for translations
        if review_name.startswith("translation_"):
            lang_code = review_name.replace("translation_", "")
            lang_name = TRANSLATION_LANGUAGES.get(lang_code, lang_code)
            logger.info(
                f"✅ Saved: {full_path} ({metrics.output_words:,} words) - Translation ({lang_name})"  # noqa: E501
            )
        else:
            logger.info(f"✅ Saved: {full_path} ({metrics.output_words:,} words)")

        return filepath

    except OSError as e:
        logger.error(f"Failed to save {review_name}: {e}")
        raise


def generate_review_summary(
    reviews: dict[str, str],
    output_dir: Path,
    session_metrics: SessionMetrics,
) -> None:
    """Generate comprehensive summary of LLM review results.

    Args:
        reviews: Dictionary of generated reviews
        output_dir: Output directory path
        session_metrics: Complete session metrics
    """
    logger.info("\n" + "=" * 60)
    logger.info("LLM Manuscript Review Summary")
    logger.info("=" * 60)

    # Input manuscript metrics
    m = session_metrics.manuscript
    logger.info("\nInput manuscript:")
    logger.info(
        f"  {m.total_chars:,} chars ({m.total_words:,} words, ~{m.total_tokens_est:,} tokens)"
    )
    if m.truncated:
        logger.info(f"  Truncated to {m.truncated_chars:,} chars")
    else:
        logger.info("  Full text sent to LLM (no truncation)")

    logger.info(f"\nOutput directory: {output_dir}")

    # Per-review metrics
    logger.info("\nReviews generated:")
    total_output_chars = 0
    total_output_words = 0

    for name in reviews:
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
    logger.info("\nFiles created:")
    translation_files = []
    other_files = []
    for filepath in sorted(output_dir.glob("*")):
        if filepath.name.startswith("translation_"):
            translation_files.append(filepath)
        else:
            other_files.append(filepath)

    # Log translation files with language names, full paths, and word counts
    if translation_files:
        logger.info("\n  Translation files:")
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
                logger.info(
                    f"    • {full_path} ({lang_name}): {size_kb:.1f} KB, {word_count:,} words"
                )
            else:
                logger.info(f"    • {full_path} ({lang_name}): {size_kb:.1f} KB")

    # Log other files with full paths and word counts
    if other_files:
        logger.info("\n  Other files:")
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
