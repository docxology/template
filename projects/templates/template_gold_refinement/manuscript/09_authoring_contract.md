# Authoring Contract {#sec:authoring_contract}

## Obligations

| Obligation | Requirement |
|------------|-------------|
| Domain validator | Add domain-specific evidence before making domain claims beyond the exemplar. |
| Config ownership | Keep lexicon and slots in config.yaml, not in generated prose. |
| Regeneration contract | Regenerate outputs through the pipeline, not by hand-editing. |

## Fork checklist

1. Remap metallurgical stages to domain operations in `src/refinery.py`
2. Update lexicon categories in `manuscript/config.yaml` under `gold_refinement.lexicon`
3. Update `contribution_claims` with domain-specific evidence pointers
4. Add domain validators beyond the exemplar's generic gates
5. Regenerate all outputs through the pipeline:
   ```bash
   uv run python scripts/refinement_analysis.py
   uv run python scripts/z_generate_manuscript_variables.py
   ```
6. Do not hand-edit generated manuscript, PDFs, or figures
