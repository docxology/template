"""Standalone scientific modules and declared verifier SDK boundary.

Scientific modules must import without the platform or sibling projects. The
verifier launcher may call only its declared, exact-version development SDK
interfaces; undeclared imports and cross-project imports remain forbidden.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import pkgutil
import tomllib
from pathlib import Path
from typing import Any, Callable, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
FORBIDDEN_ROOTS = ("infrastructure", "projects")
# Directories whose .py files must stay free of monorepo imports.
GUARDED_DIRS = ("src", "scripts", "tests")


def _declared_verifier_sdk_imports(py_file: Path, project_root: Path) -> dict[str, frozenset[str]]:
    if py_file.resolve() != (project_root / "src/orchestration/_verification_launcher.py").resolve():
        return {}
    try:
        metadata = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        version = metadata["tool"]["template"]["platform_version"]
        dependencies = metadata["project"]["optional-dependencies"]["dev"]
    except OSError, KeyError, tomllib.TOMLDecodeError:
        return {}
    if (
        not isinstance(version, str)
        or not isinstance(dependencies, list)
        or not all(isinstance(item, str) for item in dependencies)
        or f"research-project-template=={version}" not in dependencies
    ):
        return {}
    return {
        "infrastructure.core.testing.project_test_runtime": frozenset(
            {"build_audited_project_test_command", "ProjectTestRuntimeError", "admit_project_test_runtime"}
        ),
        "infrastructure.core.runtime.python_binding": frozenset({"analysis_runtime_binding"}),
    }


def _forbidden_imports(py_file: Path, *, project_root: Path = PROJECT_ROOT) -> list[str]:
    """Return undeclared platform or cross-project imports in a genuine source file."""
    admitted = _declared_verifier_sdk_imports(py_file, project_root)
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except SyntaxError:  # pragma: no cover - a syntax error is a different test's job
        return []
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOTS:
                    hits.append(f"{py_file.name}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            # Absolute imports only (node.level == 0); relative imports stay in-package.
            if node.level == 0 and node.module:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_ROOTS and not {alias.name for alias in node.names}.issubset(
                    admitted.get(node.module, frozenset())
                ):
                    hits.append(f"{py_file.name}: from {node.module} import ...")
    return hits


def test_no_infrastructure_or_cross_project_imports() -> None:
    """Only the explicitly declared development verifier may call its SDK interfaces."""
    violations: list[str] = []
    for rel in GUARDED_DIRS:
        base = PROJECT_ROOT / rel
        if not base.is_dir():
            continue
        for py_file in base.rglob("*.py"):
            if ".egg-info" in py_file.parts:
                continue
            violations.extend(_forbidden_imports(py_file))
    assert not violations, "monorepo imports break standalone publishability:\n" + "\n".join(violations)


def test_every_src_module_imports_with_infrastructure_blocked() -> None:
    """Clean-room proof: every src module imports with `infrastructure` removed.

    Installs an import hook that raises on any `infrastructure` import, then imports
    every discovered src module. A standalone checkout has no `infrastructure`, so a
    hidden runtime dependency would surface here, not in production.
    """
    real_import = cast(Callable[..., object], builtins.__import__)

    def blocking_import(name: str, *args: Any, **kwargs: Any) -> object:
        if name == "infrastructure" or name.startswith("infrastructure."):
            raise AssertionError(f"self-containment violation: imported {name}")
        return real_import(name, *args, **kwargs)

    violations: list[str] = []
    imported = 0
    builtins.__dict__["__import__"] = blocking_import
    try:
        for mod in pkgutil.walk_packages([str(SRC)]):
            try:
                importlib.import_module(mod.name)
                imported += 1
            except AssertionError as exc:
                violations.append(f"{mod.name}: {exc}")
            except Exception as exc:  # noqa: BLE001 - only infra-caused failures are violations
                if "infrastructure" in str(exc):
                    violations.append(f"{mod.name}: {exc}")
    finally:
        builtins.__dict__["__import__"] = real_import

    assert imported > 0, "no src modules were discovered"
    assert not violations, "src modules require infrastructure at import time:\n" + "\n".join(violations)


@pytest.mark.parametrize("required", ["pyproject.toml", "README.md", "src", "tests", "manuscript"])
def test_standalone_repo_skeleton_present(required: str) -> None:
    """A standalone GitHub repo needs these top-level entries."""
    assert (PROJECT_ROOT / required).exists(), f"standalone repo missing {required}"


@pytest.mark.parametrize(
    "relative,dependency,module,name,accepted",
    [
        (
            "src/orchestration/_verification_launcher.py",
            "research-project-template==4.0.1",
            "infrastructure.core.runtime.python_binding",
            "analysis_runtime_binding",
            True,
        ),
        (
            "src/orchestration/_verification_launcher.py",
            "research-project-template==3.8.0",
            "infrastructure.core.runtime.python_binding",
            "analysis_runtime_binding",
            False,
        ),
        (
            "src/orchestration/_verification_launcher.py",
            "",
            "infrastructure.core.runtime.python_binding",
            "analysis_runtime_binding",
            False,
        ),
        (
            "src/analysis.py",
            "research-project-template==4.0.1",
            "infrastructure.core.runtime.python_binding",
            "analysis_runtime_binding",
            False,
        ),
        (
            "src/orchestration/_verification_launcher.py",
            "research-project-template==4.0.1",
            "infrastructure.core.runtime.python_binding",
            "*",
            False,
        ),
        (
            "src/orchestration/_verification_launcher.py",
            "research-project-template==4.0.1",
            "infrastructure.core.pipeline",
            "PipelineRunner",
            False,
        ),
        (
            "src/orchestration/_verification_launcher.py",
            "research-project-template==4.0.1",
            "projects.template_code_project",
            "run",
            False,
        ),
    ],
)
def test_declared_sdk_boundary_refuses_undeclared_source_imports(
    tmp_path: Path, relative: str, dependency: str, module: str, name: str, accepted: bool
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        f'[project.optional-dependencies]\ndev = ["{dependency}"]\n[tool.template]\nplatform_version = "4.0.1"\n',
        encoding="utf-8",
    )
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_text(f"from {module} import {name}\n", encoding="utf-8")
    assert bool(_forbidden_imports(source, project_root=tmp_path)) is not accepted
