"""Tests for the unified telemetry module.

All tests use real objects — zero mocks, in compliance with the
Zero-Mock policy.
"""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.logging.diagnostic import (
    DiagnosticReporter,
)
from infrastructure.core.telemetry.collector import TelemetryCollector
from infrastructure.core.telemetry.config import TelemetryConfig
from infrastructure.core.telemetry.models import (
    PerformanceWarning,
    PipelineTelemetry,
    StageTelemetry,
)


# ── TelemetryConfig ─────────────────────────────────────────────────


class TestTelemetryConfig:
    """Test TelemetryConfig construction and serialization."""

    def test_defaults(self) -> None:
        config = TelemetryConfig()
        assert config.enabled is True
        assert config.track_resources is True
        assert config.track_diagnostics is True
        assert "json" in config.output_formats
        assert config.slow_stage_multiplier == 2.0

    def test_from_dict(self) -> None:
        data = {"enabled": False, "high_memory_mb": 512.0, "unknown_key": "ignored"}
        config = TelemetryConfig.from_dict(data)
        assert config.enabled is False
        assert config.high_memory_mb == 512.0
        # unknown keys silently ignored
        assert not hasattr(config, "unknown_key")

    def test_to_dict_roundtrip(self) -> None:
        config = TelemetryConfig(enabled=True, slow_stage_multiplier=3.0)
        d = config.to_dict()
        assert d["slow_stage_multiplier"] == 3.0
        restored = TelemetryConfig.from_dict(d)
        assert restored.slow_stage_multiplier == 3.0

    def test_from_empty_dict(self) -> None:
        config = TelemetryConfig.from_dict({})
        assert config.enabled is True  # all defaults


# ── StageTelemetry ──────────────────────────────────────────────────


class TestStageTelemetry:
    """Test StageTelemetry dataclass and serialization."""

    def test_to_dict(self) -> None:
        s = StageTelemetry(
            stage_name="PDF Rendering", stage_num=5, duration=12.345, success=True
        )
        d = s.to_dict()
        assert d["stage_name"] == "PDF Rendering"
        assert d["duration"] == 12.345
        assert d["success"] is True

    def test_defaults(self) -> None:
        s = StageTelemetry(stage_name="Test")
        assert s.exit_code == 0
        assert s.memory_mb == 0.0
        assert s.diagnostic_errors == 0


# ── PipelineTelemetry ───────────────────────────────────────────────


class TestPipelineTelemetry:
    """Test PipelineTelemetry report dataclass."""

    def test_properties(self) -> None:
        report = PipelineTelemetry(
            project_name="test_project",
            total_duration=100.0,
            stages=[
                StageTelemetry(stage_name="A", stage_num=1, duration=30.0, success=True),
                StageTelemetry(stage_name="B", stage_num=2, duration=70.0, success=False),
            ],
        )
        assert report.total_stages == 2
        assert len(report.failed_stages) == 1
        assert report.failed_stages[0].stage_name == "B"
        assert report.slowest_stage is not None
        assert report.slowest_stage.stage_name == "A"  # only successful

    def test_to_dict(self) -> None:
        report = PipelineTelemetry(project_name="p")
        d = report.to_dict()
        assert d["project_name"] == "p"
        assert "stages" in d
        assert "warnings" in d

    def test_slowest_stage_empty(self) -> None:
        report = PipelineTelemetry(project_name="empty")
        assert report.slowest_stage is None


# ── PerformanceWarning ──────────────────────────────────────────────


class TestPerformanceWarning:
    """Test PerformanceWarning serialization."""

    def test_to_dict(self) -> None:
        w = PerformanceWarning(
            warning_type="slow_stage",
            stage_name="Analysis",
            message="Slow",
            value=60.0,
            threshold=30.0,
        )
        d = w.to_dict()
        assert d["warning_type"] == "slow_stage"
        assert d["value"] == 60.0


# ── TelemetryCollector ──────────────────────────────────────────────


