"""Generate data descriptor release-review artifacts from the fixture descriptor."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_descriptor import (  # noqa: E402
    build_descriptor_report,
    build_release_bundle_manifest,
    summarize_field_constraints,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=PROJECT_ROOT / "data" / "example_descriptor.json",
        help="Descriptor JSON fixture to validate and export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "reports",
        help="Directory for generated descriptor artifacts.",
    )
    args = parser.parse_args()

    descriptor = cast("dict[str, Any]", json.loads(args.descriptor.read_text(encoding="utf-8")))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    report = build_descriptor_report(descriptor)
    manifest = build_release_bundle_manifest(descriptor)
    constraints = tuple(asdict(summary) for summary in summarize_field_constraints(descriptor))

    outputs = {
        "descriptor_report.json": {
            **asdict(report),
            "findings": tuple(asdict(finding) for finding in report.findings),
        },
        "release_bundle_manifest.json": manifest,
        "field_constraints.json": {
            "schema_fingerprint": report.schema_fingerprint,
            "field_count": report.field_count,
            "constraints": constraints,
        },
    }
    written: dict[str, str] = {}
    for filename, payload in outputs.items():
        path = args.output_dir / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[filename] = path.as_posix()

    print(json.dumps({"valid": report.valid, "readiness_score": report.readiness_score, "outputs": written}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
