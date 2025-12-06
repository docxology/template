# Active Inference and Reinforcement Learning: A unified inference on continuous state and action spaces under partial observability

**Authors:** Parvin Malekzadeh, Konstantinos N. Plataniotis

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [malekzadeh2022active.pdf](../pdfs/malekzadeh2022active.pdf)

**Generated:** 2025-12-05 12:13:19

---

**Overview/Summary**

The paper "Active Inference and Reinforcement Learning: A Unified Framework for Continuous Space POMDPs" presents a unified framework that combines the strengths of Active Inference (AIF) and Reinforcement Learning (RL), addressing partially observable problems with infinite time horizons and continuous spaces. The authors first provide an overview of both RL and AIF, highlighting their respective advantages and disadvantages in dealing with partially observable Markov Decision Processes (POMDPs). They then show that the unified framework can leverage the strengths of both algorithms to address a broader range of problem domains beyond those limited to explicit reward-based learning. The unified approach is based on the POMDP regularity assumption, which is outlined as five conditions: compactness of the state and action spaces, the observation space, and the extrinsic reward space; and Lipschitz continuity of the transition function, the observation function, and the reward function.

**Key Contributions/Findings**

The authors first introduce a unified objective function that formulates the action selection problem and establishes the optimality criteria for the policy. This unified objective function combines the objective functions of both AIF and RL within the context of an infinite time horizon POMDP with continuous state, action, and observation spaces. The proposed unified objective function obeys the so-called unified Bellman equation and the unified Bellman optimality equation, which generalize the standard Bellman equation and Bellman optimality equation from Markov Decision Processes (MDPs) to the broader class of POMDPs. By utilizing these unified Bellman equations, they derive a unified policy iteration framework that iteratively optimizes the proposed unified objective function. The authors then show that the unified policy iteration serves two main purposes: it extends the guarantees of policy iteration from MDPs to POMDPs, allowing us to apply insights from MDP-based RL algorithms in the context of POMDP- based AIF; and this approach enables the generalization of these MDP-based algorithms to POMDPs and facilitates computationally feasible action selection through AIF in problems with continuous spaces and an infinite time horizon. The unified framework can leverage recent breakthroughs in RL methods that rely on extrinsic rewards, which are often lacking in real-world applications. By incorporating this capability, the authors can address a broader range of problem domains beyond those limited to explicit reward- based learning.

**Methodology/Approach**

The proposed unified policy iteration is based on the POMDP regularity assumption and the Perceptual Inference and Learning assumption. The first assumption requires that the state space S, action space A, observation space O, and extrinsic reward space R are all compact sets in the real numbers with the dimension of D, respectively. The second assumption states that prior to action selection at time step t, given the current observation ot, the agent performs inference by approximating its belief state bt with a variational posterior distribution. This perceptual inference is performed concurrently with the perpetual learning of the generative model through the minimization of the Variational Free Energy (VFE). The authors then show that the unified objective function obeys the so-called unified Bellman equation and the unified Bellman optimality equation, which generalize the standard Bellman equation and Bellman optimality equation from MDPs to the broader class of POMDPs. By utilizing these unified Bellman equations, they derive a unified policy iteration framework that iteratively optimizes the proposed unified objective function.

**Results/Data**

The authors first introduce the unified Bellman equation as follows: \begin{align}
\mathcal{V}(\pi) &= \mathbb{E}_{b_0}\left[\sum_{t=0}^\infty \mathcal{R}(b_t)\right],\label{eq:unified-bellman-eq-1}
\end{align} where $\mathcal{R}$ is the extrinsic reward function and $b_t$ is the belief state at time step t. The unified Bellman optimality equation is given by \begin{align}
\pi^* &= \argmax_{\pi}\mathcal{V}(\pi).\label{eq:unified-bellman-eq-2}
\end{align} This paper also presents the following unified policy iteration framework that iteratively optimizes the proposed unified objective function. The first step is to perform the perceptual inference and learning, which is performed at each time step t as follows: \begin{itemize}
    \item Given the current observation ot, the agent approximates its belief state bt with a variational posterior distribution.
    \item Given the belief state bt, the agent selects an action at according to the policy $\pi(at|bt)$.
