"""Thin-orchestrator drift detection for scripts/ trees."""

from __future__ import annotations

import ast
from pathlib import Path

from infrastructure.project.drift.models import Report

# Trivial helpers allowed in thin orchestrators without counting toward "fat".
_TRIVIAL_FUNC_NAMES = frozenset(
    {
        "_parse_args",
        "_main",
        "main",
        "_bootstrap_paths",
        "ensure_project_paths",
    }
)

# Subprocess-heavy schedulers — exempt from non-trivial function count if name matches.
_SUBPROCESS_SCHEDULER_NAMES = frozenset(
    {
        "run_all.py",
        "regression_gate.py",
        "build_lean.py",
        "build_mathlib_proofs.py",
    }
)

_COMPUTE_IMPORTS = frozenset({"numpy", "np", "matplotlib", "matplotlib.pyplot", "plt", "scipy"})

_PROJECT_SCRIPT_WARN_LINES = 120
_FAT_SCRIPT_FAIL_LINES = 200
_FAT_MIN_FUNCTIONS = 3


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _is_skipped_script(path: Path) -> bool:
    name = path.name
    if name.startswith("_") or name == "__init__.py":
        return True
    parts = path.parts
    if "fixtures" in parts:
        return True
    return False


def _count_non_trivial_functions(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    count = 0
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in _TRIVIAL_FUNC_NAMES or node.name.startswith("_parse_"):
            continue
        body_lines = sum(1 for child in ast.walk(node) if hasattr(child, "lineno") and child.lineno >= node.lineno)
        if body_lines > 8 or len(node.body) > 3:
            count += 1
    return count


def _uses_compute_imports(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _COMPUTE_IMPORTS or alias.asname in _COMPUTE_IMPORTS:
                    return True
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in _COMPUTE_IMPORTS:
                return True
    return False


def _is_subprocess_scheduler(path: Path, source: str) -> bool:
    if path.name not in _SUBPROCESS_SCHEDULER_NAMES:
        return False
    if "subprocess" not in source:
        return False
    return _count_non_trivial_functions(source) <= 1


def _analyze_script(path: Path, repo_root: Path) -> tuple[str | None, str | None]:
    """Return (severity, message) if the script violates thin-orchestrator rules."""
    if _is_skipped_script(path):
        return None, None
    source = path.read_text(encoding="utf-8")
    line_count = source.count("\n") + (1 if source and not source.endswith("\n") else 0)
    if _is_subprocess_scheduler(path, source):
        return None, None

    rel = _rel(path, repo_root)
    normalized = rel.replace("\\", "/")
    is_project_script = normalized.startswith("projects/") and "/scripts/" in normalized

    if is_project_script and line_count >= _PROJECT_SCRIPT_WARN_LINES:
        non_trivial = _count_non_trivial_functions(source)
        if line_count >= _FAT_SCRIPT_FAIL_LINES and non_trivial >= _FAT_MIN_FUNCTIONS:
            return (
                "ERROR",
                f"{rel}: {line_count} lines with {non_trivial} non-trivial functions (move logic to src/)",
            )
        if line_count >= _PROJECT_SCRIPT_WARN_LINES and non_trivial >= 1:
            return (
                "WARNING",
                f"{rel}: {line_count} lines — consider moving logic to src/",
            )

    if not is_project_script and line_count >= _FAT_SCRIPT_FAIL_LINES:
        non_trivial = _count_non_trivial_functions(source)
        if non_trivial >= _FAT_MIN_FUNCTIONS or _uses_compute_imports(source):
            return (
                "WARNING",
                f"{rel}: {line_count} lines — consider moving helpers to infrastructure/",
            )

    if _uses_compute_imports(source) and is_project_script:
        non_trivial = _count_non_trivial_functions(source)
        if non_trivial >= 2:
            return (
                "ERROR",
                f"{rel}: compute imports with {non_trivial} functions in script (move to src/)",
            )

    return None, None


def _iter_script_files(scripts_dir: Path) -> list[Path]:
    if not scripts_dir.is_dir():
        return []
    return sorted(p for p in scripts_dir.rglob("*.py") if p.is_file())


def check_project_scripts(
    project_root: Path,
    repo_root: Path,
    report: Report,
    project: str,
) -> None:
    scripts_dir = project_root / "scripts"
    for script in _iter_script_files(scripts_dir):
        severity, message = _analyze_script(script, repo_root)
        if severity and message:
            report.add(severity, project, "thin_orchestrator", message)


def check_repo_scripts(repo_root: Path, report: Report) -> None:
    scripts_dir = repo_root / "scripts"
    for script in _iter_script_files(scripts_dir):
        if "gates" in script.parts and script.name != "__init__.py":
            # Gate scripts checked after extraction; still analyze.
            pass
        severity, message = _analyze_script(script, repo_root)
        if severity and message:
            report.add(severity, "repo", "thin_orchestrator", message)
