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

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
