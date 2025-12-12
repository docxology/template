"""Output validation for LLM responses."""
from infrastructure.llm.validation.core import OutputValidator
from infrastructure.llm.validation.format import (
    is_off_topic,
    has_on_topic_signals,
    detect_conversational_phrases,
    check_format_compliance,
    OFF_TOPIC_PATTERNS_START,
    OFF_TOPIC_PATTERNS_ANYWHERE,
    CONVERSATIONAL_PATTERNS,
    ON_TOPIC_SIGNALS,
)
from infrastructure.llm.validation.repetition import (
    calculate_unique_content_ratio,
    detect_repetition,
    deduplicate_sections,
)
from infrastructure.llm.validation.structure import (
    validate_section_completeness,
    extract_structured_sections,
    validate_response_structure,
)

__all__ = [
    "OutputValidator",
    "detect_repetition",
    "calculate_unique_content_ratio",
    "deduplicate_sections",
    "is_off_topic",
    "has_on_topic_signals",
    "detect_conversational_phrases",
    "check_format_compliance",
    "OFF_TOPIC_PATTERNS_START",
    "OFF_TOPIC_PATTERNS_ANYWHERE",
    "CONVERSATIONAL_PATTERNS",
    "ON_TOPIC_SIGNALS",
    "validate_section_completeness",
    "extract_structured_sections",
    "validate_response_structure",
]


