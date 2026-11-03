"""A native refusal names its reason; the reason reaches both recorded places."""

from __future__ import annotations

import json
import time

import pytest

from infrastructure.reporting.native_installed_invocation import NativeInstalledInvocationFailure
from infrastructure.reporting.native_installed_launcher import _signed_failure
from infrastructure.reporting.native_original_progress import (
    _PHASES,
    _preflight_phase,
    _representative_preflight_diagnostics,
)


def _refusing_result(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "accepted": True,
        "original_exit_code": 1,
        "timed_out": False,
        "diagnostics": [],
        "stderr": "private child body that must never be rendered",
    }
    result.update(overrides)
    return result


def test_installed_invocation_failure_str_names_the_actual_refusing_result() -> None:
    """The launcher records str(error); an opaque category discards the reason."""
    error = NativeInstalledInvocationFailure(_refusing_result())
    rendered = str(error)
    assert "actual cold installed invocation refused or failed" in rendered
    assert "accepted=True" in rendered
    assert "original_exit_code=1" in rendered
    # The retained result stays available and unchanged for the signed exit.
    assert error.result["original_exit_code"] == 1
    assert _signed_failure(error.result) == 1


def test_installed_invocation_failure_str_carries_structured_diagnostics() -> None:
    error = NativeInstalledInvocationFailure(
        _refusing_result(diagnostics=["native tool aggregate stream byte ceiling refused"], timed_out=True)
    )
    rendered = str(error)
    assert "diagnostics=native tool aggregate stream byte ceiling refused" in rendered
    assert "timed_out=True" in rendered


def test_installed_invocation_failure_str_never_renders_raw_child_streams() -> None:
    """Only the exception line is named; other stream content is not echoed."""
    error = NativeInstalledInvocationFailure(
        _refusing_result(stdout="private stdout body", stderr="private stderr body")
    )
    rendered = str(error)
    assert "private stdout body" not in rendered
    assert "private stderr body" not in rendered


def test_installed_invocation_failure_str_names_the_child_exception_when_no_diagnostics() -> None:
    """A real refusal states its reason in the child's final exception line."""
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "<string>", line 22, in <module>\n'
        "    runpy.run_module('infrastructure.reporting.native_hosted_reader',run_name='__main__')\n"
        "    from infrastructure.reporting.required_acceptance_aggregate import produce_aggregate\n"
        "ModuleNotFoundError: No module named 'infrastructure.reporting.native_cell_selection'\n"
    )
    rendered = str(NativeInstalledInvocationFailure(_refusing_result(stderr=stderr)))
    assert (
        "child_error=ModuleNotFoundError: No module named 'infrastructure.reporting.native_cell_selection'" in rendered
    )
    # Only the exception line is named, not the surrounding traceback.
    assert "runpy" not in rendered
    assert "Traceback" not in rendered


def test_child_exception_line_never_echoes_private_content_from_other_lines() -> None:
    """A secret on a non-final line must not be pulled into the message."""
    rendered = str(
        NativeInstalledInvocationFailure(
            _refusing_result(stderr="/private/secret/path/manuscript.md\nValueError: actual reason\n")
        )
    )
    assert "child_error=ValueError: actual reason" in rendered
    assert "/private/secret/path" not in rendered


def test_child_error_is_omitted_when_the_stream_has_no_exception_line() -> None:
    """Never guess a reason from ordinary progress output."""
    rendered = str(
        NativeInstalledInvocationFailure(
            _refusing_result(accepted=False, original_exit_code=None, stderr="progress only\n")
        )
    )
    assert "child_error=" not in rendered
    assert "accepted=False" in rendered


def test_structured_diagnostics_take_precedence_over_the_child_stream() -> None:
    rendered = str(
        NativeInstalledInvocationFailure(
            _refusing_result(diagnostics=["retained ceiling refused"], stderr="ValueError: shadowed\n")
        )
    )
    assert "diagnostics=retained ceiling refused" in rendered
    assert "child_error=" not in rendered


