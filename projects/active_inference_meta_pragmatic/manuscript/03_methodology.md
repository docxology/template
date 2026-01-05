# Methodology {#sec:methodology}

This section presents the core methodological contribution: a \(2 \times 2\) matrix structure for understanding Active Inference as a meta-pragmatic and meta-epistemic methodology. The structure organizes cognitive processing along two dimensions: Data/Meta-Data and Cognitive/Meta-Cognitive, revealing four distinct quadrants of cognitive operation. Each quadrant represents a different combination of processing level (cognitive vs. meta-cognitive) and data type (data vs. meta-data), enabling systematic analysis of how Active Inference operates across multiple levels of abstraction.

## The \(2 \times 2\) Matrix Framework

Active Inference's meta-level operation becomes apparent when analyzed through a structure that distinguishes between data processing and meta-data processing, as well as cognitive and meta-cognitive levels of operation (Figure \ref{fig:quadrant_matrix}). This \(2 \times 2\) organization reveals how Active Inference operates simultaneously across multiple levels, from basic data processing to framework-level reasoning.

### Framework Dimensions

**Data vs Meta-Data (X-axis):**
- **Data:** Raw sensory inputs and immediate cognitive processing
- **Meta-Data:** Information about data processing (confidence scores, timestamps, reliability metrics, processing provenance)

**Cognitive vs Meta-Cognitive (Y-axis):**
- **Cognitive:** Direct processing and transformation of information
- **Meta-Cognitive:** Processing about processing; self-reflection, monitoring, and control of cognitive processes

### Quadrant Definitions

#### Quadrant 1: Data Processing (Cognitive) {#sec:q1_definition}

**Definition:** Basic cognitive processing of raw sensory data at the fundamental level of cognition, where agents directly process observations without incorporating quality information or self-reflection.

**Active Inference Role:** Baseline pragmatic and epistemic processing through Expected Free Energy minimization, providing the foundation upon which all other quadrants build. This quadrant implements the core Active Inference mechanism in its simplest form.

**Mathematical Formulation:**
```{=latex}
\[\mathcal{F}(\pi) = G(\pi) + H[Q(\pi)]\label{eq:efe_simple}\]
```

Where \(G(\pi)\) represents pragmatic value (goal achievement) and \(H[Q(\pi)]\) represents epistemic affordance (information gain). This formulation is shown in Equation \eqref{eq:efe_simple}.

**Example:** A thermostat maintaining temperature through direct sensor readings and immediate action selection. The thermostat processes temperature data at the cognitive level, selecting heating or cooling actions to minimize EFE. The pragmatic component \(G(\pi)\) reflects the preference for comfortable temperature (minimizing deviation from setpoint), while the epistemic component \(H[Q(\pi)]\) captures information gain about environmental conditions (learning whether the environment is heating or cooling). This basic operation demonstrates the fundamental balance between goal achievement and information gathering that characterizes all Active Inference systems.

#### Quadrant 2: Meta-Data Organization (Cognitive) {#sec:q2_definition}

**Definition:** Cognitive processing that incorporates meta-data (information about data quality, reliability, and provenance) to enhance primary data processing, improving decision reliability beyond what basic data processing can achieve.

**Active Inference Role:** Enhanced epistemic and pragmatic processing through meta-data integration, extending Quadrant 1 operations by weighting observations and inferences based on quality information.

**Mathematical Formulation:** Extended EFE with meta-data weighting:
```{=latex}
\[\mathcal{F}(\pi) = w_e \cdot H[Q(\pi)] + w_p \cdot G(\pi) + w_m \cdot M(\pi)\label{eq:efe_metadata}\]
```

Where \(M(\pi)\) represents meta-data derived utility, \(w_e\) is the epistemic weight, \(w_p\) is the pragmatic weight, and \(w_m\) is the meta-data weight. These weights adapt based on context and processing requirements. This extended formulation is shown in Equation \eqref{eq:efe_metadata}.

