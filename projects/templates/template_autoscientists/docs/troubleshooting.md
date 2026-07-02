# Troubleshooting — AutoScientists

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Ablation figures missing | `scripts/run_ablation.py` not run | Run it before `04_validate_output.py` |
| Clean metric equals reported metric | Noise band too wide or seed count too low | Check `confirmation.py` default seeds |
| Dead-end registry never triggers | Threshold too high for search budget | Lower `DEAD_END_THRESHOLD` in `src/dead_ends.py` |
| Live Hermes proposer not found | Ollama not running | Use `DeterministicProposer` (default) or start Ollama |