def test_installed_invocation_failure_str_tolerates_a_non_mapping_result() -> None:
    error = NativeInstalledInvocationFailure(None)  # type: ignore[arg-type]
    assert str(error) == "actual cold installed invocation refused or failed"


def test_refusal_record_reaches_the_sink_before_it_closes(capfd: pytest.CaptureFixture[str]) -> None:
    """The finally block must record why the protected body raised."""

    class ObservedFailure(RuntimeError):
        pass

    deadline = time.monotonic() + 20
    with pytest.raises(ObservedFailure, match="protected body reason"):
        with _representative_preflight_diagnostics(deadline):
            raise ObservedFailure("protected body reason")

    rows = [json.loads(line) for line in capfd.readouterr().err.splitlines()]
    phases = [row["phase"] for row in rows]
    assert "diagnostics-stop" in phases
    refusal = next(row for row in rows if row["phase"] == "preflight-body-raised")
    assert refusal["schema_version"] == "template-native-preflight-refusal-v1"
    assert refusal["error_type"] == "ObservedFailure"
    assert refusal["error_message"] == "protected body reason"
    assert refusal["observed_monotonic"] + refusal["remaining_seconds"] == deadline
    # The reason is written into the sink that closes right after it.
    assert phases[-2:] == ["preflight-body-raised", "diagnostics-stop"]


def test_successful_body_records_no_refusal(capfd: pytest.CaptureFixture[str]) -> None:
    deadline = time.monotonic() + 20
    with _representative_preflight_diagnostics(deadline):
        _preflight_phase("source-admission-begin", deadline)

    rows = [json.loads(line) for line in capfd.readouterr().err.splitlines()]
    assert not any(row["phase"] == "preflight-body-raised" for row in rows)
    assert [row["phase"] for row in rows] == ["diagnostics-start", "source-admission-begin", "diagnostics-stop"]


def test_refusal_message_is_bounded_and_never_dropped(capfd: pytest.CaptureFixture[str]) -> None:
    """A long reason must shrink to fit the fixed record ceiling, not vanish."""

    class VerboseFailure(RuntimeError):
        pass

    deadline = time.monotonic() + 20
    message = "x" * 5000
    with pytest.raises(VerboseFailure):
        with _representative_preflight_diagnostics(deadline):
            raise VerboseFailure(message)

    raw = capfd.readouterr().err
    rows = [json.loads(line) for line in raw.splitlines()]
    refusal = next(row for row in rows if row["phase"] == "preflight-body-raised")
    assert refusal["error_type"] == "VerboseFailure"
    assert refusal["error_message"].startswith("xxx")
    assert all(len(line.encode()) + 1 <= 512 for line in raw.splitlines())


def test_refusal_phase_label_stays_outside_the_ordinary_phase_allowlist() -> None:
    """The refusal record is a distinct schema, not a forged ordinary phase."""
    assert "preflight-body-raised" not in _PHASES


def test_enclosing_handled_exception_is_never_reported_as_the_body_refusal(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """A successful body inside an outer except block must record no refusal."""
    deadline = time.monotonic() + 20
    try:
        raise ValueError("unrelated enclosing failure")
    except ValueError:
        with _representative_preflight_diagnostics(deadline):
            _preflight_phase("source-admission-begin", deadline)

    rows = [json.loads(line) for line in capfd.readouterr().err.splitlines()]
    assert not any(row["phase"] == "preflight-body-raised" for row in rows)
    assert "unrelated enclosing failure" not in json.dumps(rows)


def test_sink_refusal_does_not_replace_the_original_exception() -> None:
    """Recording a reason can never convert the real failure or its type."""

    class PrimaryFailure(SystemExit):
        pass

    with pytest.raises(PrimaryFailure):
        with _representative_preflight_diagnostics(time.monotonic() + 20):
            raise PrimaryFailure(23)


def test_refusal_recording_is_absent_outside_the_representative_context(capfd: pytest.CaptureFixture[str]) -> None:
    """An ordinary caller has no sink; the exception still propagates untouched."""
    with pytest.raises(ValueError, match="no sink here"):
        raise ValueError("no sink here")
    assert capfd.readouterr().err == ""
