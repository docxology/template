# Lab — Systems Overview {#sec:lab_part_II_systems_overview}

<!-- chapter-metadata-badge -->
> Guided lab · Materials: Python environment, notebook or terminal, and a written observation record

## Objectives

Execute `textbook.models.logistic_growth` with the declared inputs, compare
its output with an independently worked expectation, and explain which part of
the chapter's claim the result checks. Track state, update rule and measurement process as separate parts of a system record.

## Background

Linked chapter: [@sec:part_II_systems_overview]. A dashboard shows a stock approaching a ceiling. One observer attributes the ceiling to limited capacity; another points to a change in counting rules. Both explanations can produce a flat line. A systems overview asks what changed inside the system, what crossed its boundary, and what the dashboard actually measured.
The values below are instructional inputs. No experiment on people, organisms
or services is being reported. The exercise checks mathematical behavior under
the model's assumptions rather than supplying evidence that the scenario is real.

## Procedure

1. Write the input quantities, units and assumptions from [@tbl:part_II_systems_overview_parameters].
2. Before running code, predict one boundary value and one interior value using
   [@eq:part_II_systems_overview_model]. Keep the prediction even if it proves incorrect.
3. Run the workflow below in a fresh interpreter. Preserve the command and output.
4. Change one allowed input or parameter and explain which qualitative feature
   should change. Run again as a separately recorded comparison.
5. Try one invalid or degenerate case from the function's documented contract;
   record whether it is rejected or handled by an explicit convention.

## Analysis

At time zero the denominator is $1+19=20$, so the state is exactly five units. At time two it is $1+19e^{-1.4}$, giving about $17.59$ units. The state approaches $100$ as the exponential term approaches zero. These are predictions of a chosen model, not measured evidence that a real population or service has a fixed capacity.

Check both the value and its interpretation. A discrepancy in arithmetic should
lead you to inspect units, input order and the declared convention. Agreement
on these synthetic inputs establishes a limited computational result; it does
not establish the opening scenario's observation rule or empirical adequacy.

## Computational Workflow

```python
import numpy as np
from textbook.models import logistic_growth

time = np.array([0.0, 2.0, 5.0])
values = logistic_growth(time, r=0.7, carrying_capacity=100.0, initial=5.0)
assert np.isclose(values[0], 5.0)
assert np.all(np.diff(values) > 0)
assert np.all(values < 100.0)
print(values)
```

The code calls the shared model implementation and asserts independently known
properties. Add the changed-input result to the same record without overwriting
the first one. If an assertion fails, preserve the failing inputs and exception
before changing the computation.

## Reflection

- Does a flat dashboard establish equilibrium? Explain your answer before consulting the question bank.
- When should an omitted component be added?
- Which observation, not included in this synthetic exercise, would be needed
  to decide whether the model is useful for a real instance of the scenario?

## Worked Solution

No: measurement limits or observation-rule changes can also flatten it. When it addresses a specific observed inadequacy and its parameters can be supported by an observation plan.
The code's assertions give the expected numerical control. The changed-input
comparison should identify what changed and what was held fixed, while the
boundary case should be tied to the documented input domain. A real evaluation
would need an observation protocol, actual data and a comparison capable of
challenging the model rather than another copy of its constructed example.
