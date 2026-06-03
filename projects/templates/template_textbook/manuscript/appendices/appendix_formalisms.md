# Appendix — Formalisms {#sec:appendix_formalisms}

A worked example of every **formal** element a technical book uses: definitions,
theorems with proofs, lemmas, algorithms in pseudocode, step-by-step
derivations, systems of numbered equations, and dimensioned quantities. Each maps
to a tested function in `src/textbook/models.py`, so the prose and the code stay
in agreement. <!-- STUB: replace these generic statements with your field's. -->

> **Convention.** Theorem-like environments below use a portable bold-label
> block-quote form that renders in every target. If your render profile loads
> `amsthm` (the preamble does), you may instead use native LaTeX `theorem`,
> `lemma`, `definition`, and `proof` environments.

---

## 1. Definitions

> **Definition 1 (Equilibrium).** A state $N^{*}$ of a dynamical system
> $\dot N = f(N)$ is an *equilibrium* if $f(N^{*}) = 0$. See
> [**equilibrium**](#gl:equilibrium).

> **Definition 2 (Carrying capacity).** For logistic dynamics, the *carrying
> capacity* $K$ is the non-zero equilibrium toward which trajectories converge.

---

## 2. A theorem with proof

> **Theorem 1 (Logistic limit).** For the logistic model in
> [@eq:formalisms_logistic] with $r > 0$ and $0 < N_0 \le K$, the trajectory
> satisfies $\lim_{t \to \infty} N(t) = K$.

$$ N(t) = \frac{K}{1 + A e^{-rt}}, \qquad A = \frac{K - N_0}{N_0} . $$ {#eq:formalisms_logistic}

*Proof.* Because $r > 0$, the term $e^{-rt} \to 0$ as $t \to \infty$. Hence the
denominator $1 + A e^{-rt} \to 1$, and therefore $N(t) \to K/1 = K$. The
constant $A \ge 0$ follows from $0 < N_0 \le K$, so $N(t)$ is increasing and the
limit is approached from below. $\qquad\blacksquare$

This is exactly the asymptotic behaviour the test
`tests/test_models.py::test_logistic_growth_starts_at_initial_and_approaches_capacity`
verifies numerically — the proof and the test assert the same fact.

---

## 3. A lemma

> **Lemma 1 (Half-life).** For exponential decay $y(t) = y_0 e^{-\lambda t}$ with
> $\lambda > 0$, the time at which $y$ falls to half its initial value is
> $t_{1/2} = \ln 2 / \lambda$, independent of $y_0$.

*Proof.* Set $y(t_{1/2}) = y_0/2$. Then $e^{-\lambda t_{1/2}} = 1/2$, so
$-\lambda t_{1/2} = -\ln 2$, giving $t_{1/2} = \ln 2 / \lambda$. The result does
not depend on $y_0$. $\qquad\blacksquare$

Implemented as `textbook.models.half_life`.

---

## 4. Algorithms (pseudocode)

Where the preamble provides an algorithm package, use it; otherwise this fenced
form renders everywhere.

```text
Algorithm 1: Ordinary least-squares line fit
Input : points (x_i, y_i), i = 1..n,  n >= 2
Output: slope m, intercept b, coefficient of determination R^2
1  x_bar <- mean(x);  y_bar <- mean(y)
2  m <- sum((x_i - x_bar)(y_i - y_bar)) / sum((x_i - x_bar)^2)
3  b <- y_bar - m * x_bar
4  SS_res <- sum((y_i - (m x_i + b))^2)
5  SS_tot <- sum((y_i - y_bar)^2)
6  R^2 <- 1 - SS_res / SS_tot      (define R^2 = 1 when SS_tot = 0)
7  return (m, b, R^2)
```

This is `textbook.models.linear_fit`; Step 6's degenerate case is covered by
`tests/test_models.py::test_linear_fit_constant_y_gives_r_squared_one`.

---

## 5. A step-by-step derivation

Starting from the logistic differential equation and separating variables:

$$
\begin{aligned}
\frac{dN}{dt} &= rN\left(1 - \frac{N}{K}\right) \\
\int \frac{dN}{N(1 - N/K)} &= \int r \, dt \\
\ln\!\left(\frac{N}{K - N}\right) &= rt + C \\
N(t) &= \frac{K}{1 + A e^{-rt}}, \qquad A = e^{-C},
\end{aligned}
$$

which recovers [@eq:formalisms_logistic]. Each line is one algebraic move; show
your work at this granularity so readers can follow without gaps.

---

## 6. A system of numbered equations

A simple predator–prey system, with each equation individually referenceable
([@eq:formalisms_prey], [@eq:formalisms_pred]):

$$ \frac{dx}{dt} = \alpha x - \beta x y $$ {#eq:formalisms_prey}

$$ \frac{dy}{dt} = \delta x y - \gamma y $$ {#eq:formalisms_pred}

The vector-field figure style for such systems is demonstrated by the quiver plot
in the format gallery ([@sec:appendix_format_gallery]).

---

## 7. Dimensioned quantities

State parameters with units explicitly, in math mode so they render in every
target:

: Worked-model parameters with representative dimensioned values.
{#tbl:formalisms_units}

| Symbol     | Quantity            | Example value             |
| ---------- | ------------------- | ------------------------- |
| $r$        | intrinsic rate      | $0.8\ \mathrm{s^{-1}}$    |
| $\lambda$  | decay constant      | $0.5\ \mathrm{s^{-1}}$    |
| $t_{1/2}$  | half-life           | $1.386\ \mathrm{s}$       |
| $K$        | carrying capacity   | $100$ individuals         |

---

## 8. Notation summary

<!-- STUB: maintain a running notation table; cross-reference Appendix B. -->
Symbols used throughout are collected in the notation appendix
([@sec:appendix_notation]); glossary definitions for narrative terms such as
[**gradient**](#gl:gradient) and [**threshold**](#gl:threshold) are in the master
glossary.
