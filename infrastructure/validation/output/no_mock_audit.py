"""Repository-level CLI for lexical mock checks and stand-in inventory.

The default mode is the existing CI gate: it fails only on prohibited
mock-framework imports/calls or an incomplete scan. The explicit inventory mode
classifies ``pytest.monkeypatch`` operations. CI enables
``--fail-on-dependency-replacement`` and holds the measured replacement count
at zero; the advisory mode remains available for exploratory local inventories.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from infrastructure.core.project_paths import find_repo_root
from infrastructure.validation.output.no_mock_enforcer import (
    SemanticStandInUse,
    StandInCategory,
    scan_lexical_mock_policy,
    scan_semantic_standins,
    scan_test_roots,
)

SUCCESS = 0
FAILURE = 1

_CATEGORY_ORDER: tuple[StandInCategory, ...] = (
    StandInCategory.environment_isolation,
    StandInCategory.import_path_isolation,
    StandInCategory.dependency_replacement,
    StandInCategory.other,
)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _repository_test_roots(repo_root: Path) -> tuple[Path, ...]:
    """Return unique policy roots in deterministic display-path order."""
    unique: dict[str, Path] = {}
    for path in scan_test_roots(repo_root):
        resolved = path.resolve() if path.exists() else path.absolute()
        unique[resolved.as_posix()] = path
    return tuple(
        sorted(
            unique.values(),
            key=lambda path: _display_path(path, repo_root),
        )
    )


@dataclass(frozen=True)
class LexicalAuditReport:
    """Repository-level result for the enforced lexical gate."""

    test_roots: tuple[str, ...]
    python_files: int
    violations: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def status(self) -> str:
        """Return the gate status: ``"scan_error"`` if errors occurred, else ``"fail"`` or ``"pass"``."""
        if self.errors:
            return "scan_error"
        return "fail" if self.violations else "pass"

    @property
    def exit_code(self) -> int:
        """Return ``SUCCESS`` (0) when the gate passes, otherwise ``FAILURE`` (1)."""
        return SUCCESS if self.status == "pass" else FAILURE

    def to_dict(self) -> dict[str, Any]:
        """Serialize the lexical audit report as a deterministic JSON-serializable dict."""
        return {
            "schema_version": 1,
            "mode": "lexical_mock_framework_gate",
            "status": self.status,
            "exit_code": self.exit_code,
            "policy": "prohibited mock-framework imports and calls",
            "scope": {
                "test_roots": list(self.test_roots),
                "python_files": self.python_files,
            },
            "violations": list(self.violations),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class StandInInventoryReport:
    """Repository-level monkeypatch inventory result."""

    test_roots: tuple[str, ...]
    python_files: int
    uses: tuple[SemanticStandInUse, ...]
    errors: tuple[str, ...]
    fail_on_dependency_replacement: bool = False

    @property
    def counts(self) -> dict[str, int]:
        """Return per-category stand-in counts plus a ``"total"`` entry."""
        counts = {category.value: 0 for category in _CATEGORY_ORDER}
        for use in self.uses:
            counts[use.category.value] += 1
        counts["total"] = len(self.uses)
        return counts

    @property
    def status(self) -> str:
        """Return ``"scan_error"``, ``"fail"``/``"advisory_debt"`` (if replacement debt), or ``"clear"``."""
        if self.errors:
            return "scan_error"
        dependency_replacements = self.counts[StandInCategory.dependency_replacement.value]
        if dependency_replacements:
            return "fail" if self.fail_on_dependency_replacement else "advisory_debt"
        return "clear"

    @property
    def exit_code(self) -> int:
        """Return ``FAILURE`` (1) on scan errors or enforced failures, else ``SUCCESS`` (0)."""
        return FAILURE if self.status in {"scan_error", "fail"} else SUCCESS

    def to_dict(self) -> dict[str, Any]:
        """Serialize the semantic stand-in inventory as a deterministic JSON-serializable dict."""
        return {
            "schema_version": 1,
            "mode": "semantic_standin_inventory",
            "status": self.status,
            "exit_code": self.exit_code,
            "enforced": self.fail_on_dependency_replacement,
            "scope": {
                "test_roots": list(self.test_roots),
                "python_files": self.python_files,
            },
            "counts": self.counts,
            "uses": [use.to_dict() for use in self.uses],
            "errors": list(self.errors),
        }


def collect_lexical_audit(repo_root: Path) -> LexicalAuditReport:
    """Collect the enforced lexical policy report for a repository."""
    roots = _repository_test_roots(repo_root)
    errors: list[str] = []
    violations: list[str] = []
    files_scanned = 0
    if not (repo_root / "tests").is_dir():
        errors.append(f"required tests directory not found: {repo_root / 'tests'}")

    for tests_dir in roots:
        result = scan_lexical_mock_policy(tests_dir, repo_root)
        files_scanned += result.files_scanned
        violations.extend(result.violations)
        errors.extend(result.errors)

    return LexicalAuditReport(
        test_roots=tuple(_display_path(path, repo_root) for path in roots),
        python_files=files_scanned,
        violations=tuple(sorted(set(violations))),
        errors=tuple(sorted(set(errors))),
    )


def collect_standin_inventory(
    repo_root: Path,
    *,
    fail_on_dependency_replacement: bool = False,
) -> StandInInventoryReport:
    """Collect the advisory semantic-stand-in inventory for a repository."""
    roots = _repository_test_roots(repo_root)
    errors: list[str] = []
    uses: list[SemanticStandInUse] = []
    files_scanned = 0
    if not (repo_root / "tests").is_dir():
        errors.append(f"required tests directory not found: {repo_root / 'tests'}")

    for tests_dir in roots:
        result = scan_semantic_standins(tests_dir, repo_root)
        files_scanned += result.files_scanned
        uses.extend(result.uses)
        errors.extend(result.errors)

    return StandInInventoryReport(
        test_roots=tuple(_display_path(path, repo_root) for path in roots),
        python_files=files_scanned,
        uses=tuple(
            sorted(
                uses,
                key=lambda use: (
                    use.path,
                    use.line,
                    use.column,
                    use.method,
                    use.source,
                ),
            )
        ),
        errors=tuple(sorted(set(errors))),
        fail_on_dependency_replacement=fail_on_dependency_replacement,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the shared CLI parser used by both compatibility wrappers."""
    parser = argparse.ArgumentParser(
        description=("Check prohibited mock-framework syntax or inventory pytest.monkeypatch semantic stand-ins.")
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="Report monkeypatch usage categories; advisory unless explicitly gated",
    )
    parser.add_argument(
        "--fail-on-dependency-replacement",
        action="store_true",
        help="With --inventory, exit 1 when setattr/setitem-style debt is non-zero",
    )
    parser.add_argument(
        "--max-dependency-replacements",
        type=int,
        help="With --inventory, fail when replacement debt exceeds this ratchet",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="With --inventory, print every classified operation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a deterministic JSON report",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help=argparse.SUPPRESS,
    )
    return parser


