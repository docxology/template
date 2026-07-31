"""Focused static contracts used by the public capability manifest."""

from __future__ import annotations

import ast
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from packaging.specifiers import InvalidSpecifier, Specifier, SpecifierSet
from packaging.utils import InvalidName, canonicalize_name
from packaging.version import InvalidVersion, Version

PACKAGE_NAME_OVERRIDES = {
    "templates/template_template": "template-template-meta-project",
}


@dataclass(frozen=True)
class SkipContract:
    """One statically discovered optional or fixture-dependent skip."""

    path: str
    line: int
    kind: str
    reason: str
    category: str


@dataclass(frozen=True)
class EntrypointContract:
    """Static compile and invocation-shape evidence for one Python entrypoint."""

    digest: str | None
    smoke: str
    issues: tuple[str, ...]
    evidence: tuple[str, ...]


def package_identity_contract(
    project: str,
    declared_name: str,
) -> tuple[str, str, tuple[str, ...], tuple[str, ...]]:
    """Bind a distribution name to its project using PEP 503 normalization."""
    expected_name = PACKAGE_NAME_OVERRIDES.get(project, Path(project).name)
    issues: list[str] = []
    try:
        normalized_name = str(canonicalize_name(declared_name, validate=True)) if declared_name else ""
    except InvalidName:
        normalized_name = ""
        issues.append(f"package name {declared_name!r} is not a valid distribution name")
    normalized_expected = str(canonicalize_name(expected_name))
    if declared_name and normalized_name != normalized_expected:
        issues.append(
            f"package name {declared_name!r} does not match project {project!r}; "
            f"expected {expected_name!r} after hyphen/underscore normalization"
        )
    evidence = (
        f"normalized-name={normalized_name or '<missing>'}",
        f"expected-name={expected_name}",
        f"identity-contract={'override' if project in PACKAGE_NAME_OVERRIDES else 'project-basename'}",
    )
    return normalized_name, expected_name, tuple(issues), evidence


def validate_unique_package_names(
    project_packages: Sequence[tuple[str, str]],
) -> tuple[str, ...]:
    """Require globally unique distribution identities after normalization."""
    normalized: list[tuple[str, str]] = []
    for project, name in project_packages:
        if not name:
            continue
        try:
            normalized.append((project, str(canonicalize_name(name, validate=True))))
        except InvalidName:
            continue
    counts = Counter(name for _, name in normalized)
    issues: list[str] = []
    for name in sorted(candidate for candidate, count in counts.items() if count > 1):
        projects = sorted(project for project, candidate in normalized if candidate == name)
        issues.append(f"normalized package name {name!r} is shared by projects: {', '.join(projects)}")
    return tuple(issues)


def python_minor_series_compatibility(
    requires_python: str,
    minor_series: Sequence[str],
) -> tuple[list[str], tuple[str, ...]]:
    """Prove that every stable patch release in each CI minor series is admitted."""
    if not requires_python:
        return ["cannot validate CI Python versions without requires-python"], ("specifier=<missing>",)
    try:
        specifier_set = SpecifierSet(requires_python)
    except InvalidSpecifier as exc:
        return [f"invalid requires-python specifier: {exc}"], (f"specifier={requires_python}",)

    issues: list[str] = []
    evidence: list[str] = [f"specifier={requires_python}"]
    for series in minor_series:
        parsed = _parse_minor_series(series)
        if parsed is None:
            issues.append(f"canonical CI Python selector {series!r} must be a major.minor series")
            evidence.append(f"python-{series}-series=invalid")
            continue
        major, minor = parsed
        incompatible = tuple(
            str(clause) for clause in specifier_set if not _clause_admits_minor_series(clause, major, minor)
        )
        compatible = not incompatible
        evidence.append(f"python-{series}-series={'compatible' if compatible else 'incompatible'}")
        if incompatible:
            issues.append(
                f"CI Python {series}.x series is not fully admitted by "
                f"requires-python {requires_python!r}; restrictive clauses: {', '.join(incompatible)}"
            )
    return issues, tuple(evidence)


def validate_python_files(
    paths: Sequence[Path],
    root: Path,
    *,
    label: str,
) -> tuple[list[str], tuple[str, ...]]:
    """Parse and compile every discovered Python file, failing closed on errors."""
    files = tuple(sorted(paths))
    issues: list[str] = []
    for path in files:
        relative = _relative(path, root)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(f"could not read {label} Python file {relative}: {type(exc).__name__}")
            continue
        try:
            tree = ast.parse(source, filename=relative)
            compile(tree, relative, "exec")
        except SyntaxError as exc:
            location = f":{exc.lineno}" if exc.lineno is not None else ""
            issues.append(f"{label} Python file does not compile: {relative}{location}: {exc.msg}")
        except ValueError as exc:
            issues.append(f"{label} Python file does not compile: {relative}: {exc}")
    evidence = (
        f"{label}-files={len(files)}",
        f"{label}-syntax={'fail' if issues else 'pass'}",
    )
    return issues, evidence


