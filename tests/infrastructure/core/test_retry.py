"""Tests for infrastructure.core.retry module.

Comprehensive tests for retry decorators and retryable operations.
"""

import time
import pytest
from unittest.mock import patch

from infrastructure.core.retry import (
    retry_with_backoff,
    retry_on_transient_failure,
    RetryableOperation,
)


class TestRetryWithBackoff:
    """Test retry_with_backoff decorator."""

    def test_retry_success_first_attempt(self):
        """Test function succeeds on first attempt."""
        @retry_with_backoff(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        
        assert result == "success"

    def test_retry_success_after_retries(self):
        """Test function succeeds after retries."""
        attempt_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def retry_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = retry_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_failure_after_max_attempts(self):
        """Test function fails after max attempts."""
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def failing_function():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            failing_function()

    def test_retry_specific_exception(self):
        """Test retry only on specific exceptions."""
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        def function_with_wrong_exception():
            raise TypeError("Wrong exception type")
        
        # Should not retry, raise immediately
        with pytest.raises(TypeError):
            function_with_wrong_exception()

    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        delays = []
        
        def record_delay(attempt, exception):
            delays.append(time.time())
        
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            exponential_base=2.0,
            on_retry=record_delay
        )
        def retry_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ValueError("Retry")
            return "success"
        
        start = time.time()
        result = retry_function()
        total_time = time.time() - start
        
        assert result == "success"
        # Should have delays between retries
        assert len(delays) == 2
        # Total time should reflect backoff
        assert total_time >= 0.1 + 0.2  # initial + exponential

    def test_retry_max_delay(self):
        """Test that delay doesn't exceed max_delay."""
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=0.5,  # Max delay less than exponential would be
            exponential_base=2.0
        )
        def retry_function():
            attempt_count[0] += 1
            if attempt_count[0] < 5:
                raise ValueError("Retry")
            return "success"
        
        start = time.time()
        result = retry_function()
        total_time = time.time() - start
        
        assert result == "success"
        # All delays should be capped at max_delay
        # Total time should be less than if exponential was used
        assert total_time < 5.0  # Would be much more with full exponential

    def test_retry_with_jitter(self):
        """Test retry with jitter."""
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            jitter=True
        )
        def retry_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"
        
        result = retry_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_without_jitter(self):
        """Test retry without jitter."""
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            jitter=False
        )
        def retry_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"
        
        result = retry_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_function_preserves_signature(self):
        """Test that retry decorator preserves function signature."""
        @retry_with_backoff()
        def function_with_args(a, b, c=3):
            return a + b + c
        
        # Should work with original signature
        result = function_with_args(1, 2, c=4)
        assert result == 7


class TestRetryOnTransientFailure:
    """Test retry_on_transient_failure decorator."""

    def test_retry_on_ioerror(self):
        """Test retry on IOError."""
        attempt_count = [0]
        
        @retry_on_transient_failure(max_attempts=3, initial_delay=0.01)
        def io_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise IOError("File locked")
            return "success"
        
        result = io_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_on_connection_error(self):
        """Test retry on ConnectionError."""
        attempt_count = [0]
        
        @retry_on_transient_failure(max_attempts=3, initial_delay=0.01)
        def network_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ConnectionError("Network issue")
            return "success"
        
        result = network_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_on_timeout_error(self):
        """Test retry on TimeoutError."""
        attempt_count = [0]
        
        @retry_on_transient_failure(max_attempts=3, initial_delay=0.01)
        def timeout_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise TimeoutError("Timeout")
            return "success"
        
        result = timeout_function()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_no_retry_on_other_exception(self):
        """Test that non-transient exceptions are not retried."""
        @retry_on_transient_failure(max_attempts=3, initial_delay=0.01)
        def function_with_wrong_exception():
            raise ValueError("Not a transient error")
        
        # Should not retry, raise immediately
        with pytest.raises(ValueError):
            function_with_wrong_exception()


