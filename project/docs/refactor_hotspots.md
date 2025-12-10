# Refactor Hotspots and Dependency Map

This note summarizes current module boundaries in `project/src/` and highlights quick refactor targets to make future changes safer and more modular.

## Module Dependency Map (scientific layer)
- `data_generator` → pure NumPy; no intra-project imports.
- `data_processing` → pure NumPy; no intra-project imports.
- `statistics` → pure NumPy/Scipy-style; no intra-project imports.
- `metrics` → imports `performance.analyze_convergence` for convergence metrics; otherwise pure NumPy.
- `performance` → pure NumPy/time; no intra-project imports.
- `validation` → pure NumPy; no intra-project imports.
- `visualization` / `plots` → Matplotlib; `plots` imports `visualization.VisualizationEngine`.
- `reporting` → pure JSON/Path; no intra-project imports.
- `simulation` → owns SimulationBase/State; no other project imports.

## Hotspots / Risks
- **Cross-module coupling**: `metrics.calculate_convergence_metrics` imports `performance.analyze_convergence` without package qualification. If the package name changes or relative imports become necessary, this is the likely break-point.
- **Global RNG usage**: Several generators/seeds set `np.random.seed` directly (`data_generator`, `simulation`) which can interfere across modules. Prefer explicit RNG objects passed through public APIs.
- **Path handling**: Scripts and modules assume `output/...` relative paths; centralizing these would simplify future refactors and enable temp-dir based tests.
- **Logging consistency**: Some modules print while others use `logging`. A shared logger helper would make pipeline output easier to parse.
- **Style drift**: Visualization defaults live in `VisualizationEngine.STYLE_CONFIG` while scripts still tweak figures manually. Consolidating styling through the engine reduces duplication.

## Near-Term Refactor Opportunities
- **Stabilize imports**: Convert intra-project imports to absolute package form (`from project.src.performance import ...`) or add a small compatibility shim to avoid path-order fragility when embedded elsewhere.
- **Randomness control**: Introduce an optional `np.random.Generator` parameter for data generation and simulations; default to `np.random.default_rng(seed)` to isolate streams.
- **Central output dirs**: Provide a small `paths.py` helper that computes `output/figures`, `output/data`, `output/reports` once, and reuse in scripts/tests.
- **Logging helper**: Add a `get_logger(name)` helper with consistent format and module-aware prefixes; replace direct `print` in scripts with structured logging.
- **Visualization presets**: Expose named presets from `VisualizationEngine` (`publication`, `slides`, `debug`) and ensure all script plotting routes through it (no ad-hoc `plt.subplots` sizing).

## Suggested Safeguards
- Add a lightweight import-smoke test to ensure intra-project imports work when `sys.path` does not contain the repo root (simulate downstream reuse).
- Add property-based tests for generator functions (`data_generator`, `data_processing`) to guard against shape/NaN regressions.
- Add performance baseline tests (micro-benchmarks) for `performance.analyze_convergence` to detect accidental O(n²) changes.



