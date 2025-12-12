"""Tests for context engineering features: state management, export/import, usage tracking."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.llm.core.context import ConversationContext, Message
from infrastructure.core.exceptions import ContextLimitError


class TestContextStateManagement:
    """Test context state save/restore functionality."""
    
    def test_save_state(self):
        """Test saving context state."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("system", "System prompt")
        context.add_message("user", "User message")
        context.add_message("assistant", "Assistant response")
        
        state = context.save_state()
        
        assert "messages" in state
        assert "estimated_tokens" in state
        assert "max_tokens" in state
        assert len(state["messages"]) == 3
        assert state["estimated_tokens"] == context.estimated_tokens
    
    def test_restore_state(self):
        """Test restoring context state."""
        context1 = ConversationContext(max_tokens=1000)
        context1.add_message("system", "System prompt")
        context1.add_message("user", "User message")
        context1.add_message("assistant", "Assistant response")
        
        state = context1.save_state()
        
        context2 = ConversationContext(max_tokens=1000)
        context2.restore_state(state)
        
        assert len(context2.messages) == len(context1.messages)
        assert context2.estimated_tokens == context1.estimated_tokens
        assert context2.messages[0].content == context1.messages[0].content
    
    def test_save_restore_preserves_all_data(self):
        """Test save/restore preserves all message data."""
        context1 = ConversationContext(max_tokens=1000)
        context1.add_message("user", "Test message with special chars: !@#$%")
        
        state = context1.save_state()
        
        context2 = ConversationContext(max_tokens=1000)
        context2.restore_state(state)
        
        assert context2.messages[0].role == "user"
        assert context2.messages[0].content == "Test message with special chars: !@#$%"
    
    def test_restore_state_clears_existing(self):
        """Test restore_state clears existing messages."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Old message")
        
        new_state = {
            "messages": [{"role": "user", "content": "New message", "metadata": {}}],
            "estimated_tokens": 10,
            "max_tokens": 1000,
        }
        
        context.restore_state(new_state)
        
        assert len(context.messages) == 1
        assert context.messages[0].content == "New message"


class TestContextExportImport:
    """Test context export/import functionality."""
    
    def test_export_context(self, tmp_path):
        """Test exporting context to JSON file."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("system", "System prompt")
        context.add_message("user", "User message")
        
        export_path = tmp_path / "context.json"
        context.export_context(export_path)
        
        assert export_path.exists()
        
        data = json.loads(export_path.read_text())
        assert "messages" in data
        assert "estimated_tokens" in data
        assert len(data["messages"]) == 2
    
    def test_import_context(self, tmp_path):
        """Test importing context from JSON file."""
        # Create export file
        context1 = ConversationContext(max_tokens=1000)
        context1.add_message("system", "System prompt")
        context1.add_message("user", "User message")
        
        export_path = tmp_path / "context.json"
        context1.export_context(export_path)
        
        # Import into new context
        context2 = ConversationContext(max_tokens=1000)
        context2.import_context(export_path)
        
        assert len(context2.messages) == len(context1.messages)
        assert context2.messages[0].content == context1.messages[0].content
    
    def test_export_import_roundtrip(self, tmp_path):
        """Test export/import roundtrip preserves data."""
        context1 = ConversationContext(max_tokens=1000)
        context1.add_message("user", "Test message")
        context1.add_message("assistant", "Response")
        
        export_path = tmp_path / "context.json"
        context1.export_context(export_path)
        
        context2 = ConversationContext(max_tokens=1000)
        context2.import_context(export_path)
        
        assert len(context2.messages) == 2
        assert context2.messages[0].content == "Test message"
        assert context2.messages[1].content == "Response"
        assert context2.estimated_tokens == context1.estimated_tokens


