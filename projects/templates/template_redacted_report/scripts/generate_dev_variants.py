"""Generate redaction-style/background proof PDFs for development review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from redacted_report import RedactionDecision, RedactionSegment, write_dev_variant_pdfs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_ROOT / "data" / "example_segments.json",
        help="Fixture JSON containing segments and redaction decisions.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "dev" / "redaction_variants",
        help="Directory for generated proof PDFs and variant_matrix.json.",
    )
    parser.add_argument(
        "--no-steganography",
        action="store_true",
        help="Generate only visual proof PDFs, without secure steganography variants.",
    )
    parser.add_argument(
        "--no-kmyth",
        action="store_true",
        help="Do not request optional Kmyth TPM sidecar sealing.",
    )
    parser.add_argument(
        "--with-kmyth",
        action="store_true",
        help="Request optional Kmyth TPM sidecar sealing.",
    )
    parser.add_argument(
        "--kmyth-binary-dir",
        type=Path,
        default=None,
        help="Optional directory containing kmyth-seal and kmyth-unseal.",
    )
    parser.add_argument(
        "--require-kmyth",
        action="store_true",
        help="Fail generation if Kmyth tools are unavailable or sealing fails.",
    )
    parser.add_argument(
        "--kmyth-timeout-seconds",
        type=int,
        default=120,
        help="Timeout for each kmyth-seal invocation.",
    )
    parser.add_argument(
        "--pdf-password",
        default=None,
        help="Optional development-only PDF password for encrypted steganography variants.",
    )
    args = parser.parse_args()
    request_kmyth = (args.with_kmyth or args.kmyth_binary_dir is not None or args.require_kmyth) and not args.no_kmyth

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    segments = [
        RedactionSegment(
            id=item["id"],
            classification=item["classification"],
            text=item["text"],
            source_controls=tuple(item.get("source_controls", [])),
        )
        for item in payload["segments"]
    ]
    decisions = [RedactionDecision(**item) for item in payload["redactions"]]
    result = write_dev_variant_pdfs(
        segments,
        decisions,
        args.output_dir,
        include_steganography=not args.no_steganography,
        include_kmyth=request_kmyth,
        pdf_password=args.pdf_password,
        kmyth_binary_dir=args.kmyth_binary_dir,
        kmyth_required=args.require_kmyth,
        kmyth_timeout_seconds=args.kmyth_timeout_seconds,
    )
    print(
        json.dumps(
            {
                "variant_count": result["variant_count"],
                "matrix": result["variant_matrix_path"],
                "kmyth": result["kmyth"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
