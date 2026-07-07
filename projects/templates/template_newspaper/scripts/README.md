# scripts/

Thin Stage-02 orchestrators, run by the pipeline in lexicographic order. Each
wires engine functions to the filesystem; all logic lives in `src/newspaper/`.

| Script | Role |
|--------|------|
| `_bootstrap.py` | shared path/logging helper (repo-root discovery + logger fallback) |
| `00_preflight.py` | confirm deps import and the edition loads/validates |
| `10_generate_figures.py` | write halftone scenes + charts to `output/figures/` |
| `20_render_newspaper.py` | render the 12-page PDF + write render report/summary |

```bash
python scripts/00_preflight.py
python scripts/10_generate_figures.py
python scripts/20_render_newspaper.py            # fails on over-set by default; --allow-overset to downgrade to a warning
```

They run standalone (dev) and under `./run.sh --project templates/template_newspaper --pipeline`.