**Example:** Processing sensory data with associated confidence scores and temporal metadata to improve decision reliability. For instance, a navigation system might weight GPS readings by signal strength (confidence \(c(t)\)) and temporal consistency (meta-data \(\tau(t)\)), giving less weight to readings that conflict with recent measurements or have low signal quality. The meta-data weight \(w_m\) adapts dynamically: when confidence is high and temporal consistency is good, \(w_m\) increases, allowing the system to rely more heavily on the meta-data enhanced inference. This adaptive weighting demonstrates how meta-data integration improves cognitive performance beyond basic data processing.

#### Quadrant 3: Reflective Processing (Meta-Cognitive) {#sec:q3_definition}

**Definition:** Meta-cognitive evaluation and control of data processing, where agents reflect on their own cognitive processes, assess inference quality, and adaptively adjust processing strategies based on self-assessment.

**Active Inference Role:** Self-monitoring and adaptive cognitive control through hierarchical EFE evaluation, enabling systems to regulate their own cognitive operations based on confidence and performance assessment.

**Mathematical Formulation:** Hierarchical EFE with self-assessment:
```{=latex}
\[\mathcal{F}(\pi) = \mathcal{F}_{primary}(\pi) + \lambda \cdot \mathcal{F}_{meta}(\pi)\label{eq:efe_hierarchical}\]
```

Where \(\mathcal{F}_{meta}\) evaluates the quality of primary processing and \(\lambda\) controls meta-cognitive influence. The hierarchical structure enables self-monitoring by evaluating primary cognitive processes through meta-level assessment. This hierarchical formulation is shown in Equation \eqref{eq:efe_hierarchical}.

**Example:** An agent assessing its confidence in inferences and adjusting processing strategies accordingly. When confidence drops below threshold \(\gamma\), the meta-cognitive control parameter \(\lambda\) increases, amplifying the influence of \(\mathcal{F}_{meta}(\pi)\) in policy selection. This triggers adaptive responses: allocating more computational resources to inference, switching to more conservative decision-making strategies, or seeking additional information before acting. The hierarchical structure \(\mathcal{F}(\pi) = \mathcal{F}_{primary}(\pi) + \lambda \cdot \mathcal{F}_{meta}(\pi)\) enables the system to monitor and regulate its own cognitive processes, demonstrating self-awareness and adaptive control.

#### Quadrant 4: Higher-Order Reasoning (Meta-Cognitive) {#sec:q4_definition}

**Definition:** Meta-cognitive processing of meta-data about cognition itself, where systems analyze patterns in their own meta-cognitive performance to optimize fundamental framework parameters, enabling recursive self-analysis at the highest level of cognitive abstraction.

**Active Inference Role:** Framework-level reasoning and meta-theoretical analysis through parameter optimization, allowing systems to evolve their cognitive architectures based on higher-order performance analysis.

**Mathematical Formulation:** Multi-level hierarchical optimization:
```{=latex}
\[\min_{\Theta} \mathcal{F}(\pi; \Theta) + \mathcal{R}(\Theta)\label{eq:framework_optimization}\]
```

Where \(\Theta\) represents framework parameters and \(\mathcal{R}(\Theta)\) is a regularization term ensuring framework coherence. This optimization enables the system to adapt its fundamental cognitive architecture through recursive self-analysis. The framework optimization is shown in Equation \eqref{eq:framework_optimization}.

**Example:** Analyzing patterns in meta-cognitive performance to adapt fundamental processing frameworks. A system might observe that its confidence assessments are consistently miscalibrated (average confidence \(\bar{c}\) deviates from actual accuracy), leading it to optimize framework parameters \(\Theta\) including confidence thresholds \(\theta_c\), adaptation rates \(\alpha\), and strategy selection parameters \(\beta\). The optimization \(\min_{\Theta} \mathcal{F}(\pi; \Theta) + \mathcal{R}(\Theta)\) balances performance improvement with framework coherence, ensuring that parameter changes maintain system stability. This recursive self-analysis enables the system to evolve its fundamental cognitive architecture, representing the highest level of meta-cognitive operation.

## Active Inference as Meta-Epistemic

Active Inference supports meta-epistemic modeling by allowing researchers to specify the epistemological frameworks within which agents operate. This specification power transforms epistemology from an external constraint into an internal design parameter, enabling systematic exploration of how different ways of knowing shape cognition.

### Epistemic Framework Specification

Through the generative model matrices, researchers define:

