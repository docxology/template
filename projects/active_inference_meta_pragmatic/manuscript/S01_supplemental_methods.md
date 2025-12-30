# Supplemental Methods {#sec:supplemental_methods}

This supplemental section provides extended methodological details, including complete generative model specifications, mathematical derivations, and implementation algorithms.

## Complete Generative Model Specifications {#sec:complete_generative_models}

### Matrix A: Observation Likelihoods

The observation likelihood matrix defines the probabilistic mapping from hidden states to observations:

\[A = \begin{pmatrix}
P(o_1|s_1) & P(o_1|s_2) & \cdots & P(o_1|s_n) \\
P(o_2|s_1) & P(o_2|s_2) & \cdots & P(o_2|s_n) \\
\vdots & \vdots & \ddots & \vdots \\
P(o_m|s_1) & P(o_m|s_2) & \cdots & P(o_m|s_n)
\end{pmatrix}\]

**Normalization:** Each column sums to 1, representing a valid probability distribution over observations for each state.

**Interpretation:**
- Rows correspond to observation modalities
- Columns correspond to hidden state conditions
- Entry A[i,j] represents the probability of observing o_i given state s_j

### Matrix B: State Transition Dynamics

The transition matrix defines how actions influence state changes:

\[B(a) = \begin{pmatrix}
P(s_1'|s_1,a) & P(s_2'|s_1,a) & \cdots & P(s_n'|s_1,a) \\
P(s_1'|s_2,a) & P(s_2'|s_2,a) & \cdots & P(s_n'|s_2,a) \\
\vdots & \vdots & \ddots & \vdots \\
P(s_1'|s_n,a) & P(s_2'|s_n,a) & \cdots & P(s_n'|s_n,a) \\
\end{pmatrix}\]

**Structure:** 3D tensor with dimensions [n_states, n_states, n_actions]

**Properties:**
- Each B[:,:,a] is a stochastic matrix (rows sum to 1)
- Enables modeling of controllable state transitions
- Different actions can implement different transition dynamics

### Matrix C: Preference Landscape

The preference matrix defines the desirability of different observations:

\[C = \begin{pmatrix} c_1 \\ c_2 \\ \vdots \\ c_m \end{pmatrix}\]

**Interpretation:**
- Positive values indicate preferred observations
- Negative values indicate avoided observations
- Magnitude indicates strength of preference/aversion
- Used in softmax normalization: P(o) ∝ exp(C)

### Matrix D: Prior State Distribution

The prior beliefs over hidden states:

\[D = \begin{pmatrix} d_1 \\ d_2 \\ \vdots \\ d_n \end{pmatrix}\]

**Properties:**
- Sums to 1 (valid probability distribution)
- Represents initial beliefs before observation
- Can encode innate biases or learned priors

## Extended EFE Derivation {#sec:extended_efe_derivation}

### Complete EFE Formulation

The Expected Free Energy combines epistemic and pragmatic components:

\[\mathcal{F}(\pi) = \overbrace{\mathbb{E}_{q(s_\tau|\pi)}[\log q(s_\tau|\pi) - \log p(s_\tau|\pi)]}^{\text{Epistemic Affordance}} + \overbrace{\mathbb{E}_{q(o_\tau,s_\tau|\pi)}[\log p(o_\tau,s_\tau) - \log q(s_\tau,o_\tau|\pi)]}^{\text{Pragmatic Value}}\]

### Epistemic Component Expansion

The epistemic affordance measures information gain:

\[H[Q(\pi)] = \mathbb{E}_{q(s_\tau|\pi)}[\log q(s_\tau|\pi)] - \mathbb{E}_{q(s_\tau|\pi)}[\log p(s_\tau|\pi)]\]

This can be rewritten using KL divergence:

\[H[Q(\pi)] = KL[q(s_\tau|\pi)||p(s_\tau|\pi)]\]

### Pragmatic Component Expansion

The pragmatic value measures goal achievement:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau|\pi)}[\log p(o_\tau,s_\tau) - \log q(s_\tau,o_\tau|\pi)]\]

Using the generative model decomposition:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau|\pi)}[\log p(o_\tau|s_\tau) + \log p(s_\tau) - \log q(s_\tau|\pi) - \log p(o_\tau|\pi)]\]

The pragmatic value becomes:

\[G(\pi) = \mathbb{E}_{q(o_\tau,s_\tau|\pi)}[\log \tilde{A}(o_\tau,s_\tau) + \log p(s_\tau) - \log q(s_\tau|\pi)]\]

Where \(\tilde{A}\) includes the preference weighting.

## Meta-Data Integration Methods {#sec:meta_data_integration}

### Confidence-Weighted Inference

Incorporate observation confidence into belief updating:

\[q(s|o,c) \propto q(s) \cdot A(o|s) \cdot w(c)\]

Where w(c) is a confidence-dependent weighting function:

\[w(c) = \begin{cases}
c & \text{if } c > \theta \\
\frac{\theta}{2} & \text{if } c \leq \theta
\end{cases}\]

### Temporal Meta-Data Processing

Incorporate temporal consistency information:

\[q(s_t|o_{1:t}, m_t) \propto q(s_t|o_t) \cdot \phi(m_t|s_{t-1})\]

Where ϕ represents temporal meta-data likelihood.

### Multi-Source Meta-Data Fusion

Combine multiple meta-data sources:

\[w_{combined} = \prod_{k=1}^K w_k(m_k)\]

Where each w_k represents a different meta-data weighting function.

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

Where Θ includes:
- Confidence thresholds
- Adaptation rates
- Strategy selection parameters
- Meta-data weighting functions

### Hierarchical Optimization

Multi-level optimization for complex systems:

1. **Level 1:** Optimize EFE for immediate action selection
2. **Level 2:** Optimize meta-cognitive parameters for attention allocation
3. **Level 3:** Optimize framework parameters for long-term adaptation

### Gradient-Based Meta-Learning

Use gradient information for framework adaptation:

\[\frac{d\Theta}{dt} = -\eta \cdot \nabla_{\Theta} \mathcal{L}(performance, \Theta)\]

Where \(\mathcal{L}\) measures performance degradation due to suboptimal framework parameters.

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

- **EFE Calculation:** O(n_states × n_actions × horizon)
- **Inference:** O(n_states × n_observations)
- **Meta-Cognitive Assessment:** O(n_beliefs)
- **Framework Optimization:** O(iterations × parameters)

### Space Complexity

- **Generative Model:** O(n_states × n_observations + n_states² × n_actions)
- **Belief States:** O(n_states)
- **Meta-Cognitive History:** O(history_length × n_beliefs)
- **Optimization State:** O(n_parameters)

### Optimizations

- **Sparse Representations:** Use sparse matrices for large state spaces
- **Approximate Inference:** Implement variational approximations
- **Hierarchical Models:** Reduce complexity through hierarchical structure
- **Parallel Computation:** Distribute computation across processing units

This supplemental methods section provides the technical foundation for implementing and validating the Active Inference meta-pragmatic framework across all four quadrants of the 2×2 matrix.