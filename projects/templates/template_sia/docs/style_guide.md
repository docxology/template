# Style guide — template_sia

## Rules

1. **Thin orchestrators.** `scripts/*.py` parse argv, call `src/` functions, print output paths. No business logic in scripts.

2. **Infrastructure imports in Layer 2.** `src/` may import `infrastructure.sia` and `infrastructure.core.config`. Avoid importing `infrastructure.rendering` package init from project venv paths (use lazy load in `reports.write_resolved_manuscript_tree`).

3. **Typed settings.** Use `SiaLoopSettings` dataclass from `loop_config.py`; do not scatter raw YAML access.

4. **Explicit paths.** Resolve `project_root` from `Path(__file__).resolve().parent.parent` in scripts; pass `Path` objects into `src/` APIs.

5. **Determinism.** Fixed fixture metrics for gens 1–3; document any new fixture generation steps in `tests/` and commit artifacts under `src/fixtures/`.

6. **Show-not-tell docstrings.** One-line module docstrings; explain non-obvious contracts (public/private split, live vs replay) only where the code is not self-explanatory.

7. **Error messages.** Fail fast with relative paths and the remediation command (`run scripts/run_sia_loop.py first`).

## Module size

Keep `src/*.py` under the exemplar drift line-count guidance. Split new logic into focused modules rather than expanding `loop.py`.
