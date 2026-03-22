# Buoyancy and media contrast

`buoyancy.py` implements static-fluid helpers (no surface tension, no drag): `relative_density` as \(\rho_{\mathrm{body}}/\rho_{\mathrm{medium}}\), `density_difference_kg_m3` as \(\rho_{\mathrm{body}}-\rho_{\mathrm{medium}}\), and `buoyancy_regime` mapping to `BuoyancyRegime` (`float` if \(\rho_{\mathrm{body}}<\rho_{\mathrm{medium}}\), `neutral` if equal within a tiny numerical tolerance, else `sink`). These labels are **classification** outputs for comparing a single scalar body density to a single scalar medium density.

`scenario_water_contrast_at_25c` in `scenarios.py` pairs a preset’s mixture density with `WATER_DENSITY_25C_KG_M3` (997.0 kg m⁻³) for reproducible reporting. With default presets and component densities, **all three illustrative presets sink** in that reference fresh water: model \(\rho\) exceeds 997 kg m⁻³ in the central parameter choice. That outcome is not a claim about real insects (which are anatomically complex, often surface-linked, and sometimes gas-carrying in ways not captured here); it is the behaviour of this **specific** parameter box.

## Other media

The same helpers apply if you substitute another reference density—for example **seawater** at the illustrative 15 °C anchor (1025 kg m⁻³) raises the medium density and narrows or reverses contrast versus fresh water for a fixed body \(\rho\). Section "Temperature, salinity, and scale" discusses when those shifts matter interpretively.
