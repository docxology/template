#!/usr/bin/env python3
"""Execute one manifest-selected child in core mode with independent custody checks."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BOOTSTRAP = importlib.util.spec_from_file_location(
    "autopoiesis_script_bootstrap", PROJECT_ROOT / "scripts/_bootstrap.py"
)
if _BOOTSTRAP is None or _BOOTSTRAP.loader is None:
    raise ImportError("actual project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP)
_BOOTSTRAP.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_ROOT)

from template_autopoiesis.gates.realization_contract import realize_selected_children  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.gates.child_execution import ChildCapabilityBlocked  # noqa: E402 - actual provider selection precedes own imports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)
    try:
        print(realize_selected_children(args.project_root, single=True))
    except ChildCapabilityBlocked as exc:
        print(f"Required child execution blocked: {exc}", file=sys.stderr)
        return 75
    except (OSError, ValueError, TypeError, NotImplementedError) as exc:
        print(f"Required child realization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
