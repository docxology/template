# Background and Theoretical Foundations {#sec:background}

Active Inference represents a paradigm shift in our understanding of cognition, perception, and action. Originating from the Free Energy Principle [@friston2010free], Active Inference provides a unified mathematical formalism for understanding biological agents as systems that minimize variational free energy through perception and action. This section establishes the theoretical foundations that enable Active Inference to operate as a meta-theoretical methodology—specifying the frameworks within which cognition occurs.

## The Free Energy Principle {#sec:fep_foundation}

The Free Energy Principle (FEP) defines a "thing" as a system that maintains its structure over time through free energy minimization. This principle applies across multiple scales of organization:

**Physical Level:** Boundary maintenance through Markov blankets—systems maintain physical structure by minimizing thermodynamic free energy, creating boundaries that separate internal from external states.

**Cognitive Level:** Belief updating through Expected Free Energy (EFE) minimization—cognitive agents maintain accurate world models by minimizing expected free energy, updating beliefs through Bayesian inference while selecting actions that reduce uncertainty.

**Meta-Cognitive Level:** Framework adaptation through higher-order reasoning—meta-cognitive systems maintain adaptive cognitive architectures by optimizing framework parameters, evolving their own processing structures based on performance analysis.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/fep_system_boundaries.png}
\caption{Free Energy Principle system boundaries showing Markov blanket separating internal and external states. The Markov blanket defines the boundary between a system (internal states) and its environment (external states) through sensory and active states. Systems maintain their structure by minimizing variational free energy $\mathcal{F}[q]$, which bounds surprise.}
\label{fig:fep_system_boundaries}
\end{figure}

### Variational Free Energy

The Variational Free Energy bounds the surprise:
```{=latex}
\begin{equation}
\mathcal{F}[q] = \mathbb{E}_{q(s)}[\log q(s) - \log p(s,o)]
\label{eq:variational_free_energy}
\end{equation}
```

Systems self-organize by minimizing free energy:
```{=latex}
\begin{equation}
\dot{\phi} = -\frac{\partial \mathcal{F}}{\partial \phi}
\label{eq:self_organization}
\end{equation}
```

Where $\phi$ represents system parameters that can be controlled.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/free_energy_dynamics.png}
\caption{Free energy minimization dynamics showing convergence over time and epistemic/pragmatic components. The trajectory shows how variational free energy $\mathcal{F}[q]$ decreases over time as the system updates its beliefs and actions.}
\label{fig:free_energy_dynamics}
\end{figure}

## Expected Free Energy Formulation {#sec:efe_formulation}

The Expected Free Energy (EFE) combines epistemic and pragmatic components in a unified formalism:

```{=latex}
\begin{equation}
\mathcal{F}(\pi) = \mathbb{E}_{q(s_\tau)}[\log q(s_\tau) - \log p(s_\tau \mid \pi)] + \mathbb{E}_{q(o_\tau)}[\log p(o_\tau \mid s_\tau) + \log p(s_\tau) - \log q(s_\tau)]
\label{eq:efe}
\end{equation}
```

### Epistemic-Pragmatic Decomposition

The EFE decomposes into two fundamental terms:

**Epistemic Value (Information Gain):**
```{=latex}
\begin{equation}
H[Q(\pi)] = \mathbb{E}_{q(s_\tau)}[\log q(s_\tau) - \log p(s_\tau \mid \pi)]
\label{eq:epistemic_component}
\end{equation}
```

This term (Equation \eqref{eq:epistemic_component}) is minimized when executing policy $\pi$ reduces uncertainty about hidden states.

**Pragmatic Value (Goal Achievement):**
```{=latex}
\begin{equation}
G(\pi) = \mathbb{E}_{q(o_\tau)}[\log p(o_\tau \mid s_\tau) + \log p(s_\tau) - \log q(s_\tau)]
\label{eq:pragmatic_component}
\end{equation}
```

This term (Equation \eqref{eq:pragmatic_component}) measures goal achievement through preferred observations.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/efe_decomposition.png}
\caption{Expected Free Energy (EFE) decomposition into epistemic and pragmatic components (Equation \eqref{eq:efe}). The EFE $\mathcal{F}(\pi)$ combines epistemic affordance $H[Q(\pi)]$ (information gain) and pragmatic value $G(\pi)$ (goal achievement), enabling systematic analysis of how agents balance exploration and exploitation.}
\label{fig:efe_decomposition}
\end{figure}

### Perception-Action Loop

Active Inference implements a continuous cycle where agents update beliefs and select actions to minimize expected free energy:

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/perception_action_loop.png}
\caption{Active Inference perception-action loop showing how perception drives action through EFE minimization (Equation \eqref{eq:efe}). The cycle consists of: (1) Observation of sensory data; (2) Bayesian inference updating posterior beliefs $q(s)$ about hidden states; (3) Policy evaluation computing EFE $\mathcal{F}(\pi)$ for candidate actions; (4) Action selection minimizing EFE; (5) Action execution generating new observations.}
\label{fig:perception_action_loop}
\end{figure}

## Generative Model Specification {#sec:generative_model}

