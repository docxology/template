# src/ — API reference

## `constants.py`

- `R_UNIVERSAL`, `STANDARD_PRESSURE_PA`, `T_STP_K`
- `DRY_AIR_MOLAR_MASS_KG_MOL`, `MOLAR_MASS_N2_KG_MOL`, `MOLAR_MASS_O2_KG_MOL`, `MOLAR_MASS_CO2_KG_MOL`

## `ideal_gas.py`

- `ideal_gas_density_kg_m3(pressure_pa, temperature_k, molar_mass_kg_mol) -> float`
- `dry_air_density_stp_ideal_kg_m3(...) -> float`
- `DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3`, `DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3`

## `fluid_reference.py`

- `water_density_linear_celsius(temp_celsius, ...) -> float`
- `reference_liquids_table() -> dict`

## `composite_density.py`

- `mixture_density_mass_fractions(mass_fractions, component_density_kg_m3) -> float`

## `insect_composition.py`

- `CompositionPreset`, `list_presets()`, `find_preset(name)`
- `default_component_densities_kg_m3()`, `normalize_fractions`
- `DENSITY_INTERNAL_GAS_SPACE_KG_M3` — effective density for `internal_gas` compartment

## `buoyancy.py`

- `relative_density`, `density_difference_kg_m3`, `buoyancy_regime` → `BuoyancyRegime`

## `envelopes.py`

- `Interval`, `interval_from_samples`, `scale_interval`

## `scenarios.py`

- `internal_gas_export_sweep_bounds`, `mixture_density_for_preset`, `sweep_internal_gas_mass_fraction_interval`, `sweep_air_fraction_interval` (alias)
- `scenario_water_contrast_at_25c`, `scenario_custom_mass_map`
