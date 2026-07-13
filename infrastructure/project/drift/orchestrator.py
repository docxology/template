"""Thin-orchestrator drift detection for scripts/ trees."""

from __future__ import annotations

import ast
from pathlib import Path

from infrastructure.core.files.serialization import relative_or_self as _rel
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
_ROOT_REUSABLE_HELPER_MIN_FUNCTIONS = 4
_ROOT_REUSABLE_HELPER_MIN_LINES = 1


def _is_skipped_script(path: Path) -> bool:
    name = path.name
    if name.startswith("_") or name == "__init__.py":
        return True
    parts = path.parts
    if "fixtures" in parts:
        return True
    return False


FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def _function_body_line_count(node: FunctionNode) -> int:
    """Approximate physical lines spanned by a function definition."""
    if not node.body:
        return 0
    end_lines = [
        getattr(child, "end_lineno", getattr(child, "lineno", node.lineno))
        for child in ast.walk(node)
        if hasattr(child, "lineno")
    ]
    return max(end_lines) - node.lineno + 1


def _function_complexity_score(node: FunctionNode) -> tuple[int, int]:
    """Return (ast_node_count, physical_line_span) for non-trivial heuristics."""
    node_count = sum(1 for child in ast.walk(node) if hasattr(child, "lineno") and child.lineno >= node.lineno)
    return node_count, _function_body_line_count(node)


def _count_non_trivial_functions(source: str, *, script_line_count: int = 0) -> int:
    tree = ast.parse(source)
    candidates: list[FunctionNode] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            candidates.append(node)
        elif isinstance(node, ast.ClassDef):
            candidates.extend(
                child for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    count = 0
    for node in candidates:
        if node.name.startswith("_parse_"):
            continue
        if node.name in _TRIVIAL_FUNC_NAMES:
            if node.name == "main" and script_line_count >= 150:
                _, physical_lines = _function_complexity_score(node)
                if physical_lines >= 120:
                    count += 1
            continue
        node_count, physical_lines = _function_complexity_score(node)
        if node_count > 8 or len(node.body) > 3 or physical_lines > 12:
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


def _is_subprocess_scheduler(path: Path, source: str, *, line_count: int) -> bool:
    if path.name not in _SUBPROCESS_SCHEDULER_NAMES:
        return False
    if "subprocess" not in source:
        return False
    return _count_non_trivial_functions(source, script_line_count=line_count) <= 1


def _analyze_script(path: Path, repo_root: Path) -> tuple[str | None, str | None]:
    """Return (severity, message) if the script violates thin-orchestrator rules."""
    if _is_skipped_script(path):
        return None, None
    source = path.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        rel = _rel(path, repo_root)
        return "ERROR", f"{rel}:{exc.lineno or 0}: syntax error: {exc.msg}"
    line_count = source.count("\n") + (1 if source and not source.endswith("\n") else 0)
    if _is_subprocess_scheduler(path, source, line_count=line_count):
        return None, None

    rel = _rel(path, repo_root)
    normalized = rel.replace("\\", "/")
    is_project_script = normalized.startswith("projects/") and "/scripts/" in normalized

    if is_project_script and line_count >= _PROJECT_SCRIPT_WARN_LINES:
        non_trivial = _count_non_trivial_functions(source, script_line_count=line_count)
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
        non_trivial = _count_non_trivial_functions(source, script_line_count=line_count)
        if non_trivial >= _FAT_MIN_FUNCTIONS or _uses_compute_imports(source):
            return (
                "WARNING",
                f"{rel}: {line_count} lines — consider moving helpers to infrastructure/",
            )

    if not is_project_script and line_count >= _ROOT_REUSABLE_HELPER_MIN_LINES:
        non_trivial = _count_non_trivial_functions(source, script_line_count=line_count)
        if non_trivial >= _ROOT_REUSABLE_HELPER_MIN_FUNCTIONS:
            return (
                "WARNING",
                f"{rel}: multiple reusable helpers ({non_trivial}); move logic to infrastructure/",
            )

    if _uses_compute_imports(source) and is_project_script:
        non_trivial = _count_non_trivial_functions(source, script_line_count=line_count)
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
    """Check project scripts."""
    scripts_dir = project_root / "scripts"
    for script in _iter_script_files(scripts_dir):
        severity, message = _analyze_script(script, repo_root)
        if severity and message:
            report.add(severity, project, "thin_orchestrator", message)


def check_repo_scripts(repo_root: Path, report: Report) -> None:
    """Check repo scripts."""
    scripts_dir = repo_root / "scripts"
    for script in _iter_script_files(scripts_dir):
        if "gates" in script.parts and script.name != "__init__.py":
            # Gate scripts checked after extraction; still analyze.
            pass
        severity, message = _analyze_script(script, repo_root)
        if severity and message:
            report.add(severity, "repo", "thin_orchestrator", message)
