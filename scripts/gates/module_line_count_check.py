#!/usr/bin/env python3
"""Advisory module line-count gate for Layer 1 and project script sources."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.line_count import (  # noqa: E402
    scan_infrastructure_and_scripts,
    scan_project_scripts,
    scan_project_src,
    scan_repository_tests,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES  # noqa: E402


def _python_files(repo_root: Path) -> list[Path]:
    """Return the exact executable source surface certified by this gate."""
    roots = [repo_root / "infrastructure", repo_root / "scripts"]
    for name in PUBLIC_PROJECT_NAMES:
        project = repo_root / "projects" / name
        roots.extend((project / "src", project / "scripts"))
    return sorted(path for root in roots if root.is_dir() for path in root.rglob("*.py"))


def _syntax_failures(repo_root: Path) -> list[tuple[str, str]]:
    """Parse every counted Python file so malformed modules fail closed."""
    failures: list[tuple[str, str]] = []
    for path in _python_files(repo_root):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            failures.append((path.relative_to(repo_root).as_posix(), str(exc)))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Emit advisory WARN lines for test modules >=800 lines (never fails the gate)",
    )
    args = parser.parse_args(argv)

    missing_roots = [name for name in ("infrastructure", "scripts") if not (args.repo_root / name).is_dir()]
    if missing_roots:
        for name in missing_roots:
            print(f"FAIL missing required scan root: {name}/")
        return 1

    warnings: list[tuple[str, int]] = []
    failures: list[tuple[str, int]] = []

    infra_warn, infra_fail = scan_infrastructure_and_scripts(args.repo_root)
    warnings.extend(infra_warn)
    failures.extend(infra_fail)

    proj_warn, proj_fail = scan_project_scripts(args.repo_root)
    warnings.extend(proj_warn)
    failures.extend(proj_fail)

    src_warn, src_fail = scan_project_src(args.repo_root)
    warnings.extend(src_warn)
    failures.extend(src_fail)

    syntax_failures = _syntax_failures(args.repo_root)

    if args.include_tests:
        test_warn, _ = scan_repository_tests(args.repo_root)
        for rel, count in sorted(test_warn):
            print(f"WARN [test] {rel}: {count} lines")

    for rel, count in sorted(warnings):
        print(f"WARN {rel}: {count} lines")
    for rel, count in sorted(failures):
        print(f"FAIL {rel}: {count} lines")
    for rel, error in syntax_failures:
        print(f"FAIL {rel}: invalid Python syntax: {error}")
    if failures or syntax_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
