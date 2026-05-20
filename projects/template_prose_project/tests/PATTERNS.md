# Test Patterns Reference — template_prose_project

Testing conventions and copy-pasteable patterns for the
`template_prose_project` zero-mock test suite. Sibling of
[`template_code_project/tests/PATTERNS.md`](../../template_code_project/tests/PATTERNS.md);
the rules below adapt the same zero-mock discipline to prose / BibTeX /
filesystem I/O.

## Zero-Mock Enforcement

Forbidden everywhere under `tests/`:

- `import unittest.mock`
- `MagicMock`, `Mock`, `AsyncMock`, `create_autospec`
- `@patch(...)`
- `monkeypatch.setattr(...)` *when used as a mock factory*
  (substituting a real function with a fake callable). Note:
  `monkeypatch.chdir`, `monkeypatch.setenv` are NOT mocking — those
  isolate the process state and are allowed.

Every test exercises real Markdown, real BibTeX, real `Path`s, and (for
script tests) real subprocesses.

## Standard Fixture Patterns

### Real manuscript on `tmp_path`

```python
def test_check_against_real_manuscript(tmp_path: Path):
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_intro.md").write_text(
        "# Intro\n\nThis is a real paragraph with real words.\n",
        encoding="utf-8",
    )
    (manuscript_dir / "references.bib").write_text(
        '@article{smith2020, title={A}, author={Smith, J.}, year={2020}}\n',
        encoding="utf-8",
    )

    config = ProjectConfig(
        manuscript_dir=manuscript_dir,
        prose=ProseAnalysisConfig(target_grade_level_min=0, target_grade_level_max=30),
        bibliography=BibliographyConfig(
            references_path=manuscript_dir / "references.bib",
            fail_on_missing=False,
            fail_on_unused=False,
        ),
        report=ReportConfig(output_path=tmp_path / "review.md"),
    )

    artifacts = run_prose_pipeline(config, project_root=tmp_path)
    assert artifacts.all_passed
```

### Real BibTeX builder

Tests covering `_check_bibliography` (which emits
`CheckResult(name="bibliography_consistency")`) write small but valid
`.bib` files and let `infrastructure.reference.citation.parse_bibfile`
parse them:

```python
def _write_bib(path: Path, entries: dict[str, dict[str, str]]) -> Path:
    """Write a minimal BibTeX file. Keys → fields → values."""
    parts = []
    for key, fields in entries.items():
        field_str = ", ".join(f'{k}={{{v}}}' for k, v in fields.items())
        parts.append(f"@article{{{key}, {field_str}}}\n")
    path.write_text("".join(parts), encoding="utf-8")
    return path
```

Never mock the `BibDatabase` return value — write the bytes, let the
parser run, assert on the resulting `CheckResult.details`.

### Real subprocess for scripts

`test_scripts.py` invokes the orchestrator scripts via
`subprocess.run`, with real argparse, real exit codes, and real
output-file existence checks:

```python
def test_run_prose_pipeline_offline(tmp_path: Path):
    iso = _setup_isolated(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_prose_pipeline.py"),
            "--config", str(iso / "manuscript" / "config.yaml"),
            "--project-root", str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (iso / "output" / "manuscript_report.json").exists()
```

The `_setup_isolated(tmp_path)` helper copies the bundled `manuscript/`
into a clean tree so subprocess tests never write into the project's
own `output/`.

## Test Class Organisation

| Class | Tests | Covers |
|---|---|---|
| `TestRunProsePipeline` | end-to-end calls | `src/pipeline.py::run_prose_pipeline` |
| `TestCheckGradeLevel` | `_check_grade_level` | one check function per test class |
| `TestCheckCitationDensity` | `_check_citation_density` | one check function per test class |
| `TestBibliographyConsistency` | `_check_bibliography` | bib parsing + cross-reference |
| `TestCheckHeadings` | `_check_h1_per_file`, `_check_no_skipped_levels` | structural checks |
| `TestCheckResult` | dataclass shape | result-type invariants |
| `TestLongSentenceThresholdWired` | config threading | proves YAML knob reaches `infrastructure.prose` |

Method naming: `test_<what_is_being_tested>` and every test method has
a docstring.

## Parametrize Usage

Use `@pytest.mark.parametrize` when testing the same check across
multiple boundary cases:

```python
@pytest.mark.parametrize("grade, expected", [
    (5.0, False),    # below 10 → fail
    (10.0, True),    # at min → pass
    (14.0, True),    # mid-band → pass
    (18.0, True),    # at max → pass
    (19.5, False),   # above 18 → fail
])
def test_grade_level_bands(grade, expected):
    """Test FKGL band check at boundaries."""
    report = ManuscriptReport(avg_flesch_kincaid_grade=grade, ...)
    result = _check_grade_level(report, lo=10.0, hi=18.0)
    assert result.passed == expected
```

Don't parametrize across fundamentally different scenarios — use
separate test methods so failures point at the specific case.

## Error-Path Testing

```python
def test_invalid_grade_band(tmp_path: Path):
    """min > max must raise ValueError with both values quoted."""
    with pytest.raises(ValueError, match=r"target_grade_level_min .* must be < target_grade_level_max"):
        ProseAnalysisConfig(
            target_grade_level_min=20.0,
            target_grade_level_max=10.0,
        )
```

- Always use `match=` to verify the error message content.
- Test every documented `Raises` clause in the docstring.

## Coverage Verification

```bash
# Run with coverage (gate is 90% enforced by pyproject.toml)
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-report=term-missing \
    --cov-fail-under=90

# HTML report
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-report=html
```

Live count + achieved coverage are tracked in
[`docs/_generated/canonical_facts.md`](../../../docs/_generated/canonical_facts.md).
Do not delete tests to make a coverage number work — fix the gap.

## Determinism

- **Fixed inputs preferred.** Prose tests use literal markdown strings.
- **`tmp_path` for every filesystem write.** Tests never write into the
  project's own `output/` tree.
- **No randomness anywhere.** The prose pipeline is deterministic by
  construction; there is no legitimate reason for an `np.random` call
  in this suite.

## Integration Test

`test_pipeline_integration.py::test_bundled_manuscript_runs` is the
end-to-end fixture. It copies the project's `manuscript/` into a
temporary location, runs `run_prose_pipeline`, and asserts on file
existence and shape (not exact value) so the test remains stable
across editorial revisions of the bundled prose.

## Zero-Mock Checklist

Before submitting any test:

- [ ] Real Markdown strings or `.md` files written to `tmp_path`.
- [ ] Real `BibDatabase` parsed from a real `.bib` file in `tmp_path`.
- [ ] No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`.
- [ ] Assertions check **properties** (passed/failed, file existence,
  field values) — never call counts.
- [ ] Subprocess tests assert exit codes AND output-file contents.
- [ ] Error-path tests use `pytest.raises(..., match=...)`.

## See Also

- [AGENTS.md](AGENTS.md) — full test inventory and run commands
- [../src/STYLE.md](../src/STYLE.md) — how source code is structured
- [../docs/testing_philosophy.md](../docs/testing_philosophy.md) — zero-mock rationale
- [`../../template_code_project/tests/PATTERNS.md`](../../template_code_project/tests/PATTERNS.md) — sibling patterns reference
