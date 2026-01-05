# Symbols and Notation {#sec:symbols_glossary}

## Core Active Inference Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(\mathcal{F}(\pi)\) | Expected Free Energy for policy \(\pi\) | ℝ |
| \(G(\pi)\) | Pragmatic value of policy \(\pi\) | ℝ |
| \(H[Q(\pi)]\) | Epistemic affordance (information gain) | ℝ |
| \(q(s)\) | Posterior beliefs over hidden states | ℝⁿ |
| \(p(s)\) | Prior beliefs over hidden states | ℝⁿ |
| \(A\) | Observation likelihood matrix \(P(o \mid s)\) | \(\mathbb{R}^{m \times n}\) |
| \(B\) | State transition matrix \(P(s' \mid s, a)\) | \(\mathbb{R}^{n \times n \times k}\) |
| \(C\) | Preference matrix (log priors over observations) | ℝ^m |
| \(D\) | Prior beliefs over initial states | ℝ^n |

## Meta-Cognitive Extensions

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(c\) | Confidence score | [0,1] |
| \(\lambda\) | Meta-cognitive weighting factor | ℝ⁺ |
| \(\Theta\) | Framework parameters | ℝ^d |
| \(w(m)\) | Meta-data weighting function | ℝ⁺ |

## Free Energy Principle

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(\mathcal{F}\) | Variational free energy | ℝ |
| \(\mathcal{S}\) | Surprise (-log evidence) | ℝ |
| \(\phi\) | System parameters | ℝ^p |
| \(p(o,s)\) | Joint distribution over observations and states | Probability space |

## Quadrant Framework

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(Q1\) | Data processing (cognitive) quadrant | Framework element |
| \(Q2\) | Meta-data organization (cognitive) quadrant | Framework element |
| \(Q3\) | Reflective processing (meta-cognitive) quadrant | Framework element |
| \(Q4\) | Higher-order reasoning (meta-cognitive) quadrant | Framework element |

## Statistical Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(\mathbb{E}[\cdot]\) | Expectation operator | Functional |
| \(KL[p\|q]\) | Kullback-Leibler divergence | ℝ⁺ |
| \(\sigma(\cdot)\) | Softmax function | Mapping to probabilities |
| \(\nabla\) | Gradient operator | Functional |

## Implementation Variables

| Symbol | Description | Domain |
|--------|-------------|---------|
| \(t\) | Time step | ℕ |
| \(\tau\) | Temporal horizon | ℕ |
| \(\eta\) | Learning rate | ℝ⁺ |
| \(\alpha\) | Adaptation rate | ℝ⁺ |
| \(\beta\) | Feedback strength | ℝ⁺ |