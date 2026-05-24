"""Tests for infrastructure.llm.core._stream_helpers module.

Tests save_partial_if_needed using real function calls (No Mocks Policy).
stream_query_impl requires a live Ollama server and is tested via integration
tests; this file targets the unit-testable pure logic.
"""

from __future__ import annotations

from infrastructure.llm.core._stream_helpers import save_partial_if_needed


def _noop_save(*args, **kwargs) -> bool:
    """Save function that always succeeds."""
    return True


def _failing_save(*args, **kwargs) -> bool:
    """Save function that always fails."""
    return False


class TestSavePartialIfNeeded:
    """Tests for save_partial_if_needed."""

    def test_returns_false_when_no_full_response(self):
        """Returns existing partial_saved when full_response is empty."""
        result = save_partial_if_needed(
            full_response=[],
            save_response=True,
            partial_saved=False,
            save_fn=_noop_save,
            chunk_count=0,
            context="test",
        )
        assert result is False

    def test_returns_false_when_save_response_is_false(self):
        """Returns existing partial_saved when save_response is False."""
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=False,
            partial_saved=False,
            save_fn=_noop_save,
            chunk_count=1,
            context="test",
        )
        assert result is False

    def test_skips_when_already_saved_and_skip_flag_set(self):
        """Returns existing partial_saved=True when skip_if_already_saved is True."""
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_fn=_noop_save,
            chunk_count=1,
            context="test",
            skip_if_already_saved=True,
        )
        assert result is True

    def test_saves_when_already_saved_and_skip_flag_false(self):
        """Calls save function when skip_if_already_saved is False, even if already saved."""
        calls = []

        def tracking_save(*args, **kwargs) -> bool:
            calls.append(args)
            return True

        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_fn=tracking_save,
            chunk_count=1,
            context="ctx",
            skip_if_already_saved=False,
        )
        assert result is True
        assert len(calls) == 1

    def test_returns_true_on_successful_save(self):
        """Returns True when save function succeeds."""
        result = save_partial_if_needed(
            full_response=["chunk1", "chunk2"],
            save_response=True,
            partial_saved=False,
            save_fn=_noop_save,
            chunk_count=2,
            context="ctx",
        )
        assert result is True

    def test_returns_false_when_save_function_fails(self):
        """Returns existing partial_saved when save function returns False."""
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=False,
            save_fn=_failing_save,
            chunk_count=1,
            context="ctx",
        )
        assert result is False

    def test_passes_correct_args_to_save_function(self):
        """Save function receives full_response, chunk_count, and is_error."""
        received = {}

        def capture_save(full_response, chunk_count, is_error=False) -> bool:
            received["full_response"] = full_response
            received["chunk_count"] = chunk_count
            received["is_error"] = is_error
            return True

        save_partial_if_needed(
            full_response=["a", "b"],
            save_response=True,
            partial_saved=False,
            save_fn=capture_save,
            chunk_count=42,
            context="error recovery",
        )
        assert received["full_response"] == ["a", "b"]
        assert received["chunk_count"] == 42
        assert received["is_error"] is True

    def test_empty_full_response_list_returns_existing_state(self):
        """Empty list treated as no response — returns existing partial_saved value."""
        result = save_partial_if_needed(
            full_response=[],
            save_response=True,
            partial_saved=True,
            save_fn=_noop_save,
            chunk_count=0,
            context="ctx",
        )
        assert result is True
