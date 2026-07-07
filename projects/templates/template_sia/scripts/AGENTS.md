# scripts/ — template_sia

| Script | Role |
| --- | --- |
| `run_sia_loop.py` | Runs `run_sia_loop_project()`; flags `--project-root`, `--live-sia` (LLM model comes from the `sia.llm_model` key in `manuscript/config.yaml`, not a flag) |
| `sia_loop_impl.py` | Holds `run_sia_loop_project()` / `build_run_config()` — the actual loop orchestration re-exported by `src/loop.py` for backward compatibility |
| `z_generate_manuscript_variables.py` | Hydrates `{{SIA_*}}` tokens after the loop |

Keep each script under 150 lines; delegate to `src/`.
