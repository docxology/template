"""Verify generated redaction-style/background proof PDFs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from redacted_report import verify_dev_variant_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "dev" / "redaction_variants",
        help="Directory containing proof PDFs and variant_matrix.json.",
    )
    parser.add_argument(
        "--render-smoke",
        action="store_true",
        help="Rasterize page 1 of every generated PDF with pdftoppm.",
    )
    parser.add_argument(
        "--require-kmyth-sidecars",
        action="store_true",
        help="Require both Kmyth .ski sidecars for every variant.",
    )
    args = parser.parse_args()

    result = verify_dev_variant_outputs(
        args.input_dir,
        render_smoke=args.render_smoke,
        require_kmyth_sidecars=args.require_kmyth_sidecars,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
