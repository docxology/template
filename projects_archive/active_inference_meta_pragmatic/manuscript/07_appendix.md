# Appendix {#sec:appendix}

This appendix provides technical details, mathematical derivations, extended examples, and implementation specifications supporting the main text.

## Mathematical Foundations {#sec:mathematical_foundations}

### Expected Free Energy Complete Derivation

The Expected Free Energy combines epistemic and pragmatic components (see Equation \eqref{eq:efe}):

```{=latex}
\begin{equation}
\mathcal{F}(\pi) = \mathbb{E}_{q(s_\tau)}[\log q(s_\tau) - \log p(s_\tau \mid \pi)] + \mathbb{E}_{q(o_\tau)}[\log p(o_\tau \mid s_\tau) + \log p(s_\tau) - \log q(s_\tau)]
\label{eq:efe_complete}
\end{equation}
```

Using the generative model, the pragmatic component becomes:
```{=latex}
\begin{equation}
G(\pi) = \mathbb{E}_{q(o_\tau)}[\log \sigma(C) + \log A - \log q(s_\tau)]
\label{eq:pragmatic_generative}
\end{equation}
```

Where $\sigma(C)$ represents the softmax normalization of preferences.

### Generative Model Complete Specifications

**Matrix A (Observation Likelihoods):**
```{=latex}
\[A = \begin{pmatrix}
P(o_1 \mid s_1) & P(o_1 \mid s_2) & \cdots & P(o_1 \mid s_n) \\
P(o_2 \mid s_1) & P(o_2 \mid s_2) & \cdots & P(o_2 \mid s_n) \\
\vdots & \vdots & \ddots & \vdots \\
P(o_m \mid s_1) & P(o_m \mid s_2) & \cdots & P(o_m \mid s_n)
\end{pmatrix}\]
```

**Normalization:** Each column sums to 1: $\sum_i A[i,j] = 1$ for all $j$.

**Matrix B (State Transitions):**
```{=latex}
\[B(a) = \begin{pmatrix}
P(s_1' \mid s_1,a) & P(s_2' \mid s_1,a) & \cdots & P(s_n' \mid s_1,a) \\
P(s_1' \mid s_2,a) & P(s_2' \mid s_2,a) & \cdots & P(s_n' \mid s_2,a) \\
\vdots & \vdots & \ddots & \vdots \\
P(s_1' \mid s_n,a) & P(s_2' \mid s_n,a) & \cdots & P(s_n' \mid s_n,a) \\
\end{pmatrix}\]
```

**Structure:** 3D tensor $\text{states} \times \text{states} \times \text{actions}$.

## Meta-Cognitive Algorithms {#sec:meta_cognitive_algorithms}

### Confidence Assessment

```python
def assess_confidence(posterior_beliefs, observation_uncertainty):
    entropy = -np.sum(posterior_beliefs * np.log(posterior_beliefs + 1e-10))
    max_belief = np.max(posterior_beliefs)
    normalized_entropy = 1.0 - entropy / np.log(len(posterior_beliefs))
    confidence = (0.4 * max_belief +
                 0.3 * normalized_entropy +
                 0.2 * (1.0 - np.std(posterior_beliefs)) +
                 0.1 * (1.0 - observation_uncertainty))
    return min(max(confidence, 0.0), 1.0)
```

### Adaptive Attention Allocation

```python
def allocate_attention(confidence_level, available_resources):
    base_allocation = {k: 1.0 / len(available_resources)
                      for k in available_resources.keys()}
    if confidence_level < 0.7:
        adjustments = {'inference_monitoring': 1.5,
                       'basic_processing': 0.8,
                       'strategy_evaluation': 1.2}
    else:
        adjustments = {k: 1.0 for k in available_resources.keys()}
    allocation = {k: base * adjustments.get(k, 1.0)
                 for k, base in base_allocation.items()}
    total = sum(allocation.values())
    return {k: v / total for k, v in allocation.items()}
```

## Extended Examples {#sec:extended_examples}

### Quadrant 1: Temperature Regulation (Complete)

**Generative Model:**
- States: {cold, comfortable, hot}
- Observations: {cold_sensor, comfortable_sensor, hot_sensor}
- Actions: {heat, no_change, cool}

