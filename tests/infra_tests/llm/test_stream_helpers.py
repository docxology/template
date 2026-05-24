"""Tests for infrastructure.llm.core._stream_helpers — comprehensive coverage."""

from infrastructure.llm.core._stream_helpers import (
    TIMEOUT_WARNING_FRACTION,
    save_partial_if_needed,
)


class TestSavePartialIfNeeded:
    def test_empty_response_noop(self):
        result = save_partial_if_needed(
            full_response=[],
            save_response=True,
            partial_saved=False,
            save_fn=lambda *a, **kw: True,
            chunk_count=0,
            context="test",
        )
        assert result is False

    def test_save_response_false_noop(self):
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=False,
            partial_saved=False,
            save_fn=lambda *a, **kw: True,
            chunk_count=1,
            context="test",
        )
        assert result is False

    def test_already_saved_skip(self):
        called = []
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_fn=lambda *a, **kw: (called.append(1), True)[-1],
            chunk_count=1,
            context="test",
            skip_if_already_saved=True,
        )
        assert result is True
        assert len(called) == 0  # save_fn NOT called

    def test_already_saved_no_skip(self):
        called = []
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=True,
            save_fn=lambda *a, **kw: (called.append(1), True)[-1],
            chunk_count=1,
            context="test",
            skip_if_already_saved=False,
        )
        assert result is True
        assert len(called) == 1  # save_fn WAS called

    def test_successful_save(self):
        result = save_partial_if_needed(
            full_response=["chunk1", "chunk2"],
            save_response=True,
            partial_saved=False,
            save_fn=lambda *a, **kw: True,
            chunk_count=2,
            context="during streaming",
        )
        assert result is True

    def test_failed_save(self):
        result = save_partial_if_needed(
            full_response=["chunk1"],
            save_response=True,
            partial_saved=False,
            save_fn=lambda *a, **kw: False,
            chunk_count=1,
            context="test",
        )
        assert result is False


class TestTimeoutWarningFraction:
    def test_constant_value(self):
        assert TIMEOUT_WARNING_FRACTION == 0.3
        assert 0 < TIMEOUT_WARNING_FRACTION < 1
