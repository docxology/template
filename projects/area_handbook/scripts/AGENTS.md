# scripts/ — area_handbook

## Pattern

1. Resolve `project_root` from `os.environ["PROJECT_DIR"]` or `Path(__file__).resolve().parent.parent`.
2. `sys.path.insert(0, str(project_root))` before importing `src.*`.
3. Insert repository root on `sys.path` when importing `infrastructure.*` (see `02_generate_handbook_figure.py`).
4. Use `infrastructure.core.logging_utils.get_logger(__name__)`.
5. Print output paths to stdout for manifest-style collection.

## Files

- `01_build_handbook_artifacts.py` — loads `data/fixtures/riverbend_area.yaml`, writes `handbook_report.json`, `area_outline.json`, `handbook_body.md`, `theme_glossary.md`, `handbook_toc.md`.
- `02_generate_handbook_figure.py` — writes `handbook_evidence_coverage.png`, `handbook_evidence_by_theme.png`, `handbook_section_gap_status.png`, and registers `fig:coverage`, `fig:bytheme`, `fig:gapstatus` in `output/figures/figure_registry.json` via `FigureManager` (required for `validate_figure_registry` in the pipeline).