def validate_python_entrypoint(project_root: Path, entrypoint: str) -> EntrypointContract:
    """Compile a confined script and require an explicit callable CLI contract."""
    scripts_path = project_root / "scripts"
    scripts_root = scripts_path.resolve()
    relative = Path(entrypoint)
    issues: list[str] = []
    if relative.is_absolute() or ".." in relative.parts:
        issues.append(f"hydration entrypoint must be a confined relative script: {entrypoint!r}")
        return EntrypointContract(None, "failed", tuple(issues), (f"entrypoint={entrypoint}",))

    candidate = project_root / relative
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(scripts_root)
    except (OSError, ValueError):
        issues.append(f"hydration entrypoint escapes or is missing from scripts/: {entrypoint!r}")
        return EntrypointContract(None, "failed", tuple(issues), (f"entrypoint={entrypoint}",))
    cursor = candidate
    uses_symlink = False
    while cursor != project_root and cursor != cursor.parent:
        uses_symlink = uses_symlink or cursor.is_symlink()
        cursor = cursor.parent
    if uses_symlink:
        issues.append(f"hydration entrypoint must not traverse symlinks: {entrypoint!r}")
    if resolved.suffix != ".py" or not resolved.is_file():
        issues.append(f"hydration entrypoint must be a Python file: {entrypoint!r}")

    try:
        source = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(f"could not read hydration entrypoint {entrypoint!r}: {exc}")
        return EntrypointContract(None, "failed", tuple(issues), (f"entrypoint={entrypoint}",))
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    try:
        tree = ast.parse(source, filename=entrypoint)
        compile(tree, entrypoint, "exec")
    except (SyntaxError, ValueError) as exc:
        issues.append(f"hydration entrypoint does not compile: {entrypoint!r}: {exc}")
        return EntrypointContract(
            digest,
            "failed",
            tuple(issues),
            (f"entrypoint={entrypoint}", f"sha256={digest}", "compile=failed"),
        )

    has_main = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main" for node in tree.body
    )
    has_guard = any(_guard_directly_invokes_main(node) for node in tree.body if isinstance(node, ast.If))
    if not has_main:
        issues.append(f"hydration entrypoint must define top-level main(): {entrypoint!r}")
    if not has_guard:
        issues.append(f"hydration entrypoint must directly invoke main() under a __main__ guard: {entrypoint!r}")
    smoke = "static-compile-main-guard" if not issues else "failed"
    evidence = (
        f"entrypoint={entrypoint}",
        f"sha256={digest}",
        "compile=pass",
        f"main={'present' if has_main else 'missing'}",
        f"main-guard={'present' if has_guard else 'missing'}",
    )
    return EntrypointContract(digest, smoke, tuple(issues), evidence)


