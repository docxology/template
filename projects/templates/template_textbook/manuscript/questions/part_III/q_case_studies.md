# Question Bank — Case Studies {#sec:q_part_III_case_studies}

Linked chapter: [@sec:part_III_case_studies]. Answers follow each question in
italics.

## Recall

1. What two summary numbers does the chapter report for each condition group, and
   which function computes them?
   *(Answer: the per-group mean — e.g. $2.20$, $3.50$, $4.95$ — plus an overall
   spread from `textbook.models.descriptive_statistics`, which returns mean, std,
   min, max, and count.)*
2. What do the slope and intercept of the fitted line
   [@eq:part_III_case_studies_fit] represent?
   *(Answer: the slope ($\approx 1.375$) is the response added per dose step; the
   intercept ($\approx 2.175$) is the predicted response at dose $0$, which should
   match the control mean.)*

## Application

3. The intercept ($2.175$) is close to the control mean ($2.20$). Why is this a
   useful check rather than a coincidence to ignore?
   *(Answer: a fit whose dose-$0$ prediction matches the measured control is
   internally consistent; a large mismatch would signal a coding error or a poor
   model.)*
4. The line predicts $\widehat{y}(3) = 6.3$. Why should this prediction be
   flagged?
   *(Answer: dose $3$ is outside the measured range $[0, 2]$ — it is an
   extrapolation, and real dose–response curves usually saturate, so a line will
   overpredict.)*

## Synthesis

5. With only three averaged points the fit reports $R^2 = 0.999$. Explain why this
   is weak evidence and describe one experiment that would strengthen — or
   overturn — the linear conclusion.
   *(Answer: $R^2$ near $1$ on three points mostly reflects that a line can pass
   through three dots; it says little about prediction. Collecting more doses,
   especially higher ones, would reveal curvature/saturation and test whether the
   linear model generalises. Accept reasoned alternatives.)*
