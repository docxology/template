# Question Bank — Core Methods and Tools {#sec:q_part_0_core_methods}

Linked chapter: [@sec:part_0_core_methods]. Write your reasoning before checking the answer;
for numeric questions retain units and the model assumption that licenses the calculation.

## Recall

1. Name four separate operations in the calibration workflow.

   *(Answer: Input reading, eligibility selection, unit conversion and model fitting.)*

2. What is a negative control?

   *(Answer: A designed case expected to fail a specific contract, such as unequal input lengths.)*

## Application

3. What slope and intercept fit the pairs (0,1), (1,3), (2,5), (3,7)?

   *(Answer: Slope two and intercept one; every residual is zero.)*

4. Does this exact fit establish real sensor accuracy?

   *(Answer: No. It checks arithmetic for constructed data, not the sensor or observation protocol.)*

## Synthesis

5. How can one implementation and an independent oracle coexist?

   *(Answer: Production callers share one tested helper, while controls derive expected answers separately.)*

## Solution Discussion

A reproducible method separates input custody, transformation, evaluation and communication. Re-running a command successfully does not establish that its scientific input or interpretation is correct.
A complete response distinguishes a designed arithmetic control from an empirical
claim, names the quantities being compared and preserves the limits of the model.