class TestRetryableOperation:
    """Test RetryableOperation context manager."""

    def test_retryable_operation_success(self):
        """Test successful operation without retries."""
        with RetryableOperation(max_attempts=3) as op:
            try:
                for attempt in op:
                    op.succeed("result")
            except StopIteration:
                # succeed() raises StopIteration to exit loop - this is expected
                pass
        
        # Should have succeeded
        assert op.succeeded is True
        assert op.result == "result"

    def test_retryable_operation_retry(self):
        """Test operation that retries."""
        attempt_count = [0]
        
        with RetryableOperation(max_attempts=3, initial_delay=0.01) as op:
            try:
                for attempt in op:
                    attempt_count[0] = attempt
                    if attempt < 2:
                        op.retry(ValueError("Retry"))
                    else:
                        op.succeed("success")
            except StopIteration:
                # succeed() raises StopIteration to exit loop - this is expected
                pass
        
        assert op.succeeded is True
        assert op.result == "success"
        assert attempt_count[0] == 2

    def test_retryable_operation_failure(self):
        """Test operation that fails after max attempts."""
        with pytest.raises(ValueError, match="Always fails"):
            with RetryableOperation(max_attempts=2, initial_delay=0.01) as op:
                for attempt in op:
                    op.retry(ValueError("Always fails"))

    def test_retryable_operation_exponential_backoff(self):
        """Test exponential backoff in RetryableOperation."""
        start = time.time()
        
        with RetryableOperation(
            max_attempts=3,
            initial_delay=0.1,
            exponential_base=2.0
        ) as op:
            try:
                for attempt in op:
                    if attempt < 3:
                        op.retry(ValueError("Retry"))
                    else:
                        op.succeed("success")
            except StopIteration:
                # succeed() raises StopIteration to exit loop - this is expected
                pass
        
        elapsed = time.time() - start
        
        # Should have delays: 0.1s, 0.2s
        assert elapsed >= 0.3
        assert op.succeeded is True

    def test_retryable_operation_max_delay(self):
        """Test max delay cap in RetryableOperation."""
        start = time.time()
        
        with RetryableOperation(
            max_attempts=5,
            initial_delay=0.1,  # Reduced for faster test
            max_delay=0.05,  # Cap at 0.05s
            exponential_base=2.0
        ) as op:
            try:
                for attempt in op:
                    if attempt < 5:
                        op.retry(ValueError("Retry"))
                    else:
                        op.succeed("success")
            except StopIteration:
                # succeed() raises StopIteration to exit loop - this is expected
                pass
        
        elapsed = time.time() - start
        
        # All delays should be capped at 0.05s
        assert elapsed < 0.5  # Would be much more without cap
        assert op.succeeded is True

    def test_retryable_operation_context_exit(self):
        """Test that context manager doesn't suppress exceptions."""
        with pytest.raises(ValueError):
            with RetryableOperation(max_attempts=2, initial_delay=0.01) as op:
                for attempt in op:
                    raise ValueError("Exception")

    def test_retryable_operation_iteration(self):
        """Test iteration over attempts."""
        attempts = []
        
        with RetryableOperation(max_attempts=3, initial_delay=0.01) as op:
            try:
                for attempt in op:
                    attempts.append(attempt)
                    if attempt < 2:
                        op.retry(ValueError("Retry"))
                    else:
                        op.succeed("done")
            except StopIteration:
                # succeed() raises StopIteration to exit loop - this is expected
                pass
        
        assert attempts == [1, 2]
        assert op.succeeded is True

    def test_retry_with_backoff_custom_exception_types(self):
        """Test retry with custom exception types."""
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exceptions=(KeyError, IndexError)
        )
        def function_with_custom_exceptions():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise KeyError("Custom error")
            return "success"
        
        result = function_with_custom_exceptions()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_with_backoff_jitter_calculation(self):
        """Test that jitter adds randomness to delays."""
        delays_with_jitter = []
        delays_without_jitter = []
        
        def record_delay_with_jitter(attempt, exception):
            delays_with_jitter.append(time.time())
        
        def record_delay_without_jitter(attempt, exception):
            delays_without_jitter.append(time.time())
        
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            jitter=True,
            on_retry=record_delay_with_jitter
        )
        def function_with_jitter():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"
        
        attempt_count[0] = 0
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            jitter=False,
            on_retry=record_delay_without_jitter
        )
        def function_without_jitter():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"
        
        function_with_jitter()
        attempt_count[0] = 0
        function_without_jitter()
        
        # Both should have recorded delays
        assert len(delays_with_jitter) > 0
        assert len(delays_without_jitter) > 0

    def test_retry_with_backoff_exponential_progression(self):
        """Test exponential backoff progression."""
        delays = []
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.1,
            exponential_base=2.0,
            max_delay=10.0  # High max to see progression
        )
        def function_with_exponential():
            attempt_count[0] += 1
            if attempt_count[0] < 4:
                delays.append(time.time())
                raise ValueError("Retry")
            return "success"
        
        start = time.time()
        result = function_with_exponential()
        total_time = time.time() - start
        
        assert result == "success"
        # Should have exponential delays: 0.1, 0.2, 0.4
        assert total_time >= 0.7  # Sum of delays

    def test_retry_with_backoff_on_retry_callback(self):
        """Test on_retry callback functionality."""
        callback_calls = []
        
        def on_retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))
        
        attempt_count = [0]
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            on_retry=on_retry_callback
        )
        def function_with_callback():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry needed")
            return "success"
        
        result = function_with_callback()
        
        assert result == "success"
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == 1
        assert "Retry needed" in callback_calls[0][1]

    def test_retry_on_transient_failure_oserror(self):
        """Test retry on OSError (transient)."""
        attempt_count = [0]
        
        @retry_on_transient_failure(max_attempts=3, initial_delay=0.01)
        def function_with_oserror():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise OSError("Resource temporarily unavailable")
            return "success"
        
        result = function_with_oserror()
        
        assert result == "success"
        assert attempt_count[0] == 2

    def test_retry_on_transient_failure_retry_count_limit(self):
        """Test that retry count is limited."""
        attempt_count = [0]
        
        @retry_on_transient_failure(max_attempts=2, initial_delay=0.01)
        def function_always_fails():
            attempt_count[0] += 1
            raise IOError("Always fails")
        
        with pytest.raises(IOError, match="Always fails"):
            function_always_fails()
        
        # Should have tried max_attempts times
        assert attempt_count[0] == 2

    def test_retryable_operation_succeed_with_result(self):
        """Test succeed() method with result value."""
        with RetryableOperation(max_attempts=3) as op:
            try:
                for attempt in op:
                    op.succeed("test_result")
            except StopIteration:
                pass
        
        assert op.succeeded is True
        assert op.result == "test_result"

    def test_retryable_operation_succeed_without_result(self):
        """Test succeed() method without result value."""
        with RetryableOperation(max_attempts=3) as op:
            try:
                for attempt in op:
                    op.succeed()  # No result
            except StopIteration:
                pass
        
        assert op.succeeded is True
        assert op.result is None

    def test_retryable_operation_retry_method(self):
        """Test retry() method functionality."""
        attempt_count = [0]
        
        with RetryableOperation(max_attempts=3, initial_delay=0.01) as op:
            try:
                for attempt in op:
                    attempt_count[0] = attempt
                    if attempt < 2:
                        op.retry(ValueError(f"Attempt {attempt} failed"))
                    else:
                        op.succeed("success")
            except StopIteration:
                pass
        
        assert op.succeeded is True
        assert attempt_count[0] == 2

    def test_retryable_operation_multiple_retries(self):
        """Test multiple retry attempts."""
        attempts = []
        
        with RetryableOperation(max_attempts=5, initial_delay=0.01) as op:
            try:
                for attempt in op:
                    attempts.append(attempt)
                    if attempt < 4:
                        op.retry(ValueError("Retry"))
                    else:
                        op.succeed("success")
            except StopIteration:
                pass
        
        assert len(attempts) == 4
        assert attempts == [1, 2, 3, 4]
        assert op.succeeded is True

    def test_retryable_operation_failure_after_max_attempts(self):
        """Test failure after max attempts."""
        attempts = []
        
        with pytest.raises(ValueError, match="Final failure"):
            with RetryableOperation(max_attempts=3, initial_delay=0.01) as op:
                for attempt in op:
                    attempts.append(attempt)
                    op.retry(ValueError("Final failure"))
        
        assert len(attempts) == 3
        assert attempts == [1, 2, 3]

    def test_retryable_operation_iterator_protocol(self):
        """Test iterator protocol usage."""
        with RetryableOperation(max_attempts=3) as op:
            # Should be iterable
            assert hasattr(op, '__iter__')
            assert hasattr(op, '__next__')
            
            # Should work with next()
            iterator = iter(op)
            assert next(iterator) == 1

