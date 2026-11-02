# src — Gold Refinement Domain Logic

See [AGENTS.md](AGENTS.md) for the technical contract.

## Quick Reference

```python
from template_gold_refinement.composition import generate_token_plan
from template_gold_refinement.config import load_gold_refinement_config
from template_gold_refinement.purity import PurityVector
from template_gold_refinement.refinery import run_refinery, stages_to_target
from template_gold_refinement.domain_adapter import load_domain_profile
from template_gold_refinement.pipeline_policy import load_pipeline_policy

result = run_refinery()
print(f"Final purity: {result.final_purity}, Karat: {result.final_karat.label}")
print([stage.name for stage in stages_to_target(0.90)])

quality = PurityVector(
    stage_completion=1.0,
    claim_support=1.0,
    token_provenance=1.0,
    figure_quality=1.0,
)
print(quality.weakest_dimension, quality.all_complete)

cfg = load_gold_refinement_config()
plan = generate_token_plan(cfg)
print(f"Tokens: {len(plan.choices)}")

profile = load_domain_profile()
policy = load_pipeline_policy()
print(profile.display_name, policy.steganography.summary())
```
