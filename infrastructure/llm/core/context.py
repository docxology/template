"""Context management for LLM interactions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.exceptions import ContextLimitError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class MessageDict(TypedDict):
    """Wire format for a single conversation turn sent to the Ollama chat API."""

    role: str
    content: str


class ContextState(TypedDict):
    """Shape of the dict produced by ``ConversationContext.save_state``."""

    messages: list[dict[str, Any]]
    estimated_tokens: int
    max_tokens: int
    usage_stats: dict[str, Any]


@dataclass
class Message:
    """A single message in the conversation."""

    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> MessageDict:
        """Convert to wire-format dict for Ollama chat API."""
        return MessageDict(role=self.role, content=self.content)


class ConversationContext:
    """Manages conversation history and token limits."""

    def __init__(self, max_tokens: int = 262144):  # Default to 256K for large-context models
        """Initialize conversation context."""
        self.messages: list[Message] = []
        self.max_tokens = max_tokens
        self.estimated_tokens = 0
        # Usage tracking
        self._total_messages_added = 0
        self._total_tokens_estimated = 0
        self._prune_count = 0
        self._clear_count = 0

    def add_message(self, role: str, content: str) -> None:
        """Append a message; prunes oldest history when token budget is exceeded."""
        # Simple estimation: 1 token ~= 4 chars
        tokens = len(content) // 4

        logger.debug(
            "Adding message to context role=%s len=%d tokens_est=%d total=%d/%d msgs=%d",
            role, len(content), tokens, self.estimated_tokens, self.max_tokens, len(self.messages),
        )

        if self.estimated_tokens + tokens > self.max_tokens:
            self._prune_context(tokens)

        self.messages.append(Message(role, content))
        self.estimated_tokens += tokens
        self._total_messages_added += 1
        self._total_tokens_estimated += tokens

    def get_messages(self) -> list[MessageDict]:
        """Return messages as list of {'role', 'content'} dicts for Ollama API."""
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        """Discard all messages and reset token estimate; system prompt is not re-added."""
        logger.debug("Clearing context msgs=%d tokens=%d", len(self.messages), self.estimated_tokens)
        self.messages = []
        self.estimated_tokens = 0
        self._clear_count += 1

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
            },
        )

        while self.messages and (self.estimated_tokens + new_tokens > self.max_tokens):
            removed = self.messages.pop(0)
            # Don't remove system prompt — put it back and either remove the next
            # message or stop pruning when only the system message is left.
            if removed.role == "system":
                self.messages.insert(0, removed)
                if len(self.messages) < 2:
                    # Only the system message remains; nothing more to prune.
                    break
                removed = self.messages.pop(1)

            removed_tokens = len(removed.content) // 4
            self.estimated_tokens -= removed_tokens
            pruned_count += 1

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
            },
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
                },
            )
            raise ContextLimitError(
                "Message too large for context window",
                context={
                    "size": new_tokens,
                    "limit": self.max_tokens,
                    "estimated_total": self.estimated_tokens + new_tokens,
                },
            )

    def save_state(self) -> ContextState:
        """Save current context state for restoration via ``restore_state``."""
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
            },
        )

        return state

    def restore_state(self, state: ContextState) -> None:
        """Restore context from a ``save_state`` dictionary."""
        logger.info(
            "Restoring context state",
            extra={
                "messages_in_state": len(state.get("messages", [])),
                "tokens_in_state": state.get("estimated_tokens", 0),
            },
        )

        self.messages = [Message(**msg) for msg in state.get("messages", [])]
        self.estimated_tokens = state.get("estimated_tokens", 0)
        self.max_tokens = state.get("max_tokens", self.max_tokens)

    def export_context(self, path: Path) -> None:
        """Export context to a JSON file at *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "messages": [asdict(msg) for msg in self.messages],
            "estimated_tokens": self.estimated_tokens,
            "max_tokens": self.max_tokens,
            "usage_stats": self.get_usage_stats(),
        }

        _tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            _tmp.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
            _tmp.replace(path)
        except OSError:
            _tmp.unlink(missing_ok=True)
            raise

        logger.info(
            "Context exported",
            extra={
                "path": str(path),
                "messages_count": len(self.messages),
                "estimated_tokens": self.estimated_tokens,
            },
        )

    def import_context(self, path: Path) -> None:
        """Import context from a JSON file at *path*."""
        import_data = json.loads(path.read_text(encoding="utf-8"))

        logger.info(
            "Importing context",
            extra={
                "path": str(path),
                "messages_in_file": len(import_data.get("messages", [])),
            },
        )

        self.restore_state(import_data)

    def get_usage_stats(self) -> dict[str, Any]:
        """Return context usage statistics dictionary."""
        usage_percent = (
            (self.estimated_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
        )

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
        """Return 'healthy', 'warning', or 'critical' based on usage percentage."""
        if usage_percent < 50:
            return "healthy"
        elif usage_percent < 80:
            return "warning"
        else:
            return "critical"

    def check_health(self) -> tuple[str, dict[str, Any]]:
        """Return ``(status, stats)`` where status is 'healthy', 'warning', or 'critical'."""
        stats = self.get_usage_stats()
        status = stats["health_status"]

        if status == "warning":
            logger.warning(
                "Context usage approaching limit",
                extra={
                    "usage_percent": stats["usage_percent"],
                    "current_tokens": stats["current_tokens_est"],
                    "max_tokens": stats["max_tokens"],
                },
            )
        elif status == "critical":
            logger.error(
                "Context usage critical",
                extra={
                    "usage_percent": stats["usage_percent"],
                    "current_tokens": stats["current_tokens_est"],
                    "max_tokens": stats["max_tokens"],
                },
            )

        return status, stats
