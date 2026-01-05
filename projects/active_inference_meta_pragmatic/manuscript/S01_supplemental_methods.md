# Supplemental Methods {#sec:supplemental_methods}

This supplemental section provides methodological details, including generative model specifications, mathematical derivations, and implementation algorithms. These materials support the main text by providing complete technical specifications that enable replication and extension of the quadrant structure analysis.

## Generative Model Specifications {#sec:complete_generative_models}

### Matrix A: Observation Likelihoods

The observation likelihood matrix defines the probabilistic mapping from hidden states to observations:

```{=latex}
\[A = \begin{pmatrix}
P(o_1 \mid s_1) & P(o_1 \mid s_2) & \cdots & P(o_1 \mid s_n) \\
P(o_2 \mid s_1) & P(o_2 \mid s_2) & \cdots & P(o_2 \mid s_n) \\
\vdots & \vdots & \ddots & \vdots \\
P(o_m \mid s_1) & P(o_m \mid s_2) & \cdots & P(o_m \mid s_n)
\end{pmatrix}\]
```

**Normalization:** Each column sums to 1: \(\sum_i A[i,j] = 1\) for all \(j\), representing a valid probability distribution over observations for each state. This ensures that for any hidden state \(s_j\), the probabilities of all possible observations sum to 1.

**Interpretation:**
- Rows correspond to observation modalities (different types of sensory inputs: visual, auditory, tactile, etc.)
- Columns correspond to hidden state conditions (different possible world states: object present/absent, temperature high/low, etc.)
- Entry \(A[i,j]\) represents the probability of observing \(o_i\) given state \(s_j\), encoding how reliably observations indicate underlying states
- High diagonal values (\(A[i,i]\)) indicate reliable observations (state \(s_i\) strongly predicts observation \(o_i\))
- Non-zero off-diagonal values indicate observation ambiguity (multiple states can produce the same observation, creating uncertainty)

### Matrix B: State Transition Dynamics

The transition matrix defines how actions influence state changes:

```{=latex}
\[B(a) = \begin{pmatrix}
P(s_1' \mid s_1,a) & P(s_2' \mid s_1,a) & \cdots & P(s_n' \mid s_1,a) \\
P(s_1' \mid s_2,a) & P(s_2' \mid s_2,a) & \cdots & P(s_n' \mid s_2,a) \\
\vdots & \vdots & \ddots & \vdots \\
P(s_1' \mid s_n,a) & P(s_2' \mid s_n,a) & \cdots & P(s_n' \mid s_n,a) \\
\end{pmatrix}\]
```

**Structure:** 3D tensor with dimensions \(\text{states} \times \text{states} \times \text{actions}\), where each slice \(B[:,:,a]\) is a \(n_{\text{states}} \times n_{\text{states}}\) transition matrix for action \(a\).

**Properties:**
- Each \(B[:,:,a]\) is a stochastic matrix: \(\sum_j B[i,j,a] = 1\) for all \(i, a\), ensuring valid probability distributions over next states
- Enables modeling of controllable state transitions: different actions lead to different transition probabilities
- Different actions can implement different transition dynamics: action \(a_1\) might make certain transitions likely while action \(a_2\) makes different transitions likely
- The tensor structure allows modeling of how the same action can have different effects depending on the current state

### Matrix C: Preference Landscape

The preference matrix defines the desirability of different observations:

```{=latex}
\[C = \begin{pmatrix} c_1 \\ c_2 \\ \vdots \\ c_m \end{pmatrix}\]
```

**Interpretation:**
- Positive values indicate preferred observations
- Negative values indicate avoided observations
- Magnitude indicates strength of preference/aversion
- Used in softmax normalization: \(P(o) \propto \exp(C)\)

### Matrix D: Prior State Distribution

The prior beliefs over hidden states:

```{=latex}
\[D = \begin{pmatrix} d_1 \\ d_2 \\ \vdots \\ d_n \end{pmatrix}\]
```

**Properties:**
- Sums to 1 (valid probability distribution)
- Represents initial beliefs before observation
- Can encode innate biases or learned priors

## EFE Derivation {#sec:extended_efe_derivation}

### EFE Formulation

The Expected Free Energy combines epistemic and pragmatic components:

```{=latex}
\[\mathcal{F}(\pi) = \overbrace{\mathbb{E}_{q(s_\tau \mid \pi)}[\log q(s_\tau \mid \pi) - \log p(s_\tau \mid \pi)]}^{\text{Epistemic Affordance}} + \overbrace{\mathbb{E}_{q(o_\tau,s_\tau \mid \pi)}[\log p(o_\tau,s_\tau) - \log q(s_\tau,o_\tau \mid \pi)]}^{\text{Pragmatic Value}}\]
```

### Epistemic Component Expansion

The epistemic affordance measures information gain:

\[H[Q(\pi)] = \mathbb{E}_{q(s_\tau \mid \pi)}[\log q(s_\tau \mid \pi)] - \mathbb{E}_{q(s_\tau \mid \pi)}[\log p(s_\tau \mid \pi)]\]

This can be rewritten using KL divergence:

\[H[Q(\pi)] = KL[q(s_\tau \mid \pi)||p(s_\tau \mid \pi)]\]

### Pragmatic Component Expansion

The pragmatic value measures goal achievement:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau|\pi)}[\log p(o_\tau,s_\tau) - \log q(s_\tau,o_\tau|\pi)]\]

Using the generative model decomposition:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau \mid \pi)}[\log p(o_\tau \mid s_\tau) + \log p(s_\tau) - \log q(s_\tau \mid \pi) - \log p(o_\tau \mid \pi)]\]

