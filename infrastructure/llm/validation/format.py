"""Format compliance checking for LLM output validation."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Off-topic detection patterns (indicates LLM confusion or hallucination)
# These patterns detect when the model is not reviewing the actual manuscript
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
    # Generic book/guide language at start (indicates hallucinated content)
    r"^This book is",                 # Generic book intro
    r"^This guide",                   # Generic guide intro
    r"^Chapter 1",                    # Chapter numbering (not manuscript)
    r"^Introduction\s*\n\s*This book", # Book intro pattern
]

OFF_TOPIC_PATTERNS_ANYWHERE = [
    # AI assistant refusal patterns (critical - indicates model can't process)
    r"I can't help",
    r"I cannot help",
    r"I'm unable to",
    r"I am unable to",
    r"I don't have access to",
    r"I cannot access",
    r"I'm not able to",
    # AI self-identification (indicates confusion)
    r"As an AI assistant",
    r"as a language model",
    r"I am an AI",
    r"I'm an AI assistant",
    r"I'm happy to help you with",
    r"I'm not sure if I can help",
    # External URLs (indicates external references, not manuscript content)
    r"https?://[^\s]+",               # Any URL
    # Generic book/guide language (indicates hallucinated content)
    r"this book provides",
    r"this guide explains",
    r"chapter \d+ deals with",
    r"chapter \d+ covers",
    r"the book is divided",
    r"this manual",
    # Code-focused responses when expecting prose
    r"^```python\n",                  # Code block at very start
    r"import pandas as pd\nimport",   # Multi-import block
    r"CMakeLists\.txt",               # Build system files
    r"\.cpp\b",                       # C++ file extensions
    r"\.hpp\b",                       # C++ header extensions
    # User requirement patterns (indicates form/registration confusion)
    r"must be a minimum of \d+ years",
    r"must have a valid email",
    r"must provide a.*phone number",
]

# Conversational AI phrases that indicate poor review quality
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


def check_format_compliance(response: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Check response for format compliance issues.
    
    Simplified validation focusing on structural compliance only.
    Emojis and tables are allowed.
    
    Detects:
    - Conversational AI phrases (unprofessional for formal review)
    
    Args:
        response: The generated review text
        
    Returns:
        Tuple of (is_compliant, list of issues, details dict)
    """
    issues = []
    details: Dict[str, Any] = {
        "conversational_phrases": [],
    }
    
    # Check for conversational phrases (only format check we keep)
    phrases = detect_conversational_phrases(response)
    if phrases:
        details["conversational_phrases"] = phrases[:5]  # Limit to first 5
        # This is a warning, not a hard failure
        issues.append(f"Contains conversational AI phrases: {phrases[0][:30]}...")
    
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










