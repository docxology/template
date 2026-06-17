"""Tests for infrastructure.core.logging.pipeline_logging."""

import logging
import time

import pytest

from infrastructure.core.logging.pipeline_logging import (
    log_function_call,
    log_header,
    log_live_resource_usage,
    log_operation,
    log_pipeline_stage_with_eta,
    log_progress,
    log_stage,
    log_substep,
    log_success,
    log_timing,
)


class TestLogOperation:
    def test_basic(self, caplog: pytest.LogCaptureFixture):
        """Entering the context emits a 'Starting:' line; a sub-threshold duration emits no 'Completed:'."""
        log = logging.getLogger("test_log_op")
        with caplog.at_level(logging.INFO, logger="test_log_op"):
            with log_operation("test operation", logger=log):
                pass
        assert "Starting: test operation" in caplog.text
        assert "Completed: test operation" not in caplog.text

    def test_logs_slow_operation(self, caplog: pytest.LogCaptureFixture):
        """min_duration_to_log=0 forces the 'Completed:' line to be emitted."""
        log = logging.getLogger("test_log_op_slow")
        with caplog.at_level(logging.INFO, logger="test_log_op_slow"):
            with log_operation("slow op", logger=log, min_duration_to_log=0.0):
                pass
        assert "Starting: slow op" in caplog.text
        assert "Completed: slow op" in caplog.text

    def test_does_not_log_fast_operation(self, caplog: pytest.LogCaptureFixture):
        """A high min_duration threshold suppresses the completion line."""
        log = logging.getLogger("test_log_op_fast")
        with caplog.at_level(logging.INFO, logger="test_log_op_fast"):
            with log_operation("fast op", logger=log, min_duration_to_log=999.0):
                pass
        assert "Starting: fast op" in caplog.text
        assert "Completed: fast op" not in caplog.text

    def test_log_completion_false(self, caplog: pytest.LogCaptureFixture):
        """log_completion=False suppresses the completion line even past the threshold."""
        log = logging.getLogger("test_no_completion")
        with caplog.at_level(logging.INFO, logger="test_no_completion"):
            with log_operation("op", logger=log, log_completion=False, min_duration_to_log=0.0):
                pass
        assert "Starting: op" in caplog.text
        assert "Completed: op" not in caplog.text

    def test_exception_logged(self, caplog: pytest.LogCaptureFixture):
        """A raised exception is logged as 'Failed:' at ERROR and then re-raised."""
        log = logging.getLogger("test_log_op_err")
        with caplog.at_level(logging.ERROR, logger="test_log_op_err"):
            with pytest.raises(ValueError, match="boom"):
                with log_operation("failing op", logger=log):
                    raise ValueError("boom")
        assert "Failed: failing op" in caplog.text
        assert "boom" in caplog.text

    def test_default_logger(self):
        with log_operation("default logger op"):
            pass


class TestLogTiming:
    def test_basic(self):
        log = logging.getLogger("test_timing")
        with log_timing("Test task", logger=log):
            pass

    def test_default_logger(self):
        with log_timing("Default"):
            pass


class TestLogFunctionCall:
    def test_decorator(self):
        log = logging.getLogger("test_func_call")

        @log_function_call(logger=log)
        def my_func(x):
            return x * 2

        result = my_func(5)
        assert result == 10

    def test_decorator_exception(self):
        log = logging.getLogger("test_func_call_err")

        @log_function_call(logger=log)
        def failing_func():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError, match="fail"):
            failing_func()

    def test_default_logger(self):
        @log_function_call()
        def add(a, b):
            return a + b

        assert add(1, 2) == 3


class TestLogSuccess:
    def test_with_logger(self):
        log = logging.getLogger("test_success")
        log_success("Task done", logger=log)

    def test_default_logger(self):
        log_success("Done")


class TestLogHeader:
    def test_with_logger(self):
        log = logging.getLogger("test_header")
        log_header("Section Title", logger=log)

    def test_default_logger(self):
        log_header("Title")


class TestLogProgress:
    def test_basic(self):
        log = logging.getLogger("test_progress")
        log_progress(5, 10, "Processing", logger=log)

    def test_zero_total(self):
        log = logging.getLogger("test_progress_z")
        log_progress(0, 0, "Empty", logger=log)

    def test_default_logger(self):
        log_progress(1, 5, "Working")


class TestLogStage:
    def test_basic(self):
        log = logging.getLogger("test_stage")
        log_stage(1, 5, "Build", logger=log)

    def test_default_logger(self):
        log_stage(2, 10, "Test")


class TestLogSubstep:
    def test_basic(self):
        log = logging.getLogger("test_substep")
        log_substep("Running analysis", logger=log)

    def test_default_logger(self):
        log_substep("Step detail")


class TestLogPipelineStageWithEta:
    def test_without_pipeline_start(self):
        log = logging.getLogger("test_stage_eta")
        log_pipeline_stage_with_eta(3, 10, "Build", logger=log)

    def test_with_pipeline_start(self):
        log = logging.getLogger("test_stage_eta2")
        pipeline_start = time.time() - 10.0
        log_pipeline_stage_with_eta(5, 10, "Test", pipeline_start=pipeline_start, logger=log)

    def test_at_stage_zero(self):
        log = logging.getLogger("test_stage_eta0")
        log_pipeline_stage_with_eta(0, 10, "Init", pipeline_start=time.time(), logger=log)

    def test_default_logger(self):
        log_pipeline_stage_with_eta(1, 5, "Setup")


class TestLogLiveResourceUsage:
    def test_basic(self):
        log = logging.getLogger("test_resource")
        log_live_resource_usage(stage_name="build", logger=log)

    def test_no_stage_name(self):
        log = logging.getLogger("test_resource2")
        log_live_resource_usage(logger=log)

    def test_default_logger(self):
        log_live_resource_usage()
