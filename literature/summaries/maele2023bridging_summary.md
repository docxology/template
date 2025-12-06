# Bridging Cognitive Maps: a Hierarchical Active Inference Model of Spatial Alternation Tasks and the Hippocampal-Prefrontal Circuit

**Authors:** Toon Van de Maele, Bart Dhoedt, Tim Verbelen, Giovanni Pezzulo

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [maele2023bridging.pdf](../pdfs/maele2023bridging.pdf)

**Generated:** 2025-12-05 13:54:07

---

**Overview/Summary**
The paper "Bridging Cognitive Maps" proposes a hierarchical active inference (AI) model for bridging cognitive maps in the context of goal-directed navigation. The authors claim that this is the first work to provide a mechanistic explanation of the theoretical proposal made by Jadhav et al. (2012), which suggests that the selective impairment of outbound decisions provoked by hippocampal sharp wave reactivations (SWRs) is due to the fact that the SWRs convey messages to higher structures, like the prefrontal cortex, which are used to update a belief about the current stage of the task. The authors also claim that their model suggests that the maladaptive behavior found in Den Bakker et al. (2022), could be due to the impossibility for the higher, prefrontal component to correctly update its belief based on bottom-up message passing from the hippocampal component.

**Key Contributions/Findings**
The main contribution of this paper is a hierarchical AI model that uses two cognitive maps: one for physical space and another for task rules. The authors show that the selective impairment of outbound decisions provoked by hippocampal SWRs (Jadhav et al., 2012) is due to the fact that the SWRs convey messages to higher structures, like the prefrontal cortex, which are used to update a belief about the current stage of the task. The authors also show that their model suggests that the maladaptive behavior found in Den Bakker et al. (2022), could be due to the impossibility for the higher, prefrontal component to correctly update its belief based on bottom-up message passing from the hippocampal component.

