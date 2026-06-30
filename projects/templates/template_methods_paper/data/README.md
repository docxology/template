# template_methods_paper/data

Project-maintained **inputs** for the methods-paper exemplar (not pipeline outputs).

## Quick reference

| File | Role |
| --- | --- |
| `claim_ledger.yaml` | Source-backed numeric and artifact claims for evidence validation |

This exemplar has no dataset fixture: the controlled vocabulary the manuscript
describes is declared directly in `src/methods_dsl/vocabulary.py` and
`src/methods_dsl/units.py`, which is itself the project's versioned "input."
Generated analysis outputs (compiled plans, gate reports, figures) belong
under `output/` during pipeline runs, not here.

Schema and edit protocol: [`AGENTS.md`](AGENTS.md).
