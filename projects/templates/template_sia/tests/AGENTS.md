# tests/ — template_sia

- Real filesystem fixtures under `../src/template_sia/fixtures/recorded_generations/`
- No mocks — subprocess and temp dirs only
- Opt-in Ollama tests: `@pytest.mark.requires_ollama` (excluded from the
  default gate; the marker also keeps the coverage run offline)
- `conftest.py` exposes the `copy_project_sandbox` fixture (guarded project
  copy that excludes volatile coverage/cache/output trees)

## Cluster directories (post-flat mirror, SUBMODULAR-SIA-1)

Behavior tests are co-located with their subject module's subpackage:

| Directory | Role |
| --- | --- |
| [`loop/`](loop/AGENTS.md) | `test_approval.py`, `test_loop.py`, `test_loop_live.py`, `test_reference_agent.py`, `test_src_reference_agent.py` |
| [`ledger/`](ledger/AGENTS.md) | `test_artifact_manifest.py`, `test_generation_records.py` |
| [`manuscript/`](manuscript/AGENTS.md) | `test_manuscript_variables.py`, `test_reports.py` |

## Cross-cluster test files

| File | Role |
| --- | --- |
| `test_architecture_contract.py` | Thin-orchestrator boundary: `src` never imports scripts; CLI imports the `template_sia.loop.loop` adapter |
| `test_figures.py` | Deterministic PNGs, figure specs ↔ manuscript caption sync, registry ↔ manuscript references |
| `test_fixture_live_separation.py` | Replay (fixtures) vs live (no fixtures) config resolution; fail-closed on missing fixtures |
| `test_gate_negative_controls.py` | Negative controls: hollow/wrong-typed results JSON, missing task dirs/files, missing manifest paths |
| `test_scripts.py` | Script smoke tests: `run_sia_loop.py` and `z_generate_manuscript_variables.py` |
| `test_claim_ledger.py` | Committed `data/claim_ledger.yaml` integrity |

Run one pytest process per project directory (repo-wide convention).
