# Introduction {#sec:introduction}

Active Inference, grounded in the Free Energy Principle \cite{friston2010free}, has emerged as a powerful unifying framework for understanding perception, action, and learning in biological and artificial agents. By casting cognition as variational inference over generative models, Active Inference explains how agents minimize surprise through coordinated belief updating and action selection \cite{friston2015active, parr2022active}. Recent extensions to scale-free formulations \cite{friston2025scalefree} and variational planning \cite{champion2025efeplanning} have further demonstrated the framework's generality.

However, most existing treatments focus on Active Inference as a *first-order* theory: a method for computing policies given a fixed generative model. Comparatively little work has examined the meta-level structure of Active Inference---the fact that the modeler's specification of matrices $A$, $B$, $C$, and $D$ constitutes a meta-pragmatic and meta-epistemic act that defines what can be known and what matters before any inference begins. This meta-level perspective is critical because it reveals that Active Inference does not merely specify *how* agents reason; it specifies the *frameworks within which* reasoning occurs.

The distinction matters for several reasons. In reinforcement learning, reward functions are typically treated as given, and the research question concerns optimal policy computation \cite{sajid2022active}. In Active Inference, the preference prior $C$---which plays an analogous role to reward---is itself a design parameter. Similarly, the observation model $A$, transition dynamics $B$, and initial beliefs $D$ are not fixed environmental properties but modeler-specified epistemic commitments. This makes framework specification a first-class research variable, with profound consequences for cognitive science, AI safety, and cognitive security.

This paper makes the following contributions:

1. **A systematic $2 \times 2$ framework** (Data/Meta-Data $\times$ Cognitive/Meta-Cognitive) that organizes Active Inference's meta-level contributions into four distinct quadrants, each with specific mathematical formulations and computational implications.

2. **A meta-level analysis of Expected Free Energy** demonstrating that EFE operates not merely as a policy selection criterion but as a meta-theoretical construct whose properties depend on framework specification choices.

3. **Computational validation** through quadrant-specific implementations showing quantifiable benefits of meta-data integration, meta-cognitive control, and framework-level optimization.

4. **A cognitive security analysis** mapping attack surfaces and defense strategies to specific quadrants, revealing how meta-level processing creates both novel vulnerabilities and principled defenses against manipulation of belief formation and value structures.

The remainder of this paper is organized as follows. Section \ref{sec:related_work} reviews related work spanning Active Inference, meta-cognition, predictive processing, and cognitive security. Section \ref{sec:background} establishes the theoretical foundations including the Free Energy Principle, EFE formulation, and generative model specification. Section \ref{sec:methodology} describes our theoretical and computational methodology. Section \ref{sec:quadrant_model} presents the $2 \times 2$ quadrant framework with detailed analysis of each quadrant. Section \ref{sec:security} examines cognitive security implications. Section \ref{sec:discussion} discusses theoretical contributions and limitations. Section \ref{sec:conclusions} concludes with a synthesis of contributions and future directions.