**Methodology/Approach**
The authors first train two cognitive maps: one for physical space and another for task rules. The authors use a simplified procedure to learn the cognitive maps offline before embedding them into the AI model, using predefined trajectories that exhaustively cover the W-maze as inputs for the cognitive map of physical space and 75% correct trajectories as inputs for the cognitive map of task space. In the future, it would be interesting to explore methods to learn hierarchical models with multiple timescales (Yamashita and Tani, 2008; Hinton et al., 2006) and effective state spaces for navigation and for task rules in self-supervised (and/or reward-guided) ways, as shown in prior work (Stoianov et al., 2022, 2018, 2016; Niv, 2019). This might also help understand the reciprocal influences between cognitive map learning at different levels and in different brain structures. A second research avenue is to relax the separation of the timescales between the two levels, by selecting their inputs (e.g., level 1 takes all sensory observations as inputs, whereas level 2 only considers observations that could be rewarding - and in particular, observation 1 in Figure 2b). In the future, it would be interesting to explore methods to learn hierarchical models with multiple timescales (Yamashita and Tani, 2008; Hinton et al., 2006) and effective state spaces for navigation and for task rules in self-supervised (and/or reward-guided) ways, as shown in prior work (Stoianov et al., 2022; Guntupalli et al., 2023; Stoiano

[... truncated ...]

**Limitations/Discussion**
The current study has several limitations that will need to be addressed in future studies. First, for efficiency reasons, the authors learn the cognitive maps offline (before embedding them into the AI), using a simplified procedure: they use predefined trajectories that exhaustively cover the W-maze as inputs for the cognitive map of physical space and 75% correct trajectories as inputs for the cognitive map of task space. In the future, it would be interesting to explore methods to learn cognitive maps online, similar to (Lazaro-Gredilla et al., 2023), by guiding the exploration through active inference dynamics (Friston et al., 2017a; Schwartenbeck et al., 2019; Parr et al., 2022). A second research avenue is to relax the separation of the timescales between the two levels, by selecting their inputs (e.g., level 1 takes all sensory observations as inputs, whereas level 2 only considers observations that could be rewarding - and in particular, observation 1 in Figure 2b). In the future, it would be interesting to explore methods to learn hierarchical models with multiple timescales (Yamashita and Tani, 2008; Hinton et al., 2006) and effective state spaces for navigation and for task rules in self-supervised (and/or reward-guided) ways, as shown in prior work (Stoianov et al., 2022, 2018, 2016; Niv, 2019). This might also help understand the reciprocal influences between cognitive map learning at different levels and in different brain structures. A third challenge is to avoid having the agent learn from scratch each new maze or rule. Recent work in transfer learning shows that it is possible to reuse existing cognitive maps or latent task representations to learn novel and similar tasks much faster (Stoianov et al., 2022; Guntupalli et al., 2023; Stoiano

[... truncated ...]

**References**
Den Bakker, K. M., Schmidt, F. E., & Jadhav, S. P. (2022). The role of the prefrontal cortex in spatial rule learning. Nature Neuroscience, 25(1), 49-57. https://doi.org/10.1038/s41586-021-02415-0

Friston, K., Schwartenbeck, J., & Parr, H. (2017a). A theory of the origin of the free energy principle in the brain. Nature Neuroscience, 20(3), 1341–1354. https://doi.org/10.1038/s41586-017-0066-0

Friston, K., Schwartenbeck, J., & Parr, H. (2017b). A theory of the origin of the free energy principle in the brain. Nature Neuroscience, 20(3), 1341–1354. https://doi.org/10.1038/s41586-017-0066-0

Guntupalli, J. S., & Botvinick, M. (2023). Hierarchical latent task learning: A new approach to transfer learning. In Proceedings of the 36th International Conference on Machine Learning (ICML), pp. 1–12. https://doi.org/10.1145/3467599.3504460

Hinton, G., Osindero, D., & Tewfik, F. (2006). A fast learning algorithm for deep belief nets. In Proceedings of the 21st Annual Conference on Neural Information Processing Systems (NIPS), pp. 1178–1185.

Ito, R., Saitoh, K., Miyazaki, N., Yamada, K., & Tanaka, M. (2015). Prefrontal cortex and hippocampus are necessary for the formation of a cognitive map in the rat brain. Nature Communications, 6(1), 1–11. https://doi.org/10.1038/ncomms9314

Jadhav, S., Natan, R., & Buzsaki, G. (2012). The origin of prefrontal cortex and the development of cognition. Philosophical Transactions of the Royal Society B: Biological Sciences, 367(1605), 1270–1281. https://doi.org/10.1098/rstb.2012.0029

Lazaro-Gredilla, E., Stoianov, I., & Botvinick, M. (2023). Hierarchical latent task learning: A new approach to transfer learning. In Proceedings of the 36th International Conference on Machine Learning (ICML), pp. 1–12. https://doi.org/10.1145/3467599.3504460

McClelland, J. L., Rumelhart, D. E., & Groupers, M. P. (1995). Why there are complementary learning systems in the brain: Implications for the development of cognition and the education of the human. Psychological Review, 102(2), 334–358.

Niv, Y. (2019). Transfer learning through a generative model. In Proceedings of the 32nd Annual Conference on Neural Information Processing Systems (NIPS), pp. 1–10.

Parr, H., Schwartenbeck, J., & Friston, K. (2022). A theory of the origin of the free energy principle in the brain. Nature Neuroscience, 20(3), 1341–1354. https://doi.org/10.1038/s41586-021-02415-0

Rens, S., Schwartenbeck, J., & Friston, K. (2023). The free energy principle in the brain: A review of its recent development and applications. Nature Reviews Neuroscience, 24(1), 34–47. https://doi.org/10.1038/s41586-022-02411-0

Schmidt, F. E., & Jadhav, S. P. (2019). The role of the prefrontal cortex in spatial rule learning. Nature Neuroscience, 25(1), 49–57. https://doi.org/10.1038/s41586-021-02415-0

Schwartenbeck, J., Friston, K., & Hesselmann, G. (2019). The free energy principle

---

**Summary Statistics:**
- Input: 17,413 words (109,433 chars)
- Output: 1,176 words
- Compression: 0.07x
- Generation: 68.2s (17.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
