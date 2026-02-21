# Introduction {#sec:introduction}

## Linguistic Priors and Generative Models

Scientific inquiry is a process of **active inference**, where researchers refine generative models to minimize surprise about biological observations \cite{friston2010free}. Language acts as the **hyper-prior** for these models: it constrains the hypothesis space before data collection even begins. When entomologists employ terms like "queen" or "caste," they are not merely labeling phenomena; they are importing a high-precision prior from human social systems into their model of insect biology. If this prior is structurally misaligned with the target system—for instance, assuming top-down control in a stigmergic network—the resulting model will necessarily suffer from high variational free energy, manifesting as persistent anomalies and "epicycles" in theoretical explanations \cite{kuhn1996, clark2013whatever}.

We can formally model the **scientific community itself as a multi-scale Active Inference agent**. Its collective task is to minimize long-term surprise (variational free energy) about the entomological world it observes. Its "Generative Model" is the shared ontology of the field—the lexicon and conceptual structures encoded in the literature. When this ontology is precise and plastic, the community efficiently updates its priors in response to new sensory data (e.g., genomic evidence). However, when the ontology is rigid or laden with hidden anthropomorphic priors, the agent suffers from **Prior Dogmatism**: a failure of belief updating where high-precision, fixed priors overwhelm contradictory sensory evidence. In this state, anomalies are explained away rather than used to update the model. Terminology reform is thus not a political act but a **model selection** process: optimizing the community's generative model to restore its ability to minimize free energy.

This optimization requires specific criteria. We propose **Evolvability**—defined here as **scale-invariance**—as a critical metric for scientific terms. An evolvable term maintains its validity across biological scales (gene, organism, superorganism) without fracturing. A term like "queen," by contrast, is scale-brittle: it functions as a metaphor at the colony level but dissolves into incoherence when applied to the underlying genetic or molecular mechanisms of caste determination.

Recent formal work by \citet{friedman2021active} demonstrates that ant colonies can be modeled as ensembles of *active inferants*—individual agents performing Bayesian inference over local states via chemical stigmergy—without any centralized controller; yet the dominant vocabulary of the field continues to presuppose one.

Our work examines this epistemic risk through systematic analysis of *Ento-Linguistic domains*: specific areas where linguistic priors obscure the causal architecture of ant systems.

## Motivation: Minimizing Model Misspecification

The drive for clarity is not merely a stylistic preference but a requirement for model integrity. As \citet{keller1995language} argued, the language of science constitutes the cognitive scaffolding of research. In the framework of Active Inference, an undefined or metaphor-laden term introduces **irreducible uncertainty** (entropy) into the scientific communication channel.

The present moment demands this formalization. Recent cognitive science emphasizes that metaphor is a mechanism of predictive processing \cite{steen2017deliberate}. Rather than perpetuating "legacy code" in our linguistic ontology, researchers must critically assess whether their terminological priors minimize or maximize the complexity of their biological models.

