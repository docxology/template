"""Knowledge-graph calibration fixture tests."""

from pathlib import Path

from knowledge_graph.calibration import evaluate_calibration_cases, validate_calibration_fixture


PROJECT = Path(__file__).resolve().parents[2]


def test_calibration_fixture_preserves_score_direction():
    report = validate_calibration_fixture(PROJECT / "data" / "fixtures" / "kg_calibration.json")
    assert report["status"] == "pass"
    assert report["case_count"] == 3


def test_calibration_rejects_inverted_expected_direction():
    report = evaluate_calibration_cases(
        [
            {
                "case_id": "wrong",
                "hypothesis_id": "PRIMARY_EFFICACY",
                "expected": "negative",
                "assertions": [{"assertion_type": "supports", "citation_count": 10, "confidence": 1.0}],
            }
        ]
    )
    assert report["status"] == "fail"
    assert report["issues"]