**Observation Model (Matrix \(A\)):** What can be known about the world
```{=latex}
\[A = [a_{ij}] \quad a_{ij} = P(o_i \mid s_j)\label{eq:matrix_a}\]
```

**Prior Knowledge (Matrix \(D\)):** Initial assumptions about the world
```{=latex}
\[D = [d_i] \quad d_i = P(s_i)\label{eq:matrix_d}\]
```

**Causal Structure (Matrix \(B\)):** How actions influence the world
```{=latex}
\[B = [b_{ijk}] \quad b_{ijk} = P(s_j \mid s_i, a_k)\label{eq:matrix_b}\]
```

### Meta-Epistemic Implications

By specifying these matrices, researchers define not just current beliefs, but the fundamental structure of knowledge acquisition and representation. This meta-epistemic power supports systematic exploration of epistemological questions that were previously difficult to formalize:

1. **Framework Comparison:** Epistemic frameworks can be compared by varying \(A\), \(B\), \(D\) specifications. For example, comparing empirical frameworks (high diagonal values in \(A\), indicating strong trust in observations) versus skeptical frameworks (lower diagonal values, indicating greater uncertainty) reveals how different assumptions about observation reliability shape knowledge acquisition strategies. Researchers can systematically explore how different epistemic assumptions lead to different cognitive behaviors, learning speeds, and adaptation patterns. This comparative approach enables formal analysis of epistemological questions that were previously limited to philosophical discourse.

2. **Knowledge Architecture Design:** The structure of cognition itself becomes a design parameter. Researchers can design knowledge architectures optimized for specific tasks, environments, or constraints, exploring how different epistemic structures enable or constrain cognitive capabilities. For instance, designing an \(A\) matrix with high off-diagonal values creates an epistemic framework that maintains uncertainty longer, requiring more evidence before committing to beliefs—useful for environments with high observation noise.

3. **Epistemological Pluralism:** Different ways of knowing can be modeled and compared within the same mathematical structure. This supports systematic analysis of how different epistemic approaches (empirical, theoretical, intuitive) lead to different cognitive outcomes, providing a formal basis for epistemological analysis. The structure allows researchers to explore questions like: How does an empirical epistemic framework (high observation reliability) compare to a theoretical framework (strong prior structure in \(D\)) in terms of learning speed, robustness, and adaptability? This pluralistic approach enables formal comparison of epistemological traditions that were previously considered incommensurable.

## Active Inference as Meta-Pragmatic

Active Inference supports meta-pragmatic modeling by allowing specification of pragmatic frameworks beyond simple reward functions. This specification power transforms value system design from an external constraint into an internal research question, enabling systematic exploration of how different value structures shape cognition and behavior.

### Pragmatic Framework Specification

**Preference Structure (Matrix \(C\)):** What matters to the agent
```{=latex}
\[C = [c_i] \quad c_i = \log P(o_i)\label{eq:matrix_c}\]
```

This specification goes beyond traditional reinforcement learning by enabling researchers to specify value landscapes.

### Meta-Pragmatic Implications

The meta-pragmatic aspect supports systematic exploration of value systems and their cognitive consequences, making value system design a research question:

1. **Value System Design:** Specification of what constitutes "good" outcomes through matrix \(C\) enables researchers to design value systems optimized for specific goals, constraints, or ethical principles. This goes beyond simple reward functions to enable complex value hierarchies with trade-offs. For example, a \(C\) matrix can encode preferences that balance individual benefit with collective welfare, or that prioritize long-term sustainability over short-term gains, revealing how different value structures shape decision-making patterns.

2. **Pragmatic Pluralism:** Different pragmatic frameworks can be explored and compared. Researchers can model how different value systems (utilitarian, deontological, virtue-based) shape decision-making and behavior, revealing the cognitive consequences of different ethical frameworks. A utilitarian \(C\) matrix might prioritize outcomes that maximize aggregate utility, while a deontological matrix might encode categorical imperatives, enabling systematic comparison of how these different ethical approaches lead to different cognitive and behavioral patterns.

3. **Value Learning:** How value systems themselves evolve and adapt can be modeled through learning mechanisms that update matrix \(C\) based on experience, feedback, or reflection. This supports exploration of how agents develop their own value systems over time, modeling processes like moral development, cultural value acquisition, and personal preference formation. The structure allows researchers to study how value systems change in response to experience, social influence, or self-reflection, providing formal models of value system dynamics that were previously difficult to formalize.

