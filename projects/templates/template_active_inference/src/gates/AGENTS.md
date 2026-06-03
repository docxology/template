# Gate Notes

Gates must fail closed: a missing, empty, or inconsistent artifact is an error,
never a silent pass. Add a negative-control test for every new gate so it is
proven to reject bad input, not just accept good input.

## Module layout

| Module | Role |
| --- | --- |
| [`validation.py`](validation.py) | Public facade: `validate_outputs`, `validate_manuscript`, `build_lean` |
| [`artifact_manifest.py`](artifact_manifest.py) | `REQUIRED_OUTPUTS` SSOT for output gate checks |
| [`output_checks.py`](output_checks.py) | Pipeline artifact existence + SI schema checks |
| [`manuscript_checks.py`](manuscript_checks.py) | Sheaf manifest, tokens, hydration, layers markers |
| [`claim_ledger.py`](claim_ledger.py) | Claim ledger vs on-disk artifacts (`data/claim_ledger.yaml` required) |
| [`lean.py`](lean.py) | Conditional `lake build` when `lean/lakefile.lean` exists |
| [`method_inventory.py`](method_inventory.py) | AST-backed report for every `def` and `class` under `src/` and `scripts/` |

## Manuscript gates (`validate_manuscript`)

| Key | Contract |
| --- | --- |
| `methods_sheaf_layers` | Composed `08_methods_sheaf.md` contains `sheaf_layers_overview.png` plus HTML markers `<!-- sheaf-layers:registry -->`, `<!-- sheaf-layers:binding-matrix -->`, `<!-- sheaf-layers:legend -->` |
| `manuscript_tokens_registered` | Every `{{token}}` under `manuscript/*.md` maps to a key from `generate_variables()` |
| `resolved_manuscript_hydrated` | `output/manuscript/*.md` contains no unresolved `{{` placeholders after `z_generate_manuscript_variables.py` |
| `full_sheaf_appendix_tracks` | `16_appendix_full_sheaf.md` contains every `sheaf-track:{id}` marker bound in the `appendix_full_sheaf` manifest section; counts come from the manifest/registry |

Negative controls: `test_validate_manuscript_methods_sheaf_layers_negative` (registry marker) and `test_validate_manuscript_methods_sheaf_layers_negative_markers` (binding-matrix, legend, figure path).

## Output gates (`validate_outputs`)

Requires analysis figures, SI JSON, merged and per-domain invariant reports, plus sheaf artifacts: `output/figures/sheaf_layers_overview.png`, `output/figures/sheaf_coverage_heatmap.png`, and `output/data/sheaf_coverage_matrix.json` (compose + `generate_figures.py`).

When reports exist, also checks:

| Key | Contract |
| --- | --- |
| `invariants_all_pass` | Top-level `all_pass` in `output/reports/invariants.json` |
| `simulation_invariants_all_pass` | All values in merged `simulation` block when present |
| `si_invariants_all_pass` | Top-level `all_pass` in `output/reports/si_invariants.json` |
| `experiment_plan_metrics` | Analytical invariants pass, SI summary present, and when SI summary exists `si_invariants.json` must exist with `all_pass` |

Negative controls: `test_validate_outputs_negative_missing_sweep`, `test_validate_outputs_negative_missing_sheaf_matrix`, `test_validate_outputs_negative_missing_si_invariants_report`, `test_validate_outputs_negative_si_invariants_fail`, `test_validate_outputs_negative_analytical_invariants_fail`.

## Lean gate (`build_lean`)

| Helper | Contract |
| --- | --- |
| `lean_project_present(root)` | `True` when `lean/lakefile.lean` exists |
| `build_lean(root)` | Runs `lake build` when present (must exit 0); returns skip message when absent |

Negative controls: `test_build_lean_when_present_must_succeed`, `test_build_lean_skips_without_lakefile`, `test_validate_manuscript_gnn_concordance_negative`, `test_validate_manuscript_claim_ledger_negative`, `test_validate_manuscript_claim_ledger_missing_file_negative`, `test_validate_manuscript_tokens_registered_negative`.

## Method inventory (`generate_method_inventory.py`)

[`method_inventory.py`](method_inventory.py) writes
`docs/reference/method-inventory.md` from the live AST. The report documents
every source/script `def` and `class`; entries without inline docstrings are
marked `inventory fallback` so missing method-level docstrings stay visible.
`tests/test_method_inventory.py` pins the generated inventory shape and docs
signposts.
