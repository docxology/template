"""``methods_dsl`` — a small, tested domain language for specifying controlled methods.

Public surface, grouped by the BPL-inspired pipeline stage it belongs to
(see ``docs/architecture.md`` and ``manuscript/02_methodology.md``):

- **Model** (``model.py``): :class:`Method`, :class:`Step`, :class:`Resource`,
  :class:`Parameter`, :class:`MethodModelError`.
- **Units** (``units.py``): :class:`Quantity`, :class:`Dimension`,
  :class:`DimensionError`.
- **Vocabulary** (``vocabulary.py``): :class:`StepKind`, :class:`Target`.
- **Validation** (``validation.py``): :class:`GateResult`, the four gate
  functions, and :func:`run_all_gates`.
- **Compiler** (``compiler.py``): :class:`Plan`, :class:`PlanStep`,
  :func:`compile_method`, :func:`topological_order`,
  :class:`MethodValidationError`, :class:`CycleError`.
- **Export** (``export.py``): worklist/CSV/Mermaid/JSON renderers.
- **Trust** (``trust.py``): :class:`ProvenanceTier`, :class:`StateRecord`,
  hash-chain helpers.
- **Examples** (``examples_methods.py``): worked example methods.
"""

from __future__ import annotations

from .compiler import (
    CycleError,
    MethodValidationError,
    Plan,
    PlanStep,
    compile_method,
    topological_order,
)
from .examples_methods import (
    all_example_methods,
    pbs_preparation_method,
    sensor_calibration_method,
)
from .export import (
    to_csv_rows,
    to_json,
    to_mermaid,
    to_worklist_markdown,
    write_all_exports,
    write_csv,
    write_json,
    write_json_report,
)
from .model import Method, MethodModelError, Parameter, Resource, Step
from .trust import ProvenanceTier, StateRecord, append_record, demo_chain_report, verify_chain
from .units import Dimension, DimensionError, Quantity, check_compatible, dimension_of, known_units
from .validation import GateResult, plan_gate, run_all_gates, semantic_gate, structural_gate, target_gate
from .vocabulary import StepKind, Target, target_accepts

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
