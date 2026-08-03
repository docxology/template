# tests/ — template_sia

- Real filesystem fixtures under `../src/fixtures/recorded_generations/`
- No mocks — subprocess and temp dirs only
- Opt-in Ollama tests: `@pytest.mark.requires_ollama` (excluded from the
  default gate; the marker also keeps the coverage run offline)
- `conftest.py` exposes the `copy_project_sandbox` fixture (guarded project
  copy that excludes volatile coverage/cache/output trees)

## Test files

| File | Role |
| --- | --- |
| `test_architecture_contract.py` | Thin-orchestrator boundary: `src` never imports scripts; CLI imports the `src.loop` adapter |
| `test_artifact_manifest.py` | Artifact manifest writer: path collection, dedup, deterministic hashes, timestamp |
| `test_figures.py` | Deterministic PNGs, figure specs ↔ manuscript caption sync, registry ↔ manuscript references |
| `test_fixture_live_separation.py` | Replay (fixtures) vs live (no fixtures) config resolution; fail-closed on missing fixtures |
| `test_gate_negative_controls.py` | Negative controls: hollow/wrong-typed results JSON, missing task dirs/files, missing manifest paths |
| `test_generation_records.py` | `run_summary.json` loading, generation-metric extraction, fixture-run replay |
| `test_loop.py` | Settings loading, config building, full fixture-replay loop run, variables and report writers |
| `test_loop_live.py` | Bounded live subprocess runs; feedback written but target code never mutated; opt-in Ollama |
| `test_manuscript_variables.py` | `{{SIA_*}}` token coverage of manuscript files, metrics-table/delta tokens, edge values |
| `test_reference_agent.py` | Reference target agent CLI (predictions file output) |
| `test_reports.py` | Metric formatting, empty/non-numeric metrics, empty YAML config fallbacks |
| `test_scripts.py` | Script smoke tests: `run_sia_loop.py` and `z_generate_manuscript_variables.py` |
| `test_src_reference_agent.py` | `reference_agent.py` internals: majority label, threshold predictions, CLI main |

Run one pytest process per project directory (repo-wide convention).