Active Inference agents operate through generative models defined by four core matrices. The specification of these matrices transforms framework design from an external constraint into an internal research question.

### Matrix A: Observation Likelihoods

Defines how hidden states generate observations:
```{=latex}
\begin{equation}
A = [a_{ij}] \quad a_{ij} = P(o_i \mid s_j)
\label{eq:matrix_a}
\end{equation}
```

**Properties:**
- Each column sums to 1 (valid probability distribution)
- Rows represent observation modalities
- Columns represent hidden state conditions
- Diagonal dominance indicates reliable observations

### Matrix B: State Transitions

Defines how actions influence state changes:
```{=latex}
\begin{equation}
B = [b_{ijk}] \quad b_{ijk} = P(s_j \mid s_i, a_k)
\label{eq:matrix_b}
\end{equation}
```

**Structure:** 3D tensor with dimensions $\text{states} \times \text{states} \times \text{actions}$, where each action defines a transition matrix.

### Matrix C: Preferences

Defines desired outcomes (the pragmatic landscape):
```{=latex}
\begin{equation}
C = [c_i] \quad c_i = \log P(o_i)
\label{eq:matrix_c}
\end{equation}
```

**Interpretation:**
- Positive values: preferred observations
- Negative values: avoided observations
- Magnitude indicates strength of preference

### Matrix D: Prior Beliefs

Defines initial state beliefs:
```{=latex}
\begin{equation}
D = [d_i] \quad d_i = P(s_i)
\label{eq:matrix_d}
\end{equation}
```

**Role:** Represents initial beliefs before observation, encoding innate biases or learned priors.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/generative_model_structure.png}
\caption{Structure of generative models in Active Inference showing $A$, $B$, $C$, $D$ matrices and their relationships. Matrix $A$ (Equation \eqref{eq:matrix_a}) defines observation likelihoods. Matrix $B$ (Equation \eqref{eq:matrix_b}) defines state transitions. Matrix $C$ (Equation \eqref{eq:matrix_c}) defines preferences. Matrix $D$ (Equation \eqref{eq:matrix_d}) defines prior beliefs.}
\label{fig:generative_model_structure}
\end{figure}

## Meta-Epistemic and Meta-Pragmatic Aspects {#sec:meta_aspects}

Active Inference operates at a fundamentally meta-level that distinguishes it from traditional decision-making algorithms. Rather than simply providing another method for selecting actions given fixed observation models and reward functions, Active Inference allows researchers to specify the very frameworks within which cognition occurs.

### Meta-Epistemic Dimension

Active Inference allows modelers to specify epistemic frameworks through matrices $A$, $B$, and $D$:

- **Matrix $A$:** Defines what can be known about the world and how reliably observations indicate underlying states
- **Matrix $D$:** Sets initial assumptions about the world's structure
- **Matrix $B$:** Specifies causal relationships and how actions influence state changes

Through these specifications, researchers define not just current beliefs, but the epistemological boundaries of cognition itself—determining what knowledge is possible, how evidence accumulates, and what causal structures are assumed.

### Meta-Pragmatic Dimension

Beyond epistemic specification, Active Inference supports meta-pragmatic modeling through matrix $C$, which defines preference priors. Unlike traditional reinforcement learning where rewards are externally specified, Active Inference allows modelers to specify pragmatic landscapes—what constitutes "value" for the agent—creating opportunities to explore how different value systems shape cognition and behavior.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/meta_level_concepts.png}
\caption{Meta-pragmatic and meta-epistemic aspects showing modeler specification power. The meta-epistemic dimension enables specification of knowledge acquisition frameworks through matrices $A$, $B$, and $D$. The meta-pragmatic dimension enables specification of value landscapes through matrix $C$. This dual specification power makes Active Inference a meta-methodology for cognitive science.}
\label{fig:meta_level_concepts}
\end{figure}

### The Modeler as Architect and Subject

The structure reveals the dual role of the Active Inference modeler:

**As Architect:**
- Specifies epistemic frameworks ($A$, $B$, $D$ matrices)
- Defines pragmatic landscapes ($C$ matrix)
- Designs cognitive architectures
- Establishes boundary conditions for cognition

**As Subject:**
- Uses Active Inference to understand their own cognition
- Applies meta-epistemic principles to knowledge acquisition
- Employs meta-pragmatic frameworks for decision-making
- Engages in recursive self-modeling

This dual role creates a recursive relationship where the tools used to model others become tools for self-understanding.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/structure_preservation.png}
\caption{Structure preservation dynamics showing how systems maintain internal organization through free energy minimization. Despite external perturbations and environmental changes, systems maintain stable internal states through active inference. This principle explains how biological systems, cognitive agents, and even social structures maintain their identity over time.}
\label{fig:structure_preservation}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/physics_cognition_bridge.png}
\caption{Free Energy Principle as the bridge between physics and cognition domains. The same mathematical principle—variational free energy minimization—applies across multiple scales: physical systems, biological systems, cognitive systems, and meta-cognitive systems. This unification enables understanding of intelligence as a natural extension of physical principles.}
\label{fig:physics_cognition_bridge}
\end{figure}