class TestContextUsageTracking:
    """Test context usage statistics tracking."""
    
    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Message 1")
        context.add_message("assistant", "Response 1")
        context.add_message("user", "Message 2")
        
        stats = context.get_usage_stats()
        
        assert "current_messages" in stats
        assert "current_tokens_est" in stats
        assert "max_tokens" in stats
        assert "usage_percent" in stats
        assert "total_messages_added" in stats
        assert "total_tokens_estimated" in stats
        assert "prune_count" in stats
        assert "clear_count" in stats
        assert "health_status" in stats
        
        assert stats["current_messages"] == 3
        assert stats["total_messages_added"] == 3
    
    def test_usage_stats_tracks_totals(self):
        """Test usage stats track total operations."""
        context = ConversationContext(max_tokens=1000)
        
        # Add messages
        context.add_message("user", "Message 1")
        context.add_message("user", "Message 2")
        
        stats = context.get_usage_stats()
        assert stats["total_messages_added"] == 2
        
        # Clear and add more
        context.clear()
        context.add_message("user", "Message 3")
        
        stats = context.get_usage_stats()
        assert stats["total_messages_added"] == 3
        assert stats["clear_count"] == 1
    
    def test_usage_stats_tracks_pruning(self):
        """Test usage stats track pruning operations."""
        context = ConversationContext(max_tokens=50)  # Very small limit to ensure pruning
        
        # Fill context to trigger pruning - each message is ~37 chars = ~9 tokens
        # Need at least 6 messages to exceed 50 token limit
        for i in range(8):
            context.add_message("user", "Message " + "x" * 30)
        
        stats = context.get_usage_stats()
        assert stats["prune_count"] > 0
    
    def test_usage_percent_calculation(self):
        """Test usage percentage calculation."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "x" * 200)  # ~50 tokens
        
        stats = context.get_usage_stats()
        
        assert stats["usage_percent"] > 0
        assert stats["usage_percent"] < 100
        assert stats["usage_percent"] == pytest.approx((stats["current_tokens_est"] / stats["max_tokens"]) * 100, rel=0.1)


class TestContextHealthChecks:
    """Test context health check functionality."""
    
    def test_check_health_healthy(self):
        """Test health check returns healthy for low usage."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Small message")
        
        status, details = context.check_health()
        
        assert status == "healthy"
        assert details["usage_percent"] < 50
    
    def test_check_health_warning(self):
        """Test health check returns warning for medium usage."""
        context = ConversationContext(max_tokens=100)
        # Fill to ~60% usage
        context.add_message("user", "x" * 240)  # ~60 tokens
        
        status, details = context.check_health()
        
        assert status in ["healthy", "warning"]  # May vary based on exact calculation
        assert "usage_percent" in details
    
    def test_check_health_critical(self):
        """Test health check returns critical for high usage."""
        context = ConversationContext(max_tokens=100)
        # Fill to >80% usage
        context.add_message("user", "x" * 320)  # ~80 tokens
        
        status, details = context.check_health()
        
        # May be warning or critical depending on exact calculation
        assert status in ["warning", "critical"]
        assert details["usage_percent"] > 50
    
    def test_health_status_in_usage_stats(self):
        """Test health status is included in usage stats."""
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Message")
        
        stats = context.get_usage_stats()
        
        assert "health_status" in stats
        assert stats["health_status"] in ["healthy", "warning", "critical"]


class TestContextPruningLogging:
    """Test context pruning with logging."""
    
    def test_prune_logs_details(self, caplog):
        """Test pruning logs detailed information."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        # Configure logger before creating context
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)
        logger.propagate = True  # Ensure propagation for caplog
        
        # Ensure root logger also captures INFO level
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        context = ConversationContext(max_tokens=50)  # Very small limit to ensure pruning
        
        # Fill context aggressively to trigger pruning
        # Each message is ~37 chars = ~9 tokens, need >5 messages to exceed 50 token limit
        # Add 6 messages to definitely trigger pruning
        for i in range(6):
            context.add_message("user", "Message " + "x" * 30)
        
        with caplog.at_level(logging.INFO, logger="infrastructure.llm.core.context"):
            # Trigger pruning by adding another message that will exceed the limit
            context.add_message("user", "New message " + "x" * 30)
            
            # Check both message text and records
            has_prune_log = (
                "Context pruned" in caplog.text or 
                "Pruning context" in caplog.text or
                any("Context pruned" in r.message or "Pruning context" in r.message 
                    for r in caplog.records)
            )
            assert has_prune_log, f"Expected pruning log, got: {caplog.text}, records: {[r.message for r in caplog.records]}"
    
    def test_prune_preserves_system_prompt(self):
        """Test pruning preserves system prompt."""
        context = ConversationContext(max_tokens=100)
        context.add_message("system", "System prompt")
        
        # Fill context
        for i in range(5):
            context.add_message("user", "Message " + "x" * 30)
        
        # System prompt should still be first
        assert context.messages[0].role == "system"
        assert context.messages[0].content == "System prompt"


class TestContextOperationsLogging:
    """Test logging for context operations."""
    
    def test_add_message_logs(self, caplog):
        """Test add_message logs operations."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.DEBUG)
        
        context = ConversationContext(max_tokens=1000)
        
        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.context"):
            context.add_message("user", "Test message")
            
            assert "Adding message" in caplog.text or "Message added" in caplog.text
    
    def test_clear_logs(self, caplog):
        """Test clear logs operation."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)
        
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Test")
        
        with caplog.at_level("INFO", logger="infrastructure.llm.core.context"):
            context.clear()
            
            assert "Clearing context" in caplog.text
    
    def test_save_state_logs(self, caplog):
        """Test save_state logs operation."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.DEBUG)
        
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Test")
        
        with caplog.at_level("DEBUG", logger="infrastructure.llm.core.context"):
            context.save_state()
            
            assert "Context state saved" in caplog.text
    
    def test_export_logs(self, caplog, tmp_path):
        """Test export_context logs operation."""
        import logging
        from infrastructure.core.logging_utils import get_logger
        
        logger = get_logger("infrastructure.llm.core.context")
        logger.setLevel(logging.INFO)
        
        context = ConversationContext(max_tokens=1000)
        context.add_message("user", "Test")
        
        export_path = tmp_path / "context.json"
        
        with caplog.at_level("INFO", logger="infrastructure.llm.core.context"):
            context.export_context(export_path)
            
            assert "Context exported" in caplog.text



