"""File I/O and output formatting for LLM review generation."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict

from infrastructure.core.logging_utils import get_logger, log_success
from infrastructure.llm.validation.format import detect_conversational_phrases, check_format_compliance
from infrastructure.llm.templates import TRANSLATION_LANGUAGES
from infrastructure.llm.review.metrics import ReviewMetrics, SessionMetrics
from infrastructure.llm.review.generator import (
    get_max_input_length,
    get_review_max_tokens,
    get_review_timeout,
)

logger = get_logger(__name__)


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
{translations_section}---

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

