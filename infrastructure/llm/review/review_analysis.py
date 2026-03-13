"""Analysis and summary extraction from LLM review content.

Functions for extracting action items, calculating format compliance,
and generating quality summaries from review text. Split from io.py
to keep each module under 300 LOC.
"""

from __future__ import annotations

import re

from infrastructure.llm.validation.format import detect_conversational_phrases


def extract_action_items(reviews: dict[str, str]) -> str:
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

        if in_high_priority and line.strip().startswith(
            ("- **", "- *", "1.", "2.", "3.", "4.", "5.")
        ):
            # Extract the issue/recommendation
            item = line.strip()
            if item.startswith("- "):
                item = item[2:]
            if item.startswith(
                ("**Issue**:", "*Issue*:", "**Recommendation**:", "*Recommendation*:")
            ):
                item = item.split(":", 1)[1].strip()
            if len(item) > 10 and item not in todos:
                todos.append(f"[ ] {item[:100]}..." if len(item) > 100 else f"[ ] {item}")

    if not todos:
        todos = [
            "[ ] Review executive summary for accuracy",
            "[ ] Address issues in quality review",
            "[ ] Consider methodology suggestions",
            "[ ] Prioritize high-priority improvements",
        ]

    return "\n".join(todos[:10])  # Limit to 10 items


def calculate_format_compliance_summary(reviews: dict[str, str]) -> str:
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
    compliance_rate = (
        ((total_reviews - conversational_count) / total_reviews) * 100 if total_reviews > 0 else 100
    )

    # Build summary
    summary_parts = [f"**Format Compliance:** {compliance_rate:.0f}%"]

    if conversational_count > 0:
        summary_parts.append(
            f"*Notes: {conversational_count} review(s) with conversational phrases*"
        )
    else:
        summary_parts.append("*All reviews comply with format requirements*")

    return "\n".join(summary_parts)


def calculate_quality_summary(reviews: dict[str, str]) -> str:
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
    score_pattern = r"\*\*Score:\s*(\d)\*\*|\bScore:\s*(\d)\b"
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
