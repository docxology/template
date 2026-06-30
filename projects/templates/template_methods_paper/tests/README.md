# template_methods_paper/tests

Zero-mock test suite for the `src.methods_dsl` controlled-method
specification library.

## Quick reference

| File | Covers |
| --- | --- |
| `conftest.py` | Shared `Method` fixtures (linear chain, diamond DAG, and one fixture per gate-failure mode) |
| `test_vocabulary.py` | `StepKind`, `Target`, `target_accepts` |
| `test_units.py` | `Dimension`, `Quantity`, `DimensionError`, dimensional arithmetic |
| `test_model.py` | `Method`, `Step`, `Resource`, `Parameter` shape validation |
| `test_validation.py` | The four staged gates and `run_all_gates` ordering/short-circuit |
| `test_compiler.py` | `topological_order`, `compile_method`, determinism, plan-hash stability |
| `test_export.py` | Worklist markdown, CSV, Mermaid, and canonical-JSON renderers |
| `test_trust.py` | `ProvenanceTier`, hash-chain append/verify, tamper detection |
| `test_examples_methods.py` | The two worked example methods compile and pass all gates |
| `test_project_paths.py` | Output-directory resolution |
| `test_manuscript_variables.py` | `{{TOKEN}}` generation from config + analysis outputs |
| `test_methods_analysis_script.py` | `scripts/methods_analysis.py` end-to-end against a temp output root |

## Run

```bash
uv run pytest projects/templates/template_methods_paper/tests \
  --cov=projects/templates/template_methods_paper/src --cov-fail-under=90
```

Conventions and rationale: [`AGENTS.md`](AGENTS.md) and [`PATTERNS.md`](PATTERNS.md).
