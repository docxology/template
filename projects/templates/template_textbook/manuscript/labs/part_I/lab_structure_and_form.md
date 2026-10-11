# Lab — Structure and Form {#sec:lab_part_I_structure_and_form}

<!-- chapter-metadata-badge -->
> Guided lab · Materials: Python environment, notebook or terminal, and a written observation record

## Objectives

Execute `textbook.models.normalize_unit_interval` with the declared inputs, compare
its output with an independently worked expectation, and explain which part of
the chapter's claim the result checks. Preserve units, reference bounds and identifiers when transforming a representation.

## Background

Linked chapter: [@sec:part_I_structure_and_form]. Three rooms have readings of ten, twenty and thirty units. A normalized display colors them zero, one half and one. A second building with one hundred, two hundred and three hundred units receives the same colors. The pattern is comparable, but the magnitude has disappeared. A useful representation keeps both the pattern and its reference scale available.
The values below are instructional inputs. No experiment on people, organisms
or services is being reported. The exercise checks mathematical behavior under
the model's assumptions rather than supplying evidence that the scenario is real.

## Procedure

1. Write the input quantities, units and assumptions from [@tbl:part_I_structure_and_form_parameters].
2. Before running code, predict one boundary value and one interior value using
   [@eq:part_I_structure_and_form_model]. Keep the prediction even if it proves incorrect.
3. Run the workflow below in a fresh interpreter. Preserve the command and output.
4. Change one allowed input or parameter and explain which qualitative feature
   should change. Run again as a separately recorded comparison.
5. Try one invalid or degenerate case from the function's documented contract;
   record whether it is rejected or handled by an explicit convention.

## Analysis

The reference range is twenty. Subtracting ten from the three observations gives zero, ten and twenty, and division by the range gives zero, one half and one. A constant collection has no nonzero range, so the tested function explicitly returns zeros. That convention prevents division by zero; it does not manufacture variation or an interpretable physical distance.

Check both the value and its interpretation. A discrepancy in arithmetic should
lead you to inspect units, input order and the declared convention. Agreement
on these synthetic inputs establishes a limited computational result; it does
not establish the opening scenario's observation rule or empirical adequacy.

## Computational Workflow

```python
import numpy as np
from textbook.models import normalize_unit_interval

z = normalize_unit_interval([10.0, 20.0, 30.0])
assert np.allclose(z, [0.0, 0.5, 1.0])
assert np.allclose(normalize_unit_interval([7.0, 7.0]), [0.0, 0.0])
print(z)
```

The code calls the shared model implementation and asserts independently known
properties. Add the changed-input result to the same record without overwriting
the first one. If an assertion fails, preserve the failing inputs and exception
before changing the computation.

## Reflection

- What is lost if normalization bounds are discarded? Explain your answer before consulting the question bank.
- Why are separately normalized buildings not an absolute comparison?
- Which observation, not included in this synthetic exercise, would be needed
  to decide whether the model is useful for a real instance of the scenario?

## Worked Solution

The original unit scale and the ability to reconstruct original magnitudes. Each uses different reference bounds; matching relative positions can hide different magnitudes.
The code's assertions give the expected numerical control. The changed-input
comparison should identify what changed and what was held fixed, while the
boundary case should be tied to the documented input domain. A real evaluation
would need an observation protocol, actual data and a comparison capable of
challenging the model rather than another copy of its constructed example.
