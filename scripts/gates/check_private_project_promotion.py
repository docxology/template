#!/usr/bin/env python3
"""Compatibility entrypoint for the private-project promotion security gate."""

from __future__ import annotations

import sys

from infrastructure.project.promotion import main as promotion_main


def main(argv: list[str] | None = None) -> int:
    """Delegate the historical script surface to the package CLI."""
    return promotion_main(["candidate", *(argv if argv is not None else sys.argv[1:])])


if __name__ == "__main__":
    raise SystemExit(main())
