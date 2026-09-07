# infrastructure/validation/output/ - Output Validation

Pipeline output validation helpers.

## Files

- `validator.py`
- `pipeline.py`
- `render_formats.py`
- `pdf_checks.py`
- `markdown_checks.py`
- `design.py`
- `artifacts.py`
- `prose_quality.py`
- `claim_verification.py`
- `no_mock_enforcer.py`
- `no_mock_audit.py`
- `layout.py`

`render_formats.py` is the shared Stage 4/5 contract for loading effective
YAML-plus-environment format toggles, validating each enabled canonical
deliverable, rejecting disabled-format leftovers, and filtering only
renderer-owned artifacts from the freshly copied publication tree.

Stage 4 structure and size statistics use the artifact layer's canonical stable
inventory. Public exemplars use `stable-shippable-output-v1`; an explicitly
resolved non-template lifecycle project may use `stable-local-output-v1`.
TeX intermediates, logs, telemetry/history, snapshots, self-referential reports,
hidden paths, and runtime-only empty directories cannot change the deterministic
validation report or its rendered-provenance receipt. Every
stable file is counted, including DOCX/EPUB, hydrated manuscripts, release
packages, and root archives; enabled canonical formats must themselves belong
to this inventory. Stage 5 evaluates copied paths through the source project's
Git-ignore context because the root delivery mirror is intentionally ignored.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
