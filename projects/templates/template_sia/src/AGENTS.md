# src/ — template_sia

| Module | Role |
| --- | --- |
| `loop.py` | Thin wrapper → `infrastructure.sia.run_sia_loop` |
| `loop_config.py` | Reads `sia:` block from `manuscript/config.yaml` |
| `reports.py` | Loop markdown + manuscript variable hydration |
| `fixtures/` | Recorded generation payloads for deterministic CI |

Scripts under `../scripts/` must import from here — no business logic in scripts.
