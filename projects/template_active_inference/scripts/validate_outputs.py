#!/usr/bin/env python3
"""Validate generated outputs against the track contract."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gates.validation import validate_manuscript, validate_outputs


def main() -> int:
    outputs = validate_outputs(PROJECT_ROOT)
    manuscript = validate_manuscript(PROJECT_ROOT)
    failed = {**{k: v for k, v in outputs.items() if not v}, **{k: v for k, v in manuscript.items() if not v}}
    print(json_dumps({"outputs": outputs, "manuscript": manuscript}))
    return 1 if failed else 0


def json_dumps(obj: object) -> str:
    import json

    return json.dumps(obj, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
