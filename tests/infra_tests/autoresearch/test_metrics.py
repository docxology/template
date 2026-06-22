from __future__ import annotations

from infrastructure.autoresearch import mad_confidence, metric_unit_from_name, parse_metric_lines


def test_parse_metric_lines_trusts_only_exact_metric_contract() -> None:
    output = """
    setup log
    METRIC accuracy_pct=91.5
    METRIC latency_ms=12.25
    METRIC loss=1.2e-3
    done
    """

    assert parse_metric_lines(output) == {
        "accuracy_pct": 91.5,
        "latency_ms": 12.25,
        "loss": 0.0012,
    }


def test_parse_metric_lines_rejects_invalid_metric_evidence() -> None:
    for output in (
        "METRIC score=nan\n",
        "METRIC score=1e9999\n",
        "METRIC score=1 extra\n",
        "METRIC score=1\nMETRIC score=2\n",
        "METRIC 1score=2\n",
    ):
        try:
            parse_metric_lines(output)
        except ValueError:
            continue
        raise AssertionError(f"invalid metric output was accepted: {output!r}")


def test_metric_unit_from_name_infers_known_suffixes() -> None:
    assert metric_unit_from_name("latency_ms") == "ms"
    assert metric_unit_from_name("wall_clock.seconds") == "s"
    assert metric_unit_from_name("accuracy_pct") == "%"
    assert metric_unit_from_name("cost_usd") == "USD"
    assert metric_unit_from_name("payload_bytes") == "bytes"
    assert metric_unit_from_name("score") == ""


def test_mad_confidence_reports_improvement_over_noise_floor() -> None:
    confidence = mad_confidence([8.0, 10.0, 12.0], baseline=10.0, best=14.0)

    assert confidence == 2.0


def test_mad_confidence_returns_none_when_noise_is_not_estimable() -> None:
    assert mad_confidence([1.0], baseline=1.0, best=1.2) is None
    assert mad_confidence([1.0, 1.0, 1.0], baseline=1.0, best=1.2) is None
    assert mad_confidence([1.0, float("inf"), "invalid"], baseline=1.0, best=1.2) is None
