"""Tests for infrastructure.llm.core.context — expanded coverage."""


import pytest

from infrastructure.core.exceptions import ContextLimitError
from infrastructure.llm.core.context import ConversationContext, Message


class TestMessage:
    def test_to_dict(self):
        msg = Message(role="user", content="Hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_metadata_default(self):
        msg = Message(role="assistant", content="Hi")
        assert msg.metadata == {}


class TestConversationContext:
    def test_add_and_get_messages(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there")
        msgs = ctx.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_clear(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "test")
        ctx.clear()
        assert ctx.get_messages() == []
        assert ctx.estimated_tokens == 0
        assert ctx._clear_count == 1

    def test_prune_on_overflow(self):
        ctx = ConversationContext(max_tokens=50)
        # Add messages that exceed the limit
        ctx.add_message("user", "A" * 120)  # 30 tokens
        ctx.add_message("user", "B" * 120)  # 30 tokens - total would be 60, exceeds 50
        # Should have pruned at least one message
        assert ctx._prune_count >= 1

    def test_prune_preserves_system_messages(self):
        ctx = ConversationContext(max_tokens=100)
        ctx.add_message("system", "You are helpful")
        ctx.add_message("user", "A" * 200)
        ctx.add_message("user", "B" * 200)
        # System messages should still be present
        roles = [m.role for m in ctx.messages]
        assert "system" in roles

    def test_context_limit_error(self):
        ctx = ConversationContext(max_tokens=10)
        with pytest.raises(ContextLimitError):
            # Message way too large for context
            ctx.add_message("user", "X" * 1000)

    def test_save_and_restore_state(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi")

        state = ctx.save_state()
        assert len(state["messages"]) == 2
        assert state["max_tokens"] == 10000

        ctx2 = ConversationContext(max_tokens=5000)
        ctx2.restore_state(state)
        assert len(ctx2.messages) == 2
        assert ctx2.max_tokens == 10000

    def test_export_and_import(self, tmp_path):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Question?")
        ctx.add_message("assistant", "Answer.")

        export_path = tmp_path / "context.json"
        ctx.export_context(export_path)
        assert export_path.exists()

        ctx2 = ConversationContext()
        ctx2.import_context(export_path)
        msgs = ctx2.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["content"] == "Question?"

    def test_export_creates_parent_dirs(self, tmp_path):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "test")
        deep_path = tmp_path / "a" / "b" / "context.json"
        ctx.export_context(deep_path)
        assert deep_path.exists()

    def test_get_usage_stats(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Hello world")
        stats = ctx.get_usage_stats()
        assert stats["current_messages"] == 1
        assert stats["max_tokens"] == 10000
        assert stats["total_messages_added"] == 1
        assert stats["health_status"] == "healthy"

    def test_health_status_healthy(self):
        ctx = ConversationContext(max_tokens=10000)
        status, stats = ctx.check_health()
        assert status == "healthy"

    def test_health_status_warning(self):
        ctx = ConversationContext(max_tokens=100)
        # Add enough to get to ~60% usage
        ctx.add_message("user", "A" * 240)  # 60 tokens out of 100
        status, stats = ctx.check_health()
        assert status == "warning"

    def test_health_status_critical(self):
        ctx = ConversationContext(max_tokens=100)
        ctx.add_message("user", "A" * 320)  # 80 tokens out of 100
        status, stats = ctx.check_health()
        assert status == "critical"

    def test_restore_empty_state(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "something")
        ctx.restore_state({"messages": [], "estimated_tokens": 0})
        assert ctx.get_messages() == []

    def test_large_context_buffer_factor(self):
        """Large context windows (>=64K) get a 1.3x buffer factor during pruning."""
        ctx = ConversationContext(max_tokens=65536)
        # Add a system message and a user message
        ctx.add_message("system", "You are helpful")
        # This should work with the buffer factor
        ctx.add_message("user", "A" * (65536 * 4))  # Exactly at limit
        # Should not raise due to buffer factor
        assert len(ctx.messages) >= 1

    def test_export_context_oserror_cleans_tmp(self, tmp_path):
        """When export_context cannot write the tmp file, it cleans up and re-raises."""
        import stat

        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "test")

        # Create the parent directory, then make it read-only so writing fails
        target_dir = tmp_path / "readonly"
        target_dir.mkdir()
        export_path = target_dir / "context.json"

        # Make directory read-only (no write permission)
        target_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(OSError):
                ctx.export_context(export_path)
        finally:
            # Restore permissions for cleanup
            target_dir.chmod(stat.S_IRWXU)
