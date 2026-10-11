"""Fixed Code numeric DATA reconstruction under genuine held Source custody.

The normal Source-owned config loader and existing pre-import code audit are
reused. No loader callback, receipt flag, caller expectation or new native
capability is accepted. The enclosing adapter still admits Original execution,
current native operation, the generated-byte graph and every remaining axis.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from dataclasses import asdict
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any

import yaml

from infrastructure.core.bytecode_audit import canonical_code
from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_value_predicate import (
    ScalarQuadraticConfig,
    validate_explicit_scalar_config,
    validate_scalar_csv,
    validate_scalar_variables,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCOPE = "templates/template_code_project"
PACKAGE = "template_code_project"
PROJECT = f"projects/{SCOPE}"
SRC = f"{PROJECT}/src/{PACKAGE}"
CONFIG = f"{PROJECT}/manuscript/config.yaml"
LOADER = f"{SRC}/core/experiment_config.py"
CSV = f"{PROJECT}/output/data/optimization_results.csv"
VARIABLES = f"{PROJECT}/output/data/manuscript_variables.json"
REMAINING = (
    "genuine-original-analysis-and-leaf-process-request-runtime-output-consumption",
    "full-stability-grid-independent-report-value-and-figure-truth",
    "full-benchmark-dimension-independent-report-value-and-figure-truth",
    "all-other-generated-values-unit-sign-and-provenance-domains",
    "complete-native-semantic-and-visual-consumption-of-every-generated-occurrence",
)


def _binding(item: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": item.relative, "sha256": item.sha256, "bytes": len(item.content)}


def _normal_config(value: Any) -> ScalarQuadraticConfig:
    matrix, linear = value.quadratic_A, value.quadratic_b
    if (
        type(matrix) is not tuple
        or len(matrix) != 1
        or type(matrix[0]) is not tuple
        or len(matrix[0]) != 1
        or type(linear) is not tuple
        or len(linear) != 1
    ):
        raise ValueError("Code independent numeric predicate covers the authored scalar quadratic only")
    return ScalarQuadraticConfig(
        step_sizes=value.step_sizes,
        coefficient=matrix[0][0],
        linear=linear[0],
        initial_point=value.initial_point,
        max_iterations=value.max_iterations,
        tolerance=value.tolerance,
        convergence_tolerance=value.convergence_tolerance,
        stability_starting_points=value.stability_starting_points,
        stability_step_sizes=value.stability_step_sizes,
        benchmark_dimensions=value.benchmark_dimensions,
    )


def _source_functions(module: ModuleType, source: ArtifactSnapshot) -> None:
    """Bind the actual normal loader's functions to its full Source compilation."""
    compiled = compile(source.content, str(source.path), "exec", dont_inherit=True, optimize=sys.flags.optimize)
    expected = {code.co_name: code for code in compiled.co_consts if hasattr(code, "co_code")}
    names = [node.name for node in ast.parse(source.content).body if isinstance(node, ast.FunctionDef)]
    for name in names:
        function = getattr(module, name, None)
        if (
            not isinstance(function, FunctionType)
            or function.__globals__ is not module.__dict__
            or function.__module__ != module.__name__
            or function.__code__.co_filename != str(source.path)
            or name not in expected
            or canonical_code(function.__code__) != canonical_code(expected[name])
        ):
            raise ValueError("Code typed loader function differs from its full actual Source compilation")


def _loaded_source_modules(
    root: Path, package_root: Path, held: dict[str, ArtifactSnapshot], deadline: float
) -> list[dict[str, Any]]:
    closure = []
    for name, module in tuple(sys.modules.items()):
        if name != PACKAGE and not name.startswith(PACKAGE + "."):
            continue
        remaining(deadline)
        path_raw = getattr(module, "__file__", None)
        if not isinstance(path_raw, str):
            raise ValueError("Code package cannot substitute a namespace or module without physical Source")
        path = Path(path_raw).absolute()
        if path.is_symlink() or not path.is_relative_to(package_root) or path.resolve(strict=True) != path:
            raise ValueError("Code typed loader imported an unadmitted physical project Source")
        relative = path.relative_to(root).as_posix()
        if relative not in held or path != held[relative].path:
            raise ValueError("Code typed loader imported outside its complete held Python Source roster")
        closure.append({"module": name, **_binding(held[relative])})
    if not closure or not any(row["path"] == LOADER for row in closure):
        raise ValueError("Code numeric reconstruction lacks the actual Source-owned config loader")
    return sorted(closure, key=lambda row: row["module"])


