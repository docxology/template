"""File I/O operations for saving and summarizing LLM review outputs."""

import json
import ntpath
import re
from datetime import datetime
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.llm.review.formatting import (
    build_combined_review_content,
    build_review_header,
    build_review_metadata,
)
from infrastructure.llm.review.metrics import ReviewMetrics, SessionMetrics
from infrastructure.llm.templates import TRANSLATION_LANGUAGES

logger = get_logger(__name__)


def _review_filename(name: str) -> str:
    filename = f"{name}.md"
    if (
        not isinstance(name, str)
        or re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", name) is None
        or ntpath.isreserved(filename)
    ):
        raise ValueError("Review name must be a safe filename component")
    return filename


def _review_output_boundary(output_dir: Path, project_dir: Path | None) -> tuple[Path, Path]:
    """Use the selected project or the caller's explicit output directory."""
    target = output_dir.absolute()
    if project_dir is not None:
        return project_dir, target
    ancestor = target.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    root = ancestor.resolve(strict=True)
    return root, root / target.relative_to(ancestor)


def save_review_outputs(
    reviews: dict[str, str],
    output_dir: Path,
    model_name: str,
    pdf_path: Path,
    session_metrics: SessionMetrics,
    *,
    project_dir: Path | None = None,
) -> bool:
    """Save all review outputs to markdown files with detailed metrics.

    Args:
        reviews: Dictionary of review name -> content
        output_dir: Output directory path
        model_name: Name of LLM model used
        pdf_path: Path to source manuscript PDF
        session_metrics: Complete session metrics
        project_dir: Selected project root for pipeline output confinement

    Returns:
        True if all files saved successfully
    """
    logger.info("Saving review outputs...")

    try:
        filenames = {name: _review_filename(name) for name in reviews}
        root, directory = _review_output_boundary(output_dir, project_dir)
    except (OSError, ValueError) as exc:
        logger.error("Review output refused: %s", exc)
        return False

    success = True
    timestamp = datetime.now().isoformat()
    date_str = timestamp[:10]

    # Save individual reviews
    for name, content in reviews.items():
        filepath = directory / filenames[name]
        try:
            metrics = session_metrics.reviews.get(name, ReviewMetrics())
            header = build_review_header(name, model_name, date_str, metrics)
            atomic_write_text_confined(root, filepath, header + content, mode=0o600)
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
        except (OSError, ValueError) as e:
            logger.error(f"Failed to save {name}: {e}", exc_info=True)
            success = False

    # Save combined review
    combined_path = directory / "combined_review.md"
    try:
        combined_content = build_combined_review_content(
            reviews,
            model_name,
            pdf_path,
            session_metrics,
            timestamp,
            date_str,
        )
        atomic_write_text_confined(root, combined_path, combined_content, mode=0o600)
        logger.info(f"  Saved combined review: {combined_path}")
    except (OSError, ValueError) as e:
        logger.error(f"Failed to save combined review: {e}", exc_info=True)
        success = False

    # Save metadata
    metadata_path = directory / "review_metadata.json"
    try:
        metadata = build_review_metadata(
            reviews,
            model_name,
            pdf_path,
            session_metrics,
            timestamp,
        )
        atomic_write_text_confined(root, metadata_path, json.dumps(metadata, indent=2), mode=0o600)
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
    *,
    project_dir: Path | None = None,
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
        project_dir: Selected project root for pipeline output confinement

    Returns:
        Path to saved file
    """
    filename = _review_filename(review_name)
    root, directory = _review_output_boundary(output_dir, project_dir)
    filepath = directory / filename

    # Create header with metadata
    timestamp = datetime.now().isoformat()
    date_str = timestamp[:10]
    header = build_review_header(review_name, model_name, date_str, metrics)

    # Write file
    try:
        atomic_write_text_confined(root, filepath, header + content, mode=0o600)

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

        return output_dir / filename

    except (OSError, ValueError) as e:
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
    logger.info("\n" + "=" * BANNER_WIDTH)
    logger.info("LLM Manuscript Review Summary")
    logger.info("=" * BANNER_WIDTH)

    # Input manuscript metrics
    m = session_metrics.manuscript
    logger.info("\nInput manuscript:")
    logger.info(f"  {m.total_chars:,} chars ({m.total_words:,} words, ~{m.total_tokens_est:,} tokens)")
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
                logger.info(f"    • {full_path} ({lang_name}): {size_kb:.1f} KB, {word_count:,} words")
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
