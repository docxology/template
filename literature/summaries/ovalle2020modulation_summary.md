# Modulation of viability signals for self-regulatory control

**Authors:** Alvaro Ovalle, Simon M. Lucas

**Year:** 2020

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [ovalle2020modulation.pdf](../pdfs/ovalle2020modulation.pdf)

**Generated:** 2025-12-05 12:49:09

---

**Overview/Summary**

The paper presents a novel approach to self-regulation in reinforcement learning (RL) by modulating the exploration-exploitation trade-off using the expected free energy (EFE). The authors propose a new agent, EFE, that is based on the variational bound of the future value function. This agent uses an ensemble of neural networks to predict the next values of the state and the parameter of the distribution over which the expected free energy is defined. The key contribution is in the way the EFE agent modulates the exploration-exploitation trade-off by using a novel instrumental value, that is the surprisal (the negative log-likelihood) of the future value function. This paper also presents an alternative to the DQN algorithm, which is based on the variational bound of the Q-function. The authors compare these two agents in the Flappy Bird environment and show that the EFE agent outperforms the DQN agent.

**Key Contributions/Findings**

The main contributions of this work are:
- A new self-regulatory agent, EFE, which is based on the variational bound of the future value function. This agent uses an ensemble of neural networks to predict the next values of the state and the parameter of the distribution over which the expected free energy is defined.
- The authors compare the DQN and EFE agents in the Flappy Bird environment and show that the EFE agent outperforms the DQN agent.

**Methodology/Approach**

The authors present an alternative to the DQN algorithm, which is based on the variational bound of the Q-function. The authors also propose a new self-regulatory agent, EFE, which is based on the variational bound of the future value function. This agent uses an ensemble of neural networks to predict the next values of the state and the parameter of the distribution over which the expected free energy is defined.

**Results/Data**

The DQN and EFE agents are trained in the Flappy Bird environment. The authors compare these two agents in this environment and show that the EFE agent outperforms the DQN agent. The results reported in the paper were obtained with a small measurement bu (i.e., queue) of 20 and a replay buﬀer size of 6. The hyperparameters used for training are shown in the table below.

The DQN agent was trained to approximate with a neural network a Q-function Qφ({s,θ},.). For our case study s = o which contains the vector of features, while θ is the parameter corresponding to the current estimated statistics of p(v). An action is sampled uniformly with probability ϵ otherwise at  = minaQφ({st,θt},a). ϵ decays during training. The EFE agent was trained in a similar way as the DQN agent but it uses an ensemble of K neural networks to predict the next values of s and θ. The transition model p(st|st−1,φ,π  ) is implemented as a N({st,θt}; fφ(st−1,θt),fφ(st−1,θt,a)). Where a is an action of a current policy π with one- hot encoding and fφ is an ensemble of K neural networks which predicts the next values of s and θ. The surprisal model is also implemented with a neural network and trained to predict directly the surprisal in the future as fξ(st−1,θt−1,a). Where  = minaQφ({st,θt},a).

**Limitations/Discussion**

The authors do not discuss any limitations or potential future work.

---

**Summary Statistics:**
- Input: 4,913 words (32,362 chars)
- Output: 532 words
- Compression: 0.11x
- Generation: 31.0s (17.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
