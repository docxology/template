# Evaluation of "As-Intended" Vehicle Dynamics using the Active Inference Framework

**Authors:** Kazuharu Kidera, Takuma Miyaguchi, Hideyoshi Yanagisawa

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kidera2025evaluation.pdf](../pdfs/kidera2025evaluation.pdf)

**Generated:** 2025-12-05 12:08:17

---

**Overview/Summary**
This study aimed to introduce a novel methodology for evaluating and understanding "as-intended" control in vehicle dynamics. The authors used the active inference framework, which is based on the free energy principle (FEP), to model the brain's learning process. They assumed that the driver learns about the vehicle by accumulating statistical regularities from sensory inputs and acts through probabilistic inference. This study focused on the "as-intended" control in the context of steering a vehicle. The authors hypothesized that lower VFE, which is the modeling error of the vehicle dynamics learned in the brain, reflects a higher degree of "as-intended" controllability. They also assumed that the VFE values obtained through offline learning using simulation data can quantify this control and potentially serve as a proxy for expert drivers' subjective "as-intended" scores.

**Key Contributions/Findings**
The authors found that the resulting VFE values correlate strongly with both reliable subjective "as-intended" scores and objective indicators (e.g., control performance or corrective steering). They also suggested that lower VFE reflects a higher degree of "as-intended" controllability. The offline learning approach proposed in this study is not limited to simulation data, but it can be applied to real-world driving data. This enables consistent and objective evaluation of "as-intended" control regardless of the evaluator.

**Methodology/Approach**
The authors introduced a novel methodology based on the active inference framework. By defining a specific task (e.g., steering), constructing a computational model of the brain capable of online learning within the active inference framework, and calculating VFE through offline learning using existing data, they demonstrated that the resulting VFE values correlate strongly with both reliable subjective "as-intended" scores and objective indicators (e.g., control performance or corrective steering). The authors used the CarSim software to simulate vehicle dynamics. They also used the pymdp library for active inference in discrete state spaces. This study was initiated by Honda R&D Co., Ltd. in collaboration with The University of Tokyo.

**Results/Data**
The authors found that the resulting VFE values correlate strongly with both reliable subjective "as-intended" scores and objective indicators (e.g., control performance or corrective steering). They also suggested that lower VFE reflects a higher degree of "as-intended" controllability. The offline learning approach proposed in this study is not limited to simulation data, but it can be applied to real-world driving data. This enables consistent and objective evaluation of "as-intended" control regardless of the evaluator.

**Limitations/Discussion**
The authors found that the learning outcomes were sensitive to factors such as the random seed used in action selection based on EFE, as well as the D vector. The sensitivity made it difficult to obtain stable and consistent VFE values for vehicle evaluation. It remains unclear whether this limitation arises from the framework itself or from the specific design of the generative model. Further studies are needed to clarify this issue.

**References**
1. Tao, M., Sugimachi, T., Suda, Y., Shibata, K., Katou, D., Fukaya, T.: A study on vehicle dynamics characteristics that realize "as-intended" driving. Trans. Soc. Automot. Eng. Jpn. 48(6), 1265–1271 (2017) (in Japanese). https://doi.org/10.11351/jsaeronbun.48.1265
2. Friston, K.: The free energy principle: a unified brain theory? Nat. Rev. Neurosci. 11(2), 127–138 (2010). https://doi.org/10.1038/nrn2787
3. Parr, T., Pezzulo, G., Friston, K.J.: Active Inference: The Free Energy Principle in Mind, Brain, and Behavior. MIT Press , Cambridge (2022). https://doi.org/10.7551/mit-press/12441.001.0001
4. Applied Intuition: CarSim. https://www.appliedintuition.com/products/carsim, last accessed 2025/05/16
5. Smith, R., Friston, K.J., Whyte, C.J.: A step-by-step tutorial on active inference and its application to empirical data. J. Math. Psychol. 107, 102632 (2022). https://doi.org/10.1016/j.jmp.2021.102632
6. Heins, C., Millidge, B., Demekas, D., Klein, B., Friston, K., Couzin, I.D., et al.: pymdp: A Python library for active inference in discrete state spaces. J. Open Source Softw. 7(73), 4098 (2022). https://doi.org/10.21105/joss.04098
7. Bradbury, J., Frostig, R., Hawkins, P., Johnson, M.J., Leary, C., Maclaurin, D., et al.: JAX: Composable transformations of Python+NumPy programs. https://github.com/google/jax, last accessed 2025/05/16
8. CEDEC Digital Library: Brainwave frequency bands and information processing speed during gameplay. https://cedil.cesa.or.jp/cedil_sessions/view/2146 (in Japanese), last accessed 2025/05/16
9. Parr, T., Markovic, D., Kiebel, S.J., Friston, K.: Neuronal message passing using Mean-field, Bethe, and Marginal approximations. Sci. Rep. 9(1), 1889 (2019). https://doi.org/10.1038/s41598-018-38246-3

**End PAPER CONTENT**

---

**Summary Statistics:**
- Input: 4,728 words (32,254 chars)
- Output: 679 words
- Compression: 0.14x
- Generation: 45.4s (14.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
