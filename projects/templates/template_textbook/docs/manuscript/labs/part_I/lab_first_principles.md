# Lab — First Principles {#sec:lab_part_I_first_principles}

<!-- chapter-metadata-badge -->
> Lab · 60 min · Materials: a computer with the project installed (`uv sync`), or
> graph paper and a calculator

## Objectives

After this lab you will be able to (1) generate a logistic trajectory for chosen
parameters, (2) read its carrying capacity and half-rise time from a plot, and
(3) recover the growth rate from data with a simple fit.

## Background

This lab makes the chapter concrete: see [@sec:part_I_first_principles] for the
logistic law and the meaning of $r$, $K$, and $N_0$. You will produce the same
S-curve shown in [@fig:part_I_first_principles] and then work backwards from
numbers to parameters.

## Procedure

1. Install the project: `uv sync`. Confirm the tests pass:
   `uv run --extra dev python -m pytest tests/test_models.py -q`.
2. Generate a trajectory for $r = 0.8$, $K = 100$, $N_0 = 5$ at
   $t = 0, 1, 2, \dots, 12$ using the computational workflow below.
3. Plot $N$ against $t$. Mark the value the curve approaches and the time at
   which $N$ first exceeds $K/2 = 50$.
4. Repeat for $r = 0.4$ and $r = 1.2$, keeping $K$ and $N_0$ fixed. Overlay the
   three curves.

## Analysis

Summarise each trajectory with
`textbook.models.descriptive_statistics(N)` and tabulate the maximum value and
the time-to-half-capacity for each $r$. Describe, in one sentence, how increasing
$r$ changes the curve without changing where it ends.

## Computational Workflow

```python
import numpy as np
from textbook import models

t = np.arange(0, 13, 1.0)
for r in (0.4, 0.8, 1.2):
    N = models.logistic_growth(t, r=r, carrying_capacity=100.0, initial=5.0)
    t_half = t[np.argmax(N > 50)]
    print(f"r={r}: N(12)={N[-1]:.1f}, first t with N>50 is t={t_half:.0f}")
    print("  stats:", models.descriptive_statistics(N))
```

## Reflection

1. Two of your three curves end at almost the same value. Which parameter sets
   that value, and why is it independent of $r$?
2. A colleague claims the population "will keep growing forever." Using
   [@eq:part_I_first_principles_model], explain in one sentence why it will not.
3. If your measured data rose past $K$ and then fell back, what would that tell
   you about the adequacy of the logistic model for that system?