4. **Ethical Framework Integration:** Incorporation of ethical considerations directly into the preference landscape enables agents to reason about moral implications of actions. This provides a formal framework for exploring how ethical principles shape cognition and behavior, enabling systematic analysis of questions like: How do different ethical frameworks (encoded in \(C\)) influence decision-making under uncertainty? How do value conflicts (competing preferences in \(C\)) get resolved?

## Integration Across Quadrants

Active Inference operates across all four quadrants simultaneously, with different aspects of the structure contributing to each quadrant. This integration creates a hierarchical cognitive architecture where lower quadrants provide foundations for higher quadrants:

- **Quadrant 1 (Foundation):** Core EFE computation with basic \(A\), \(B\), \(C\), \(D\) specifications provides the fundamental cognitive processing layer
- **Quadrant 2 (Enhancement):** Meta-data weighted EFE with confidence-weighted processing enhances Quadrant 1 operations by incorporating quality information
- **Quadrant 3 (Reflection):** Self-reflective EFE evaluation and meta-cognitive control monitors and regulates Quadrants 1 and 2, enabling adaptive strategy selection
- **Quadrant 4 (Evolution):** Framework-level EFE optimization and meta-theoretical reasoning analyzes patterns across all lower quadrants to evolve the cognitive architecture itself

This hierarchical structure enables systems to operate at multiple levels simultaneously: processing data (Q1), incorporating meta-data (Q2), reflecting on processing quality (Q3), and evolving framework parameters (Q4). The relative influence of each quadrant adapts dynamically based on context, uncertainty, and performance requirements.

## The Modeler's Dual Role

The structure reveals the dual role of the Active Inference modeler, who operates at both the cognitive and meta-cognitive levels:

### As Architect
- Specifies epistemic frameworks (\(A\), \(B\), \(D\) matrices)
- Defines pragmatic landscapes (\(C\) matrix)
- Designs cognitive architectures
- Establishes boundary conditions for cognition

### As Subject
- Uses Active Inference to understand their own cognition
- Applies meta-epistemic principles to knowledge acquisition
- Employs meta-pragmatic frameworks for decision-making
- Engages in recursive self-modeling

This dual role creates a recursive relationship where the tools used to model others become tools for self-understanding. The modeler, in specifying frameworks for studied systems, implicitly reveals their own epistemic and pragmatic assumptions. This recursive self-modeling enables researchers to apply Active Inference principles to understand their own cognitive processes, creating a virtuous cycle where modeling improves self-understanding, which in turn improves modeling capabilities.

## Validation Approach

The structure's validity is demonstrated through multiple complementary approaches that together provide strong theoretical and practical support:

1. **Theoretical Consistency:** Alignment with Free Energy Principle foundations ensures that all quadrant formulations minimize variational free energy at their respective levels, maintaining theoretical coherence with established Active Inference principles.

2. **Mathematical Rigor:** Proper formulation of EFE across all quadrants, with each quadrant's mathematical structure building systematically on previous quadrants. All formulations are grounded in established Active Inference theory and maintain probabilistic consistency.

3. **Conceptual Clarity:** Clear distinction between quadrants and processing levels enables systematic analysis. The \(2 \times 2\) structure provides unambiguous categorization of cognitive operations, facilitating both theoretical analysis and experimental design.

4. **Practical Applicability:** Framework enables systematic analysis of meta-level phenomena that were previously difficult to formalize. The quadrant structure provides a practical tool for researchers to target specific processing levels in experimental design and theoretical development.

The following sections provide concrete demonstrations of each quadrant with mathematical examples and conceptual analysis, showing how the structure applies to real cognitive scenarios. These demonstrations reveal the practical utility of the quadrant organization for understanding, designing, and improving cognitive systems.

The \(2 \times 2\) matrix structure, illustrated in Figure \ref{fig:quadrant_matrix}, organizes our analysis of Active Inference as a meta-pragmatic and meta-epistemic methodology. This structure reveals four distinct quadrants of cognitive operation, each representing different combinations of data/meta-data processing and cognitive/meta-cognitive levels, enabling systematic exploration of how Active Inference operates across multiple scales of cognitive abstraction.



