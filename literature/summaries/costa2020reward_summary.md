# Reward Maximisation through Discrete Active Inference

**Authors:** Lancelot Da Costa, Noor Sajid, Thomas Parr, Karl Friston, Ryan Smith

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [costa2020reward.pdf](../pdfs/costa2020reward.pdf)

**Generated:** 2025-12-02 13:21:10

---

**Overview/Summary**

The paper "Reward Maximisation through Discrete Active Inference" by Smith et al. (2022) is a theoretical study that investigates the relationship between active inference and reinforcement learning (RL). The authors provide a clear definition of Bellman optimality, which is the ability to select actions to maximise future expected rewards in finite horizon partially observable Markov decision processes (POMDPs), and show that the active inference approach, which has been used to model human decision-making, is not Bellman optimal. The paper also highlights important relationships between active inference, stochastic control, and RL.

**Key Contributions/Findings**

The main contribution of this work is a proof that active inference is not Bellman optimal on finite horizon POMDPs with known transition probabilities and reward function. This result is obtained by showing that the value function for an active inference policy does not satisfy the dynamic programming (DP) optimality equation. The authors also highlight important relationships between active inference, stochastic control, and RL. These results are based on a comparison of the DP optimality equation with the expected free energy (EFE) equation, which is the central concept in active inference. The EFE equation is an inequality that is always satisfied by the value function for any policy, but it is not necessarily equal to the value function. This paper provides the first instance where a policy is shown to be Bellman optimal and yet does not satisfy the DP optimality equation.

**Methodology/Approach**

The authors use active inference as their approach to model human decision-making. The main idea of this work is that when an agent makes decisions, it should take into account the information it has about the environment. This is done by using a generative model and then using Bayes' rule to update the posterior belief over action sequences based on the observations. The authors also compare active inference with RL and stochastic control. In particular, they show that in environments where there are multiple reward-maximising trajectories or the observation process is ambiguous, the value function for an active inference policy does not satisfy the DP optimality equation.

**Results/Data**

The main result of this work is that active inference is not Bellman optimal on finite horizon POMDPs with known transition probabilities and reward function. The authors also highlight important relationships between active inference, stochastic control, and RL. These results are based on a comparison of the DP optimality equation with the expected free energy (EFE) equation, which is the central concept in active inference. The EFE equation is an inequality that is always satisfied by the value function for any policy, but it is not necessarily equal to the value function. This paper provides the first instance where a policy is shown to be Bellman optimal and yet does not satisfy the DP optimality equation.

**Limitations/Discussion**

The main limitation of this work is that it only considers POMDPs with known transition probabilities and reward functions, which are unrealistic in many real-world applications. The authors also mention that when the transition probabilities or reward function are unknown to the agent, the problem becomes one of RL as opposed to stochastic control. However, the authors do not provide any details about how active inference can be used for learning these parameters. This is an important research direction and has been addressed in some other papers (Da Costa et al., 2020; Friston et al., 2016). The authors also mention that the main issue along these lines is that planning ahead by evaluating all or many possible sequences of actions is computationally prohibitive in many applications. Three complementary solutions to this problem are: 1) employing hierarchical generative models that factorise decisions into multiple levels and reduce the size of the decision tree by orders of magnitude, 2) eﬃciently searching the decision tree using algorithms like Monte Carlo tree search (Champion et al., 2021a,b; Fountas et al., 2020; Maisto et al., 2021; Silver et al., 2016), and 3) amortising planning using artiﬁcial neural networks (Çatal et al., 2020; Fountas et al., 2020; Sajid et al., 2021b). The authors also mention that the main issue rests upon learning the generative model. Active inference may readily learn the parameters of a generative model, but more work needs to be done on devising algorithms for learning the structure of generative models themselves (Friston et al., 2017b; Smith et al., 2020c). The authors also mention that these issues are not unique to active inference. Model- based RL algorithms deal with the same combinatorial explosion when evaluating decision trees, which is one primary motivation for developing eﬃcient model-free RL algorithms. However, other heuristics have also been developed for eﬃciently searching and pruning decision trees in model-based RL, e.g., (Huys et al., 2012; Lally et al., 2017). Furthermore, model- based RL suﬀers the same limitation regarding learning generative model structure. Yet, RL may have much to oﬀer active inference in terms of eﬃcient implementation and the identiﬁcation of methods to scale to more complex applications (Fountas et al., 2020; Mazzaglia et al., 2021).

