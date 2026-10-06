#!/usr/bin/env python3
"""Emit ordinary infrastructure CI matrix or export/validate its coverage union."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.core.testing.ci_infra_partition import SHARD_COUNT, ci_matrix


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument("--matrix", action="store_true")
    operations.add_argument("--export-shard", type=int, choices=range(SHARD_COUNT))
    operations.add_argument("--merge-coverage", action="store_true")
    args = parser.parse_args()
    if args.matrix:
        print(json.dumps(ci_matrix(), separators=(",", ":")))
        return 0
    from infrastructure.core.testing.ci_infra_coverage import export_shard, merge_shards

    try:
        if args.export_shard is not None:
            print(export_shard(args.repo_root, args.export_shard))
        else:
            print(f"Complete infrastructure union coverage: {merge_shards(args.repo_root):.2f}%")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Infrastructure CI coverage refused: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