The Expected Free Energy (EFE) formulation (Equation \eqref{eq:efe}) combines epistemic and pragmatic components, as shown in Figure \ref{fig:efe_decomposition}. This decomposition reveals how Active Inference balances information gathering (epistemic value, Equation \eqref{eq:epistemic_component}) with goal achievement (pragmatic value, Equation \eqref{eq:pragmatic_component}) in a principled mathematical framework.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/efe_decomposition.png}
\caption{Expected Free Energy (EFE) decomposition into epistemic and pragmatic components (Equation \eqref{eq:efe}). The EFE \(\mathcal{F}(\pi)\) combines two fundamental terms: (1) Epistemic affordance \(H[Q(\pi)]\) (Equation \eqref{eq:epistemic_component}), measuring information gain about hidden states through policy execution; (2) Pragmatic value \(G(\pi)\) (Equation \eqref{eq:pragmatic_component}), measuring goal achievement through preferred observations. This decomposition enables systematic analysis of how agents balance exploration (epistemic) and exploitation (pragmatic) in decision-making.}
\label{fig:efe_decomposition}
\end{figure}



The perception-action loop in Active Inference, illustrated in Figure \ref{fig:perception_action_loop}, demonstrates how agents continuously update beliefs and select actions to minimize expected free energy.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/perception_action_loop.png}
\caption{Active Inference perception-action loop showing how perception drives action through EFE minimization (Equation \eqref{eq:efe}). The cycle consists of: (1) Observation of sensory data; (2) Bayesian inference updating posterior beliefs \(q(s)\) about hidden states; (3) Policy evaluation computing EFE \(\mathcal{F}(\pi)\) for candidate actions; (4) Action selection minimizing EFE; (5) Action execution generating new observations. This closed loop enables agents to actively shape their sensory input while maintaining accurate world models.}
\label{fig:perception_action_loop}
\end{figure}



The generative model structure, shown in Figure \ref{fig:generative_model_structure}, illustrates how the four core matrices (\(A\), \(B\), \(C\), \(D\)) define the epistemic and pragmatic frameworks within which agents operate. These matrices are defined in Equations \eqref{eq:matrix_a}, \eqref{eq:matrix_b}, \eqref{eq:matrix_c}, and \eqref{eq:matrix_d}.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/generative_model_structure.png}
\caption{Structure of generative models in Active Inference showing \(A\), \(B\), \(C\), \(D\) matrices and their relationships. Matrix \(A\) (Equation \eqref{eq:matrix_a}) defines observation likelihoods \(P(o \mid s)\), establishing what can be known. Matrix \(B\) (Equation \eqref{eq:matrix_b}) defines state transitions \(P(s' \mid s, a)\), specifying causal structure. Matrix \(C\) (Equation \eqref{eq:matrix_c}) defines preferences over observations, establishing pragmatic goals. Matrix \(D\) (Equation \eqref{eq:matrix_d}) defines prior beliefs \(P(s)\), setting initial assumptions. Together, these matrices enable modelers to specify the fundamental frameworks of cognition.}
\label{fig:generative_model_structure}
\end{figure}



The meta-level aspects of Active Inference, demonstrated in Figure \ref{fig:meta_level_concepts}, reveal how modelers specify both epistemic and pragmatic frameworks, transcending traditional approaches to cognition.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/meta_level_concepts.png}
\caption{Meta-pragmatic and meta-epistemic aspects showing modeler specification power. The meta-epistemic dimension enables specification of knowledge acquisition frameworks through matrices \(A\) (Equation \eqref{eq:matrix_a}), \(B\) (Equation \eqref{eq:matrix_b}), and \(D\) (Equation \eqref{eq:matrix_d}), defining what can be known and how beliefs update. The meta-pragmatic dimension enables specification of value landscapes through matrix \(C\) (Equation \eqref{eq:matrix_c}), defining what matters to the agent. This dual specification power makes Active Inference a meta-methodology for cognitive science, enabling exploration of how different frameworks shape cognition.}
\label{fig:meta_level_concepts}
\end{figure}



The Free Energy Principle provides the theoretical foundation for Active Inference, as illustrated in Figure \ref{fig:fep_system_boundaries}, showing how systems maintain their structure through boundary maintenance.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/fep_system_boundaries.png}
\caption{Free Energy Principle system boundaries showing Markov blanket separating internal and external states. The Markov blanket defines the boundary between a system (internal states) and its environment (external states) through sensory and active states. Systems maintain their structure by minimizing variational free energy \(\mathcal{F}[q]\), which bounds surprise. This principle applies across multiple scales: physical systems maintain boundaries through thermodynamic processes, cognitive systems maintain beliefs through inference, and meta-cognitive systems maintain frameworks through adaptation.}
\label{fig:fep_system_boundaries}
\end{figure}



Free energy minimization dynamics, shown in Figure \ref{fig:free_energy_dynamics}, demonstrate how systems converge toward stable states through continuous optimization.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/free_energy_dynamics.png}
\caption{Free energy minimization dynamics showing convergence over time and epistemic/pragmatic components. The trajectory shows how variational free energy \(\mathcal{F}[q]\) decreases over time as the system updates its beliefs and actions. The decomposition reveals the relative contributions of epistemic (information gain) and pragmatic (goal achievement) components. Convergence indicates successful model fitting and goal achievement, while divergence may signal model inadequacy or goal conflict.}
\label{fig:free_energy_dynamics}
\end{figure}



