# Introduction: Evidence Gaps in a Rapidly Expanding Field

## The Free Energy Principle and Active Inference Framework

The Free Energy Principle (FEP), introduced by Karl Friston, proposes that self-organizing systems maintain their structural and functional integrity by minimizing variational free energy—an upper bound on sensory surprise \citep{friston2006free, friston2010free}. Under this principle, living systems are cast as approximate Bayesian inference engines that build generative models of their environment and act to reduce the discrepancy between predicted and observed states. Active Inference (AIF) extends this picture from passive perception to goal-directed behavior: agents select actions that bring about observations consistent with their preferred states, unifying perception, learning, and decision-making within a single variational framework \citep{parr2022active, friston2017active}. Since its initial formulation for sensorimotor control, AIF has been applied to navigation, visual foraging, language comprehension, social cognition, and multi-agent coordination.

## Challenges Posed by Rapid Literature Growth

The active inference literature has expanded exponentially over the past two decades, sustaining peak publication volumes into the late 2020s. While early research concentrated almost exclusively on theoretical neuroscience, the field has since diversified across biology (C5), robotics (C2), computational psychiatry (C4), algorithm scaling (B), and formal mathematics (A1). This rapid, multi-disciplinary growth creates three interrelated challenges. First, tracking which core theoretical claims—such as FEP universality or the physical realism of Markov blankets—are deeply supported, contested, or merely assumed becomes intractable. Second, because the relationship between mathematical formalisms and empirical evidence remains frequently implicit, systematic evidence synthesis demands prohibitive manual labor. Third, new entrants must navigate a literature heavily weighted toward broad qualitative philosophy (A2), interspersed with rapidly accelerating, highly specialized applied pockets.

Traditional narrative reviews attempt to address these challenges but are inherently static, subjective, and quickly outdated. Systematic reviews from evidence-based medicine offer rigorous aggregation but are structurally customized for clinical trial data with homogeneous outcome measures, rendering them ill-suited for the heterogeneous ontological and computational claims endemic to this theoretical literature. The expansion of predictive processing \citep{clark2013whatever, hohwy2013predictive} and the emergence of formal parameterizations like Bayesian mechanics \citep{sakthivadivel2023bayesian} further broaden the scope of assertions that any comprehensive meta-analysis must reconcile.

## Related Work and Prior Meta-Analyses

Several prior efforts have surveyed aspects of the Active Inference landscape. Sajid et al. \citep{sajid2021active} compare active inference with alternative decision-making frameworks; Da Costa et al. \citep{dacosta2020active} synthesize the discrete-state-space formulation; Lanillos et al. \citep{lanillos2021active} survey robotics applications; Smith et al. \citep{smith2021computational} provide a tutorial bridging theory and empirical data; and Millidge et al. \citep{millidge2021understanding} examine information-theoretic foundations of exploration behavior. Ramstead et al. \citep{ramstead2018answering} extend the FEP to questions of biological self-organization, while Pezzulo et al. \citep{pezzulo2015active} connect active inference to homeostatic regulation.

Closest to our work, Knight, Cordes, and Friedman \citep{knight2022fep} conducted a systematic literature analysis of publications using the terms "Free Energy Principle" or "Active Inference," with an emphasis on works by Karl J. Friston. Their analysis—maintained by the Active Inference Institute—combined manual annotation of structural, visual, and mathematical features with automated analyses using the Active Inference Ontology at the scale of thousands of citations and hundreds of annotated papers. That study identified six development directions—including broader scope, richer annotation, and transferable approaches—and represents an important precursor to automated meta-analysis of this field.

These works are primarily narrative reviews: they synthesize qualitative findings but do not strictly quantify the balance of evidence across the field's central claims. The systematic analysis of Knight et al. \citep{knight2022fep} pioneered quantitative literature analysis for this field using manual annotation and ontology-based automated analysis. Our framework advances this line of work by (1) fully automating assertion extraction via LLM-based hypothesis scoring, (2) constructing a structured, RDF-compatible knowledge graph scored by citation-weighted evidence, and (3) tracking how evidence for core claims evolves over time through temporal trend analysis.

