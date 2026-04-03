"""Tests for infrastructure.llm.core._stream_helpers — expanded coverage."""

from infrastructure.llm.core._stream_helpers import (
    save_partial_if_needed,
    try_save_partial,
    TIMEOUT_WARNING_FRACTION,
)


class TestSavePartialIfNeeded:
    def test_empty_response_no_save(self):
        result = save_partial_if_needed(
            full_response=[],
            save_response=True,
            partial_saved=False,
            save_fn=lambda *a, **kw: True,
            chunk_count=5,
            context="test",
        )
        assert result is False

    def test_save_disabled(self):
        result = save_partial_if_needed(
            full_response=["chunk"],
            save_response=False,
            partial_saved=False,
            save_fn=lambda *a, **kw: True,
            chunk_count=5,
            context="test",
        )
        assert result is False

    def test_already_saved_skipped(self):
        result = save_partial_if_needed(
            full_response=["chunk"],
            save_response=True,
            partial_saved=True,
            save_fn=lambda *a, **kw: True,
            chunk_count=5,
            context="test",
            skip_if_already_saved=True,
        )
        assert result is True  # Returns existing partial_saved

    def test_already_saved_not_skipped(self):
        calls = []

        def save_fn(resp, count, *, is_error=False):
            calls.append(1)
            return True

        result = save_partial_if_needed(
            full_response=["chunk"],
            save_response=True,
            partial_saved=True,
            save_fn=save_fn,
            chunk_count=5,
            context="test",
            skip_if_already_saved=False,
        )
        assert result is True
        assert len(calls) == 1

    def test_successful_save(self):
        result = save_partial_if_needed(
            full_response=["chunk1", "chunk2"],
            save_response=True,
            partial_saved=False,
            save_fn=lambda resp, count, *, is_error=False: True,
            chunk_count=10,
            context="during streaming",
        )
        assert result is True

    def test_failed_save(self):
        result = save_partial_if_needed(
            full_response=["chunk"],
            save_response=True,
            partial_saved=False,
            save_fn=lambda resp, count, *, is_error=False: False,
            chunk_count=5,
            context="test",
        )
        assert result is False


class TestTrySavePartial:
    def test_basic_call(self):
        calls = []

        def streaming_fn(resp, path, model, prompt, count, start, *, is_error=False):
            calls.append({
                "resp": resp, "path": path, "model": model,
                "prompt": prompt, "count": count, "start": start,
                "is_error": is_error,
            })
            return True

        result = try_save_partial(
            full_response=["data"],
            save_response=True,
            partial_saved=False,
            save_streaming_state_fn=streaming_fn,
            save_path="/tmp/test",
            model_name="llama3",
            prompt="test prompt",
            chunk_count=3,
            start_time=100.0,
            context="test context",
        )
        assert result is True
        assert len(calls) == 1
        assert calls[0]["model"] == "llama3"
        assert calls[0]["is_error"] is True

    def test_no_save_when_disabled(self):
        result = try_save_partial(
            full_response=["data"],
            save_response=False,
            partial_saved=False,
            save_streaming_state_fn=lambda *a, **kw: True,
            save_path=None,
            model_name="m",
            prompt="p",
            chunk_count=1,
            start_time=0.0,
            context="c",
        )
        assert result is False


class TestConstants:
    def test_timeout_warning_fraction(self):
        assert 0 < TIMEOUT_WARNING_FRACTION < 1
        assert TIMEOUT_WARNING_FRACTION == 0.3
