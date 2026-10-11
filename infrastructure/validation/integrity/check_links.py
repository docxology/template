#!/usr/bin/env python3
"""CLI entry point for documentation link and reference audits."""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.core.project_paths import find_repo_root

__all__ = ["main", "run_link_audit"]


def run_link_audit(repo_root: Path) -> int:
    """Run the comprehensive link and reference audit for ``repo_root``."""
    from infrastructure.validation.integrity.link_audit_core import run_link_audit as audit

    return audit(repo_root)


def main() -> int:
    """Check all documentation links and references comprehensively."""
    return run_link_audit(find_repo_root())


if __name__ == "__main__":
    sys.exit(main())