def discover_skip_contracts(tests_root: Path, repo_root: Path) -> Iterable[SkipContract]:
    """Discover imperative and decorator pytest skips, including bare markers."""
    if not tests_root.is_dir():
        return ()
    contracts: list[SkipContract] = []
    for path in sorted(tests_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError, ValueError):
            # ``validate_python_files`` reports this as a blocking manifest
            # issue; skip discovery remains best-effort so the report can
            # include every other deterministic finding in one invocation.
            continue
        skip_marker_calls: set[tuple[int, int]] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name in {"pytest.skip", "_pytest.skip", "pytest.importorskip"}:
                reason = _call_reason(node)
                if name == "pytest.importorskip":
                    reason = _keyword_reason(node) or (
                        f"optional import: {_literal_text(node.args[0]) or 'declared dependency'}"
                    )
                contracts.append(_skip_contract(path, repo_root, node.lineno, name, reason))
            elif name in {"pytest.mark.skip", "pytest.mark.skipif"}:
                # skipif's first positional argument is the condition, never
                # its explanation. Pytest requires ``reason=`` for that marker.
                reason = _keyword_reason(node) if name == "pytest.mark.skipif" else _call_reason(node)
                kind = name.rsplit(".", 1)[-1]
                contracts.append(_skip_contract(path, repo_root, node.lineno, kind, reason))
                if name == "pytest.mark.skip":
                    skip_marker_calls.add((node.func.lineno, node.func.col_offset))
        for owner in ast.walk(tree):
            if not isinstance(owner, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in owner.decorator_list:
                if (
                    isinstance(decorator, ast.Attribute)
                    and _call_name(decorator) == "pytest.mark.skip"
                    and (decorator.lineno, decorator.col_offset) not in skip_marker_calls
                ):
                    contracts.append(_skip_contract(path, repo_root, decorator.lineno, "skip", ""))
    return contracts


def _parse_minor_series(series: str) -> tuple[int, int] | None:
    parts = series.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    return int(parts[0]), int(parts[1])


def _clause_admits_minor_series(clause: Specifier, major: int, minor: int) -> bool:
    start = Version(f"{major}.{minor}.0")
    operator = clause.operator
    if operator in {">", ">="}:
        return clause.contains(start, prereleases=True)
    if operator in {"<", "<="}:
        try:
            bound = Version(clause.version)
        except InvalidVersion:
            return False
        if bound.epoch > 0:
            return True
        return bound.release[:2] > (major, minor)
    if operator == "~=":
        try:
            release = Version(clause.version).release
        except InvalidVersion:
            return False
        return len(release) <= 3 and clause.contains(start, prereleases=True)
    if operator == "==":
        if not clause.version.endswith(".*"):
            return False
        try:
            prefix = Version(clause.version[:-2]).release
        except InvalidVersion:
            return False
        return len(prefix) <= 2 and (major, minor)[: len(prefix)] == prefix
    if operator == "!=":
        return not _exclusion_intersects_minor_series(clause, major, minor)
    return False


def _exclusion_intersects_minor_series(clause: Specifier, major: int, minor: int) -> bool:
    raw_version = clause.version
    if raw_version.endswith(".*"):
        try:
            release = Version(raw_version[:-2]).release
        except InvalidVersion:
            return True
        if not release:
            return True
        if len(release) == 1:
            return release[0] == major
        return release[:2] == (major, minor)
    try:
        excluded = Version(raw_version)
    except InvalidVersion:
        return True
    if excluded.epoch != 0 or excluded.release[:2] != (major, minor):
        return False
    patch = excluded.release[2] if len(excluded.release) >= 3 else 0
    stable_patch = Version(f"{major}.{minor}.{patch}")
    return not clause.contains(stable_patch, prereleases=True)


def _skip_contract(
    path: Path,
    repo_root: Path,
    line: int,
    kind: str,
    reason: str,
) -> SkipContract:
    return SkipContract(
        path=_relative(path, repo_root),
        line=line,
        kind=kind.rsplit(".", 1)[-1],
        reason=reason,
        category=_skip_category(reason),
    )


def _call_reason(node: ast.Call) -> str:
    reason = _keyword_reason(node)
    if reason:
        return reason
    return _literal_text(node.args[0]) if node.args else ""


def _keyword_reason(node: ast.Call) -> str:
    for keyword in node.keywords:
        if keyword.arg == "reason":
            return _literal_text(keyword.value)
    return ""


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    left = _literal_text(node.left)
    right = _literal_text(node.comparators[0])
    return isinstance(node.ops[0], ast.Eq) and {left, right} == {"__name__", "__main__"}


def _guard_directly_invokes_main(node: ast.If) -> bool:
    """Require an executable top-level guard statement to evaluate ``main()``."""
    if not _is_main_guard(node.test):
        return False
    return any(_statement_invokes_main(statement) for statement in node.body)


def _statement_invokes_main(node: ast.stmt) -> bool:
    expressions: tuple[ast.AST | None, ...]
    if isinstance(node, ast.Expr):
        expressions = (node.value,)
    elif isinstance(node, ast.Raise):
        expressions = (node.exc, node.cause)
    elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        expressions = (node.value,)
    else:
        # Nested control flow, function/class definitions, and imports do not
        # prove that the guard itself invokes the hydration entrypoint.
        return False
    return any(expression is not None and _expression_invokes_main(expression) for expression in expressions)


def _expression_invokes_main(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if _call_name(node.func) == "main":
        return True
    # Wrappers such as ``raise SystemExit(main())`` and ``sys.exit(main())``
    # evaluate their call arguments immediately. Do not walk arbitrary child
    # expressions: lambdas, generators, boolean short-circuit branches, and
    # conditional expressions can all contain a syntactic call that never runs.
    return any(_expression_invokes_main(argument) for argument in node.args) or any(
        _expression_invokes_main(keyword.value) for keyword in node.keywords
    )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _literal_text(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
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
    "EntrypointContract",
    "PACKAGE_NAME_OVERRIDES",
    "SkipContract",
    "discover_skip_contracts",
    "package_identity_contract",
    "python_minor_series_compatibility",
    "validate_python_entrypoint",
    "validate_python_files",
    "validate_unique_package_names",
]
