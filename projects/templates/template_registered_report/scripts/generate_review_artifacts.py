"""Generate registered-report review artifacts from the fixture registration."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from registered_report import (  # noqa: E402
    build_deviation_ledger,
    build_review_packet,
    compare_analysis_to_registration,
    freeze_registration,
    validate_sensitivity_table,
)


DEFAULT_EXECUTED = {
    "outcomes": ["primary_score", "secondary_score"],
    "primary_model": "linear_model",
}
DEFAULT_DEVIATIONS = [
    {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
    {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registration",
        type=Path,
        default=PROJECT_ROOT / "data" / "example_registration.json",
        help="Registration JSON fixture to freeze and audit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "reports",
        help="Directory for generated registered-report artifacts.",
    )
    args = parser.parse_args()

    registration = cast("dict[str, Any]", json.loads(args.registration.read_text(encoding="utf-8")))
    frozen = freeze_registration(registration)
    sensitivity_rows = cast("list[dict[str, Any]]", frozen.get("sensitivity_analyses", []))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    adherence = compare_analysis_to_registration(frozen, DEFAULT_EXECUTED, DEFAULT_DEVIATIONS)
    ledger = build_deviation_ledger(frozen, DEFAULT_EXECUTED, DEFAULT_DEVIATIONS)
    sensitivity_findings = validate_sensitivity_table(frozen, sensitivity_rows)
    packet = build_review_packet(frozen, DEFAULT_EXECUTED, DEFAULT_DEVIATIONS, sensitivity_rows)

    outputs = {
        "frozen_registration.json": frozen,
        "registered_report_review_packet.json": packet,
        "deviation_ledger.json": {
            "registration_hash": packet["registration_hash"],
            "rows": tuple(asdict(row) for row in ledger),
        },
        "sensitivity_findings.json": {
            "registration_hash": packet["registration_hash"],
            "findings": tuple(asdict(finding) for finding in sensitivity_findings),
        },
        "adherence_report.json": {
            **asdict(adherence),
            "findings": tuple(asdict(finding) for finding in adherence.findings),
        },
    }
    written: dict[str, str] = {}
    for filename, payload in outputs.items():
        path = args.output_dir / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[filename] = path.as_posix()

    print(json.dumps({"valid": packet["valid"], "review_score": packet["review_score"], "outputs": written}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