## Synergizing Knowledge Graphs and LLMs

Recent systematic literature initiatives underscore a powerful reciprocal synergy between Large Language Models (LLMs) and Knowledge Graphs: LLMs parse unstructured text to rapidly extract semantic claims, efficiently populating the structured, queryable architecture of the graph \citep{quevedo2025combining, li2024unifying}. We adopt the *nanopublication* \citep{groth2010anatomy}—a minimal, machine-readable unit of scientific evidence comprising a core assertion bound to explicit provenance metadata—as the fundamental serialization format for this extracted knowledge.

## This Study: Approach and Overview

This paper presents a computational meta-analysis of the Active Inference literature ($N = 1208$). Rather than relying exclusively on bibliometric metadata or slow manual coding, we deploy a Large Language Model (LLM) to "read" each paper's abstract and assess its relationship to eight core hypotheses within the FEP paradigm. We serialize these assessments as nanopublications—each encoding an assertion ("Paper X supports Hypothesis Y") coupled with the LLM's natural-language reasoning and confidence score. The resulting knowledge graph aggregates these nanopublications and links them to paper metadata, citation networks, subfield classifications, and hypothesis definitions. A citation-weighted scoring formula quantifies the net evidence for or against each hypothesis, producing scores in $[-1, 1]$ that reflect both the direction and strength of published evidence.

## Research Questions

This meta-analysis addresses four primary research questions:

1. **RQ1 (Field Structure):** What is the disciplinary structure and growth trajectory of the Active Inference literature, and how are papers distributed across the three domains—Core Theory (A), Tools & Translation (B), and Application Domains (C)?
2. **RQ2 (Growth Dynamics):** What are the temporal growth dynamics of the field, and which subfields are experiencing the most rapid expansion?
3. **RQ3 (Hypothesis Evidence):** What is the current balance of evidence for and against the eight standard hypotheses, and how has this balance evolved over time? (See hypothesis dashboard and assertion figures in §4.)
4. **RQ4 (Tooling Readiness):** What is the state of software tooling and infrastructure for Active Inference research, and what gaps remain?

## Scope and Delimitations

This study focuses on the English-language peer-reviewed and preprint literature retrievable from arXiv, Semantic Scholar, and OpenAlex. We do not include book chapters or monographs not indexed by these sources, software documentation, or non-English publications. Domain classification uses keyword matching rather than expert annotation—a deliberate trade-off favoring reproducibility over precision, whose consequences we quantify in Section 3. Hypothesis scoring relies on LLM-extracted assertions; the fidelity and limitations of this approach are examined in Section 4a. The hypothesis definitions and domain taxonomy are informed by, but not identical to, the Active Inference Ontology used by Knight et al. \citep{knight2022fep}; future alignment would enable direct comparison with that earlier analysis.

## Principal Contributions

This work makes five contributions:

1. **A multi-source retrieval and deduplication pipeline** for Active Inference literature, using a canonical identifier hierarchy across three academic databases.

2. **A nanopublication-based knowledge graph schema** encoding directed, confidence-scored assertions about eight core hypotheses with full provenance tracking.

3. **A quantitative field overview** characterizing the growth, domain distribution (A/B/C taxonomy), citation topology, and latent topic structure of the Active Inference literature.

4. **An LLM-based hypothesis scoring dashboard** that produces differentiated evidence profiles with temporal trend visualization.

5. **A tooling assessment** of the software ecosystem supporting Active Inference research, including the implemented extraction pipeline, existing software (pymdp, SPM, RxInfer.jl), and knowledge graph infrastructure.

The remainder of this paper is organized as follows. Section 2 describes the methodology. Section 3 presents the field overview with domain-level analysis (RQ1, RQ2), supplemented by detailed domain analyses (§3a), text analytics (§3b), and citation network topology (§3c). Section 4 surveys the tooling landscape (RQ4) with a supplementary extraction pipeline (§4a), and Section 4b presents the hypothesis evidence landscape (RQ3). Section 5 concludes with limitations and future directions; Section 5a provides community recommendations and open questions. Appendix A provides notation, abbreviations, and hypothesis definitions.
