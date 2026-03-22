# Methods

## Code map

| Module | Role |
|--------|------|
| `constants.py` | \(R\), STP pressure/temperature, dry-air molar mass |
| `ideal_gas.py` | \(\rho = pM/(RT)\), dry-air STP ideal density, literature band constants |
| `fluid_reference.py` | Liquid anchors, `water_density_linear_celsius`, `reference_liquids_table` |
| `composite_density.py` | Mass-fraction mixture rule (Equation \ref{eq:mixture_rule}) |
| `insect_composition.py` | Presets, `default_component_densities_kg_m3`, `normalize_fractions` |
| `buoyancy.py` | Relative density and float/sink classification |
| `envelopes.py` | `Interval`, `interval_from_samples`, `scale_interval` |
| `scenarios.py` | Preset density, `internal_gas_export_sweep_bounds`, internal-gas sweep envelopes, water contrast, custom mass maps |

## Analysis pipeline

Thin orchestrators in `scripts/` run in lexicographic order:

1. `01_generate_density_tables.py` — writes `output/data/density_summary.json` and `output/data/preset_densities.csv` (STP air ideal + literature band, full liquid table, per-preset central \(\rho\) and sweep interval).
2. `02_plot_density_overview.py` — `output/figures/density_overview.png` (presets, fresh water at 15 °C and 25 °C, illustrative seawater, ethanol, ideal dry air at STP; dashed line at 25 °C fresh water).
3. `03_plot_preset_envelopes.py` — `output/figures/preset_density_envelopes.png` (horizontal interval per preset using `internal_gas_export_sweep_bounds` with `sweep_internal_gas_mass_fraction_interval`; nominal \(\rho\) as markers; reference lines for fresh water 25 °C and illustrative seawater 15 °C).

`PROJECT_DIR` may point at the project root; otherwise each script infers the parent of `scripts/`. `MPLBACKEND` defaults to `Agg` for headless runs.

## Testing

Tests live in `projects/density_bioscales/tests/` with `conftest.py` setting `MPLBACKEND=Agg` and inserting `src/` on `sys.path`. Coverage threshold is 90% in project `pyproject.toml`. The suite exercises validation paths, interval algebra, preset sweeps, and smoke-runs the three analysis scripts via subprocess (no mocking frameworks).

## Relation to outputs

Tabular JSON is the authoritative machine-readable summary for numerical values cited in discussion; figures are generated from the same `src/` functions so plot and table cannot silently diverge unless the scripts are edited inconsistently. After changing presets or `DENSITY_INTERNAL_GAS_SPACE_KG_M3`, run `01_run_tests.py` and regenerate exports before citing numbers in prose.
