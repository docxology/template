# Troubleshooting — AutoScientists

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Ablation figures missing | `scripts/run_ablation.py` not run | Run it before `scripts/pipeline/stage_04_validate.py` |
| Clean metric equals reported metric | Noise band too wide or seed count too low | Check `confirmation.py` default seeds |
| Dead-end registry never triggers | Threshold too high for search budget | Lower the `threshold` field when constructing `DeadEndRegistry` in `src/dead_ends.py` |
| Live Hermes proposer not found | Ollama not running | Use `DeterministicProposer` (default) or start Ollama |
