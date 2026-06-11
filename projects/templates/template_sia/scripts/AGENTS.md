# scripts/ — template_sia

| Script | Role |
| --- | --- |
| `run_sia_loop.py` | Runs `run_sia_loop_project()`; flags `--project-root`, `--live-sia` (LLM model comes from the `sia.llm_model` key in `manuscript/config.yaml`, not a flag) |
| `z_generate_manuscript_variables.py` | Hydrates `${SIA_*}` tokens after the loop |

Keep each script under 150 lines; delegate to `src/`.
