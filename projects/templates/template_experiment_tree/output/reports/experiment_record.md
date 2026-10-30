# Experiment Tree Record

3 experiments: 0 answered (0 wins, 0 losses, 0 dead ends), 1 frozen, 2 provisional.

## Results (answered nodes)

| Node | Title | Outcome | Round | Run command | Answer |
| --- | --- | --- | --- | --- | --- |
| - | No answered experiments yet | | | | |

## In progress (frozen, preregistered)

- **E003** — Frozen preregistration: momentum follow-up (`python scripts/run_baseline.py --steps 10 --scale 0.5 --momentum 0.9`)

## Dead ends (negative-result registry)

- No dead ends recorded.

## Planned (provisional)

- E001: Baseline: gradient step size sweep (`python scripts/run_baseline.py --steps 5`)
- E002: Child: halve the step size (`python scripts/run_baseline.py --steps 5 --scale 0.5`)
