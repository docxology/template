# Validation gates

Deterministic gates that check generated outputs are well-formed and concordant
across the multi-track exemplar before manuscript validation and rendering.

- `validation.py` — output/structure validation and cross-track consistency checks.
- `output_checks.py` — grouped output checks for required files, simulation,
  validation-spine, promoted-track, visualization, and canonical sheaf artifacts.
- `documentation_contract.py` — Markdown links, generated-doc links,
  README/AGENTS pairs, command context, and historical evidence wording.
- `method_inventory.py` — AST-backed source/script method inventory for
  documentation coverage.
- `lean.py` — exact installed Lean4.14.0 build and complete requested-declaration
  axiom audit. Source admission starts within the total deadline and refuses
  nonregular inputs and ancestor links. Builds consume private read-only copies
  of the admitted source and pins with a fresh Lake cache; the result records
  their consumed-source digest. The audit elaborates captured source bytes and
  requires every requested declaration with only the declared kernel axioms.
  These checks establish the Lean model's proof boundary; numerical pymdp
  oracles and manuscript binding require their own execution evidence.
