# Active Inference for Stochastic Control

**Authors:** Aswin Paul, Noor Sajid, Manoj Gopalkrishnan, Adeel Razi

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1007/978-3-030-93736-2_47

**PDF:** [paul2021active.pdf](../pdfs/paul2021active.pdf)

**Generated:** 2025-12-03 03:23:30

---

**Overview/Summary**

The paper "Active Inference for Stochastic Control" by A. Paul et al. presents a novel approach to control problems in partially observable Markov decision processes (POMDPs) using active inference. The authors first introduce the concept of active inference and its connection with dynamic programming, and then apply it to solve the finite-horizon POMDP problem. They show that the value function obtained by active inference is exactly the same as the value function for the finite-horizon optimal policy in the sense of the total expected reward. The authors also compare their approach with Q-learning and deep deterministic policy gradient (DDPG) methods, and demonstrate the effectiveness of the proposed method on a grid-world problem.

**Key Contributions/Findings**

The main contributions of this paper are as follows:
- A new algorithm for solving finite-horizon POMDPs based on active inference. The authors show that the value function obtained by active inference is exactly the same as the value function for the finite-horizon optimal policy in the sense of the total expected reward.
- The proposed method can be used to solve both the non-stochastic and stochastic control problems, but it is more effective when the transition probability is unknown. The authors compare their approach with Q-learning and DDPG methods on a grid-world problem.

**Methodology/Approach**

The paper starts by introducing the concept of active inference. In this context, active inference is defined as a process that takes into account both the dynamics of the system and the uncertainty in the observations. The authors then apply it to solve the finite-horizon POMDP problem. They show that the value function obtained by active inference is exactly the same as the value function for the finite-horizon optimal policy in the sense of the total expected reward. In order to solve a POMDP, an agent must be able to make decisions based on its current belief about the state and the outcome of the next action. The authors propose a new algorithm that can be used to solve both the non-stochastic and stochastic control problems. However, it is more effective when the transition probability is unknown.

**Results/Data**

The results section of this paper presents the performance comparison between the proposed method and Q-learning/DDPG methods on a grid-world problem. The authors use the "SPM_ MDP_XX.m" software tool to generate the POMDPs and the MDPs, which are used to evaluate the success rate for the active inference agent. The results show that the value function obtained by the proposed method is exactly the same as the value function for the finite-horizon optimal policy in the sense of the total expected reward. One of the output from "SPM_ MDP_XX.m" is "MDP .P". This distribution was used to conduct multiple trails to evaluate the success rate of the active inference agent.

**Limitations/Discussion**

The paper does not discuss any limitations or future work, but it mentions that the proposed method can be used to solve both the non-stochastic and stochastic control problems. The authors also compare their approach with Q-learning/DDPG methods on a grid-world problem. This comparison shows the effectiveness of the proposed method.

**References**

[1] Lancelot Da Costa, Thomas Parr, Noor Sajid, Karl Friston, Sophisticated Inference. Neural Comput 2021;33(3):713–763

[2] Lancelot Da Costa, Noor Sajid, Thomas Parr, Karl Friston, The relationship between dynamic programming and active inference: the discrete, finite-horizon case., arXiv 2009.08111, 2020.

[3] Lancelot Da Costa, Thomas Parr, Noor Sajid, Karl Friston, Deep Active Inference Agents using Monte-Carlo methods. arXiv preprin t arXiv:2006.04176, 2020.

[4] Zafeirios Fountas, Noor Sajid, Pedro AM Mediano, Karl Friston, Sophisticated Inference. Neural Comput 2021;33(3):713–763

[5] Lancelot Da Costa and Noor Sajid and Thomas Parr and Karl Friston and Ryan Smith:, The relationship between dynamic programming and active inference: the discrete, finite-horizon case., arXiv e-prints, 2020.

[6] Karl Friston and FitzGerald, Thomas and Rigoli, France sco and Schwartenbeck, Philipp and Pezzulo, Giovanni: Active inference: a process theory. Neu ral computation 29(1), 1–49 (2017)

[7] Sutton, R., Barto, A.: Reinforcement Learning: An Intro duction. MIT Press 2018.

[8] Karl Friston and FitzGerald, Thomas and Rigoli, France sco and Schwartenbeck, Philipp and Pezzulo, Giovanni: Active inference: a process theory. Neu ral computation 29(1), 1–49 (2017)

[9] Lancelot Da Costa and Noor Sajid and Thomas Parr and Karl Friston and Ryan Smith:, The relationship between dynamic programming and active inference: the discrete, finite-horizon case., arXiv e-prints, 2020.

[10] Da Costa, L., Parr, T., Sajid, N., V eselic, S., Neacsu, V., and Friston, K.: Active inference on discrete state-spaces: a synthesis”, arXiv e-prints, 2020.

---

**Summary Statistics:**
- Input: 4,562 words (27,633 chars)
- Output: 743 words
- Compression: 0.16x
- Generation: 43.7s (17.0 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
