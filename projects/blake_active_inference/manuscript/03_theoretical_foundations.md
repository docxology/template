# Theoretical Foundations {#theory}

*The mathematics of self.* This section reviews the formal apparatus of the Free Energy Principle and Active Inference. We present the core formalisms—variational free energy, Markov blankets, hierarchical generative models, precision weighting, prediction error, expected free energy, and multi-agent extensions—that the subsequent synthesis will bring into structural alignment with Blake's prophetic phenomenology.

## The Free Energy Principle {#fep}

Self-organizing systems persist by minimizing surprise (realism), or at least can be viewed as if they do (instrumentalism). Friston's Free Energy Principle (FEP) formalizes this imperative [@friston2010free; @friston2006free], now comprehensively synthesized in Parr, Pezzulo, and Friston's canonical textbook [@parr2022active].

**Variational free energy** provides a tractable upper bound on surprise (negative log model evidence):

\begin{equation}\label{eq:free_energy}
F = \mathbb{E}_q[\ln q(\theta) - \ln p(o, \theta)]
\end{equation}

where $o$ denotes observations, $\theta$ denotes hidden states (causes), $q(\theta)$ is a variational density encoding the agent's beliefs, and $p(o, \theta)$ is the generative model specifying how hidden states produce observations.

**Decomposition** reveals the relationship between free energy, divergence, and surprise:

\begin{equation}\label{eq:fe_decomposition}
F = D_{KL}[q(\theta) \| p(\theta | o)] - \ln p(o)
\end{equation}

Since KL-divergence is non-negative, free energy upper-bounds surprise:

\begin{equation}\label{eq:surprise_bound}
F \geq -\ln p(o)
\end{equation}

This bound is tight when $q(\theta) = p(\theta | o)$, i.e., when the agent's beliefs equal the true posterior. Minimizing $F$ thus serves two functions simultaneously: it makes beliefs more accurate (reducing the divergence term) and implicitly minimizes surprise (the model evidence term).

### Minimization Pathways

Two complementary pathways reduce free energy (Equation \ref{eq:free_energy}):

1. **Perceptual inference** — Update beliefs $q(\theta)$ toward the true posterior $p(\theta | o)$. This is changing mind to fit world.
2. **Active inference** — Select actions $a$ that sample observations $o$ consistent with predictions. This is changing world to fit mind.

Both pathways reduce the same objective. The agent that updates its beliefs *and* acts on the world is performing complete free energy minimization.

### Expected Free Energy and Policy Selection

Agents must also select among possible courses of action (policies $\pi$). The **expected free energy** $G(\pi)$ evaluates policies by their anticipated consequences:

\begin{equation}\label{eq:expected_free_energy}
G(\pi) = -\mathbb{E}_{\tilde{q}}[\ln p(o_\tau | C)] + \mathbb{E}_{\tilde{q}}[D_{KL}[q(\theta_\tau | o_\tau, \pi) \| q(\theta_\tau | \pi)]]
\end{equation}

where $C$ encodes preferred observations (prior preferences), and $\tilde{q}$ denotes the predictive density under the policy. The first term drives the agent toward outcomes it prefers; the second drives it to resolve uncertainty about hidden states. Optimal policies minimize $G(\pi)$, balancing exploitation (pragmatic value) against exploration (epistemic value) [@dacosta2020active; @parr2022active].

This decomposition is central to the synthesis that follows: it formally separates the *habitual* from the *curious*, the routine from the exploratory—categories that recur throughout the humanistic tradition under different names.

## The Markov Blanket {#blanket}

The Markov blanket defines the statistical boundary of any autonomous system, partitioning states into internal, external, and blanket (interface) components [@friston2019markov; @kirchhoff2018markov].

**Conditional independence:**

\begin{equation}\label{eq:conditional_independence}
p(\mu | \eta, B) = p(\mu | B)
\end{equation}

Internal states $\mu$ are conditionally independent of external states $\eta$ given blanket states $B$. The blanket comprises two complementary channels:

| Component | Symbol | Flow Direction | Role |
| :---------- | :------- | :--------------- | :----- |
| Sensory states | $s$ | World $\to$ Self | Carry observations |
| Active states | $a$ | Self $\to$ World | Carry interventions |
| **Blanket** | $B = \{s, a\}$ | Bidirectional | The statistical interface |

Every self-organizing system—from cell to organism to social group—possesses a Markov blanket. The blanket is constitutive: without it, there is no distinction between system and environment, hence no inference. The topology of this partition—what is inside, what is outside, what mediates—determines the scope and character of an agent's engagement with its world.

### Nested Blankets and Multi-Scale Organization

Markov blankets nest recursively: cells within organs, organs within organisms, organisms within social groups. Each scale defines its own internal/external partition and performs its own inference [@kirchhoff2018markov; @ramstead2018answering]. This nesting is not merely a descriptive convenience but a formal property of hierarchical self-organization.

## Hierarchical Generative Models {#hierarchy}

