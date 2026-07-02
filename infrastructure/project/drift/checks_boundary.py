"""Per-project drift checks for src/ ↔ infrastructure import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report

_STANDALONE_SRC_PROJECTS = frozenset(
    {
        "templates/template_active_inference",
        "templates/template_newspaper",
        "templates/template_textbook",
    }
)

_CODE_ADAPTER_ALLOWLIST = frozenset(
    {
        "src/analysis/_infra.py",
        "src/_runtime.py",
    }
)


def _load_layer_contract_allowlist(project_root: Path) -> set[str]:
    contract_path = project_root / "manuscript" / "layer_contract.yaml"
    if not contract_path.is_file():
        return set()
    loaded = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return set()
    raw = loaded.get("allow_infrastructure_imports", [])
    if not isinstance(raw, list):
        return set()
    return {str(entry).strip() for entry in raw if str(entry).strip()}


def _infra_imports_in_file(py_path: Path) -> list[str]:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    except SyntaxError:
        return []
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "infrastructure" or alias.name.startswith("infrastructure."):
                    hits.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "infrastructure" or node.module.startswith("infrastructure."):
                hits.append(f"from {node.module}")
    return hits


def check_project_src_infrastructure_boundary(
    project_root: Path,
    report: Report,
    project: str,
) -> None:
    """AST-scan ``src/**/*.py`` for ``infrastructure`` imports against layer contracts."""
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    allowlist = _load_layer_contract_allowlist(project_root)
    if project == "templates/template_code_project":
        allowlist |= _CODE_ADAPTER_ALLOWLIST
    strict = project in _STANDALONE_SRC_PROJECTS
    for py_path in sorted(src_dir.rglob("*.py")):
        rel_py = _rel(py_path, project_root)
        imports = _infra_imports_in_file(py_path)
        if not imports:
            continue
        if rel_py in allowlist:
            continue
        severity = "ERROR" if strict else "WARNING"
        joined = ", ".join(sorted(set(imports)))
        report.add(
            severity,
            project,
            "src_infrastructure_import",
            (
                f"{rel_py} imports infrastructure ({joined}) — "
                "domain src/ must stay standalone; use scripts/ or manuscript/layer_contract.yaml"
            ),
        )
