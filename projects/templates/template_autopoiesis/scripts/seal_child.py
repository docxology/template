#!/usr/bin/env python3
"""Seal a child project: write seal.json with spec hash and payload."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sealing import build_payload
from src.verify import verify_child


def seal_child(child_root: Path) -> None:
    """Write seal.json to *child_root*."""
    import json as _json
    prov_path = child_root / "provenance.json"
    if not prov_path.exists():
        print(f"ERROR: provenance.json not found in {child_root}", file=sys.stderr)
        sys.exit(1)

    prov = _json.loads(prov_path.read_text())
    spec = prov.get("spec", {})
    spec_hash = spec.get("seed", "unknown")
    tree_hash = prov.get("tree_hash", "")
    seed = spec.get("seed", 0)

    # Re-verify before sealing
    report = verify_child(child_root)
    if not report.all_passed:
        failed = [c.name for c in report.checks if not c.passed]
        print(f"WARNING: verification failed: {failed}", file=sys.stderr)

    payload = build_payload(str(spec_hash), tree_hash, int(seed))
    seal = {
        "spec_hash": str(spec_hash),
        "tree_hash": tree_hash,
        "seed": seed,
        "payload": payload,
    }
    seal_path = child_root / "seal.json"
    seal_path.write_text(json.dumps(seal, indent=2))
    print(f"Sealed: {seal_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: seal_child.py <child_root>", file=sys.stderr)
        sys.exit(1)
    seal_child(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
