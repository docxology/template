# Symbols and Notation {#sec:symbols_glossary}

## Core Active Inference Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| $\mathcal{F}(\pi)$ | Expected Free Energy for policy $\pi$ | $\mathbb{R}$ |
| $G(\pi)$ | Pragmatic value of policy $\pi$ | $\mathbb{R}$ |
| $H[Q(\pi)]$ | Epistemic affordance (information gain) | $\mathbb{R}$ |
| $q(s)$ | Posterior beliefs over hidden states | $\mathbb{R}^n$ |
| $p(s)$ | Prior beliefs over hidden states | $\mathbb{R}^n$ |
| $A$ | Observation likelihood matrix $P(o \mid s)$ | $\mathbb{R}^{m \times n}$ |
| $B$ | State transition matrix $P(s' \mid s, a)$ | $\mathbb{R}^{n \times n \times k}$ |
| $C$ | Preference matrix (log priors over observations) | $\mathbb{R}^m$ |
| $D$ | Prior beliefs over initial states | $\mathbb{R}^n$ |

## Meta-Cognitive Extensions

| Symbol | Description | Domain |
|--------|-------------|---------|
| $c$ | Confidence score | $[0,1]$ |
| $\lambda$ | Meta-cognitive weighting factor | $\mathbb{R}^+$ |
| $\Theta$ | Framework parameters | $\mathbb{R}^d$ |
| $w(m)$ | Meta-data weighting function | $\mathbb{R}^+$ |

## Free Energy Principle

| Symbol | Description | Domain |
|--------|-------------|---------|
| $\mathcal{F}$ | Variational free energy | $\mathbb{R}$ |
| $\mathcal{S}$ | Surprise (-log evidence) | $\mathbb{R}$ |
| $\phi$ | System parameters | $\mathbb{R}^p$ |
| $p(o,s)$ | Joint distribution over observations and states | Probability space |

## Quadrant Framework

| Symbol | Description | Domain |
|--------|-------------|---------|
| $Q1$ | Data processing (cognitive) quadrant | Framework element |
| $Q2$ | Meta-data organization (cognitive) quadrant | Framework element |
| $Q3$ | Reflective processing (meta-cognitive) quadrant | Framework element |
| $Q4$ | Higher-order reasoning (meta-cognitive) quadrant | Framework element |

## Statistical Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| $\mathbb{E}[\cdot]$ | Expectation operator | Functional |
| $KL[p\|q]$ | Kullback-Leibler divergence | $\mathbb{R}^+$ |
| $\sigma(\cdot)$ | Softmax function | Mapping to probabilities |
| $\nabla$ | Gradient operator | Functional |

## Implementation Variables

| Symbol | Description | Domain |
|--------|-------------|---------|
| $t$ | Time step | $\mathbb{N}$ |
| $\tau$ | Temporal horizon | $\mathbb{N}$ |
| $\eta$ | Learning rate | $\mathbb{R}^+$ |
| $\alpha$ | Adaptation rate | $\mathbb{R}^+$ |
| $\beta$ | Feedback strength | $\mathbb{R}^+$ |