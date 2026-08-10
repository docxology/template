#!/usr/bin/env python3
"""Generate the source-bound evidence index for ``STATUS.md``."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.gates.status_freshness import parse_status_rows

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "template-status-evidence/v1"


def build_status_evidence(repo_root: Path | str) -> dict[str, object]:
    """Build a deterministic receipt binding every status row to its source text."""
    root = Path(repo_root).resolve()
    source_path = root / "STATUS.md"
    text = source_path.read_text(encoding="utf-8")
    rows = parse_status_rows(text)
    if not rows:
        raise ValueError("STATUS.md contains no parseable verification rows")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_path": "STATUS.md",
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "rows": [
            {
                "id": row.identifier,
                "subsystem": row.subsystem,
                "last_verified": row.verified_on.isoformat(),
                "verified_by": row.verified_by,
                "verification_scope": row.verification_scope,
                "command": row.command,
                "receipt": row.receipt,
                "mode": row.mode,
                "health": row.health,
            }
            for row in rows
        ],
    }


def render_status_evidence(repo_root: Path | str) -> str:
    """Return the canonical JSON receipt text."""
    return json.dumps(build_status_evidence(repo_root), indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Check or write the generated status evidence receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write", action="store_true", help="write the generated receipt")
    parser.add_argument("--check", action="store_true", help="fail when the receipt is stale")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    root = args.repo_root.resolve()
    destination = root / "docs" / "_generated" / "status_evidence.json"
    rendered = render_status_evidence(root)
    if args.check or not args.write:
        if not destination.is_file() or destination.read_text(encoding="utf-8") != rendered:
            print(f"stale generated status evidence: {destination}")
            return 1
        print("status evidence: OK")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