The pragmatic value becomes:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau \mid \pi)}[\log \tilde{A}(o_\tau,s_\tau) + \log p(s_\tau) - \log q(s_\tau \mid \pi)]\]

Where \(\tilde{A}\) includes the preference weighting.

## Meta-Data Integration Methods {#sec:meta_data_integration}

### Confidence-Weighted Inference

Incorporate observation confidence into belief updating:

\[q(s \mid o,c) \propto q(s) \cdot A(o \mid s) \cdot w(c)\]

Where \(w(c)\) is a confidence-dependent weighting function:

```{=latex}
\[w(c) = \begin{cases}
c & \text{if } c > \theta \\
\frac{\theta}{2} & \text{if } c \leq \theta
\end{cases}\]
```

### Temporal Meta-Data Processing

Incorporate temporal consistency information:

\[q(s_t \mid o_{1:t}, m_t) \propto q(s_t \mid o_t) \cdot \phi(m_t \mid s_{t-1})\]

Where \(\phi\) represents temporal meta-data likelihood.

### Multi-Source Meta-Data Fusion

Combine multiple meta-data sources:

\[w_{combined} = \prod_{k=1}^K w_k(m_k)\]

Where each \(w_k\) represents a different meta-data weighting function.

## Meta-Cognitive Control Algorithms {#sec:meta_cognitive_algorithms}

### Confidence Assessment Algorithm

```python
def assess_confidence(posterior_beliefs, observation_uncertainty):
    # Calculate entropy
    entropy = -np.sum(posterior_beliefs * np.log(posterior_beliefs + 1e-10))

    # Calculate max belief strength
    max_belief = np.max(posterior_beliefs)

    # Composite confidence score
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
    # Base allocation
    base_allocation = {k: 1.0 / len(available_resources)
                      for k in available_resources.keys()}

    if confidence_level < 0.7:
        # Low confidence: increase monitoring
        adjustments = {
            'inference_monitoring': 1.5,
            'basic_processing': 0.8,
            'strategy_evaluation': 1.2
        }
    else:
        # High confidence: efficient allocation
        adjustments = {k: 1.0 for k in available_resources.keys()}

    # Apply adjustments
    allocation = {k: base * adjustments.get(k, 1.0)
                 for k, base in base_allocation.items()}

    # Normalize
    total = sum(allocation.values())
    return {k: v / total for k, v in allocation.items()}
```

## Framework Optimization Methods {#sec:framework_optimization}

### Meta-Parameter Learning

Optimize framework parameters using performance feedback:

\[\Theta^* = \arg\max_{\Theta} \mathbb{E}_{data} [\log p(data|\Theta) - \lambda \cdot complexity(\Theta)]\]

Where \(\Theta\) includes framework parameters:
- Confidence thresholds \(\theta_c\)
- Adaptation rates \(\alpha\)
- Strategy selection parameters \(\beta\)
- Meta-data weighting functions \(w_k\)

### Hierarchical Optimization

Multi-level optimization for complex systems:

1. **Level 1:** Optimize EFE for immediate action selection
2. **Level 2:** Optimize meta-cognitive parameters for attention allocation
3. **Level 3:** Optimize framework parameters for long-term adaptation

### Gradient-Based Meta-Learning

Use gradient information for framework adaptation:

\[\frac{d\Theta}{dt} = -\eta \cdot \nabla_{\Theta} \mathcal{L}(performance, \Theta)\]

Where \(\mathcal{L}(\text{performance}, \Theta)\) measures performance degradation due to suboptimal framework parameters \(\Theta\).

## Implementation Validation {#sec:implementation_validation}

### Numerical Stability Tests

- **Gradient Bounds:** Ensure gradients remain within reasonable bounds
- **Probability Normalization:** Verify distributions stay normalized
- **Convergence Criteria:** Check optimization converges reliably
- **Edge Case Handling:** Test behavior with extreme inputs

### Theoretical Correctness Validation

- **EFE Equivalence:** Verify EFE matches mathematical definition
- **Free Energy Minimization:** Confirm free energy decreases over time
- **Bayesian Consistency:** Ensure inference follows Bayesian principles
- **Meta-Level Consistency:** Validate meta-cognitive operations

### Performance Benchmarks

- **Scalability:** Test with increasing state/observation spaces
- **Computational Efficiency:** Measure time complexity
- **Memory Usage:** Monitor memory consumption
- **Accuracy:** Validate against known analytical solutions

## Algorithm Complexity Analysis {#sec:complexity_analysis}

### Time Complexity

- **EFE Calculation:** \(O(n_{\text{states}} \times n_{\text{actions}} \times \text{horizon})\)
- **Inference:** \(O(n_{\text{states}} \times n_{\text{observations}})\)
- **Meta-Cognitive Assessment:** \(O(n_{\text{beliefs}})\)
- **Framework Optimization:** \(O(\text{iterations} \times n_{\text{parameters}})\)

### Space Complexity

- **Generative Model:** \(O(n_{\text{states}} \times n_{\text{observations}} + n_{\text{states}}^2 \times n_{\text{actions}})\)
- **Belief States:** \(O(n_{\text{states}})\)
- **Meta-Cognitive History:** \(O(\text{history\_length} \times n_{\text{beliefs}})\)
- **Optimization State:** \(O(n_{\text{parameters}})\)

### Optimizations

- **Sparse Representations:** Use sparse matrices for large state spaces
- **Approximate Inference:** Implement variational approximations
- **Hierarchical Models:** Reduce complexity through hierarchical structure
- **Parallel Computation:** Distribute computation across processing units

This supplemental methods section provides the technical foundation for implementing and validating the Active Inference meta-pragmatic framework across all four quadrants of the \(2 \times 2\) matrix.