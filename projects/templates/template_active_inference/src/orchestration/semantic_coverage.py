"""Fail-closed semantic-sheaf selector discovery for coverage orchestration."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

SEMANTIC_SHEAF_COVERAGE_MODULE = "tests/test_semantic_sheaf.py"
SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_LABEL = "Semantic sheaf certificate integrity checks"
SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_LABEL = "Semantic dependency, evidence, and manuscript checks"
SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_SELECTORS = (
    "tests/test_semantic_sheaf.py::test_semantic_certificate_covers_tracks_symbols_and_variables",
    "tests/test_semantic_sheaf.py::test_semantic_certificate_key_surface_is_stable",
    "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_wrong_si_ontology",
    "tests/test_semantic_sheaf.py::test_semantic_certificate_is_written_as_generated_artifact",
    "tests/test_semantic_sheaf.py::test_semantic_outputs_settle_contract_and_staleness_artifacts",
    "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_stale_saved_certificate",
    "tests/test_semantic_sheaf.py::test_semantic_validators_reject_forged_omitted_certificate_fields",
    "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_missing_or_malformed_saved_certificate",
)
SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_SELECTORS = (
    "tests/test_semantic_sheaf.py::test_dependency_graph_rejects_required_artifact_without_configured_producer",
    "tests/test_semantic_sheaf.py::test_dependency_graph_distinguishes_missing_from_unconfigured_existing",
    "tests/test_semantic_sheaf.py::test_semantic_gluing_rejects_mutated_policy_posterior",
    "tests/test_semantic_sheaf.py::test_semantic_certificate_records_lean_graph_world_topology_witnesses",
    "tests/test_semantic_sheaf.py::test_typed_claim_evidence_rejects_wrong_expected_value",
    "tests/test_semantic_sheaf.py::test_typed_claim_evidence_supports_structured_predicates",
    "tests/test_semantic_sheaf.py::test_validate_manuscript_checks_semantic_certificate",
)


def _decorator_leaf_name(decorator: ast.expr) -> str:
    """Return the final identifier in a decorator expression."""
    current = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(current, ast.Attribute):
        return current.attr
    if isinstance(current, ast.Name):
        return current.id
    return ""


def _pytest_marker_name(expression: ast.expr) -> str | None:
    """Return the name of a static ``pytest.mark.<name>`` attribute."""
    if not isinstance(expression, ast.Attribute):
        return None
    namespace = expression.value
    if not isinstance(namespace, ast.Attribute) or namespace.attr != "mark":
        return None
    if not isinstance(namespace.value, ast.Name) or namespace.value.id != "pytest":
        return None
    return expression.attr


def semantic_sheaf_test_selectors(project_root: Path) -> list[str]:
    """Derive supported semantic-sheaf pytest node selectors in source order."""
    path = project_root / SEMANTIC_SHEAF_COVERAGE_MODULE
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"semantic sheaf coverage source must be a regular file: {path}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RuntimeError(f"cannot parse semantic sheaf coverage source {path}: {exc}") from exc

    selectors: list[str] = []
    unsupported: list[str] = []
    pytestmark_count = 0
    allowed_imports = frozenset(
        {
            ("from", "__future__", 0, (("annotations", None),)),
            ("import", "", 0, (("json", None),)),
            ("from", "pathlib", 0, (("Path", None),)),
            ("import", "", 0, (("pytest", None),)),
            (
                "from",
                "gate_support",
                0,
                (
                    ("ensure_gate_artifacts", None),
                    ("temporary_json_mutation", None),
                    ("temporary_text_mutation", None),
                ),
            ),
        }
    )
    for index, node in enumerate(tree.body):
        line = getattr(node, "lineno", 0)
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                signature = ("import", "", 0, tuple((alias.name, alias.asname) for alias in node.names))
            else:
                signature = (
                    "from",
                    node.module or "",
                    node.level,
                    tuple((alias.name, alias.asname) for alias in node.names),
                )
            if signature not in allowed_imports:
                unsupported.append(f"line {line}: unsupported import {signature}")
            continue
        if isinstance(node, ast.Assign):
            marker_names: list[str | None] = []
            if isinstance(node.value, (ast.List, ast.Tuple)):
                marker_names = [_pytest_marker_name(item) for item in node.value.elts]
            if (
                len(node.targets) != 1
                or not isinstance(node.targets[0], ast.Name)
                or node.targets[0].id != "pytestmark"
                or marker_names != ["slow", "requires_gate_artifacts"]
            ):
                unsupported.append(f"line {line}: unsupported top-level assignment")
            else:
                pytestmark_count += 1
            continue
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith("test_"):
                unsupported.append(f"line {line}: top-level helper function {node.name}")
                continue
            if any(_decorator_leaf_name(decorator) == "parametrize" for decorator in node.decorator_list):
                unsupported.append(f"line {line}: parametrized test {node.name}")
                continue
            if node.decorator_list:
                unsupported.append(f"line {line}: decorated test {node.name}")
                continue
            if node.args.defaults or any(default is not None for default in node.args.kw_defaults):
                unsupported.append(f"line {line}: test with import-time default expression {node.name}")
                continue
            if any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node)):
                unsupported.append(f"line {line}: generator-style test {node.name}")
                continue
            selectors.append(f"{SEMANTIC_SHEAF_COVERAGE_MODULE}::{node.name}")
            continue
        node_name = getattr(node, "name", type(node).__name__)
        unsupported.append(f"line {line}: unsupported top-level {type(node).__name__} {node_name}")

    if pytestmark_count != 1:
        unsupported.append(f"pytestmark assignments: expected 1, found {pytestmark_count}")
    counts = Counter(selectors)
    duplicates = sorted(selector for selector, count in counts.items() if count != 1)
    if duplicates:
        unsupported.append(f"duplicate test definitions: {duplicates}")
    if unsupported:
        raise RuntimeError(
            "semantic sheaf coverage requires a static module with top-level, nonparametrized test_* functions only: "
            + "; ".join(unsupported)
        )
    if not selectors:
        raise RuntimeError("semantic sheaf coverage source declares no supported test_* functions")
    return selectors
