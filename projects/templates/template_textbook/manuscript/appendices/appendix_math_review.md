# Appendix C — Mathematical Review {#sec:appendix_math_review}

<!-- chapter-metadata-badge -->
> Reference appendix · From explicit assumptions to runnable calculations.

This review derives the arithmetic used by the book's examples. The functions in `textbook.models` implement these formulas under declared input restrictions. Mathematical reasoning and numerical tests supply different checks: a formula explains a relationship, while an executable example checks a specific implementation and finite input.

## Functions and rescaling

A function assigns an output to each input in its domain. With reference minimum $a$ and maximum $b>a$, define $z=(x-a)/(b-a)$. For $x=[10,20,30]$, $a=10$ and $b=30$ give $z=[0,0.5,1]$. Values outside these reference bounds would lie outside the interval. The helper derives bounds from the supplied array, so fitting bounds separately to two groups can hide their absolute difference. For a constant array it returns zeros by an explicit convention, rather than dividing by zero.

```python
import numpy as np
from textbook import models

np.testing.assert_allclose(models.normalize_unit_interval(np.array([10., 20., 30.])), [0., .5, 1.])
np.testing.assert_allclose(models.normalize_unit_interval(np.array([4., 4.])), [0., 0.])
```

## Logistic growth

The rate law is $N'=rN(1-N/K)$. For $r>0$, $K>0$, and positive initial $N_0$, its solution is $N(t)=K/(1+A e^{-rt})$, where $A=(K-N_0)/N_0$. At $t=0$, the denominator is $K/N_0$, recovering the initial condition. As $t$ increases without bound, the exponential tends to zero and the quantity tends to $K$. This limit does not establish that a real population has a fixed capacity.

Take $r=0.8$, $K=100$, $N_0=5$, and $t=5$. Then $A=19$ and $e^{-4}\approx0.0183156$. The denominator is $1+19(0.0183156)\approx1.347997$, giving $N(5)\approx74.1841$. A reproducible calculation retains more precision than the printed explanation:

```python
from math import exp
from textbook import models

expected = 100. / (1. + 19. * exp(-4.))
observed = models.logistic_growth(5., r=.8, carrying_capacity=100., initial=5.)
assert abs(float(observed) - expected) < 1e-12
```

## Exponential decay

For $N'=-\lambda N$, $N(t)=N_0e^{-\lambda t}$. Solving $N(t_{1/2})=N_0/2$ gives $t_{1/2}=\ln(2)/\lambda$. If $\lambda=\ln(2)$ per time unit, the half-life is one unit: a quantity beginning at $100$ reaches $50$ at one and $25$ at two. This states a multiplicative rate; it is not a subtraction of the same amount at every step.

```python
from math import log
import numpy as np
from textbook import models

np.testing.assert_allclose(models.exponential_decay(np.array([0., 1., 2.]), initial=100., rate=log(2.)), [100., 50., 25.])
assert abs(models.half_life(log(2.)) - 1.) < 1e-12
```

## Saturating response

For positive $V_{\max}$ and $K_m$, $v(x)=V_{\max}x/(K_m+x)$ at nonnegative $x$. At zero the response is zero. At $x=K_m$ the response is $V_{\max}/2$. For large input it approaches $V_{\max}$. With $V_{\max}=1$ and $K_m=3$, inputs $0,3,12$ produce $0,0.5,0.8$. The shape is illustrative; it does not identify a biochemical mechanism from a curve alone.

```python
import numpy as np
from textbook import models

np.testing.assert_allclose(models.saturating_response(np.array([0., 3., 12.]), maximum=1., half_saturation=3.), [0., .5, .8])
```

## Least-squares fitting

A line predicts $\widehat y_i=mx_i+b$. Least squares minimizes the sum of squared residuals. If $x=[0,1,2]$ and $y=[1,3,5]$, the exact relation is $y=2x+1$ and the residuals vanish. For the case-study means $[2.20,3.50,4.95]$, the fitted slope is $1.375$ and intercept $2.175$; predictions are $[2.175,3.55,4.925]$, with residuals $[0.025,-0.05,0.025]$. Their sum is zero up to roundoff. The small residuals describe these three points, not an unseen dose.

```python
import numpy as np
from textbook import models

fit = models.linear_fit(np.array([0., 1., 2.]), np.array([1., 3., 5.]))
assert abs(fit.slope - 2.) < 1e-12
assert abs(fit.intercept - 1.) < 1e-12
```

## Means and spread

For $x=[2,4,6,8]$, the mean is $5$ and the squared deviations sum to $20$. Population variance divides by $4$, yielding $5$ and standard deviation $\sqrt5$. Sample variance divides by $3$, yielding $20/3$. Neither quantity is automatically a standard error of a mean. Reporting which denominator was used is part of reporting the result.

```python
from math import sqrt
from textbook import models

stats = models.descriptive_statistics([2., 4., 6., 8.])
assert abs(stats["mean"] - 5.) < 1e-12
assert abs(stats["std"] - sqrt(5.)) < 1e-12
```

## Exercise and solution

A learner changes the time unit from days to hours but keeps the decay rate's numeric value unchanged. Will the predicted half-life describe the same process? No: the rate must be divided by twenty-four when time is measured in hours. The numeric half-life then multiplies by twenty-four. Check units before interpreting a change in a graph.