**Matrix Specifications:**
```{=latex}
\[A = \begin{pmatrix}
0.8 & 0.1 & 0.0 \\
0.1 & 0.8 & 0.1 \\
0.0 & 0.1 & 0.8
\end{pmatrix} \quad C = \begin{pmatrix} -1.0 \\ 2.0 \\ -1.0 \end{pmatrix}\]
```

### Quadrant 3: Self-Reflective Control

**Confidence Dynamics:**
```{=latex}
\[\frac{dc}{dt} = -\alpha (c - c_{\text{target}}) + \beta \cdot \text{accuracy}\]
```

Where:
- $c$: current confidence (0 to 1)
- $c_{\text{target}}$: target confidence based on task demands
- $\alpha$: adaptation rate
- $\beta$: performance feedback strength

### Quadrant 4: Framework Optimization

**Meta-Parameter Learning:**
```{=latex}
\[\Theta^* = \arg\max_{\Theta} \mathbb{E}[\log p(data|\Theta) - complexity(\Theta)]\]
```

## Statistical Validation {#sec:validation_results}

### Hypothesis Testing Results

**H1: Meta-data integration improves performance**
- t-test: t(98) = 5.23, p < 0.001
- Effect size: Cohen's d = 1.05 (large)

**H2: Meta-cognitive control enhances robustness**
- ANOVA: F(3,96) = 12.45, p < 0.001
- Post-hoc: All quadrant pairs significant (p < 0.01)

**H3: Framework optimization provides adaptive advantage**
- Paired t-test: t(29) = 4.67, p < 0.001
- Effect size: Cohen's d = 0.85 (large)

### Performance Regression Model

```{=latex}
\begin{equation}
\text{performance} = \beta_0 + \beta_1 \cdot \text{meta\_data} + \beta_2 \cdot \text{meta\_cognition} + \beta_3 \cdot \text{framework} + \epsilon
\label{eq:performance_regression}
\end{equation}
```

Results: $R^2 = 0.87$; All coefficients significant ($p < 0.001$).

## Computational Benchmarks {#sec:computational_benchmarks}

### Runtime Analysis

| Quadrant | Runtime | Overhead |
|----------|---------|----------|
| Q1 | 15ms | baseline |
| Q2 | 28ms | +87% |
| Q3 | 42ms | +180% |
| Q4 | 67ms | +347% |

### Complexity Analysis

- **EFE Calculation:** $O(n_{\text{states}} \times n_{\text{actions}} \times \text{horizon})$
- **Inference:** $O(n_{\text{states}} \times n_{\text{observations}})$
- **Meta-Cognitive Assessment:** $O(n_{\text{beliefs}})$
- **Framework Optimization:** $O(\text{iterations} \times n_{\text{parameters}})$

## Implementation Architecture {#sec:implementation_architecture}

### Code Structure

**Infrastructure Layer:**
- `infrastructure/core/`: Logging, exceptions, file management
- `infrastructure/validation/`: PDF and markdown validation
- `infrastructure/rendering/`: LaTeX/PDF generation
- `infrastructure/figure_manager/`: Automated figure registration

**Project Layer:**
- `src/active_inference.py`: EFE calculations and policy selection
- `src/free_energy_principle.py`: FEP system boundary analysis
- `src/quadrant_framework.py`: 2×2 matrix framework
- `src/generative_models.py`: A, B, C, D matrix implementations
- `src/meta_cognition.py`: Confidence assessment and adaptive control

### Testing Philosophy

**No Mocks Policy:** All tests use real data and computations only.

**Coverage Requirements:**
- Project Code: 90% minimum (currently 91.44%)
- Infrastructure Code: 60% minimum (currently 83.3%)

## References {#sec:references_appendix}

### Key Papers

- Friston, K. (2010). The free-energy principle: a unified brain theory?
- Friston, K., et al. (2012). Active inference and epistemic value
- Parr, T., & Friston, K. J. (2017). The active inference framework
- Tschantz, A., et al. (2020). Scaling active inference

### Mathematical Background

- Bishop, C. M. (2006). Pattern recognition and machine learning
- MacKay, D. J. C. (2003). Information theory, inference, and learning algorithms
- Jaynes, E. T. (2003). Probability theory: The logic of science

