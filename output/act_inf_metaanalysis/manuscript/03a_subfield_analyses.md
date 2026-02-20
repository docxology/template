# Domain Analyses: Growth Trajectories and Open Problems \label{sec:subfield_analyses}

_This supplementary section provides detailed characterizations of each of the eight tracked Active Inference domains, organized under three tiers: A (Core Theory), B (Tools & Translation), and C (Application Domains)._

## Domain A: Core Theory

### A1 — Quantitative & Formal Theory ($n = 120$, 9.9\%)

The A1 domain develops the mathematical foundations underpinning the Free Energy Principle: information geometry, category-theoretic formulations of Markov blankets, path integral formulations of free energy minimization, and gauge-theoretic perspectives on self-organization. A central debate concerns the ontological status of Markov blankets—whether they correspond to real physical boundaries or are merely useful statistical constructs \citep{bruineberg2022emperor}. Recent work on Bayesian mechanics \citep{sakthivadivel2023bayesian} aims to place the FEP on firmer mathematical footing. With 120 papers, A1 captures nearly 10\% of the corpus, reflecting the improved classifier's ability to route papers with mathematical formalism (theorems, proofs, convergence, posterior distributions, Fokker–Planck equations) into this domain rather than the qualitative philosophy catch-all.

### A2 — Qualitative Philosophy & General Theory ($n = 154$, 12.7\%)

The A2 domain encompasses papers that develop, extend, or review the core Free Energy Principle and Active Inference framework without restricting attention to a specific application domain. This includes Friston's foundational work on variational free energy minimization \citep{friston2010free}, the textbook treatment by Parr, Pezzulo, and Friston \citep{parr2022active}, and numerous tutorial and review papers. The priority-based classifier mitigates over-assignment to A2 by routing papers with mathematical formalism to A1 and papers with domain-specific vocabulary to C1–C5 or B before the A2 catch-all is reached. Nevertheless, the count likely still conceals meaningful internal structure: papers addressing embodied cognition, Bayesian brain theory, and philosophical implications of the FEP are all subsumed under this heading. Key ongoing debates concern the explanatory scope of the FEP—whether it is a principle of physics, biology, or cognition—and the relationship between active inference and competing frameworks such as reinforcement learning and optimal control theory.

## Domain B: Tools & Translation Methods

### B — Algorithms, Scaling, and Software ($n = 267$, 22.1\%)

Domain B addresses the computational challenge of making active inference practical in complex, high-dimensional environments. Early implementations relied on small discrete state spaces amenable to exact message passing. Recent work has introduced deep active inference using neural networks to amortize inference \citep{fountas2020deep}, Monte Carlo tree search for planning \citep{champion2021realizing}, and hybrid architectures combining model-based planning with model-free components. The central open question is whether active inference agents can match deep reinforcement learning performance on standard benchmarks while retaining interpretability and sample efficiency. The availability of the pymdp library \citep{heins2022pymdp} has lowered implementation barriers, contributing to this domain's growth. The recent establishment of the Pymdp Fellowship program in 2025 and the release of real-time stream processing tools like RxInfer.jl v4.0.0 \citep{rxinfer2025} indicate a vibrant and maturing software ecosystem.

## Domain C: Application Domains

### C1 — Neuroscience ($n = 206$, 17.1\%)

Neuroscience represents the historical core of the Active Inference research program. The predictive processing account—in which cortical hierarchies minimize prediction errors through both perceptual inference and active sampling—remains one of the most empirically tested aspects of the framework \citep{friston2010free, clark2013whatever}. The broader neuroscience literature on Dynamic Causal Modeling and predictive coding is extensive; the relatively modest count here likely reflects the keyword classifier's inability to distinguish neuroscience-specific applications from general FEP theory. Bridging the gap between computational models and empirical neuroimaging data remains the domain's primary challenge.

### C2 — Robotics ($n = 170$, 14.1\%)

Robotics applications treat embodied agents as free energy minimizing systems that unify perception and action through proprioceptive and exteroceptive prediction errors \citep{lanillos2021active}. Applications include robotic arm control, mobile navigation, manipulation, and multi-robot coordination. Active inference offers roboticists a principled framework for integrating sensory processing, motor planning, and adaptive behavior without separate perception and control modules. Key challenges include real-time computational feasibility on embedded hardware, continuous high-dimensional action spaces, and sim-to-real transfer.

### C3 — Language Processing ($n = 57$, 4.7\%)

