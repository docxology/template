# Experimental Setup

This section details the complete experimental configuration used to generate the results in this study. Every parameter value below is injected programmatically from `config.yaml` and the analysis pipeline — no value is hardcoded in the manuscript source.

## Problem Definition

The optimization target is the quadratic objective function:

\begin{equation}
\label{eq:quadratic_objective}
f(x) = \frac{1}{2} x^T A x - b^T x
\end{equation}

with $A = [[1.0]]$ and $b = [1.0]$, yielding the analytical optimum at $x^* = 1.0$ with $f(x^*) = -0.5$.

## Parameter Space

The experiment systematically varies the gradient descent step size across 6 values:

- $\\alpha = 0.01$ (conservative)
- $\\alpha = 0.1$ (moderate)
- $\\alpha = 0.5$ (aggressive)
- $\\alpha = 1.0$ (very aggressive)
- $\\alpha = 1.5$
- $\\alpha = 2.5$

All runs start from the initial point $x_0 = 0.0$ and use a convergence tolerance of $\|{\nabla f}\| < 10^{-8}$ with a maximum iteration limit of $N_{\max} = 1000$.

## Numerical Stability Grid

To validate robustness, the optimizer is exercised across a grid of 8 starting points and 6 step sizes, producing 48 total evaluations. This comprehensive sweep confirms that convergence is not an artifact of a narrow parameter choice.

## Dimensional Scaling

Performance benchmarking spans problem dimensions $d \in \{1, 2, 5, 10, 20, 50\}$, from the scalar case ($d = 1$) to moderate dimensionality ($d = 50$), using identity-Hessian quadratics to isolate algorithmic scaling from problem conditioning effects.

## Computational Environment

- **Python**: 3.12.11
- **NumPy**: 2.4.1
- **Platform**: Darwin arm64
- **Generated**: 2026-03-17T22:47:01Z
