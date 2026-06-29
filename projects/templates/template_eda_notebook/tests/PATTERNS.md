# Test Patterns Reference

Testing conventions for the `template_eda_notebook` exemplar's zero-mock test
suite.

## Zero-Mock Enforcement

The following are **strictly forbidden** anywhere in this exemplar:

- `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or any mock factory.
- Synthetic result objects created solely to satisfy a type shape without
  running the real computation.
- Replacing function bodies with stubs so tests never touch real pandas math.

Every test exercises the real `src.eda` functions against either the shipped
CSV fixture (`data/measurements.csv`) or a tiny real DataFrame / temp CSV built
in the test. No infrastructure is faked.

## Fixture Patterns

### Real data, no mocks

```python
# A tiny hand-built frame with values chosen so the expected stats are exact.
def _toy_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": ["alpha", "alpha", "beta", "beta"],
            "height_cm": [10.0, 20.0, 30.0, 40.0],
            "weight_kg": [1.0, 2.0, 3.0, 4.0],
            "resting_hr_bpm": [100.0, 90.0, 80.0, 70.0],
        }
    )
```

### Temp CSV files for the loader

Use the `tmp_path` fixture to write a real CSV and load it — never patch
`pandas.read_csv`:

```python
def test_explicit_path_round_trip(tmp_path):
    csv = tmp_path / "tiny.csv"
    csv.write_text("subject_id,group,height_cm,weight_kg,resting_hr_bpm\nA,alpha,180,80,60\n")
    frame = load_dataset(csv)
    assert frame["height_cm"].tolist() == [180.0]
```

## Test Class Organisation

- One test class per public function or behaviour.
- Class name: `Test{Thing}` — e.g. `TestLoadDataset`, `TestCorrelationMatrix`,
  `TestStrongestPairs`, `TestSummaryStatistics`, `TestNotebookSrcBinding`.
- Method names: `test_{what_is_being_tested}`.

The live class inventory lives in [AGENTS.md](AGENTS.md); keep the two in sync
(the `test_class_drift` drift rule fails if a doc names a class that does not
exist in `tests/`).

## Tolerance Constants

```python
np.testing.assert_allclose(matrix.to_numpy(), matrix.to_numpy().T, atol=1e-12)
assert abs(float(norm[column].mean())) < 1e-9
```

- Use `np.testing.assert_allclose` over `pytest.approx` for array/matrix checks.
- Pick designed values so the expected result is exact (e.g. `weight = 2 * height`
  gives a correlation of exactly `+1.0`).

## Error-Path Testing

```python
def test_negative_top_n_raises():
    matrix = correlation_matrix(clean)
    with pytest.raises(ValueError, match="top_n must be non-negative"):
        strongest_pairs(matrix, top_n=-1)
```

- Always use `match=` to verify the error message content.
- Test every documented `Raises` clause (`ValueError`, `KeyError`,
  `FileNotFoundError`).

## Notebook Binding

`test_notebook.py` reads the real `.ipynb` and asserts (1) it is valid
`nbformat`, (2) every name imported `from src` exists in `src.__all__`, and
(3) no code cell defines its own `def`/`class`. This enforces the
notebook -> tested src extraction contract structurally.

## Coverage Verification

```bash
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src \
    --cov-report=term-missing \
    --cov-fail-under=90
```

`pyproject.toml` enforces `fail_under = 90` as the CI gate. Live achieved
coverage is tracked in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).
Do not delete tests to make a number work — fix the gap.

## Determinism

- Prefer fixed, hand-chosen inputs; the shipped CSV is deterministic.
- The figure preparers are pure data transforms with no RNG.

## See Also

- [AGENTS.md](AGENTS.md) — Test class listing and run commands.
- [../src/STYLE.md](../src/STYLE.md) — How source code should be structured.
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — How scripts use this code.
- [../docs/testing_philosophy.md](../docs/testing_philosophy.md) — Zero-mock rationale.
