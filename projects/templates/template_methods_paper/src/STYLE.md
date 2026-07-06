# Source Code Style Guide

Code style and design conventions for `src/` modules in the
`template_methods_paper` exemplar.

## Immutable, Side-Effect-Free Model Types

Every DSL value type (`Quantity`, `Parameter`, `Resource`, `Step`, `Method`,
`Plan`, `PlanStep`, `GateResult`, `StateRecord`) is a frozen `@dataclass`.
Validation gates and the compiler never mutate their input; they return new
values (`GateResult`, `Plan`) or raise on invalid input.

```python
# ✅ CORRECT: returns a new value; never mutates the input Method
def compile_method(method: Method) -> Plan:
    gate_results = run_all_gates(method)
    ...
    return Plan(method_name=method.name, ...)

# ❌ WRONG: mutates an attribute on a frozen dataclass (would raise anyway)
def compile_method(method: Method) -> Plan:
    method.steps = sorted(method.steps, key=...)  # frozen dataclasses reject this
```

Plotting, file I/O, and orchestration belong in `scripts/`, never in
`src/methods_dsl/`. This is why every exporter in `export.py` returns text or
takes an explicit `path: Path` argument rather than reaching for a global
output directory.

## Type Hints

Every public function and dataclass field has complete annotations. Use
`Quantity | None` for optional unit-bearing fields, `tuple[X, ...]` (never
`list[X]`) for dataclass collection fields so instances stay hashable and
immutable, and `Path` for filesystem arguments.

```python
def compile_method(method: Method) -> Plan: ...
def append_record(chain: tuple[StateRecord, ...], key: str, value: str, tier: ProvenanceTier) -> tuple[StateRecord, ...]: ...
```

## Docstring Format

reStructuredText-style docstrings with `Raises:` clauses on every function
that validates input:

```python
def topological_order(method: Method) -> tuple[Step, ...]:
    """Return *method*'s steps in a deterministic dependency-respecting order.

    Raises:
        CycleError: If the dependency graph is not acyclic.
    """
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `compile_method`, `topological_order` |
| Classes | `PascalCase` | `Method`, `GateResult`, `PlanStep` |
| Enum members | `UPPER_SNAKE` | `StepKind.TRANSFER`, `Target.AUTOMATED` |
| Private | `_leading_underscore` | `_compute_plan_hash`, `_GENESIS_HASH` |
| Parameters | descriptive `snake_case` | `step_id`, `expected_duration` |

## Determinism Idioms

```python
# ✅ Stable iteration order — never rely on dict/set iteration for scheduling
ready = sorted(step_id for step_id, deps in remaining_deps.items() if ...)

# ✅ Canonical JSON before hashing — sort_keys + fixed separators
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
plan_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

- Never iterate a `dict`/`set` directly when the order affects an output the
  manuscript reports (a `plan_hash`, a scheduled order); sort explicitly.
- Honor `SOURCE_DATE_EPOCH` for any wall-clock timestamp that reaches a
  manuscript token (`src/manuscript_variables.py::_build_timestamp`).

## Error Handling

- Validate inputs at construction time (`Step.__post_init__`,
  `Method.__post_init__`) for shape errors; validate cross-step invariants in
  `validation.py`'s gates, which run later and report every issue instead of
  raising on the first one.
- Use `ValueError` subclasses (`MethodModelError`, `DimensionError`,
  `CycleError`, `MethodValidationError`) so callers can catch the DSL's error
  surface with one `except` clause if desired.
- Never catch and silently swallow exceptions (no blanket `except Exception`).

## Module Exports

`src/__init__.py` re-exports the full public API from `src.methods_dsl`, so
callers can write `from src import compile_method`. The export set is kept in
sync with `src/methods_dsl/__init__.py` — drift is caught by
`scripts/audit/check_template_drift.py`'s `__all___doc_drift` rule:

```python
__all__ = [
    "CycleError", "Dimension", "DimensionError", "GateResult", "Method",
    "MethodModelError", "MethodValidationError", "Parameter", "Plan",
    "PlanStep", "ProvenanceTier", "Quantity", "Resource", "StateRecord",
    "Step", "StepKind", "Target", "all_example_methods", "append_record",
    "check_compatible", "compile_method", "demo_chain_report", "dimension_of",
    "known_units", "pbs_preparation_method", "plan_gate", "run_all_gates",
    "semantic_gate", "sensor_calibration_method", "structural_gate",
    "target_accepts", "target_gate", "to_csv_rows", "to_json", "to_mermaid",
    "to_worklist_markdown", "topological_order", "verify_chain",
    "write_all_exports", "write_csv", "write_json", "write_json_report",
]
```

`src/project_paths.py` and `src/manuscript_variables.py` expose orchestration
and rendering plumbing (`project_output_dirs`, `resolve_project_root`,
`generate_variables`, `save_variables`) used by `scripts/`; they are
intentionally NOT in `__init__.py.__all__`, mirroring `template_code_project`'s
convention.

## See Also

- [AGENTS.md](AGENTS.md) — API reference and infrastructure integration.
- [../tests/PATTERNS.md](../tests/PATTERNS.md) — How to test code written here.
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — How scripts use this code.
