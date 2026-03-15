"""Tests for infrastructure.llm.core._client_streaming module.

Tests the _try_save_partial helper using real function calls (No Mocks Policy).
stream_query_impl requires a live Ollama server and is tested via integration
tests; this file targets the unit-testable pure logic.
"""

from __future__ import annotations

from infrastructure.llm.core._client_streaming import _try_save_partial


def _noop_save(*args, **kwargs) -> bool:
    """Save function that always succeeds."""
    return True


def _failing_save(*args, **kwargs) -> bool:
    """Save function that always fails."""
    return False


class TestTrySavePartial:
    """Tests for _try_save_partial."""

    def test_returns_false_when_no_full_response(self):
        """Returns existing partial_saved when full_response is empty."""
        result = _try_save_partial(
            full_response=[],
            save_response=True,
            partial_saved=False,
            save_streaming_state_fn=_noop_save,
            save_path=None,
            model_name="test",
            prompt="test",
            chunk_count=0,
            start_time=0.0,
            context="test",
        )
        assert result is False

    def test_returns_false_when_save_response_is_false(self):
        """Returns existing partial_saved when save_response is False."""
        result = _try_save_partial(
            full_response=["chunk1"],
            save_response=False,
            partial_saved=False,
            save_streaming_state_fn=_noop_save,
            save_path=None,
            model_name="test",
            prompt="test",
            chunk_count=1,
            start_time=0.0,
            context="test",
        )
        assert result is False

    def test_skips_when_already_saved_and_skip_flag_set(self):
        """Returns existing partial_saved=True when skip_if_already_saved is True."""
        result = _try_save_partial(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_streaming_state_fn=_noop_save,
            save_path=None,
            model_name="test",
            prompt="test",
            chunk_count=1,
            start_time=0.0,
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

        result = _try_save_partial(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_streaming_state_fn=tracking_save,
            save_path=None,
            model_name="model",
            prompt="prompt",
            chunk_count=1,
            start_time=0.0,
            context="ctx",
            skip_if_already_saved=False,
        )
        assert result is True
        assert len(calls) == 1

    def test_returns_true_on_successful_save(self):
        """Returns True when save function succeeds."""
        result = _try_save_partial(
            full_response=["chunk1", "chunk2"],
            save_response=True,
            partial_saved=False,
            save_streaming_state_fn=_noop_save,
            save_path=None,
            model_name="model",
            prompt="prompt",
            chunk_count=2,
            start_time=0.0,
            context="ctx",
        )
        assert result is True

    def test_returns_false_when_save_function_fails(self):
        """Returns existing partial_saved when save function returns False."""
        result = _try_save_partial(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=False,
            save_streaming_state_fn=_failing_save,
            save_path=None,
            model_name="model",
            prompt="prompt",
            chunk_count=1,
            start_time=0.0,
            context="ctx",
        )
        assert result is False

    def test_passes_correct_args_to_save_function(self):
        """Save function receives full_response, save_path, model_name, prompt, chunk_count, start_time, is_error."""
        received = {}

        def capture_save(full_response, save_path, model_name, prompt, chunk_count, start_time, is_error=False) -> bool:
            received["full_response"] = full_response
            received["model_name"] = model_name
            received["prompt"] = prompt
            received["chunk_count"] = chunk_count
            received["is_error"] = is_error
            return True

        _try_save_partial(
            full_response=["a", "b"],
            save_response=True,
            partial_saved=False,
            save_streaming_state_fn=capture_save,
            save_path=None,
            model_name="gemma3:4b",
            prompt="explain AI",
            chunk_count=42,
            start_time=1000.0,
            context="error recovery",
        )
        assert received["full_response"] == ["a", "b"]
        assert received["model_name"] == "gemma3:4b"
        assert received["prompt"] == "explain AI"
        assert received["chunk_count"] == 42
        assert received["is_error"] is True

    def test_empty_full_response_list_returns_existing_state(self):
        """Empty list treated as no response — returns existing partial_saved value."""
        result = _try_save_partial(
            full_response=[],
            save_response=True,
            partial_saved=True,
            save_streaming_state_fn=_noop_save,
            save_path=None,
            model_name="m",
            prompt="p",
            chunk_count=0,
            start_time=0.0,
            context="ctx",
        )
        assert result is True