Generative models are typically layered, with each level predicting the activity of the level below [@clark2016surfing; @hohwy2013predictive].

**Hierarchical factorization:**

\begin{equation}\label{eq:hierarchical_model}
p(o, \theta) = p(o | \theta_1) \prod_{i=1}^{n-1} p(\theta_i | \theta_{i+1}) \cdot p(\theta_n)
\end{equation}

At the lowest level, $\theta_1$ generates observations through the likelihood $p(o | \theta_1)$. Each higher level $\theta_{i+1}$ provides the prior context for the level below. The deepest level $\theta_n$ encodes the most abstract, slowly varying regularities of the environment.

This architecture has several key properties:

- **Abstraction increases with depth.** Low levels encode fast sensory features; high levels encode slow contextual structure.
- **Temporal scale separation.** Higher levels change more slowly, providing a stable context for faster dynamics below [@kiebel2008hierarchy; @friston2017deep].
- **Bidirectional message passing.** Top-down predictions and bottom-up prediction errors flow through the hierarchy, settling jointly to minimize free energy.

The depth of the hierarchy determines the scope of patterns the model can represent—from local texture to global meaning.

### Model Evidence and Complexity

The marginal likelihood (model evidence) quantifies how well a generative model accounts for observations:

\begin{equation}\label{eq:model_evidence}
\ln p(o) = \mathbb{E}_{q}[\ln p(o | \theta)] - D_{KL}[q(\theta) \| p(\theta)]
\end{equation}

Good models maximize accuracy while minimizing complexity—a formal instantiation of Occam's razor. Overly simple models are inaccurate; overly complex models overfit. The free energy bound (Equation \ref{eq:surprise_bound}) ensures that minimizing $F$ implicitly maximizes model evidence, favoring parsimonious yet accurate explanations.

**Model comparison:**

\begin{equation}\label{eq:model_complexity}
F_{\text{simple}} \gg F_{\text{rich}}
\end{equation}

A model of insufficient depth incurs high free energy because it cannot account for the hierarchical structure of observations. A richer model, one with appropriate depth and structure, achieves lower free energy by capturing regularities that the shallow model misses (though a larger model may have other tradeoffs or penalization terms applied, balancing the tendency to inflate the number of parameters).

## Precision {#precision}

Precision is the inverse variance of a probability distribution—a measure of confidence or reliability:

\begin{equation}\label{eq:precision}
\pi = \sigma^{-1}
\end{equation}

In hierarchical inference, precision weights determine how strongly each level of the hierarchy influences the overall posterior. Two sources of precision compete at every level:

- **Prior precision** ($\pi_{\text{prior}}$): confidence in top-down predictions
- **Sensory precision** ($\pi_{\text{sensory}}$): confidence in bottom-up evidence

Their balance determines the character of inference:

| Regime | Condition | Perceptual Effect |
| :------- | :---------- | :------------------ |
| Prior-dominated | $\pi_{\text{prior}} \gg \pi_{\text{sensory}}$ | Expectations override evidence; hallucination-like states |
| Sensory-dominated | $\pi_{\text{sensory}} \gg \pi_{\text{prior}}$ | Sensory flooding; loss of contextual interpretation |
| Balanced | $\pi_{\text{prior}} \approx \pi_{\text{sensory}}$ | Optimal inference; accurate and contextually rich perception |

Attention, in this framework, is the optimization of precision—the process by which the brain infers the reliability of its own prediction errors and weights them accordingly [@feldman2010attention; @parr2019attention].

### Precision Dynamics and Pathology

When prior precision becomes extreme:

**Prior dominance:**

\begin{equation}\label{eq:prior_dominance}
\pi_{\text{prior}} \gg \pi_{\text{sensory}}
\end{equation}

the agent's beliefs become insensitive to new evidence. The generative model ceases to update, and perception rigidifies. Conversely, when sensory precision vastly exceeds prior precision, the agent is overwhelmed by unstructured input, unable to extract meaning. Pathological states—from delusions to anxiety disorders—can be understood as failures of precision optimization [@adams2013computational].

## Prediction Error and Message Passing {#error}

At each level of the hierarchy, the brain computes prediction error—the discrepancy between what was expected and what was observed:

\begin{equation}\label{eq:prediction_error}
\varepsilon_i = o_i - g_i(\theta_{i+1})
\end{equation}

where $g_i(\cdot)$ is the generative function mapping higher-level states to predicted observations at level $i$. Errors ascend the hierarchy; predictions descend. The system settles when $\varepsilon \rightarrow 0$ across all levels—when predictions match observations at every scale.

Each error signal (Equation \ref{eq:prediction_error}) propagates through the hierarchy defined in Equation \ref{eq:hierarchical_model}, weighted by the precision (Equation \ref{eq:precision}) assigned to that level. High-precision errors demand model revision; low-precision errors are discounted. This **precision-weighted prediction error** is the fundamental currency of hierarchical inference.

