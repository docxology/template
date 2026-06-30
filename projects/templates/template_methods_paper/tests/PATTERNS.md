# Test Patterns Reference

Testing conventions for the `template_methods_paper` exemplar's zero-mock test
suite.

## Zero-Mock Enforcement

The following are **strictly forbidden** anywhere in this exemplar:

- `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or any mock factory.
- Synthetic result objects created solely to satisfy a type shape without
  running the real validation gate or compiler.
- Replacing `compile_method`/`run_all_gates` with a stub that never touches
  the real DAG scheduling or hash computation.

Every test exercises the real `src.methods_dsl` functions against a real
`Method` object — either one of the two worked examples
(`all_example_methods()`) or a fixture built in `conftest.py`. No
infrastructure is faked.

## Fixture Patterns

### Real `Method` objects, no mocks

```python
# conftest.py builds a real, fully-constructed Method per scenario
@pytest.fixture
def linear_method() -> Method:
    return Method(
        name="LinearDemo", version="1.0", target=Target.HUMAN,
        steps=(
            Step(step_id=1, name="Add water", kind=StepKind.ADD, target=Target.HUMAN,
                 parameters=(Parameter("volume", Quantity(10.0, "mL")),)),
            Step(step_id=2, name="Mix", kind=StepKind.MIX, target=Target.HUMAN, depends_on=(1,)),
            Step(step_id=3, name="Validate", kind=StepKind.VALIDATE, target=Target.HUMAN, depends_on=(2,)),
        ),
    )
```

### One fixture per gate-failure mode

`conftest.py` ships a fixture for every way a `Method` can fail a gate
(`unknown_dependency_method` → structural, `unknown_unit_method` → semantic,
`cyclic_method` → plan, `target_mismatch_method` → target). Add a new fixture
here, not an inline `Method(...)` literal, when testing a new failure mode.

### Temp output roots for script tests

`test_methods_analysis_script.py` runs `run_methods_analysis()` against
`tmp_path`, never the real project's `output/` directory:

```python
def test_run_methods_analysis_writes_expected_artifacts(tmp_path):
    written = run_methods_analysis(project_root=tmp_path)
    assert any(p.name == "compiled_plans.json" for p in written)
```

## Test Organisation

- Flat function-style tests: `def test_{what_is_being_tested}(...)`. This
  suite does not use class-based tests (no `class Test...` declarations) —
  see [AGENTS.md](AGENTS.md) before introducing one.
- Group tests by source module: `test_<module>.py` mirrors
  `src/methods_dsl/<module>.py` one-to-one.

## Determinism Assertions

```python
def test_compile_method_is_deterministic(linear_method):
    first = compile_method(linear_method)
    second = compile_method(linear_method)
    assert first.plan_hash == second.plan_hash
```

- Assert determinism by comparing two *live* compilations, never against a
  hardcoded hash string literal — a literal silently stops testing the moment
  the canonical-JSON payload's shape changes.
- For dimensional arithmetic, use `pytest.approx` for floating-point value
  comparisons; unit/dimension equality is exact (`==`) since both are enums
  or strings.

## Error-Path Testing

```python
def test_dimension_of_unknown_unit_raises():
    with pytest.raises(DimensionError, match="unknown unit"):
        dimension_of("furlongs")
```

- Always use `match=` to verify the error message content.
- Test every documented `Raises:` clause (`DimensionError`,
  `MethodModelError`, `CycleError`, `MethodValidationError`).

## Coverage Verification

```bash
uv run pytest projects/templates/template_methods_paper/tests \
    --cov=projects/templates/template_methods_paper/src \
    --cov-report=term-missing \
    --cov-fail-under=90
```

`pyproject.toml` enforces `fail_under = 90` as the CI gate. Live achieved
coverage is tracked in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).
Do not delete tests to make a number work — fix the gap.

## See Also

- [AGENTS.md](AGENTS.md) — Test conventions and rationale.
- [../src/STYLE.md](../src/STYLE.md) — How source code should be structured.
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — How scripts use this code.
- [../docs/testing_philosophy.md](../docs/testing_philosophy.md) — Zero-mock rationale.
