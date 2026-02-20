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

## Security Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| $A_{corrupted}$ | Adversarially modified observation likelihood | $\mathbb{R}^{m \times n}$ |
| $C_{corrupted}$ | Adversarially modified preference prior | $\mathbb{R}^m$ |
| $\epsilon$ | Framework integrity tolerance threshold | $\mathbb{R}^+$ |
| $\gamma$ | Confidence detection threshold | $[0,1]$ |
| $\delta_{attack}$ | Attack magnitude (perturbation norm) | $\mathbb{R}^+$ |
| $\rho$ | Attack detection rate | $[0,1]$ |
| $\mathcal{T}$ | Threat severity score | $[0,1]$ |
| $\Theta_{baseline}$ | Baseline framework parameters for integrity checking | $\mathbb{R}^d$ |
| $validation(c)$ | Confidence calibration error | $\mathbb{R}^+$ |
| $integrity(\Theta)$ | Framework integrity metric | $\{0,1\}$ |

## Quadrant-Specific Parameters

| Symbol | Description | Domain |
|--------|-------------|---------|
| $\mathcal{F}_{Q1}(\pi)$ | Q1 baseline EFE: $G(\pi) + H[Q(\pi)]$ | $\mathbb{R}$ |
| $\mathcal{F}_{Q2}(\pi)$ | Q2 meta-data-weighted EFE: $w_e H[Q(\pi)] + w_p G(\pi) + w_m M(\pi)$ | $\mathbb{R}$ |
| $M(\pi)$ | Meta-data derived utility for Q2 | $\mathbb{R}$ |
| $\mathcal{F}_{primary}(\pi)$ | Q3 primary-level EFE component | $\mathbb{R}$ |
| $\mathcal{F}_{meta}(\pi)$ | Q3 meta-cognitive EFE component | $\mathbb{R}$ |
| $\lambda(c)$ | Q3 confidence-dependent meta-cognitive influence | $\mathbb{R}^+$ |
| $\mathcal{R}(\pi)$ | Q3 strategy complexity penalty | $\mathbb{R}^+$ |
| $\mathcal{R}(\Theta)$ | Q4 framework coherence regularization | $\mathbb{R}^+$ |
| $\theta_c$ | Q4 confidence threshold parameter | $[0,1]$ |
| $U(c, e, \kappa \mid \Theta)$ | Q4 utility over confidence, effectiveness, coherence | $\mathbb{R}$ |
| $\kappa$ | Q4 framework coherence measure | $[0,1]$ |

## Information-Theoretic Notation

| Symbol | Description | Domain |
|--------|-------------|---------|
| $H[\cdot]$ | Shannon entropy | $\mathbb{R}^+$ |
| $I(X;Y)$ | Mutual information between $X$ and $Y$ | $\mathbb{R}^+$ |
| $D_{KL}[q\|p]$ | KL divergence from $p$ to $q$ | $\mathbb{R}^+$ |
| $\mathcal{S}$ | Surprisal ($-\log p(o)$) | $\mathbb{R}$ |

## Implementation Variables

| Symbol | Description | Domain |
|--------|-------------|---------|
| $t$ | Time step | $\mathbb{N}$ |
| $\tau$ | Temporal horizon | $\mathbb{N}$ |
| $\eta$ | Learning rate | $\mathbb{R}^+$ |
| $\alpha$ | Adaptation rate | $\mathbb{R}^+$ |
| $\beta$ | Feedback strength | $\mathbb{R}^+$ |
| $Z$ | Normalization constant (partition function) | $\mathbb{R}^+$ |
| $r(t)$ | Reliability metric at time $t$ | $[0,1]$ |
| $c(t)$ | Confidence score at time $t$ | $[0,1]$ |
| $w_e, w_p, w_m$ | Epistemic, pragmatic, meta-data weights | $\mathbb{R}^+$ |

## Glossary of Key Terms

| Term | Definition |
|------|-----------|
| Active Inference | A framework where agents minimize expected free energy through coordinated perception and action |
| Expected Free Energy (EFE) | A functional combining epistemic (information gain) and pragmatic (goal achievement) value |
| Free Energy Principle (FEP) | The principle that self-organizing systems minimize variational free energy |
| Generative Model | A probabilistic model specifying how hidden states generate observations |
| Markov Blanket | The boundary separating internal from external states via sensory and active states |
| Meta-Cognition | Cognition about cognition; monitoring and control of cognitive processes |
| Cognitive Security | The protection of cognitive processes from adversarial manipulation at any quadrant level |
| Confidence Calibration | The degree to which subjective confidence matches objective accuracy |
| Epistemic Value | The information-gaining component of EFE that drives uncertainty reduction |
| Framework Flexibility | The capacity to modify cognitive structures; proposed as a formal characterization of intelligence |
| Framework Specification | The act of defining generative model parameters ($A$, $B$, $C$, $D$), viewed as a meta-level research variable |
| Meta-Epistemic | Pertaining to the specification of what can be known; operating on the epistemic framework itself via matrices $A$, $B$, $D$ |
| Meta-Pragmatic | Pertaining to the specification of what matters or has value; operating on the pragmatic landscape via matrix $C$ |
| Pragmatic Value | The goal-achieving component of EFE that drives preferred outcome attainment |
| Preference Prior | The $C$ matrix encoding desired observations in a generative model |
| Quadrant Framework | The $2 \times 2$ structure organizing processing along Data/Meta-Data and Cognitive/Meta-Cognitive axes |
| Recursive Self-Modeling | The process by which an agent models its own cognitive processes using the same formalism |
| Value Alignment | The problem of ensuring AI systems pursue objectives aligned with human values; addressed through $C$ matrix specification |
| Variational Inference | Approximating intractable posterior distributions by optimization over a family of tractable distributions |