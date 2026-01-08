# Refactor Playbook (Project Layer)

Concise guidance for refactoring or extending the scientific layer while keeping scripts, tests, and manuscript output stable.

## Principles
- Keep business logic in `project/src/`; keep `project/scripts/` thin.
- Preserve determinism: prefer `np.random.default_rng(seed)` over global seeds; surface `seed`/`rng` parameters.
- Maintain public API docstrings + type hints on all exported functions/classes.
- Add tests before or alongside changes; no mocks—use data fixtures.

*See [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) for clean break refactoring standards, [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) for testing requirements including no-mocks policy, [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) for logging patterns, and [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) for type annotation requirements.*

## Safe-Change Checklist
1) **Scope**: Identify module boundaries (see `project/docs/refactor_hotspots.md`).
2) **API contract**: Confirm inputs/outputs and error semantics; add/adjust docstrings.
3) **Determinism**: Ensure seeds or RNG objects are passed through.
4) **Paths**: Use a central helper for `output/` paths (figures, data, reports) to avoid hardcoded strings.
5) **Logging**: Use consistent `logging` (INFO for progress, DEBUG for details).
6) **Tests**: Add/extend tests:
   - Unit/property tests in `project/tests/`
   - Script CLI smoke with `--dry-run`
   - Optional slow/perf marked with `@pytest.mark.slow`
7) **Docs**: Update relevant README/AGENTS to reflect new surfaces.

## Quick Recipes
- **Add a new analysis function**:
  - Implement in `project/src/<module>.py` with type hints + docstring.
  - Add unit tests + property tests for shape/NaN invariants.
  - Wire into scripts via thin orchestrator (no new logic there).
  - Document usage in manuscript or docs as needed.

- **Introduce shared paths/logging**:
  - Add a small helper module (e.g., `project/scripts/utils/paths.py`) returning `Path` objects for outputs.
  - Add `get_logger(name)` wrapper to enforce consistent format; replace ad-hoc prints.

- **Stabilize plotting**:
  - Route plotting through `VisualizationEngine` and `plots` helpers; avoid raw `plt` in scripts.
  - Add small checksum-based regression test for key figures.

## Validation Hooks
- Run `python3 project/scripts/manuscript_preflight.py --strict` before PDF builds.
- Use `python3 project/scripts/analysis_pipeline.py --dry-run` to verify stage wiring quickly.
- For figure generation: `python3 project/scripts/generate_scientific_figures.py --dry-run --only convergence scatter`.

## See Also

**Development Standards:**
- [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) - Refactoring standards and clean break approach
- [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing patterns and coverage standards
- [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) - Logging standards and best practices
- [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) - Type annotation patterns

**Project Documentation:**
- [`AGENTS.md`](AGENTS.md) - project documentation
- [`README.md`](README.md) - Quick reference
- [`refactor_hotspots.md`](refactor_hotspots.md) - Code areas needing improvement

**Template Documentation:**
- [`../../docs/best-practices/BEST_PRACTICES.md`](../../docs/best-practices/BEST_PRACTICES.md) - Code quality and refactoring best practices