Structure preservation, illustrated in Figure \ref{fig:structure_preservation}, shows how systems maintain their internal organization despite environmental perturbations.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/structure_preservation.png}
\caption{Structure preservation dynamics showing how systems maintain internal organization through free energy minimization. Despite external perturbations and environmental changes, systems maintain stable internal states through active inference. The Markov blanket enables selective coupling with the environment, allowing systems to resist entropy while remaining responsive to relevant information. This principle explains how biological systems, cognitive agents, and even social structures maintain their identity over time.}
\label{fig:structure_preservation}
\end{figure}



The enhanced quadrant matrix, shown in Figure \ref{fig:quadrant_matrix_enhanced}, provides detailed descriptions and examples for each quadrant, facilitating systematic analysis of cognitive processes.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/quadrant_matrix_enhanced.png}
\caption{\(2 \times 2\) Quadrant Structure with detailed descriptions and examples for each quadrant. Quadrant 1 (Data, Cognitive): Basic EFE computation (Equation \eqref{eq:efe_simple}) with direct sensory processing, providing the foundation for all cognitive operations. Quadrant 2 (Meta-Data, Cognitive): Extended EFE with meta-data weighting (Equation \eqref{eq:efe_metadata}), enhancing processing through confidence scores and reliability metrics. Quadrant 3 (Data, Meta-Cognitive): Hierarchical EFE with self-assessment (Equation \eqref{eq:efe_hierarchical}), enabling self-reflective processing with confidence assessment and adaptive control. Quadrant 4 (Meta-Data, Meta-Cognitive): Framework-level optimization (Equation \eqref{eq:framework_optimization}), supporting reasoning about meta-cognitive processes with parameter optimization. Each quadrant includes mathematical formulations, practical examples (thermostat, navigation system, adaptive agent, framework-evolving system), and connections to Active Inference theory, demonstrating the hierarchical relationship between quadrants.}
\label{fig:quadrant_matrix_enhanced}
\end{figure}





The Free Energy Principle serves as a unifying bridge between physics and cognition, as demonstrated in Figure \ref{fig:physics_cognition_bridge}, revealing deep connections across domains.

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/physics_cognition_bridge.png}
\caption{Free Energy Principle as the bridge between physics and cognition domains. The same mathematical principle—variational free energy minimization—applies across multiple scales: (1) Physical systems minimize thermodynamic free energy, maintaining structure through energy flows; (2) Biological systems minimize variational free energy, maintaining organization through metabolism and behavior; (3) Cognitive systems minimize expected free energy, maintaining accurate world models through perception and action; (4) Meta-cognitive systems minimize framework-level free energy, maintaining adaptive cognitive architectures through self-reflection. This unification enables understanding of intelligence as a natural extension of physical principles.}
\label{fig:physics_cognition_bridge}
\end{figure}

