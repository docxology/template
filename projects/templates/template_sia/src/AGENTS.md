# src/ — template_sia

| Module | Role |
| --- | --- |
| `loop.py` | Layer-2 adapter: project config/fixtures → `infrastructure.sia.run_sia_loop` → reports, variables, figures, and manifest |
| `loop_config.py` | Reads `project_config.sia` from `manuscript/config.yaml` (legacy root fallback supported) |
| `reports.py` | Loop markdown + manuscript variable hydration |
| `artifact_manifest.py` | Artifact manifest writer (hashes + metadata) for SIA loop outputs |
| `generation_records.py` | Loads SIA generation records from disk |
| `manuscript_tokens_core.py` | Core `{{TOKEN}}` values for template_sia's manuscript |
| `manuscript_tokens_metrics.py` | Metric-table tokens derived from `run_summary.json` |
| `manuscript_variables.py` | Render-time manuscript variables (composes the token modules above) |
| `reference_agent.py` | Deterministic majority-vote target agent for the `mini_classify` fixture task |
| `figures/` | Figure subpackage (`figure_registry.py` + SIA loop/heatmap/improvement-delta/metrics figures) — see its own [`AGENTS.md`](figures/AGENTS.md) |
| `fixtures/` | Recorded generation payloads for deterministic CI |

Scripts under `../scripts/` must import from here — no business logic or
compatibility implementation lives in scripts.