The C3 domain formally conceptualizes linguistic processes---speech perception, sentence comprehension, sequential dialogue, and reading---as active inference operating over deep hierarchical generative models of linguistic structure \citep{friston2020generative}. Active inference models of reading have deterministically accounted for saccadic eye-movement patterns, while models of speech perception mathematically explain how human listeners integrate topological prior expectations with continuous acoustic evidence. Recent breakthroughs tightly couple active inference to large language models, pragmatics, and multi-agent communication. Notably, recent literature has conceptualized LLMs themselves as atypical active inference agents, introducing frameworks that deploy active inference as a metacognitive governor to enable adaptive, self-evolving LLM behavior \citep{heins2024active}.

### C4 — Computational Psychiatry ($n = 34$, 2.8\%)

Computational psychiatry aggressively leverages active inference to natively model psychiatric conditions as structural aberrations in belief updating, precision weighting, or prior expectation rigidity \citep{smith2021computational}. Schizophrenia has been modeled as a critical failure of precision weighting on bottom-up prediction errors; clinical depression corresponds to excessively precise, inescapable negative priors; and autism spectrum profiles as atypical sensory precision allocation. The domain continues to expand rapidly: 2025 frameworks such as Active Intersubjective Inference (AISI) seamlessly integrate psychodynamic theory (e.g., self-identity formation via embodied interactions) with predictive processing algorithms to mathematically unify the environmental and biological factors underlying stress disorders \citep{smith2025active}. Translating these expanding computational models into scalable diagnostic markers and therapeutic real-world protocols remains an urgent, ongoing objective.

### C5 — Biology & Morphogenesis ($n = 200$, 16.6\%)

The C5 domain applies active inference and the FEP to biological systems beyond the brain: cellular behavior, morphogenesis, evolutionary dynamics, and the origins of life. Morphogenetic processes have been modeled as collective active inference, where groups of cells coordinate to minimize a shared free energy functional \citep{kuchling2020morphogenesis, levin2022technological}. Recent models (e.g., MorphoNAS) demonstrate how simple rules derived from the FEP drive "neuromorphic development," steering systems with morphological degrees of freedom to independently self-organize the complex neural computing topologies fundamental to bioengineering \citep{levin2025morphonas}. As the second-largest domain, C5 reflects growing interest in extending the FEP to encompass all living systems, though the ratio of theoretical proposals to empirical validation remains high.

## Comparative Synthesis

Taken together, the three domains reveal a field in transition from a focused neuroscience program to a broad interdisciplinary framework. The core–periphery structure is clear: Domain A provides the theoretical and mathematical substrate, Domain B pursues engineering viability through scalable algorithms and software, and Domain C tests the framework's generality across neuroscience (C1), robotics (C2), language (C3), psychiatry (C4), and biology (C5). The consistent pattern across applied domains—strong theoretical motivation paired with limited empirical validation—suggests that the field's next phase of growth will be determined less by new theory than by the accumulation of decisive experimental evidence.

In direct response to **RQ1** (How is the Active Inference field structured?), the domain taxonomy reveals an asymmetric three-tier architecture: a dominant theoretical core (A), a growing translational layer (B), and an expanding but empirically sparse application periphery (C). The keyword classifier's heavy A2 concentration likely masks genuine diversity within the theoretical core, but the architecture itself—theory → tools → applications—is robust across classification approaches.

### Domain–Hypothesis Cross-Reference

Each domain has a primary hypothesis linkage (see the detailed hypothesis evidence analysis in \hyperref[sec:hypothesis_results]{Section 4b}):

| Domain | Category | $n$ | Primary Hypothesis | Evidence Direction |
| --- | --- | --- | --- | --- |
| A1 | Formal | 120 | H3 Markov Blanket Realism | Contested |
| A2 | Philosophy | 154 | H1 FEP Universality | Strongly supporting |
| B | Tools | 267 | H5 Scalability | Mixed |
| C1 | Neuroscience | 206 | H4 Predictive Coding | Supporting |
| C2 | Robotics | 170 | H2 AIF Optimality, H5 Scalability | Mixed |
| C3 | Language | 57 | H8 Language AIF | Emerging |
| C4 | Psychiatry | 34 | H6 Clinical Utility | Supporting |
| C5 | Biology | 200 | H7 Morphogenesis | Supporting |

The evidence directions summarized above are elaborated quantitatively—with citation-weighted scores, temporal trends, and three-tier evidence profiling—in the hypothesis results section (see \hyperref[sec:hypothesis_results]{Section 4b}).
