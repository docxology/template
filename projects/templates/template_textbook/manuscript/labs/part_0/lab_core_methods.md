# Lab — Core Methods and Tools {#sec:lab_part_0_core_methods}

<!-- chapter-metadata-badge -->
> Guided lab · Materials: Python environment, notebook or terminal, and a written observation record

## Objectives

Execute `textbook.models.linear_fit` with the declared inputs, compare
its output with an independently worked expectation, and explain which part of
the chapter's claim the result checks. Record transformations and run an exact arithmetic control before analyzing unfamiliar data.

## Background

Linked chapter: [@sec:part_0_core_methods]. Two classmates calculate a calibration line from the same spreadsheet and obtain different slopes. One silently removes a row; the other changes a unit. Their mathematics may be sound, but their methods are different. A useful workflow exposes both choices before either result appears in a figure.
The values below are instructional inputs. No experiment on people, organisms
or services is being reported. The exercise checks mathematical behavior under
the model's assumptions rather than supplying evidence that the scenario is real.

## Procedure

1. Write the input quantities, units and assumptions from [@tbl:part_0_core_methods_parameters].
2. Before running code, predict one boundary value and one interior value using
   [@eq:part_0_core_methods_model]. Keep the prediction even if it proves incorrect.
3. Run the workflow below in a fresh interpreter. Preserve the command and output.
4. Change one allowed input or parameter and explain which qualitative feature
   should change. Run again as a separately recorded comparison.
5. Try one invalid or degenerate case from the function's documented contract;
   record whether it is rejected or handled by an explicit convention.

## Analysis

The four deliberately constructed pairs lie on $y=2x+1$. The slope is two output units per input unit, the intercept is one output unit and every residual is zero, so the reported coefficient of determination is one. The exact fit is an arithmetic control for the implementation; it supplies no evidence about an unobserved real-world mechanism.

Check both the value and its interpretation. A discrepancy in arithmetic should
lead you to inspect units, input order and the declared convention. Agreement
on these synthetic inputs establishes a limited computational result; it does
not establish the opening scenario's observation rule or empirical adequacy.

## Computational Workflow

```python
import numpy as np
from textbook.models import linear_fit

x = np.array([0.0, 1.0, 2.0, 3.0])
y = np.array([1.0, 3.0, 5.0, 7.0])
fit = linear_fit(x, y)
assert np.isclose(fit.slope, 2.0)
assert np.isclose(fit.intercept, 1.0)
assert np.allclose(fit.predict(x), y)
print(fit)
```

The code calls the shared model implementation and asserts independently known
properties. Add the changed-input result to the same record without overwriting
the first one. If an assertion fails, preserve the failing inputs and exception
before changing the computation.

## Reflection

- What is a negative control? Explain your answer before consulting the question bank.
- How can one implementation and an independent oracle coexist?
- Which observation, not included in this synthetic exercise, would be needed
  to decide whether the model is useful for a real instance of the scenario?

## Worked Solution

A designed case expected to fail a specific contract, such as unequal input lengths. Production callers share one tested helper, while controls derive expected answers separately.
The code's assertions give the expected numerical control. The changed-input
comparison should identify what changed and what was held fixed, while the
boundary case should be tied to the documented input domain. A real evaluation
would need an observation protocol, actual data and a comparison capable of
challenging the model rather than another copy of its constructed example.
