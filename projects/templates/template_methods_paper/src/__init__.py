"""Methods-paper exemplar — tested controlled-method specification library.

This project demonstrates the *methods paper* research archetype: the
manuscript's subject is the methodology itself — a small domain language for
specifying, validating, and deterministically compiling controlled procedures
(``methods_dsl``) — rather than results produced by running a method.

The DSL's vocabulary is informed by BPL (Biology Programming Language,
https://gitlab.com/bota-biosciences-public/bpl-code), an upstream reference
for representing controlled-system protocols as programs with biology-native
types, staged validation, and deterministic compilation. See
``docs/architecture.md`` for the correspondence between this DSL's stages and
BPL's compiler pipeline.

All DSL logic lives in the ``src.methods_dsl`` subpackage and is re-exported
here so callers (scripts, tests, manuscript variable generation) can write
``from src import compile_method, run_all_gates``.
"""

from __future__ import annotations

from .methods_dsl import (
    CycleError,
    Dimension,
    DimensionError,
    GateResult,
    Method,
    MethodModelError,
    MethodValidationError,
    Parameter,
    Plan,
    PlanStep,
    ProvenanceTier,
    Quantity,
    Resource,
    StateRecord,
    Step,
    StepKind,
    Target,
    all_example_methods,
    append_record,
    check_compatible,
    compile_method,
    demo_chain_report,
    dimension_of,
    known_units,
    pbs_preparation_method,
    plan_gate,
    run_all_gates,
    semantic_gate,
    sensor_calibration_method,
    structural_gate,
    target_accepts,
    target_gate,
    to_csv_rows,
    to_json,
    to_mermaid,
    to_worklist_markdown,
    topological_order,
    verify_chain,
    write_all_exports,
    write_csv,
    write_json,
    write_json_report,
)

__all__ = [
    "CycleError",
    "Dimension",
    "DimensionError",
    "GateResult",
    "Method",
    "MethodModelError",
    "MethodValidationError",
    "Parameter",
    "Plan",
    "PlanStep",
    "ProvenanceTier",
    "Quantity",
    "Resource",
    "StateRecord",
    "Step",
    "StepKind",
    "Target",
    "all_example_methods",
    "append_record",
    "check_compatible",
    "compile_method",
    "demo_chain_report",
    "dimension_of",
    "known_units",
    "pbs_preparation_method",
    "plan_gate",
    "run_all_gates",
    "semantic_gate",
    "sensor_calibration_method",
    "structural_gate",
    "target_accepts",
    "target_gate",
    "to_csv_rows",
    "to_json",
    "to_mermaid",
    "to_worklist_markdown",
    "topological_order",
    "verify_chain",
    "write_all_exports",
    "write_csv",
    "write_json",
    "write_json_report",
]
