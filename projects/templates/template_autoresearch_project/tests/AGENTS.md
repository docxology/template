# tests/ - Agent Notes

## Purpose

This directory validates the deterministic AutoResearch exemplar with real
configuration, loop, artifact, and script execution paths.

## Scope

- `test_config.py` — manuscript settings, plan merge, and `parse_string_sequence`
- `test_loop.py` — file-backed loop orchestration, declared stage status, clean
  scaffold run against the real template repo root, pre-extrinsic phase table
- `test_reports.py` — markdown/CSV renderers and basic writer helpers
- `test_writers.py` — `write_loop_payloads()` core + finalize wrapper
- `test_manuscript_variables.py` — manuscript token hydration from loop outputs
- `test_manuscript_tables.py` — registry-backed table builders
- `test_figures.py` — figure registry and ML figure writers
- `test_gate_negative_controls.py` — substance-binding negative controls for claims/benchmarks
- `test_gate_improvements.py` — provenance, schema manifest, and governance conformance
- `test_ml_task.py` — bounded ML task orchestration
- `test_security.py` — local security profile and attestation artifacts
- `test_source_ledger.py` — citekey stability and source-ledger contract
- `test_artifact_schemas.py` — generated JSON schema conformance
- `test_models.py` — dataclass JSON serialization
- `test_format_helpers.py` — manuscript token formatters and ML data validators
- `test_edge_config.py` — config and MNIST task YAML edge cases
- `test_edge_ledger.py` — source ledger validation edge cases
- `test_edge_loop.py` — loop and loop_phases helper edge cases
- `test_edge_gates.py` — benchmark, artifact substance, security render, research-object gates
- `test_scripts.py` — thin script smoke tests (all four scripts)

## Commands

```bash
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only
uv run pytest projects/templates/template_autoresearch_project/tests/ -q
```

## Editing Rules

- Keep tests deterministic and local-only.
- Do not add network, LLM, generated-code execution, or autonomous approval
  dependencies.
- Prefer exercising real project files over mocked objects.
- Use `tmp_path` scaffolds with `repo_root=Path(__file__).resolve().parents[4]`
  when the test needs infrastructure `pipeline.yaml` without copying the full
  repository. (`parents[4]` because this exemplar lives at
  `projects/templates/<name>/tests/`; the `projects/templates/` lifecycle layout
  adds one level over the legacy `projects/<name>/` path.)