The bidirectional cascade of predictions and errors constitutes perception itself: a continuous, iterative process of generating hypotheses, testing them against evidence, and revising. Action enters when the system changes the world to reduce prediction error rather than changing beliefs.

## Temporal Depth {#temporal-depth}

Generative models can extend across time, encoding dependencies between successive observations:

**Temporal hierarchy:**

\begin{equation}\label{eq:temporal_hierarchy}
p(o_{1:T}, \theta) = \prod_{t=1}^{T} p(o_t | \theta_t) \cdot p(\theta_t | \theta_{t-1})
\end{equation}

Higher levels of the hierarchy encode slower dynamics, providing a context for the faster fluctuations below. The lowest levels track moment-to-moment sensory input; intermediate levels integrate over seconds to minutes; the deepest levels encode regularities persisting across hours, years, or longer [@kiebel2008hierarchy; @friston2017deep].

The **temporal depth** of a model determines how far into the past and future its predictions extend. A shallow model is reactive, bound to immediate stimulus; a deep model integrates broad temporal context into present inference. Extending temporal depth imposes computational cost but enables the agent to detect and exploit regularities that span long durations.

## Multi-Agent Inference {#multi-agent}

Active Inference extends naturally to systems of coupled agents, each bounded by its own Markov blanket but sharing statistical structure:

**Multi-agent coordination:**

\begin{equation}\label{eq:multi_agent}
p(o, \theta) = \prod_{i=1}^{N} p(o_i | \theta_i) \cdot p(\theta_i | \theta_{\text{shared}}) \cdot p(\theta_{\text{shared}})
\end{equation}

Multiple agents share a common prior $\theta_{\text{shared}}$—the cultural, institutional, or ecological generative model that aligns their individual inferences. Communication between agents can be formalized as generalized synchronization, where coupled systems entrain their internal dynamics to infer each other's hidden states [@friston2015duet; @veissiere2020thinking].

### Mean-Field Factorization

When the joint posterior over all hidden states is intractable, variational inference approximates it by assuming independence between factors:

**Mean-field approximation:**

\begin{equation}\label{eq:mean_field}
q(\theta) \approx \prod_{k=1}^{K} q(\theta_k)
\end{equation}

This factorization makes computation tractable but introduces coordination costs: correlations between components are lost. The quality of inference depends on how well the factorization structure matches the true dependencies in the generative model. Structured variational families that preserve key correlations improve upon the fully factorized approximation.

This formalized understanding of collective intelligence provides the necessary bridge to the aesthetic domain. If culture is a shared generative model, then art is the engineering of that model—a "cognitive" intervention that reshapes the priors of the collective.

## Cognitive Art and the Fourfold

The integration of Active Inference with broad-scale historical and aesthetic systems suggests a "cognitive art"---a practice of mind that is both rigorous and generative. Friedman's recent work on "Cognitive Art & Science" [@friedman2025cognitive] proposes a fourfold schema for intelligence that maps directly onto the Blakean/Fristonian synthesis. This framework distinguishes between the "Low Road" ($2 \rightarrow 3$) of explanatory modeling---fitting data to priors---and the "High Road" ($4 \rightarrow 3$) of anticipatory wisdom---shaping the niche to afford new forms of life. Blake's rejection of "Single Vision" (pure 2nd-ness) in favor of "Fourfold Vision" (integrated 1st, 2nd, 3rd, and 4th-ness) prefigures the move from mere error minimization to the active construction of a "wise" sensorimotor niche.

## Summary of Formal Apparatus

The following table collects the core equations and their roles in the synthesis that follows:

| Equation | Name | Role in Synthesis (§4) |
| :------ | :------- | :----------------------- |
| \ref{eq:free_energy} | Variational Free Energy | Objective function for perception and action |
| \ref{eq:fe_decomposition} | FEP Decomposition | Relation of divergence and surprise |
| \ref{eq:surprise_bound} | Surprise Bound | Evidence lower bound (ELBO) logic |
| \ref{eq:expected_free_energy} | Expected Free Energy | Policy selection (exploration/exploitation) |
| \ref{eq:conditional_independence} | Conditional Independence | Markov blanket as statistical boundary |
| \ref{eq:hierarchical_model} | Hierarchical Factorization | Depth of generative model |
| \ref{eq:model_evidence} | Model Evidence | Accuracy–Complexity trade-off |
| \ref{eq:model_complexity} | Model Comparison | Necessity of hierarchical depth |
| \ref{eq:precision} | Precision | Confidence weighting |
| \ref{eq:prior_dominance} | Prior Dominance | Pathological rigidity |
| \ref{eq:prediction_error} | Prediction Error | Bidirectional message passing |
| \ref{eq:temporal_hierarchy} | Temporal Hierarchy | Depth of temporal prediction |
| \ref{eq:multi_agent} | Multi-Agent Coordination | Shared priors and collective inference |
| \ref{eq:mean_field} | Mean-Field Approximation | Factorized variational inference |

Each of these formalisms will be brought into structural alignment with a specific aspect of Blake's prophetic phenomenology in the sections that follow.
