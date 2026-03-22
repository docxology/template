# scripts/

## Environment

- `PROJECT_DIR` optional; default parent of `scripts/` is project root.
- `sys.path`: project `src/` inserted for `import ideal_gas` style imports.
- Logging: `infrastructure.core.logging_utils.get_logger` when repo root is importable; else stdlib logging.

## `01_generate_density_tables.py`

Builds a JSON summary (STP dry air ideal + literature band, liquid table, preset densities and internal-gas sweep intervals) and a CSV of preset rows.

## `02_plot_density_overview.py`

Headless matplotlib (`MPLBACKEND=Agg`): horizontal bar chart of preset densities, fresh water 15/25 °C, illustrative seawater, ethanol, ideal dry air; dashed line at 25 °C water reference; bar-end numeric labels.

No emoji in plot text (font compatibility).

## `03_plot_preset_envelopes.py`

Horizontal interval per preset (`internal_gas_export_sweep_bounds` + `sweep_internal_gas_mass_fraction_interval`); nominal density markers; reference lines for fresh water 25 °C and seawater 15 °C.
