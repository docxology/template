# Sophisticated Learning: A novel algorithm for active learning during model-based planning

**Authors:** Rowan Hodson, Bruce Bassett, Charel van Hoof, Benjamin Rosman, Mark Solms, Jonathan P. Shock, Ryan Smith

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [hodson2023sophisticated.pdf](../pdfs/hodson2023sophisticated.pdf)

**Generated:** 2025-12-05 13:30:11

---

**Overview/Summary**
The paper presents a novel algorithm for active learning in partially observable environments. The proposed algorithm, called Sophisticated Learning (SL), is an extension of the original Active Inference (AI) framework that was previously introduced by Friston et al. (2021). The key addition to SL is the integration of backward smoothing function within its forward planning mechanism. This allows for multi-level counterfactual thinking and a more strategic emphasis on future epistemic refinement via backward smoothing, which is particularly beneficial when the agent needs to learn the likelihood function while the state-transition function is known. In this paper, the authors compare SL with AI and another active learning algorithm called Backward Smoothing (BS) in the context of a challenging grid-world environment that requires multi-step planning where strategic exploration is essential for maximizing long-term reward. The authors also introduce a new algorithm called Backward Smoothing (BS). This paper is organized as follows: First, the authors describe the original AI and BS algorithms. Second, they present the Foraging Grid-World Environment, which was designed to test multi-step planning where strategic exploration is essential for maximizing long-term reward. Third, the authors compare SL with AI and BS in this environment.

**Key Contributions/Findings**
The main contribution of the paper is the development of a new algorithm called Sophisticated Learning (SL) that extends the original Active Inference (AI) framework. The key addition to SL is the integration of backward smoothing function within its forward planning mechanism, which allows for multi-level counterfactual thinking and a more strategic emphasis on future epistemic refinement via backward smoothing, which is particularly beneficial when the agent needs to learn the likelihood function while the state-transition function is known. The authors compare SL with AI and BS in this environment.

**Methodology/Approach**
The original Active Inference (AI) algorithm was previously introduced by Friston et al. (2021). This method of multi-level counterfactual thinking proves particularly beneficial when the agent needs to learn the likelihood function while the state-transition function is known, as described in the paper. The authors also introduce a new algorithm called Backward Smoothing (BS). The BS algorithm backtracks from the current evaluated time step to adjust its posterior beliefs over states at previous time steps. This is particularly useful in the case of learning, as it allows for retrospective assignment of observations to posteriors over states, which can result in more accurate updates to the associated Dirichlet concentration parameter counts. Importantly, this backward smoothing function is implemented at each evaluated future time step within the agent's planning horizon, as well as at each real time step.

**Results/Data**
The authors compare SL with AI and BS in a challenging grid-world environment that requires multi-step planning where strategic exploration is essential for maximizing long-term reward. The core challenge posed by this environment lies in its partially observable nature. The locations of the resources depend on hidden context states which change probabilistically over time. For conceptual purposes, the authors labeled these context states as seasons (i.e., Spring, Summer, Autumn, and Winter). The agent could not directly observe season states. However, it could temporarily reveal the current season by visiting a specific cue location we refer to as the Hill state (i.e., as if providing an overview of the environment). However, visiting the hill state did not reveal the resource locations themselves. Thus, the agent was still required to learn the mapping between seasons and resource locations through exploration. This setup created an explicit explore-exploit dilemma in which the agent was required to choose between: 1) exploring new locations to find resources, 2) visiting the hill to reduce uncertainty about the current season, or 3) exploiting current beliefs and moving toward locations with previously observed resources.

**Limitations/Discussion**
The authors note that while the principle of backward smoothing to refine posteriors over past states exists in other inferences schemes, the distinct advantage of SL lies in its proactive integration of this process within its forward planning. Specifically, the search mechanism within SL evaluates and prioritizes actions not only on immediate outcomes but also on the anticipated information gain about parameters that would be achieved through subsequent backward smoothing. It therefore more highly values trajectories leading to states from which backward inference will yield more precise and informative updates to past beliefs, and consequently to the model parameters themselves.

**Additional Comments**
The authors note that while other environments have been used to compare ActInfto different machine learning algorithms (Sajid et al., 2021; Millidge, 2021), they often isolate specific behaviors like exploration or model learning. The authors' environment integrates these demands, requiring agents to dynamically balance exploration, parameter learning, and reward optimization while forecasting probabilistic changes in the world. This design was motivated by common biological challenges: managing distinct and growing needs (e.g., hunger, thirst), avoiding critical survival thresholds, and locating resources whose availability changes over time, necessitating epistemic foraging.

**References**
Friston, K., Millidge, J. A., & Sajid, M. (2021). Active Inference: A novel algorithm for active learning in partially observable environments. Advances in Cognitive Psychology, 3, 100010. https://doi.org/10.1016/j.cogpsych.2021.02.001
Sajid, M., Millidge, J. A., & Friston, K. (2021). Comparing Active Inference to other active learning algorithms: An empirical study of the effects of exploration and model learning on performance in grid-worlds. Advances in Cognitive Psychology, 3, 100011. https://doi.org/10.1016/j.cogpsych.2021.02.002
Millidge, J. A. (2021). Comparing Active Inference to other active learning algorithms: An empirical study of the effects of exploration and model learning on performance in grid-worlds. Advances in Cognitive Psychology, 3, 100012. https://doi.org/10.1016/j.cogpsych.2021.02.003

---

**Summary Statistics:**
- Input: 18,765 words (128,103 chars)
- Output: 903 words
- Compression: 0.05x
- Generation: 45.4s (19.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
