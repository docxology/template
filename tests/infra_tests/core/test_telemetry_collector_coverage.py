"""Tests for infrastructure.core.telemetry.collector — comprehensive coverage."""


from infrastructure.core.telemetry.collector import TelemetryCollector
from infrastructure.core.telemetry.config import TelemetryConfig
from infrastructure.core.telemetry.models import StageTelemetry


class TestTelemetryCollectorDisabled:
    def test_disabled_noop(self):
        config = TelemetryConfig(enabled=False)
        collector = TelemetryCollector(config, "test")
        info = collector.capture_system_info()
        assert info == {}
        collector.start_stage("stage1", 1)
        stage = collector.end_stage("stage1", 1)
        assert isinstance(stage, StageTelemetry)
        report = collector.finalize()
        assert report.project_name == "test"


class TestTelemetryCollectorEnabled:
    def test_basic_lifecycle(self, tmp_path):
        config = TelemetryConfig(
            enabled=True,
            track_resources=False,
            track_diagnostics=False,
            persist_report=False,
        )
        collector = TelemetryCollector(config, "myproject", output_dir=tmp_path)
        collector.capture_system_info()

        collector.start_stage("build", 1)
        stage = collector.end_stage("build", 1, success=True, exit_code=0)
        assert stage.stage_name == "build"
        assert stage.success is True

        collector.start_stage("test", 2)
        stage = collector.end_stage("test", 2, success=False, exit_code=1, error_message="fail")
        assert stage.success is False

        report = collector.finalize(total_duration=5.0)
        assert report.total_duration == 5.0
        assert len(report.stages) == 2

    def test_auto_total_duration(self):
        config = TelemetryConfig(
            enabled=True, track_resources=False, track_diagnostics=False, persist_report=False
        )
        collector = TelemetryCollector(config, "proj")
        collector.start_stage("s1", 1)
        collector.end_stage("s1", 1)
        report = collector.finalize()
        assert report.total_duration >= 0

    def test_detect_slow_stage_warning(self):
        config = TelemetryConfig(
            enabled=True,
            track_resources=False,
            track_diagnostics=False,
            persist_report=False,
            slow_stage_multiplier=2.0,
        )
        collector = TelemetryCollector(config, "proj")

        # Create stages with artificial durations
        from infrastructure.core.telemetry.models import StageTelemetry as ST
        collector._report.stages = [
            ST(stage_name="fast", stage_num=1, duration=1.0, success=True),
            ST(stage_name="fast2", stage_num=2, duration=1.0, success=True),
            ST(stage_name="slow", stage_num=3, duration=10.0, success=True),
        ]
        warnings = collector._detect_warnings()
        assert any(w.warning_type == "slow_stage" for w in warnings)

    def test_detect_high_memory_warning(self):
        config = TelemetryConfig(
            enabled=True, track_resources=False, persist_report=False,
            high_memory_mb=100.0,
        )
        collector = TelemetryCollector(config, "proj")

        from infrastructure.core.telemetry.models import StageTelemetry as ST
        collector._report.stages = [
            ST(stage_name="hungry", stage_num=1, duration=1.0, success=True, memory_mb=500.0),
        ]
        warnings = collector._detect_warnings()
        assert any(w.warning_type == "high_memory" for w in warnings)

    def test_detect_high_cpu_warning(self):
        config = TelemetryConfig(
            enabled=True, track_resources=False, persist_report=False,
            high_cpu_percent=50.0,
        )
        collector = TelemetryCollector(config, "proj")

        from infrastructure.core.telemetry.models import StageTelemetry as ST
        collector._report.stages = [
            ST(stage_name="hot", stage_num=1, duration=1.0, success=True, cpu_percent=95.0),
        ]
        warnings = collector._detect_warnings()
        assert any(w.warning_type == "high_cpu" for w in warnings)

    def test_no_warnings_for_empty_stages(self):
        config = TelemetryConfig(enabled=True, track_resources=False, persist_report=False)
        collector = TelemetryCollector(config, "proj")
        warnings = collector._detect_warnings()
        assert warnings == []

    def test_persist_report(self, tmp_path):
        config = TelemetryConfig(
            enabled=True,
            track_resources=False,
            track_diagnostics=False,
            persist_report=True,
            output_formats=["json", "text"],
        )
        collector = TelemetryCollector(config, "proj", output_dir=tmp_path)
        collector.start_stage("s1", 1)
        collector.end_stage("s1", 1)
        collector.finalize()

        assert (tmp_path / "reports" / "telemetry.json").exists()
        assert (tmp_path / "reports" / "telemetry.txt").exists()

    def test_format_text_report(self):
        config = TelemetryConfig(enabled=True, persist_report=False)
        collector = TelemetryCollector(config, "proj")

        from infrastructure.core.telemetry.models import StageTelemetry as ST, PerformanceWarning as PW
        collector._report.stages = [
            ST(stage_name="build", stage_num=1, duration=2.5, success=True, memory_mb=100, cpu_percent=30),
            ST(stage_name="test", stage_num=2, duration=5.0, success=False, error_message="timeout"),
        ]
        collector._report.warnings = [
            PW(warning_type="slow_stage", stage_name="test", message="Test was slow",
               suggestion="Optimize", value=5.0, threshold=3.0),
        ]
        text = collector._format_text_report()
        assert "TELEMETRY REPORT" in text
        assert "build" in text
        assert "test" in text
        assert "slow_stage" in text

    def test_report_property(self):
        config = TelemetryConfig(enabled=True, persist_report=False)
        collector = TelemetryCollector(config, "proj")
        assert collector.report.project_name == "proj"

    def test_capture_system_info_no_resource_tracking(self):
        config = TelemetryConfig(enabled=True, track_resources=False)
        collector = TelemetryCollector(config, "proj")
        info = collector.capture_system_info()
        assert info == {}