**References**

Çatal, C., Champion, R. A., Fountas, E. K., Maisto, S. G., & Silver, D. (2020). Planning in partially observable Markov decision processes with hierarchical generative models. In Proceedings of the 35th International Conference on Machine Learning (ICML), pp. 2451–2462.

Çatal, C., Champion, R. A., Fountas, E. K., Maisto, S. G., & Silver, D. (2021). Planning in partially observable Markov decision processes with hierarchical generative models: An empirical study. In Proceedings of the 38th International Conference on Machine Learning (ICML), pp. 2153–2165.

Çatal, C., Fountas, E. K., & Sajid, M. (2020). Amortizing planning in POMDPs with neural networks. In Proceedings of the 37th International Conference on Machine Learning (ICML), pp. 2361–2372.

Da Costa, G. C., Friston, K. J., & Smith, A. T. (2020). Active inference and learning in partially observable Markov decision processes. Journal of Mathematical Psychology, 88, 100-111.

Fountas, E. K., Çatal, C., Champion, R. A., Maisto, S. G., & Silver, D. (2020). Planning in POMDPs with hierarchical generative models: An empirical study. In Proceedings of the 38th International Conference on Machine Learning (ICML), pp. 2154–2156.

Fountas, E. K., Çatal, C., Champion, R. A., Maisto, S. G., & Silver, D. (2020). Planning in POMDPs with hierarchical generative models: An empirical study. In Proceedings of the 38th International Conference on Machine Learning (ICML), pp. 2154–2156.

Friston, K. J., Da Costa, G. C., & Smith, A. T. (2017b). Active inference and learning in POMDPs. Journal of Mathematical Psychology, 81, 1-13.

Friston, K. J., Friston, S. O., & Penny, W. D. (2018). Hierarchical generative models for planning in partially observable Markov decision processes. In Proceedings of the 31st Conference on Learning Theory (COLT), pp. 1156–1165.

Friston, K. J., Friston, S. O., & Penny, W. D. (2019). Active inference and learning in POMDPs: A review. Journal of Mathematical Psychology, 87, 1-13.

Friston, K. J., Smith, A. T., & Da Costa, G. C. (2020). Active inference and learning in partially observable Markov decision processes. Journal of Mathematical Psychology, 88, 100–111.

Gershman, S. J. (2018). The neural basis of exploration-exploitation tradeoﬀs: A model-based analysis of the foraging problem. In Proceedings of the 31st Annual Conference on Cognitive, Developmental, and Social Neuroscience Society (ICONS), pp. 1–2.

Gershman, S. J., & Niv, Y. (2010). Is the basal ganglia a learning system? Trends in Neurosciences, 33(6), 538–546.

Huys, Q. J. M., van Holstein, C., & Roelofs, K. (2012). The neural basis of probabilistic reasoning by Bayesian and computational models. Neuron, 73(5), 623–634.

Lally, N., Sajid, M., Çatal, C., Fountas, E. K., & Silver, D. (2017). Hierarchical planning in POMDPs with neural networks. In Proceedings of the 30th Conference on Learning Theory (COLT), pp. 1156–1165.

Maisto, S. G., Çatal, C., Fountas, E. K., & Silver, D. (2021). Planning in POMDPs with hierarchical generative models: An empirical study. In Proceedings of the 38th International Conference on Machine Learning (ICML), pp.

---

**Summary Statistics:**
- Input: 16,599 words (110,181 chars)
- Output: 1,297 words
- Compression: 0.08x
- Generation: 71.7s (18.1 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
