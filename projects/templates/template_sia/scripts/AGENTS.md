# scripts/ — template_sia

| Script | Role |
| --- | --- |
| `run_sia_loop.py` | Thin CLI for fixture/reference execution or `live_proposals.run_live_proposals()`; proposal flags include an explicit model, immutable local image ID, loopback origin, and fresh output directory |
| `z_generate_manuscript_variables.py` | Hydrates `{{SIA_*}}` tokens after the loop |

Keep each script under 150 lines; delegate configuration, fixture selection,
loop execution, and artifact generation to `src/`.
