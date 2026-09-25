#!/usr/bin/env python3
"""Generate manuscript variables from the experiment tree (hydration entrypoint).

Strict by default: fails when the tree store is missing or, with
``--require-answered``, when nothing has been answered yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from template_experiment_tree import ManuscriptVariablesError, generate_variables  # noqa: E402
from template_experiment_tree.store import default_store_path  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=None, help="Override the tree store path.")
    parser.add_argument("--out", default=None, help="Override the variables output path.")
    parser.add_argument("--require-answered", action="store_true", help="Fail when the tree has no answered nodes.")
    args = parser.parse_args(argv)

    store = Path(args.store) if args.store else default_store_path(PROJECT_ROOT)
    out = Path(args.out) if args.out else PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    try:
        variables = generate_variables(store, out, require_answered=args.require_answered)
    except ManuscriptVariablesError as exc:
        print(f"FAILED: {exc}")
        return 1
    print(f"wrote {out} ({len(variables)} variables)")
    print(json.dumps({k: v for k, v in variables.items() if not isinstance(v, dict)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
