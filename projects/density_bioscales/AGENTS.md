# AGENTS: density_bioscales

## Purpose

Reproducible toy models linking gas/liquid reference densities to mixture-based effective “body” density and buoyancy contrast, with interval envelopes for internal gas mass fraction.

## Modules (`src/`)

| File | Public API |
|------|------------|
| `constants.py` | `R_UNIVERSAL`, `STANDARD_PRESSURE_PA`, `T_STP_K`, molar masses |
| `ideal_gas.py` | `ideal_gas_density_kg_m3`, `dry_air_density_stp_ideal_kg_m3`, literature band constants |
| `fluid_reference.py` | Liquid anchors, `water_density_linear_celsius`, `reference_liquids_table` |
| `composite_density.py` | `mixture_density_mass_fractions` |
| `insect_composition.py` | `CompositionPreset`, presets, `default_component_densities_kg_m3`, `normalize_fractions` |
| `buoyancy.py` | `BuoyancyRegime`, `relative_density`, `buoyancy_regime`, `density_difference_kg_m3` |
| `envelopes.py` | `Interval`, `interval_from_samples`, `scale_interval` |
| `scenarios.py` | `internal_gas_export_sweep_bounds`, `mixture_density_for_preset`, `sweep_internal_gas_mass_fraction_interval`, `sweep_air_fraction_interval`, `scenario_water_contrast_at_25c`, `scenario_custom_mass_map` |
| `__init__.py` | Re-exports stable public names |

## Scripts

- `01_generate_density_tables.py` → `output/data/density_summary.json`, `preset_densities.csv`
- `02_plot_density_overview.py` → `output/figures/density_overview.png`
- `03_plot_preset_envelopes.py` → `output/figures/preset_density_envelopes.png`

Respect `PROJECT_DIR` when set; otherwise infer project root from `__file__`.

## Tests

| File | Focus |
|------|--------|
| `test_constants.py` | Constant sanity |
| `test_ideal_gas.py` | STP band, validation |
| `test_fluid_reference.py` | Water linear proxy, table |
| `test_composite_density.py` | Mixture rule, errors |
| `test_insect_composition.py` | Presets, `normalize_fractions` |
| `test_buoyancy.py` | Regimes, errors |
| `test_envelopes.py` | Intervals |
| `test_scenarios.py` | Presets, sweeps, alias |
| `test_package_init.py` | `__init__` import |
| `test_analysis_scripts_smoke.py` | Subprocess smoke for `scripts/*.py` |

## See also

- [docs/guides/new-project-setup.md](../../docs/guides/new-project-setup.md)
- [projects/code_project/](../code_project/) — exemplar layout
