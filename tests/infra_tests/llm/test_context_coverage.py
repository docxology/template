"""Tests for infrastructure.llm.core.context — comprehensive coverage."""

import json

import pytest

from infrastructure.core.exceptions import ContextLimitError
from infrastructure.llm.core.context import (
    Message,
    ConversationContext,
)


class TestMessage:
    def test_create_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {}

    def test_to_dict(self):
        msg = Message(role="assistant", content="Hi there")
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["content"] == "Hi there"

    def test_metadata(self):
        msg = Message(role="user", content="test", metadata={"key": "val"})
        assert msg.metadata["key"] == "val"


class TestConversationContext:
    def test_init_defaults(self):
        ctx = ConversationContext()
        assert ctx.max_tokens == 262144
        assert ctx.estimated_tokens == 0
        assert ctx.messages == []

    def test_init_custom_max(self):
        ctx = ConversationContext(max_tokens=1000)
        assert ctx.max_tokens == 1000

    def test_add_message(self):
        ctx = ConversationContext()
        ctx.add_message("user", "Hello world")
        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == "user"
        assert ctx.messages[0].content == "Hello world"
        assert ctx.estimated_tokens > 0

    def test_get_messages(self):
        ctx = ConversationContext()
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi")
        msgs = ctx.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_clear(self):
        ctx = ConversationContext()
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi")
        ctx.clear()
        assert len(ctx.messages) == 0
        assert ctx.estimated_tokens == 0
        assert ctx._clear_count == 1

    def test_prune_context(self):
        ctx = ConversationContext(max_tokens=20)
        # Add messages until pruning occurs
        ctx.add_message("user", "A" * 40)  # ~10 tokens
        ctx.add_message("assistant", "B" * 40)  # ~10 tokens
        # This should trigger pruning
        ctx.add_message("user", "C" * 40)  # ~10 tokens
        assert ctx._prune_count > 0

    def test_prune_preserves_system_messages(self):
        ctx = ConversationContext(max_tokens=30)
        ctx.add_message("system", "System prompt")
        ctx.add_message("user", "A" * 60)  # ~15 tokens
        ctx.add_message("user", "B" * 60)  # ~15 tokens - should trigger prune
        # System message should be preserved
        system_msgs = [m for m in ctx.messages if m.role == "system"]
        assert len(system_msgs) == 1

    def test_context_limit_error(self):
        ctx = ConversationContext(max_tokens=10)
        # Very large message that can't fit even after pruning
        with pytest.raises(ContextLimitError):
            ctx.add_message("user", "X" * 200)

    def test_save_state(self):
        ctx = ConversationContext(max_tokens=1000)
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi")
        state = ctx.save_state()
        assert "messages" in state
        assert "estimated_tokens" in state
        assert "max_tokens" in state
        assert "usage_stats" in state
        assert len(state["messages"]) == 2

    def test_restore_state(self):
        ctx = ConversationContext(max_tokens=1000)
        ctx.add_message("user", "Hello")
        state = ctx.save_state()

        ctx2 = ConversationContext()
        ctx2.restore_state(state)
        assert len(ctx2.messages) == 1
        assert ctx2.messages[0].role == "user"
        assert ctx2.messages[0].content == "Hello"
        assert ctx2.estimated_tokens == state["estimated_tokens"]

    def test_restore_empty_state(self):
        ctx = ConversationContext()
        ctx.restore_state({})
        assert len(ctx.messages) == 0
        assert ctx.estimated_tokens == 0

    def test_export_context(self, tmp_path):
        ctx = ConversationContext(max_tokens=1000)
        ctx.add_message("user", "Test message")
        export_path = tmp_path / "context.json"
        ctx.export_context(export_path)
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Test message"

    def test_export_creates_parent_dirs(self, tmp_path):
        ctx = ConversationContext()
        ctx.add_message("user", "Hello")
        export_path = tmp_path / "deep" / "nested" / "context.json"
        ctx.export_context(export_path)
        assert export_path.exists()

    def test_import_context(self, tmp_path):
        ctx1 = ConversationContext(max_tokens=1000)
        ctx1.add_message("user", "Saved message")
        ctx1.add_message("assistant", "Response")
        export_path = tmp_path / "context.json"
        ctx1.export_context(export_path)

        ctx2 = ConversationContext()
        ctx2.import_context(export_path)
        assert len(ctx2.messages) == 2
        assert ctx2.messages[0].content == "Saved message"
        assert ctx2.messages[1].content == "Response"

    def test_get_usage_stats(self):
        ctx = ConversationContext(max_tokens=1000)
        ctx.add_message("user", "Hello")
        stats = ctx.get_usage_stats()
        assert stats["current_messages"] == 1
        assert stats["current_tokens_est"] > 0
        assert stats["max_tokens"] == 1000
        assert "usage_percent" in stats
        assert stats["total_messages_added"] == 1
        assert stats["prune_count"] == 0
        assert stats["clear_count"] == 0
        assert stats["health_status"] == "healthy"

    def test_health_status_healthy(self):
        ctx = ConversationContext(max_tokens=10000)
        assert ctx._get_health_status(10.0) == "healthy"
        assert ctx._get_health_status(49.9) == "healthy"

    def test_health_status_warning(self):
        ctx = ConversationContext()
        assert ctx._get_health_status(50.0) == "warning"
        assert ctx._get_health_status(79.9) == "warning"

    def test_health_status_critical(self):
        ctx = ConversationContext()
        assert ctx._get_health_status(80.0) == "critical"
        assert ctx._get_health_status(99.0) == "critical"

    def test_check_health_healthy(self):
        ctx = ConversationContext(max_tokens=10000)
        status, stats = ctx.check_health()
        assert status == "healthy"
        assert stats["usage_percent"] < 50

    def test_check_health_warning(self):
        ctx = ConversationContext(max_tokens=100)
        # Fill to ~60%
        ctx.add_message("user", "A" * 240)  # ~60 tokens
        status, stats = ctx.check_health()
        assert status == "warning"

    def test_check_health_critical(self):
        ctx = ConversationContext(max_tokens=100)
        # Fill to >80%
        ctx.add_message("user", "A" * 340)  # ~85 tokens
        status, stats = ctx.check_health()
        assert status == "critical"

    def test_usage_stats_zero_max(self):
        ctx = ConversationContext(max_tokens=0)
        stats = ctx.get_usage_stats()
        assert stats["usage_percent"] == 0

    def test_roundtrip_save_restore(self):
        ctx1 = ConversationContext(max_tokens=5000)
        ctx1.add_message("system", "You are helpful.")
        ctx1.add_message("user", "Hello")
        ctx1.add_message("assistant", "Hi there!")
        state = ctx1.save_state()

        ctx2 = ConversationContext()
        ctx2.restore_state(state)
        assert len(ctx2.messages) == 3
        assert ctx2.max_tokens == 5000
        msgs = ctx2.get_messages()
        assert msgs[0]["role"] == "system"
        assert msgs[2]["content"] == "Hi there!"
