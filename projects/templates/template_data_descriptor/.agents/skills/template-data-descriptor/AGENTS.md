# template-data-descriptor skill - AGENTS.md

Agent skill for the `template_data_descriptor` exemplar: schema, provenance,
license, and dataset release-readiness validation.

## Claim traceability

| Assertion | Source |
| --- | --- |
| Descriptor shape/safety/completeness validation | `src/data_descriptor/descriptor.py` (`validate_descriptor`, `build_descriptor_report`) |
| Order-independent schema fingerprint | `descriptor_fingerprint()` + `tests/test_descriptor.py` |
| Byte-level descriptor↔file reconciliation | `src/data_descriptor/verification.py` (`verify_descriptor_files`) |
| Figure data comes from tested preparers | `src/data_descriptor/figures.py` + `tests/test_figures.py` |
| Five manuscript figures, registry-backed | `scripts/generate_figures.py` + `tests/test_generate_figures_script.py` |
| Claims bound to data structure, not empirical effects | `manuscript/AGENTS.md` + root `AGENTS.md` contracts |

Keep this skill aligned with the project README and tests. Update the traceability
table when a claim boundary or test surface changes.
