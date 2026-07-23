"""Static functional-contract inventory for canonical public exemplars."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REQUIRED_DIRECTORIES = ("src", "tests", "manuscript", "scripts", ".agents/skills")
REQUIRED_FILES = ("README.md", "AGENTS.md", "pyproject.toml")


@dataclass(frozen=True)
class SkipContract:
    """One statically discovered optional or fixture-dependent skip."""

    path: str
    line: int
    kind: str
    reason: str
    category: str


@dataclass(frozen=True)
class PublicCapability:
    """Structural and skip-contract facts for one public exemplar."""

    project: str
    required_directories: tuple[str, ...]
    required_files: tuple[str, ...]
    source_file_count: int
    test_file_count: int
    script_file_count: int
    missing_paths: tuple[str, ...]
    skip_contracts: tuple[SkipContract, ...]
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the exemplar has a complete static contract."""
        return not self.missing_paths and not self.issues and self.test_file_count > 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the inventory for CI and readiness reports."""
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


@dataclass(frozen=True)
class PublicCapabilityReport:
    """Aggregate public-exemplar capability inventory."""

    projects: tuple[PublicCapability, ...]

    @property
    def passed(self) -> bool:
        """Return whether every canonical public exemplar passes."""
        return all(project.passed for project in self.projects)

    def to_dict(self) -> dict[str, object]:
        """Serialize the complete report."""
        return {
            "project_count": len(self.projects),
            "passed": self.passed,
            "projects": [project.to_dict() for project in self.projects],
        }


def audit_public_capability(repo_root: Path | str, project: str) -> PublicCapability:
    """Audit one qualified public project using only repository-local facts."""
    root = Path(repo_root).resolve()
    project_root = root / "projects" / project
    missing_paths = tuple(
        path for path in (*REQUIRED_DIRECTORIES, *REQUIRED_FILES) if not (project_root / path).exists()
    )
    source_files = tuple(_python_files(project_root / "src"))
    test_files = tuple(_python_files(project_root / "tests", include_private=False))
    script_files = tuple(_python_files(project_root / "scripts", include_private=False))
    skip_contracts = tuple(_discover_skip_contracts(project_root / "tests", root))
    issues: list[str] = []
    if project_root.is_symlink():
        issues.append("public exemplar path must not be a symlink")
    if not source_files:
        issues.append("src/ has no Python source files")
    if not test_files:
        issues.append("tests/ has no test modules")
    if any(not contract.reason.strip() for contract in skip_contracts):
        issues.append("every discovered skip must have a reason or imported capability name")
    return PublicCapability(
        project=project,
        required_directories=REQUIRED_DIRECTORIES,
        required_files=REQUIRED_FILES,
        source_file_count=len(source_files),
        test_file_count=len(test_files),
        script_file_count=len(script_files),
        missing_paths=missing_paths,
        skip_contracts=skip_contracts,
        issues=tuple(issues),
    )


def audit_public_capabilities(repo_root: Path | str) -> PublicCapabilityReport:
    """Audit the authoritative canonical public roster."""
    return PublicCapabilityReport(
        tuple(audit_public_capability(repo_root, project) for project in PUBLIC_PROJECT_NAMES)
    )


def _python_files(directory: Path, *, include_private: bool = True) -> Iterable[Path]:
    if not directory.is_dir():
        return ()
    return (path for path in sorted(directory.rglob("*.py")) if include_private or not path.name.startswith("_"))


def _discover_skip_contracts(tests_root: Path, repo_root: Path) -> Iterable[SkipContract]:
    if not tests_root.is_dir():
        return ()
    contracts: list[SkipContract] = []
    for path in sorted(tests_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node.func)
                if name in {"pytest.skip", "_pytest.skip", "pytest.importorskip"}:
                    reason = _literal_text(node.args[0]) if node.args else ""
                    if name == "pytest.importorskip" and not reason:
                        reason = f"optional import: {_literal_text(node.args[0]) or 'declared dependency'}"
                    contracts.append(
                        SkipContract(
                            path=_relative(path, repo_root),
                            line=node.lineno,
                            kind=name.rsplit(".", 1)[-1],
                            reason=reason,
                            category=_skip_category(reason),
                        )
                    )
                elif name == "pytest.mark.skipif":
                    reason = ""
                    for keyword in node.keywords:
                        if keyword.arg == "reason":
                            reason = _literal_text(keyword.value)
                    contracts.append(
                        SkipContract(
                            path=_relative(path, repo_root),
                            line=node.lineno,
                            kind="skipif",
                            reason=reason,
                            category=_skip_category(reason),
                        )
                    )
    return contracts


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _literal_text(node: ast.AST) -> str:
    if isinstance(node, ast.JoinedStr):
        return "<computed skip reason>"
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return ""
    return value if isinstance(value, str) else str(value) if value is not None else ""


def _skip_category(reason: str) -> str:
    normalized = reason.lower()
    if not normalized:
        return "UNLABELED"
    if any(token in normalized for token in ("ollama", "lake", "pymdp", "not installed", "optional import")):
        return "OPTIONAL_CAPABILITY"
    if any(token in normalized for token in ("missing", "not found", "absent", "run ", "config")):
        return "FIXTURE_OR_GENERATED_INPUT"
    return "DECLARED_CONDITION"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "PublicCapability",
    "PublicCapabilityReport",
    "REQUIRED_DIRECTORIES",
    "REQUIRED_FILES",
    "SkipContract",
    "audit_public_capability",
    "audit_public_capabilities",
]
