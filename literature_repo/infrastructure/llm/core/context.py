"""Context management for LLM interactions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

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

    def __init__(self, max_tokens: int = 262144):  # Default to 256K for large-context models
        self.messages: List[Message] = []
        self.max_tokens = max_tokens
        self.estimated_tokens = 0
        # Usage tracking
        self._total_messages_added = 0
        self._total_tokens_estimated = 0
        self._prune_count = 0
        self._clear_count = 0

    def add_message(self, role: str, content: str) -> None:
        """Add a message to context."""
        # Simple estimation: 1 token ~= 4 chars
        tokens = len(content) // 4
        
        logger.debug(
            "Adding message to context",
            extra={
                "role": role,
                "content_length": len(content),
                "tokens_est": tokens,
                "current_tokens_est": self.estimated_tokens,
                "max_tokens": self.max_tokens,
                "messages_before": len(self.messages),
            }
        )
        
        if self.estimated_tokens + tokens > self.max_tokens:
            self._prune_context(tokens)
            
        self.messages.append(Message(role, content))
        self.estimated_tokens += tokens
        self._total_messages_added += 1
        self._total_tokens_estimated += tokens
        
        logger.debug(
            "Message added to context",
            extra={
                "role": role,
                "messages_after": len(self.messages),
                "tokens_est_after": self.estimated_tokens,
                "usage_percent": (self.estimated_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            }
        )

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API."""
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        """Clear context."""
        messages_before = len(self.messages)
        tokens_before = self.estimated_tokens
        
        logger.info(
            "Clearing context",
            extra={
                "messages_cleared": messages_before,
                "tokens_cleared": tokens_before,
            }
        )
        
        self.messages = []
        self.estimated_tokens = 0
        self._clear_count += 1
        
        logger.debug("Context cleared", extra={"clear_count": self._clear_count})

    def _prune_context(self, new_tokens: int) -> None:
        """Remove old messages to fit new ones."""
        messages_before = len(self.messages)
        tokens_before = self.estimated_tokens
        pruned_count = 0
        
        logger.debug(
            "Pruning context",
            extra={
                "new_tokens": new_tokens,
                "current_tokens": self.estimated_tokens,
                "max_tokens": self.max_tokens,
                "messages_before": messages_before,
            }
        )
        
        while self.messages and (self.estimated_tokens + new_tokens > self.max_tokens):
            removed = self.messages.pop(0)
            # Don't remove system prompt if it's the first message
            if removed.role == "system" and self.messages:
                # Put it back and remove next
                self.messages.insert(0, removed)
                removed = self.messages.pop(1)
            
            removed_tokens = len(removed.content) // 4
            self.estimated_tokens -= removed_tokens
            pruned_count += 1
            
            logger.debug(
                "Pruned message",
                extra={
                    "role": removed.role,
                    "content_length": len(removed.content),
                    "tokens_removed": removed_tokens,
                    "tokens_after": self.estimated_tokens,
                    "messages_remaining": len(self.messages),
                }
            )
        
        self._prune_count += 1
        
        logger.info(
            "Context pruned",
            extra={
                "messages_pruned": pruned_count,
                "messages_before": messages_before,
                "messages_after": len(self.messages),
                "tokens_before": tokens_before,
                "tokens_after": self.estimated_tokens,
                "prune_count": self._prune_count,
            }
        )
        
        # For large context windows (>= 64K), be more lenient with estimation errors
        # Token estimation can be off by 20-30%, so allow some buffer
        buffer_factor = 1.3 if self.max_tokens >= 65536 else 1.0
        effective_limit = int(self.max_tokens * buffer_factor)
        
        if self.estimated_tokens + new_tokens > effective_limit:
            logger.error(
                "Context limit exceeded after pruning",
                extra={
                    "new_tokens": new_tokens,
                    "current_tokens": self.estimated_tokens,
                    "max_tokens": self.max_tokens,
                    "effective_limit": effective_limit,
                }
            )
            raise ContextLimitError(
                "Message too large for context window",
                context={"size": new_tokens, "limit": self.max_tokens, "estimated_total": self.estimated_tokens + new_tokens}
            )
    
    def save_state(self) -> Dict[str, Any]:
        """Save current context state for restoration.
        
        Returns:
            Dictionary containing context state
            
        Example:
            >>> state = context.save_state()
            >>> # ... later ...
            >>> context.restore_state(state)
        """
        state = {
            "messages": [asdict(msg) for msg in self.messages],
            "estimated_tokens": self.estimated_tokens,
            "max_tokens": self.max_tokens,
            "usage_stats": self.get_usage_stats(),
        }
        
        logger.debug(
            "Context state saved",
            extra={
                "messages_count": len(self.messages),
                "estimated_tokens": self.estimated_tokens,
            }
        )
        
        return state
    
    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore context from saved state.
        
        Args:
            state: State dictionary from save_state()
            
        Example:
            >>> state = context.save_state()
            >>> context.clear()
            >>> context.restore_state(state)
        """
        logger.info(
            "Restoring context state",
            extra={
                "messages_in_state": len(state.get("messages", [])),
                "tokens_in_state": state.get("estimated_tokens", 0),
            }
        )
        
        self.messages = [Message(**msg) for msg in state.get("messages", [])]
        self.estimated_tokens = state.get("estimated_tokens", 0)
        self.max_tokens = state.get("max_tokens", self.max_tokens)
        
        logger.debug(
            "Context state restored",
            extra={
                "messages_restored": len(self.messages),
                "estimated_tokens": self.estimated_tokens,
            }
        )
    
    def export_context(self, path: Path) -> None:
        """Export context to JSON file.
        
        Args:
            path: Path to save context JSON file
            
        Example:
            >>> context.export_context(Path("context.json"))
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "messages": [asdict(msg) for msg in self.messages],
            "estimated_tokens": self.estimated_tokens,
            "max_tokens": self.max_tokens,
            "usage_stats": self.get_usage_stats(),
        }
        
        path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        
        logger.info(
            "Context exported",
            extra={
                "path": str(path),
                "messages_count": len(self.messages),
                "estimated_tokens": self.estimated_tokens,
            }
        )
    
    def import_context(self, path: Path) -> None:
        """Import context from JSON file.
        
        Args:
            path: Path to context JSON file
            
        Example:
            >>> context.import_context(Path("context.json"))
        """
        import_data = json.loads(path.read_text(encoding="utf-8"))
        
        logger.info(
            "Importing context",
            extra={
                "path": str(path),
                "messages_in_file": len(import_data.get("messages", [])),
            }
        )
        
        self.restore_state(import_data)
        
        logger.debug("Context imported successfully")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get context usage statistics.
        
        Returns:
            Dictionary with usage statistics
            
        Example:
            >>> stats = context.get_usage_stats()
            >>> print(f"Total messages: {stats['total_messages_added']}")
        """
        usage_percent = (self.estimated_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
        
        stats = {
            "current_messages": len(self.messages),
            "current_tokens_est": self.estimated_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "total_messages_added": self._total_messages_added,
            "total_tokens_estimated": self._total_tokens_estimated,
            "prune_count": self._prune_count,
            "clear_count": self._clear_count,
            "health_status": self._get_health_status(usage_percent),
        }
        
        return stats
    
    def _get_health_status(self, usage_percent: float) -> str:
        """Get health status based on usage percentage.
        
        Args:
            usage_percent: Current usage percentage
            
        Returns:
            Health status string ("healthy", "warning", "critical")
        """
        if usage_percent < 50:
            return "healthy"
        elif usage_percent < 80:
            return "warning"
        else:
            return "critical"
    
    def check_health(self) -> Tuple[str, Dict[str, Any]]:
        """Check context health and return status with details.
        
        Returns:
            Tuple of (status, details_dict)
            - status: "healthy", "warning", or "critical"
            - details: Dictionary with health details
            
        Example:
            >>> status, details = context.check_health()
            >>> if status == "warning":
            ...     print(f"Context usage: {details['usage_percent']:.1f}%")
        """
        stats = self.get_usage_stats()
        status = stats["health_status"]
        
        if status == "warning":
            logger.warning(
                "Context usage approaching limit",
                extra={
                    "usage_percent": stats["usage_percent"],
                    "current_tokens": stats["current_tokens_est"],
                    "max_tokens": stats["max_tokens"],
                }
            )
        elif status == "critical":
            logger.error(
                "Context usage critical",
                extra={
                    "usage_percent": stats["usage_percent"],
                    "current_tokens": stats["current_tokens_est"],
                    "max_tokens": stats["max_tokens"],
                }
            )
        
        return status, stats

