# Appendix B — Notation and Symbols {#sec:appendix_notation}

<!-- chapter-metadata-badge -->
> Reference appendix · Symbol and unit conventions for the worked models.

A symbol acquires meaning from its definition, units, and domain. The same letter can represent different quantities in different models; a local parameter table therefore governs the chapter in which it appears. These conventions summarize the computational examples rather than imposing a universal scientific vocabulary.

## Conventions

Scalars are italic; vectors and arrays are collections of scalar observations. Subscript zero denotes an initial value. A hat denotes a prediction. Time is nonnegative in the examples. SI units are used when a physical unit is declared; otherwise time and response units are explicitly illustrative. Counts have a unit of counted entities even when their numeric representation is dimensionless.

| Symbol | Meaning | Units | Convention |
| --- | --- | --- | --- |
| $t$ | elapsed time | time | Origin is the stated initial observation. |
| $N(t)$ | evolving quantity | entities or response | Positive in the logistic example. |
| $N_0$ | initial quantity | same as $N$ | Satisfies $N(0)=N_0$. |
| $r$ | logistic rate | inverse time | Positive rates used for growth. |
| $K$ | carrying capacity | same as $N$ | Positive finite reference scale. |
| $\lambda$ | decay rate | inverse time | Positive for declining trajectories. |
| $t_{1/2}$ | half-life | time | $\ln(2)/\lambda$. |
| $V_{\max}$ | response ceiling | response | Positive scale in the response example. |
| $K_m$ | half-response input | input | Positive; does not denote a sharp cutoff. |
| $x_i,y_i$ | paired observations | input, response | Index $i$ identifies the same pair. |
| $m,b$ | line slope and intercept | response/input, response | Prediction is $\widehat y=mx+b$. |
| $\overline x,\sigma$ | mean and population spread | data units | Statistics helper uses denominator $n$. |
| $s$ | sample spread | data units | Uses denominator $n-1$, when defined. |
| $e,u,k$ | control error, command, gain | state, state/time, inverse time | Ideal integrator example only. |
| $z$ | normalized value | dimensionless | Depends on the chosen reference bounds. |
| $R^2$ | fraction of fitted variation explained | dimensionless | Descriptive fit score, not future accuracy. |

## A dimensional check

The exponent in $e^{-rt}$ must be dimensionless, so $r$ has inverse-time units. If $r=0.7$ per day and $t=2$ days, then $rt=1.4$. Replacing days with hours changes the numeric rate to $0.7/24$ per hour while preserving the product at $t=48$ hours. Keeping the old rate with the new time would change the model rather than its notation.

In $v=V_{\max}x/(K_m+x)$, the denominator sums quantities with the same input unit. Their ratio is dimensionless, and the result has the response unit of $V_{\max}$. In a line, the intercept retains response units while the slope converts input increments into response increments. Normalize deliberately: removing units from a representation does not remove them from the interpretation.

## Distinguish indices and parameters

An index enumerates observations; a parameter specifies a model. The six rows in the case-study fixture are not six independent estimates of a physical law. Their condition labels and supplied error magnitudes remain part of the record. A change in an observation requires a new computation, while a change in an assumed parameter requires a new scenario. Both changes should be documented before comparing results.

See [@sec:appendix_math_review] for numerical examples and [@sec:appendix_formalisms] for mathematical domains.