def reconstruct_code_numeric_consumption(
    source: NativeSourceContext, reader: SnapshotReader, *, deadline: float
) -> dict[str, Any]:
    """Compare held full CSV and recognized variable meanings independently.

    A complete fresh pre-import Source audit is required before importing the
    fixed project's ordinary package. This function does not start a worker,
    infer native Original authority or turn its DATA graph into admission.
    """
    if not isinstance(source, NativeSourceContext) or reader.root != source.bindings.current_root:
        raise ValueError("Code numeric reconstruction requires genuine held Source and the exact current root")
    remaining(deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    prefix = source.fresh_pycache_prefix
    if prefix is None or sys.pycache_prefix is None or Path(sys.pycache_prefix).absolute() != prefix.absolute():
        raise ValueError("Code numeric loader requires its independently launched fresh code-audit prefix")
    package_root = reader.root / SRC
    # This existing API checks that the root belonged to the original
    # pre-import audit; an empty current import roster cannot invent it.
    verify_fresh_module_bytecode(package_root, prefix)
    names = tuple(
        relative
        for relative, kind, _ in source.source_records
        if kind == "file" and relative.startswith(SRC + "/") and relative.endswith(".py")
    )
    if not 0 < len(names) <= 128 or len(set(names)) != len(names):
        raise ValueError("Code numeric loader needs its complete bounded unique Source Python roster")
    held: dict[str, ArtifactSnapshot] = {}
    for relative in sorted(names):
        remaining(deadline)
        item = reader.read(relative, max_bytes=1024 * 1024)
        if item.content != source.reference.read(relative):
            raise ValueError("Code numeric loader Source differs from the independently held original")
        held[relative] = item
    config = reader.read(CONFIG, max_bytes=1024 * 1024)
    if config.content != source.reference.read(CONFIG):
        raise ValueError("Code numeric configuration differs from independently held original Source")
    for name, module in tuple(sys.modules.items()):
        if name == PACKAGE or name.startswith(PACKAGE + "."):
            origin = getattr(module, "__file__", None)
            if not isinstance(origin, str) or not Path(origin).absolute().is_relative_to(package_root):
                raise ValueError("Code Source package name is already occupied by a different project")
    import_root = str(reader.root / PROJECT / "src")
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, import_root)
        module = importlib.import_module(PACKAGE + ".core.experiment_config")
    finally:
        sys.path[:] = previous_path
    _loaded_source_modules(reader.root, package_root, held, deadline)
    verify_fresh_module_bytecode(package_root, prefix)
    _source_functions(module, held[LOADER])
    typed = module.load_experiment_config(reader.root / PROJECT)
    if type(typed) is not module.ExperimentConfig:
        raise ValueError("Code Source loader did not return its actual fixed typed configuration")
    normalized = _normal_config(typed)
    # Reuse the existing Source-owned bounded YAML ambiguity check, then bind
    # every typed field to explicit authenticated declarations. Module/class
    # state replacement cannot choose the purported Source config DATA.
    from infrastructure.reporting.native_format_html_source_metadata import require_unambiguous_yaml

    remaining(deadline)
    require_unambiguous_yaml(config.content)
    authored_config = yaml.safe_load(config.content)
    if not isinstance(authored_config, dict) or not isinstance(authored_config.get("experiment"), dict):
        raise ValueError("Code independent numeric proof requires its actual explicit authored experiment")
    validate_explicit_scalar_config(normalized, authored_config["experiment"])
    remaining(deadline)
    csv = reader.read(CSV, max_bytes=1024 * 1024)
    variables = reader.read(VARIABLES, max_bytes=4 * 1024 * 1024)
    rows = validate_scalar_csv(normalized, csv.content, deadline=deadline)
    decoded = variables.json_object()
    checked = validate_scalar_variables(normalized, csv.content, decoded, deadline=deadline)
    closure = _loaded_source_modules(reader.root, package_root, held, deadline)
    _source_functions(module, held[LOADER])
    verify_fresh_module_bytecode(package_root, prefix)
    body = {
        "schema": "template-native-code-scalar-value-consumption-v1",
        "scope": SCOPE,
        "source_identity": source.reference.source_identity,
        "config": _binding(config),
        "complete_python_source_roster": [_binding(held[name]) for name in sorted(held)],
        "actual_audited_loader_import_closure": closure,
        "normalized_scalar_config": asdict(normalized),
        "csv": _binding(csv),
        "variables": _binding(variables),
        "complete_serialized_scalar_rows": [list(row) for row in rows],
        "independently_checked_variable_names": list(checked),
        "unqualified_variable_names": sorted(set(decoded) - set(checked)),
        "independent_algorithm": "stdlib-binary64-scalar-quadratic-full-grid-last-finite-state",
        "remaining_obligations": list(REMAINING),
        "claim_boundary": "partial-scalar-DATA-math-and-config-result-token-meaning-only",
    }
    if hashlib.sha256(reader.read(CONFIG).content).hexdigest() != config.sha256 or not reader.unchanged():
        raise ValueError("Code Source, configuration or complete generated bodies changed during reconstruction")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    verify_fresh_module_bytecode(package_root, prefix)
    remaining(deadline)
    if not reader.unchanged():
        raise ValueError("Code Source/current artifacts changed during closing execution custody")
    return {**body, "content_digest": canonical_digest(body)}