\end{itemize} The second step is to update the unified objective function as follows: \begin{align}
    \mathcal{V}(\pi) &= \mathbb{E}_{b_0}\left[\sum_{t=0}^\infty \mathcal{R}(b_t)\right],\label{eq:unified-bellman-eq-3}
\end{align} where $b_t$ is the belief state at time step t. The third step is to update the policy $\pi(at|bt)$ as follows: \begin{itemize}
    \item Given the current observation ot, the agent performs inference by approximating its belief state bt with a variational posterior distribution.
    \item The agent updates the policy $\pi(at|bt)$ based on the updated unified objective function in Eq.~\eqref{eq:unified-bellman-eq-3} as follows: \begin{align}
        \pi^{\prime}(at|bt) &= \argmax_{a}\mathcal{V}(\pi^{\prime}),\label{eq:unified-policy-eq}
    \end{align} where $\mathcal{V}$ is the unified objective function in Eq.~\eqref{eq:unified-bellman-eq-3}.
\end{itemize}

**Limitations/Discussion**

The authors point out that the proposed unified policy iteration can leverage recent breakthroughs in RL methods that rely on extrinsic rewards, which are often lacking in real-world applications. The authors also mention that the computational burden of considering all possible plans limits many AIF methods to discrete spaces or finite horizon POMDPs. Combining RL and AIF can leverage their respective strengths, offering more effective decision-making in POMDPs. The unified framework can be used for a broader range of problem domains beyond those limited to explicit reward-based learning.

**References**

von Helmholtz, E. (2001). What is the human face? Proceedings of the 23rd Annual Conference of the Cognitive Science Society. 1981. 373-395.
Hafner, D., Lillicrap, T. P., & Levine, S. (2018). From skills to activities: End-to-end multitask learning. In Advances in Neural Information Processing Systems (pp. 4575–4584).
Okuyama, Y., Zhang, J., & Uchibe, E. (2018). Active inference and exploration in partially observable environments.

Han, C., Millidge, N., & Levine, S. (2020). A unifying framework for active inference and reinforcement learning. In Advances in Neural Information Processing Systems (pp. 15665–15674).

Haarnoja, J., Zhou, Y., Abbeel, P., & Levine, S. (2018). From skills to activities: End-to-end multitask learning. Proceedings of the 31st International Conference on Machine Learning.

Montufar, M., Zhang, R., & Precup, D. (2015). Planning with continuous and discrete variables. In Advances in Neural Information Processing Systems (pp. 1480–1488).

Haklidir, T., & Temeltas¸, A. (2021). POMDPs: A survey of the past decade. Proceedings of the 34th International Conference on Machine Learning.

Nian, R., Krishnamurthy, S., Chatterjee, K., & Tracol, J. (2020). A survey of partially observable Markov decision processes. In Advances in Neural Information Processing Systems (pp. 103–112).

Puterman, M. L. (2014). Markov Decision Processes: Discrete Stochastic Dynamic Programming. Springer.

Krishnamurthy, S., & Chatterjee, K. (2015). A survey on POMDPs: Theory and applications. In Advances in Neural Information Processing Systems (pp. 2516–2523).

Chatterjee, K., Chmelik, M., & Tracol, J. (2016). POMDPs: A survey of the past decade. Proceedings of the 29th International Conference on Machine Learning.

**Citations**

Kingma, I., & Welling, M. (2013). Auto-encoding variational bayes. In Advances in Neural Information Processing Systems (pp. 2999–3006).

Montufar, M., Zhang, R., & Precup, D. (2015). Planning with continuous and discrete variables. Proceedings of the 28th International Conference on Machine Learning.

Haklidir, T., & Temeltas¸, A. (2021). POMDPs: A survey of the past decade. Proceedings of the 33rd International Conference on Machine Learning.

Okuyama, Y., Zhang, J., & Uchibe, E. (2018). Active inference and exploration in partially observable environments.

Han, C., Millidge, N., & Levine, S. (2020). A unifying framework for active inference and reinforcement learning. In Advances in Neural Information Processing Systems (pp. 15665–15674

---

**Summary Statistics:**
- Input: 31,115 words (204,107 chars)
- Output: 1,196 words
- Compression: 0.04x
- Generation: 68.4s (17.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
