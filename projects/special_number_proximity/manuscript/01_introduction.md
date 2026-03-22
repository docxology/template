# Introduction

Rational numbers are dense in the reals, yet the **quality** of the best rational approximation at a fixed denominator ceiling varies sharply across individual $x$. Number theory classifies extremes: algebraic irrationals of degree two have bounded partial quotients in their continued fraction expansion and are *badly approximable* in the sense of [@cassels1957]; almost every $x \in \mathbb{R}$ satisfies Khinchin-type statistics for the growth of those quotients [@khinchin1964continued]. Transcendental constants carry no finite-degree algebraic constraint, but particular numbers such as $\pi$ or $e$ still admit **structured** rational approximations from series, integrals, or independent constructions—so their finite-$Q$ behaviour need not resemble a “generic” draw from a simple continuous law.

### Finite $Q$ as a deliberate lens

As $Q$ grows, $\delta_Q(x)$ tends to $0$ for every irrational $x$, and $\mu_Q(x)$ admits universal upper bounds tied to continued-fraction convergents [@hurwitz1891]. Those limits wash out differences on a logarithmic scale unless one studies **rates** or **exceptional sets**. By contrast, fixing $Q$ at a moderate value (for example $Q=120$ in the default configuration) asks a different question: *among all rationals with denominators up to $Q$, how small is the best error, and how does that single number compare to the same functional evaluated on random $X$?* The answer is a **scalar summary**—an empirical percentile relative to a chosen reference law—not a Diophantine *type* in the classical sense.

### Statistical comparison protocol

The implementation draws a pooled sample $X_1,\ldots,X_n$ on $[0,1)$, computes $\delta_Q(X_i)$ and $\mu_Q(X_i)$ for each draw, and records distribution summaries (quantiles, tail percentiles). For each registered constant $x^\star$ it stores $\delta_Q(x^\star)$, $\mu_Q(x^\star)$, and the **empirical rank** (proportion of reference samples strictly below the constant's value). Optional `experiment.q_sensitivity` repeats the constant table at additional $Q$ values **without resampling** $X$, so shifts in rank isolate the effect of enlarging the rational search set.

### Scope of this note

We do not prove new Diophantine bounds. The goal is **methodological**: connect classical statements about $Q\to\infty$ to concrete finite-$Q$ measurements, document the numerical chain (three-numerator scan, lattice cross-checks, convergent-only certificates), and parameterize the study from YAML so $Q$, sample sizes, reference components, and `compare_mod1` can change without editing infrastructure code.
