"""Tests for infrastructure.core.progress — ProgressBar, LLMProgressTracker, SubStageProgress."""

import time

from infrastructure.core.progress import (
    LLMProgressTracker,
    ProgressBar,
    SubStageProgress,
)


class TestProgressBar:
    def test_init_defaults(self):
        bar = ProgressBar(total=100)
        assert bar.total == 100
        assert bar.current == 0
        assert bar.show_eta is True
        assert bar.use_ema is True

    def test_init_custom(self):
        bar = ProgressBar(total=50, task="Rendering", width=20, show_eta=False, use_ema=False)
        assert bar.total == 50
        assert bar.task == "Rendering"
        assert bar.width == 20
        assert bar.show_eta is False

    def test_update(self):
        bar = ProgressBar(total=10, update_interval=0.0)
        bar.update(5, force=True)
        assert bar.current == 5

    def test_update_clamps_to_total(self):
        bar = ProgressBar(total=10)
        bar.update(20, force=True)
        assert bar.current == 10

    def test_update_throttled(self):
        bar = ProgressBar(total=10, update_interval=999.0)
        bar.update(1)
        # Should not render due to throttle (unless force)

    def test_render_zero_total(self):
        bar = ProgressBar(total=0)
        bar.update(0, force=True)
        # Should not crash with division by zero

    def test_render_with_ema(self):
        bar = ProgressBar(total=10, use_ema=True, update_interval=0.0)
        bar.start_time = time.time() - 5.0  # Pretend 5s elapsed
        bar.update(5, force=True)
        # Should compute ETA via EMA path

    def test_render_with_linear_eta(self):
        bar = ProgressBar(total=10, use_ema=False, update_interval=0.0)
        bar.start_time = time.time() - 5.0
        bar.update(5, force=True)

    def test_render_ema_second_update(self):
        bar = ProgressBar(total=10, use_ema=True, update_interval=0.0)
        bar.start_time = time.time() - 2.0
        bar.update(2, force=True)
        bar.start_time = time.time() - 5.0
        bar.update(5, force=True)
        # previous_eta should have been updated through EMA

    def test_finish(self):
        bar = ProgressBar(total=10, task="Building", update_interval=0.0)
        bar.update(10, force=True)
        bar.finish()

    def test_finish_no_task(self):
        bar = ProgressBar(total=10, update_interval=0.0)
        bar.update(10, force=True)
        bar.finish()


class TestLLMProgressTracker:
    def test_init_defaults(self):
        t = LLMProgressTracker()
        assert t.total_tokens is None
        assert t.task == "LLM Generation"
        assert t.generated_tokens == 0
        assert t.chunks_received == 0

    def test_init_custom(self):
        t = LLMProgressTracker(total_tokens=1000, task="Review", show_throughput=False)
        assert t.total_tokens == 1000
        assert t.show_throughput is False

    def test_update_tokens(self):
        t = LLMProgressTracker(total_tokens=100)
        t.update_tokens(10)
        assert t.generated_tokens == 10
        assert t.chunks_received == 1

    def test_update_tokens_multiple(self):
        t = LLMProgressTracker(total_tokens=100)
        t.last_update_time = 0  # Force display
        t.update_tokens(30)
        t.last_update_time = 0
        t.update_tokens(40)
        assert t.generated_tokens == 70
        assert t.chunks_received == 2

    def test_update_tokens_no_total(self):
        t = LLMProgressTracker()
        t.last_update_time = 0
        t.update_tokens(50)
        assert t.generated_tokens == 50

    def test_display_with_total(self):
        t = LLMProgressTracker(total_tokens=100)
        # Just test that _display doesn't crash
        t.generated_tokens = 50
        t._display(25.0)

    def test_display_without_total(self):
        t = LLMProgressTracker()
        t.generated_tokens = 50
        t._display(25.0)

    def test_display_zero_throughput(self):
        t = LLMProgressTracker(total_tokens=100)
        t.generated_tokens = 0
        t._display(0.0)

    def test_finish(self):
        t = LLMProgressTracker(total_tokens=100)
        t.generated_tokens = 100
        t.finish()


class TestSubStageProgress:
    def test_init_defaults(self):
        sp = SubStageProgress(total=5)
        assert sp.total == 5
        assert sp.current == 0
        assert sp.stage_name == ""
        assert sp.use_ema is True
        assert sp.substage_durations == []

    def test_start_substage(self):
        sp = SubStageProgress(total=3, stage_name="Render")
        sp.start_substage(1, "file1.md")
        assert sp.current == 1
        assert sp.current_substage_name == "file1.md"
        assert sp.substage_start_time is not None

    def test_start_substage_no_name(self):
        sp = SubStageProgress(total=3)
        sp.start_substage(1)
        assert sp.current == 1

    def test_complete_substage(self):
        sp = SubStageProgress(total=3)
        sp.start_substage(1, "step1")
        sp.complete_substage()
        assert len(sp.substage_durations) == 1
        assert sp.substage_durations[0] >= 0.0

    def test_complete_substage_without_start(self):
        sp = SubStageProgress(total=3)
        sp.complete_substage()  # substage_start_time is None, should be no-op
        assert len(sp.substage_durations) == 0

    def test_get_eta_at_zero(self):
        sp = SubStageProgress(total=5)
        assert sp.get_eta() is None

    def test_get_eta_with_ema(self):
        sp = SubStageProgress(total=10, use_ema=True)
        sp.start_time = time.time() - 5.0  # 5s elapsed
        sp.current = 5
        eta = sp.get_eta()
        # Should return some positive value
        assert eta is not None
        assert eta >= 0

    def test_get_eta_ema_second_call(self):
        sp = SubStageProgress(total=10, use_ema=True)
        sp.start_time = time.time() - 2.0
        sp.current = 2
        eta1 = sp.get_eta()
        sp.start_time = time.time() - 5.0
        sp.current = 5
        eta2 = sp.get_eta()
        assert eta1 is not None
        assert eta2 is not None

    def test_get_eta_linear(self):
        sp = SubStageProgress(total=10, use_ema=False)
        sp.start_time = time.time() - 5.0
        sp.current = 5
        eta = sp.get_eta()
        assert eta is not None

    def test_get_eta_with_confidence(self):
        sp = SubStageProgress(total=5)
        sp.start_time = time.time() - 3.0
        sp.current = 3
        sp.substage_durations = [0.9, 1.0, 1.1]
        estimate = sp.get_eta_with_confidence()
        # Should return an ETAEstimate
        assert hasattr(estimate, "optimistic")
        assert hasattr(estimate, "realistic")
        assert hasattr(estimate, "pessimistic")

    def test_get_eta_with_confidence_at_zero(self):
        sp = SubStageProgress(total=5)
        estimate = sp.get_eta_with_confidence()
        assert estimate.optimistic is None
        assert estimate.realistic is None
        assert estimate.pessimistic is None

    def test_log_progress(self):
        sp = SubStageProgress(total=5, stage_name="Build")
        sp.start_time = time.time() - 2.0
        sp.current = 2
        sp.log_progress()  # Should not crash

    def test_log_progress_zero_total(self):
        sp = SubStageProgress(total=0)
        sp.log_progress()
