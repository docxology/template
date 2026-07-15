#!/usr/bin/env python3
"""Fail closed when a pip-audit exemption lacks accountable metadata."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ADVISORY = re.compile(r"^(?:CVE-\d{4}-\d+|GHSA-[\w-]+|PYSEC-\d{4}-\d+)$")
REQUIRED_FIELDS = ("owner", "expires", "fix-version", "reason")


def validate_ignore_policy(path: Path, *, today: date | None = None) -> list[str]:
    """Return deterministic policy errors for ``path``."""
    errors: list[str] = []
    metadata: dict[str, str] = {}
    current_date = today or date.today()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("#"):
            content = stripped[1:].strip()
            if ":" in content:
                key, value = content.split(":", 1)
                if key in REQUIRED_FIELDS:
                    metadata[key] = value.strip()
            continue
        if not stripped:
            metadata = {}
            continue
        advisory = stripped.split("#", 1)[0].strip()
        if not ADVISORY.fullmatch(advisory):
            errors.append(f"{path}:{line_number}: invalid advisory id {advisory!r}")
            metadata = {}
            continue
        missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
        if missing:
            errors.append(f"{path}:{line_number}: {advisory} missing {', '.join(missing)}")
        else:
            try:
                expiry = date.fromisoformat(metadata["expires"])
            except ValueError:
                errors.append(f"{path}:{line_number}: {advisory} has invalid expires date")
            else:
                if expiry < current_date:
                    errors.append(f"{path}:{line_number}: {advisory} expired on {expiry}")
        metadata = {}
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path(".github/pip-audit-ignore.txt"))
    args = parser.parse_args()
    errors = validate_ignore_policy(args.path)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"pip-audit ignore policy passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
