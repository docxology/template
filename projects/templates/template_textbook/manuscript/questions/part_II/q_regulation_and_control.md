# Question Bank — Regulation and Control {#sec:q_part_II_regulation_and_control}

Linked chapter: [@sec:part_II_regulation_and_control]. Write your reasoning before checking the answer;
for numeric questions retain units and the model assumption that licenses the calculation.

## Recall

1. What is the chosen signed-error convention?

   *(Answer: Setpoint minus measured state.)*

2. Which plant assumption yields exponential error decay under proportional action?

   *(Answer: An ideal integrator plant with state derivative equal to the action.)*

## Application

3. What is the error magnitude after one half-life from one hundred?

   *(Answer: Fifty.)*

4. Why can an actuator limit invalidate the exponential response?

   *(Answer: The action no longer equals gain times error when clipped, changing the state law.)*

## Synthesis

5. What additional evidence is needed for a real stability claim?

   *(Answer: The plant and controller update laws, measurement timing, limits, parameter domain and appropriate mathematical or observed checks.)*

## Solution Discussion

Regulation is a declared relationship between a measured error and an action, with assumptions about timing and limits. Drawing a negative-feedback loop does not prove that it is stable.
A complete response distinguishes a designed arithmetic control from an empirical
claim, names the quantities being compared and preserves the limits of the model.
