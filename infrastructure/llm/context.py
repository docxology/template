"""Context management for LLM interactions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import ContextLimitError

logger = get_logger(__name__)


@dataclass
class Message:
    """A single message in the conversation."""
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API."""
        return {"role": self.role, "content": self.content}


class ConversationContext:
    """Manages conversation history and token limits."""

    def __init__(self, max_tokens: int = 4096):
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.estimated_tokens = 0

    def add_message(self, role: str, content: str) -> None:
        """Add a message to context."""
        # Simple estimation: 1 token ~= 4 chars
        tokens = len(content) // 4
        
        if self.estimated_tokens + tokens > self.max_tokens:
            self._prune_context(tokens)
            
        self.messages.append(Message(role, content))
        self.estimated_tokens += tokens

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API."""
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        """Clear context."""
        self.messages = []
        self.estimated_tokens = 0

    def _prune_context(self, new_tokens: int) -> None:
        """Remove old messages to fit new ones."""
        while self.messages and (self.estimated_tokens + new_tokens > self.max_tokens):
            removed = self.messages.pop(0)
            # Don't remove system prompt if it's the first message
            if removed.role == "system" and self.messages:
                # Put it back and remove next
                self.messages.insert(0, removed)
                removed = self.messages.pop(1)
            
            self.estimated_tokens -= (len(removed.content) // 4)
            
        if self.estimated_tokens + new_tokens > self.max_tokens:
            raise ContextLimitError(
                "Message too large for context window",
                context={"size": new_tokens, "limit": self.max_tokens}
            )

