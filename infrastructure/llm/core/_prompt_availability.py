"""Availability sentinels for the optional prompt system.

Centralises the try/except-at-import pattern so it only runs once.
Import from here instead of duplicating the try/except block.
"""

from __future__ import annotations

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

try:
    from infrastructure.llm.prompts.composer import PromptComposer  # noqa: F401

    PROMPT_COMPOSER_AVAILABLE = True
except ImportError:
    PROMPT_COMPOSER_AVAILABLE = False
    logger.debug("Prompt composer not available, using template system")

try:
    from infrastructure.llm.prompts.loader import get_default_loader  # noqa: F401

    PROMPT_SYSTEM_AVAILABLE = True
except ImportError:
    PROMPT_SYSTEM_AVAILABLE = False
