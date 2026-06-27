# src — Gold Refinement Domain Logic

See [AGENTS.md](AGENTS.md) for the technical contract.

## Quick Reference

```python
from src import run_refinery, generate_token_plan, load_gold_refinement_config
from domain_adapter import load_domain_profile
from pipeline_policy import load_pipeline_policy

result = run_refinery()
print(f"Final purity: {result.final_purity}, Karat: {result.final_karat.label}")

cfg = load_gold_refinement_config()
plan = generate_token_plan(cfg)
print(f"Tokens: {len(plan.choices)}")

profile = load_domain_profile()
policy = load_pipeline_policy()
print(profile.display_name, policy.steganography.summary())
```
