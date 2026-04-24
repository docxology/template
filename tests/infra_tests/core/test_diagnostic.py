"""Tests for infrastructure.core.logging.diagnostic."""

import json
from pathlib import Path


from infrastructure.core.logging.diagnostic import (
    DiagnosticEvent,
    DiagnosticReporter,
    DiagnosticSeverity,
)


class TestDiagnosticSeverity:
    def test_values(self):
        assert DiagnosticSeverity.ERROR.value == "ERROR"
        assert DiagnosticSeverity.WARNING.value == "WARNING"
        assert DiagnosticSeverity.INFO.value == "INFO"


class TestDiagnosticEvent:
    def test_basic_creation(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.ERROR,
            category="test",
            message="something broke",
        )
        assert e.severity == DiagnosticSeverity.ERROR
        assert e.category == "test"
        assert e.message == "something broke"
        assert e.file_path is None
        assert e.line_number is None
        assert e.fix_suggestion is None
        assert e.context == {}

    def test_full_creation(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.WARNING,
            category="lint",
            message="unused import",
            file_path="/foo/bar.py",
            line_number=42,
            fix_suggestion="Remove the import",
            context={"rule": "F401"},
        )
        assert e.file_path == "/foo/bar.py"
        assert e.line_number == 42
        assert e.fix_suggestion == "Remove the import"
        assert e.context == {"rule": "F401"}

    def test_to_dict(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.INFO,
            category="check",
            message="all good",
            file_path=Path("/some/file.txt"),
        )
        d = e.to_dict()
        assert d["severity"] == "INFO"
        assert d["category"] == "check"
        assert d["message"] == "all good"
        assert d["file_path"] == "/some/file.txt"

    def test_to_dict_no_file_path(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.ERROR,
            category="x",
            message="m",
        )
        d = e.to_dict()
        assert d["file_path"] is None