class TestTelemetryCollector:
    """Test TelemetryCollector lifecycle and reporting."""

    def test_basic_lifecycle(self, tmp_path: Path) -> None:
        """Test start → end → finalize produces a valid report."""
        config = TelemetryConfig(enabled=True, track_resources=False)
        collector = TelemetryCollector(
            config=config, project_name="test", output_dir=tmp_path
        )

        collector.start_stage("Stage A", stage_num=1)
        result_a = collector.end_stage("Stage A", stage_num=1, success=True)
        assert result_a.success is True

        collector.start_stage("Stage B", stage_num=2)
        result_b = collector.end_stage(
            "Stage B", stage_num=2, success=False, exit_code=1, error_message="boom"
        )
        assert result_b.success is False
        assert result_b.error_message == "boom"

        report = collector.finalize(total_duration=5.0)
        assert report.total_stages == 2
        assert report.total_duration == 5.0
        assert len(report.failed_stages) == 1

    def test_json_persistence(self, tmp_path: Path) -> None:
        """Test that finalize writes telemetry.json."""
        config = TelemetryConfig(
            enabled=True, track_resources=False, output_formats=["json"]
        )
        collector = TelemetryCollector(
            config=config, project_name="persist_test", output_dir=tmp_path
        )

        collector.start_stage("S1", 1)
        collector.end_stage("S1", 1, success=True)
        collector.finalize(total_duration=1.0)

        report_file = tmp_path / "reports" / "telemetry.json"
        assert report_file.exists()
        data = json.loads(report_file.read_text())
        assert data["project_name"] == "persist_test"
        assert len(data["stages"]) == 1

    def test_text_persistence(self, tmp_path: Path) -> None:
        """Test that finalize writes telemetry.txt."""
        config = TelemetryConfig(
            enabled=True, track_resources=False, output_formats=["json", "text"]
        )
        collector = TelemetryCollector(
            config=config, project_name="text_test", output_dir=tmp_path
        )

        collector.start_stage("S1", 1)
        collector.end_stage("S1", 1, success=True)
        collector.finalize(total_duration=1.0)

        text_file = tmp_path / "reports" / "telemetry.txt"
        assert text_file.exists()
        content = text_file.read_text()
        assert "TELEMETRY REPORT" in content
        assert "text_test" in content

    def test_disabled_noop(self, tmp_path: Path) -> None:
        """When disabled, collector produces empty report and no files."""
        config = TelemetryConfig(enabled=False)
        collector = TelemetryCollector(
            config=config, project_name="disabled", output_dir=tmp_path
        )

        collector.start_stage("X", 1)
        collector.end_stage("X", 1, success=True)
        report = collector.finalize()

        assert report.total_stages == 0  # nothing collected
        assert not (tmp_path / "reports" / "telemetry.json").exists()

    def test_diagnostic_integration(self, tmp_path: Path) -> None:
        """Test that diagnostic events are counted per-stage."""
        reporter = DiagnosticReporter(project_name="diag_test")
        config = TelemetryConfig(
            enabled=True, track_resources=False, track_diagnostics=True
        )
        collector = TelemetryCollector(
            config=config,
            project_name="diag_test",
            output_dir=tmp_path,
            diagnostic_reporter=reporter,
        )

        collector.start_stage("Validate", 1)

        # Simulate diagnostics recorded during this stage
        reporter.record_error("Links", "Broken link: foo.md")
        reporter.record_warning("Links", "Redirect: bar.md")
        reporter.record_warning("Links", "Redirect: baz.md")

        result = collector.end_stage("Validate", 1, success=True)
        assert result.diagnostic_errors == 1
        assert result.diagnostic_warnings == 2

    def test_slow_stage_warning(self, tmp_path: Path) -> None:
        """Test that slow stage detection produces a warning."""
        config = TelemetryConfig(
            enabled=True, track_resources=False, slow_stage_multiplier=1.5
        )
        collector = TelemetryCollector(
            config=config, project_name="warn_test", output_dir=tmp_path
        )

        # Manually inject stages instead of waiting real time
        collector._report.stages = [
            StageTelemetry(stage_name="Fast", stage_num=1, duration=1.0, success=True),
            StageTelemetry(stage_name="Fast2", stage_num=2, duration=1.0, success=True),
            StageTelemetry(stage_name="Slow", stage_num=3, duration=10.0, success=True),
        ]

        report = collector.finalize(total_duration=12.0)
        slow_warnings = [w for w in report.warnings if w.warning_type == "slow_stage"]
        assert len(slow_warnings) >= 1
        assert "Slow" in slow_warnings[0].stage_name

    def test_system_info_captured(self, tmp_path: Path) -> None:
        """Test capture_system_info returns info (may be empty without psutil)."""
        config = TelemetryConfig(enabled=True, track_resources=True)
        collector = TelemetryCollector(
            config=config, project_name="sysinfo", output_dir=tmp_path
        )
        info = collector.capture_system_info()
        # info may be empty if psutil is not available, that's OK
        assert isinstance(info, dict)

    def test_report_accessor(self, tmp_path: Path) -> None:
        """Test the report property returns the current report."""
        config = TelemetryConfig(enabled=True, track_resources=False)
        collector = TelemetryCollector(
            config=config, project_name="accessor", output_dir=tmp_path
        )
        assert collector.report.project_name == "accessor"


# ── load_telemetry_config ───────────────────────────────────────────


class TestLoadTelemetryConfig:
    """Test YAML telemetry config loading."""

    def test_loads_from_yaml(self, tmp_path: Path) -> None:
        from infrastructure.core.pipeline.dag import load_telemetry_config

        yaml_content = """
stages:
  - name: Test
    script: test.py

telemetry:
  enabled: false
  high_memory_mb: 2048
"""
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text(yaml_content)
        config = load_telemetry_config(yaml_file)
        assert config is not None
        assert config.enabled is False
        assert config.high_memory_mb == 2048

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        from infrastructure.core.pipeline.dag import load_telemetry_config

        yaml_content = """
stages:
  - name: Test
    script: test.py
"""
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text(yaml_content)
        config = load_telemetry_config(yaml_file)
        assert config is None

    def test_returns_none_on_invalid_file(self, tmp_path: Path) -> None:
        from infrastructure.core.pipeline.dag import load_telemetry_config

        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("!!invalid yaml ][")
        config = load_telemetry_config(yaml_file)
        assert config is None
