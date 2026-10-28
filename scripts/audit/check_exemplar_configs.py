#!/usr/bin/env python3
"""Check every canonical exemplar's configuration and SDK binding."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.project.exemplar_config_contract import (  # noqa: E402
    format_exemplar_config_report,
    validate_exemplar_configs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    report = validate_exemplar_configs(args.repo_root)
    print(format_exemplar_config_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