def _print_lexical_report(report: LexicalAuditReport) -> None:
    print("Mode: lexical mock-framework gate (enforced)")
    print(f"Scope: {len(report.test_roots)} test roots; {report.python_files} Python files")
    if report.errors:
        print(f"SCAN ERROR: {len(report.errors)} file/scope error(s)")
        for error in report.errors:
            print(error)
    elif report.violations:
        print(f"FAIL: prohibited mock-framework imports or calls detected ({len(report.violations)})")
        for violation in report.violations:
            print(violation)
    else:
        print("PASS: no prohibited mock-framework imports or calls detected.")
    print(
        "Boundary: this lexical gate does not evaluate pytest.monkeypatch "
        "dependency replacement; run with --inventory for that evidence."
    )


def _print_inventory_report(
    report: StandInInventoryReport,
    *,
    details: bool,
) -> None:
    mode = "enforced" if report.fail_on_dependency_replacement else "advisory"
    print(f"Mode: semantic stand-in inventory ({mode})")
    print(f"Scope: {len(report.test_roots)} test roots; {report.python_files} Python files")
    for category in _CATEGORY_ORDER:
        print(f"{category.value}: {report.counts[category.value]}")
    print(f"total: {report.counts['total']}")
    print(f"Status: {report.status}")
    if report.errors:
        for error in report.errors:
            print(error)
    elif report.status == "advisory_debt":
        print(
            "ADVISORY: dependency replacements are measured migration debt; "
            "they do not affect exit status without "
            "--fail-on-dependency-replacement."
        )
    if details:
        for use in report.uses:
            print(f"{use.path}:{use.line}:{use.column}: {use.category.value}: {use.method}: {use.source}")


def main(
    argv: Sequence[str] | None = None,
    *,
    repo_root: Path | None = None,
) -> int:
    """Run the shared audit CLI and return deterministic exit semantics."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.fail_on_dependency_replacement and not args.inventory:
        parser.error("--fail-on-dependency-replacement requires --inventory")
    if args.max_dependency_replacements is not None and not args.inventory:
        parser.error("--max-dependency-replacements requires --inventory")
    if args.details and not args.inventory:
        parser.error("--details requires --inventory")

    root = (args.repo_root or repo_root or find_repo_root()).resolve()
    if args.inventory:
        report = collect_standin_inventory(
            root,
            fail_on_dependency_replacement=args.fail_on_dependency_replacement,
        )
        ratchet_exceeded = (
            args.max_dependency_replacements is not None
            and report.counts["dependency_replacement"] > args.max_dependency_replacements
        )
        if args.json:
            payload = report.to_dict()
            payload["dependency_replacement_ceiling"] = args.max_dependency_replacements
            payload["ratchet_exceeded"] = ratchet_exceeded
            if ratchet_exceeded:
                payload["status"] = "ratchet_exceeded"
                payload["exit_code"] = 1
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_inventory_report(report, details=args.details)
            if ratchet_exceeded:
                print(
                    "FAIL: dependency replacement debt "
                    f"{report.counts['dependency_replacement']} exceeds ceiling "
                    f"{args.max_dependency_replacements}"
                )
        return 1 if ratchet_exceeded else report.exit_code

    lexical_report = collect_lexical_audit(root)
    if args.json:
        print(json.dumps(lexical_report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_lexical_report(lexical_report)
    return lexical_report.exit_code


__all__ = [
    "LexicalAuditReport",
    "StandInInventoryReport",
    "build_parser",
    "collect_lexical_audit",
    "collect_standin_inventory",
    "main",
]