class TestDiagnosticCode:
    """Tests for the optional ``code`` identifier added to DiagnosticEvent."""

    def test_default_code_is_none(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.ERROR,
            category="x",
            message="m",
        )
        assert e.code is None

    def test_code_in_to_dict(self):
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.WARNING,
            category="markdown",
            message="bare pipe",
            code="MARKDOWN.PANDOC_BARE_PIPE",
        )
        d = e.to_dict()
        assert d["code"] == "MARKDOWN.PANDOC_BARE_PIPE"

    def test_code_round_trip_via_persisted_report(self, tmp_path):
        """Construct -> save -> load through DiagnosticReporter; code survives."""
        r1 = DiagnosticReporter("rt", output_dir=tmp_path)
        r1.record_error(
            "markdown",
            "Undefined citation key '@missing'",
            code="BIBTEX.UNDEFINED_KEY",
            file_path="manuscript/01_intro.md",
        )
        r1.save_report()

        r2 = DiagnosticReporter("rt", output_dir=tmp_path)
        assert len(r2.events) == 1
        loaded = r2.events[0]
        assert loaded.code == "BIBTEX.UNDEFINED_KEY"
        assert loaded.message == "Undefined citation key '@missing'"
        assert loaded.severity == DiagnosticSeverity.ERROR

    def test_record_helpers_accept_code_kwarg(self):
        r = DiagnosticReporter("p")
        e = r.record_warning("cat", "msg", code="MARKDOWN.PANDOC_BARE_PIPE")
        assert e.code == "MARKDOWN.PANDOC_BARE_PIPE"
        assert r.events[0].code == "MARKDOWN.PANDOC_BARE_PIPE"

    def test_legacy_report_without_code_loads(self, tmp_path):
        """A report written before the field existed must round-trip cleanly."""
        report_dir = tmp_path / "reports"
        report_dir.mkdir()
        (report_dir / "diagnostics.json").write_text(
            json.dumps(
                {
                    "project_name": "legacy",
                    "total_events": 1,
                    "errors": 1,
                    "warnings": 0,
                    "events": [
                        {
                            "severity": "ERROR",
                            "category": "markdown",
                            "message": "old finding without a code",
                            "file_path": "x.md",
                            "line_number": None,
                            "fix_suggestion": None,
                            "context": {},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        r = DiagnosticReporter("legacy", output_dir=tmp_path)
        assert len(r.events) == 1
        assert r.events[0].code is None


class TestDiagnosticReporter:
    def test_init_no_output_dir(self):
        r = DiagnosticReporter("test_project")
        assert r.project_name == "test_project"
        assert r.output_dir is None
        assert r.events == []

    def test_init_with_output_dir_no_file(self, tmp_path):
        r = DiagnosticReporter("proj", output_dir=tmp_path)
        assert r.events == []

    def test_record_event(self):
        r = DiagnosticReporter("proj")
        e = DiagnosticEvent(
            severity=DiagnosticSeverity.ERROR,
            category="test",
            message="fail",
        )
        r.record(e)
        assert len(r.events) == 1
        assert r.events[0] is e

    def test_record_error(self):
        r = DiagnosticReporter("proj")
        e = r.record_error("cat", "msg")
        assert e.severity == DiagnosticSeverity.ERROR
        assert e.category == "cat"
        assert e.message == "msg"
        assert len(r.events) == 1

    def test_record_warning(self):
        r = DiagnosticReporter("proj")
        e = r.record_warning("cat", "msg")
        assert e.severity == DiagnosticSeverity.WARNING

    def test_record_info(self):
        r = DiagnosticReporter("proj")
        e = r.record_info("cat", "msg")
        assert e.severity == DiagnosticSeverity.INFO

    def test_has_errors_true(self):
        r = DiagnosticReporter("proj")
        r.record_error("cat", "error msg")
        assert r.has_errors() is True

    def test_has_errors_false(self):
        r = DiagnosticReporter("proj")
        r.record_warning("cat", "warn msg")
        assert r.has_errors() is False

    def test_has_errors_empty(self):
        r = DiagnosticReporter("proj")
        assert r.has_errors() is False

    def test_print_report_empty(self):
        """print_report should not raise with no events."""
        r = DiagnosticReporter("proj")
        r.print_report()  # Should just log "No diagnostic events"

    def test_print_report_with_events(self):
        """print_report should not raise with mixed events."""
        r = DiagnosticReporter("proj")
        r.record_error("cat", "error msg", file_path="/foo.py", line_number=10)
        r.record_warning("cat2", "warn msg", fix_suggestion="do X")
        r.record_info("cat3", "info msg")
        r.print_report()  # Should not raise

    def test_save_report_no_output_dir(self):
        r = DiagnosticReporter("proj")
        r.record_error("cat", "msg")
        r.save_report()  # Should be a no-op without output_dir

    def test_save_report_no_events(self, tmp_path):
        r = DiagnosticReporter("proj", output_dir=tmp_path)
        r.save_report()
        assert not (tmp_path / "reports" / "diagnostics.json").exists()

    def test_save_report_creates_json(self, tmp_path):
        r = DiagnosticReporter("proj", output_dir=tmp_path)
        r.record_error("lint", "bad import")
        r.record_warning("style", "long line")
        r.save_report()

        report_file = tmp_path / "reports" / "diagnostics.json"
        assert report_file.exists()

        data = json.loads(report_file.read_text())
        assert data["project_name"] == "proj"
        assert data["total_events"] == 2
        assert data["errors"] == 1
        assert data["warnings"] == 1
        assert len(data["events"]) == 2

    def test_save_report_deduplicates(self, tmp_path):
        r = DiagnosticReporter("proj", output_dir=tmp_path)
        # Add same event twice
        r.record_error("cat", "same msg")
        r.record_error("cat", "same msg")
        r.save_report()

        data = json.loads((tmp_path / "reports" / "diagnostics.json").read_text())
        assert data["total_events"] == 1

    def test_load_existing_events(self, tmp_path):
        # First save some events
        r1 = DiagnosticReporter("proj", output_dir=tmp_path)
        r1.record_error("cat", "persisted error")
        r1.record_warning("cat", "persisted warning")
        r1.save_report()

        # Now create a new reporter — should load those events
        r2 = DiagnosticReporter("proj", output_dir=tmp_path)
        assert len(r2.events) == 2
        assert r2.events[0].severity == DiagnosticSeverity.ERROR
        assert r2.events[0].message == "persisted error"

    def test_load_existing_events_invalid_json(self, tmp_path):
        report_dir = tmp_path / "reports"
        report_dir.mkdir(parents=True)
        (report_dir / "diagnostics.json").write_text("not valid json")

        # Should not raise, just log warning
        r = DiagnosticReporter("proj", output_dir=tmp_path)
        assert r.events == []

    def test_load_existing_events_invalid_severity(self, tmp_path):
        report_dir = tmp_path / "reports"
        report_dir.mkdir(parents=True)
        data = {
            "events": [
                {"severity": "BOGUS", "category": "test", "message": "msg"},
            ]
        }
        (report_dir / "diagnostics.json").write_text(json.dumps(data))

        r = DiagnosticReporter("proj", output_dir=tmp_path)
        # Should fall back to ERROR severity
        assert len(r.events) == 1
        assert r.events[0].severity == DiagnosticSeverity.ERROR

    def test_load_avoids_duplicates(self, tmp_path):
        report_dir = tmp_path / "reports"
        report_dir.mkdir(parents=True)
        data = {
            "events": [
                {"severity": "INFO", "category": "c", "message": "m"},
                {"severity": "INFO", "category": "c", "message": "m"},
            ]
        }
        (report_dir / "diagnostics.json").write_text(json.dumps(data))

        r = DiagnosticReporter("proj", output_dir=tmp_path)
        assert len(r.events) == 1
