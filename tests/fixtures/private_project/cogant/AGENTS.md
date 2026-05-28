# tests/fixtures/private_project/cogant/

Fixture tree for COGANT `private_project` infra tests. Real staging at `projects/working/cogant/` (private-repo mirror) overrides these paths when its `tools/` directory exists.

## Layout

| Path | Role |
| --- | --- |
| `tools/audit_manuscript_crossrefs.py` | Section/table cross-reference audit |
| `tools/check_coverage_table.py` | Coverage report / Table 9 parse helpers |
| `manuscript/` | Minimal manuscript fragment that passes audit |