A paradigmatic example is the "slave-making" debate. \citet{herbers2006} showed that the term "slave" naturalizes a human institution while obscuring the biological mechanism of **social parasitism**. In formal terms, the "slave" metaphor implies a conscious coercion policy, whereas the replacement term "dulosis" correctly identifies the phenomenon as a breakdown in nestmate recognition signals (a failure of the Markov Blanket's security filter). Reform, therefore, is not just about ethics; it is about restoring the causal fidelity of the scientific model.

## The Challenge of Terminological Reform

A common objection to improving scientific language is that changing terminology creates disconnection from existing literature. If entomologists abandon terms like "caste" or "slave," how would researchers locate papers on task performance or social parasitism?

This objection, however, inadvertently strengthens the case for reform. Retaining problematic terminology for convenience perpetuates and compounds conceptual distortions rather than addressing them \cite{herbers2006}. The appropriate response is to work systematically toward clearer communication while developing the necessary infrastructure for literature synthesis—restructuring information from existing sources and establishing new meta-standards for scientific discourse. Recent community-level momentum confirms this trajectory: discussions at the MirMeco 2023 International Ant Meeting \cite{laciny2024terminology} and the Entomological Society of America's Better Common Names Project \cite{betternamesproject2024} demonstrate that the professional community increasingly shares these concerns.

## Ento-Linguistic Domains: A Framework for Analysis

We organize our analysis around six domains where entomological language creates ambiguity or imports unjustified assumptions. Each domain isolates a distinct category of terminological friction between human conceptual frameworks and ant biology.

**Unit of Individuality.** The definition of a biological individual is formally equivalent to the specification of a **Markov Blanket**—the statistical boundary separating internal states from external states \cite{friston2013life}. Terms like "colony," "superorganism," and "individual" confuse these boundaries, creating models where the relevant unit of agency is undefined.

**Behavior and Identity.** Task performance in ants is a fluid process of **policy selection** based on local cues \cite{gordon2010}. However, terminology transforms these transient policies into categorical identities ("forager," "nurse"). This effectively hard-codes a fixed-role prior into the model, obscuring the plasticity and Bayesian updating that actually drives task allocation.

**Power \& Labor.** Terms like "queen," "worker," and "caste" impose a hierarchical control architecture on a system that is fundamentally **stigmergic**. This introduces a causal error: it attributes colony-level regulation to centralized agency (the queen) rather than distributed feedback loops, fundamentally misrepresenting the system's control theory.

**Sex \& Reproduction.** Terms like "sex determination" and "sex differentiation" carry implicit assumptions about binary systems that may not map onto ant reproductive biology, where haplodiploidy creates fundamentally different patterns \cite{chandra2021epigenetics}.

**Kin \& Relatedness.** Human kinship terminology, grounded in bilateral relatedness, creates systematic friction when applied to ant societies structured by haplodiploidy. In haplodiploid species, full sisters share an average relatedness coefficient of $r = 0.75$—higher than the mother–daughter coefficient of $r = 0.5$—a fundamental asymmetry absent from human kinship models. Terms such as "sister," "mother," and "family" obscure this asymmetry and its profound consequences for kin selection theory \cite{chandra2021epigenetics}.

**Economics.** Economic metaphors—markets, trade, investment, cost-benefit—shape analysis of ant foraging, resource distribution, and colony-level resource management. This domain investigates how transactional frameworks constrain biological interpretation by conflating proximate energetic expenditure with ultimate fitness costs, importing assumptions of rational optimisation from microeconomics into systems that operate through evolved heuristics rather than deliberative calculation.

## Research Approach

This work employs a mixed-methodology framework combining computational text analysis with theoretical discourse examination. The computational component processes a **comprehensive literature corpus of 3,253 publications** using automated term extraction, co-occurrence network construction, and ambiguity scoring to identify statistical patterns in language use. The theoretical component, informed by \citeauthor{foucault1972archaeology}'s archaeological method \citeyearpar{foucault1972archaeology}, conceptual metaphor theory \cite{lakoff1980metaphors}, and \citeauthor{gordon2023ecology}'s \citeyearpar{gordon2023ecology} ecological framework for collective behaviour, examines how these patterns reflect deeper conceptual structures. All data and analysis code are reproducible and available for validation and extension.

## Terminology Network Visualization

To illustrate the framework's output, Figure \ref{fig:concept_map} shows how terms cluster around the six Ento-Linguistic domains and form cross-domain networks of meaning; detailed quantitative analysis follows in Section \ref{sec:experimental_results}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/concept_map.png}
\caption{Conceptual map of Ento-Linguistic domains showing relationships between terminology networks. Each node represents an extracted concept; node size is proportional to term frequency in the corpus and node colour encodes the primary domain assignment. Edges connect co-occurring concepts, with thickness reflecting co-occurrence strength. The six domains form interconnected clusters; central hub terms such as ``colony,''``caste,'' and ``individual'' bridge multiple domains, demonstrating how specific terminological choices propagate across the scientific discourse of entomology.}
\label{fig:concept_map}
\end{figure}
