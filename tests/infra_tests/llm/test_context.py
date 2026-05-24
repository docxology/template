"""Tests for infrastructure.llm.core.context."""

from __future__ import annotations

import os
import stat

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
    def test_add_message(self):
        ctx = ConversationContext(max_tokens=100)
        ctx.add_message("user", "Hello")
        assert len(ctx.messages) == 1
        assert ctx.estimated_tokens > 0

    def test_add_and_get_messages(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there")
        msgs = ctx.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_prune_context(self):
        ctx = ConversationContext(max_tokens=2)
        ctx.add_message("user", "1234")
        assert len(ctx.messages) == 1
        ctx.add_message("assistant", "5678")
        assert len(ctx.messages) == 2
        ctx.add_message("user", "9012")
        assert len(ctx.messages) == 2
        assert ctx.messages[0].content == "5678"
        assert ctx.messages[1].content == "9012"

    def test_prune_on_overflow(self):
        ctx = ConversationContext(max_tokens=50)
        ctx.add_message("user", "A" * 120)
        ctx.add_message("user", "B" * 120)
        assert ctx._prune_count >= 1

    def test_system_prompt_preservation(self):
        ctx = ConversationContext(max_tokens=10)
        ctx.add_message("system", "1234")
        ctx.add_message("user", "12341234")
        ctx.add_message("asst", "12341234")
        ctx.add_message("user", "1234" * 6)
        assert ctx.messages[0].role == "system"
        assert ctx.messages[-1].content == "1234" * 6

    def test_prune_preserves_system_messages(self):
        ctx = ConversationContext(max_tokens=100)
        ctx.add_message("system", "You are helpful")
        ctx.add_message("user", "A" * 200)
        ctx.add_message("user", "B" * 200)
        roles = [m.role for m in ctx.messages]
        assert "system" in roles

    def test_context_limit_error(self):
        ctx = ConversationContext(max_tokens=1)
        with pytest.raises(ContextLimitError):
            ctx.add_message("user", "12341234")

    def test_context_limit_error_oversized_single_message(self):
        ctx = ConversationContext(max_tokens=10)
        with pytest.raises(ContextLimitError):
            ctx.add_message("user", "X" * 1000)

    def test_clear(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "test")
        ctx.clear()
        assert ctx.get_messages() == []
        assert ctx.estimated_tokens == 0
        assert ctx._clear_count == 1

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

    def test_restore_empty_state(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "something")
        ctx.restore_state({"messages": [], "estimated_tokens": 0})
        assert ctx.get_messages() == []

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

    def test_export_context_oserror_cleans_tmp(self, tmp_path):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "test")

        target_dir = tmp_path / "readonly"
        target_dir.mkdir()
        export_path = target_dir / "context.json"
        target_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(OSError):
                ctx.export_context(export_path)
        finally:
            target_dir.chmod(stat.S_IRWXU)

    def test_get_usage_stats(self):
        ctx = ConversationContext(max_tokens=10000)
        ctx.add_message("user", "Hello world")
        stats = ctx.get_usage_stats()
        assert stats["current_messages"] == 1
        assert stats["max_tokens"] == 10000
        assert stats["total_messages_added"] == 1
        assert stats["health_status"] == "healthy"

    @pytest.mark.parametrize(
        ("message_chars", "expected_status"),
        [
            (0, "healthy"),
            (240, "warning"),
            (320, "critical"),
        ],
    )
    def test_check_health_status(self, message_chars, expected_status):
        ctx = ConversationContext(max_tokens=100)
        if message_chars:
            ctx.add_message("user", "A" * message_chars)
        status, _stats = ctx.check_health()
        assert status == expected_status

    def test_large_context_buffer_factor(self):
        ctx = ConversationContext(max_tokens=65536)
        ctx.add_message("system", "You are helpful")
        ctx.add_message("user", "A" * (65536 * 4))
        assert len(ctx.messages) >= 1
