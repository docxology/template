# Deep Active Inference as Variational Policy Gradients

**Authors:** Beren Millidge

**Year:** 2019

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [millidge2019deep.pdf](../pdfs/millidge2019deep.pdf)

**Generated:** 2025-12-02 13:39:01

---

**Overview/Summary**

The paper proposes a new approach to deep active inference (DAI) by casting it as variational policy gradients (VPG). The authors claim that the VPG formulation of DAI is more interpretable and provides an alternative perspective on the problem. This is achieved by using the VPG framework to derive the DAI update rules, which are then compared with the original DAI update rules in a theoretical analysis. The paper also compares the performance of the proposed approach with two baseline reinforcement learning algorithms (Q-learning and actor-critic) on three tasks from the OpenAI Gym.

**Key Contributions/Findings**

The main contributions of this work are:
1. A new perspective on the problem of DAI by using the VPG framework to derive the DAI update rules, which are then compared with the original DAI update rules in a theoretical analysis.
2. The proposed approach is competitive with the two baseline reinforcement learning algorithms (Q-learning and actor-critic) on three tasks from the OpenAI Gym.

**Methodology/Approach**

The paper starts by reviewing the current state of the art for DAI, which is to use the variational autoencoder (VAE) framework. The authors then propose a new approach that casts DAI as VPG and compare it with the original DAI update rules in a theoretical analysis. In the experimental section, the performance of the proposed approach is compared with two baseline reinforcement learning algorithms (Q-learning and actor-critic) on three tasks from the OpenAI Gym.

**Results/Data**

The paper compares the full Active Inference agent with two ablated versions. One model lacks the epistemic value component of the value function (see equation 19), and instead estimates the reward only, as in Q learning. The second model lacks the entropy term of the KL loss, and so only optimizes the policy by minimizing ∫Q(a|s)logp(a|s) without the entropy term. The results are plotted below:

The performance of the Active Inference agent was compared to two baseline reinforcement learning algorithms (Actor-Critic and Q-learn). Each agent began with randomly initialized neural networks and had to learn how to play from scratch, using only the state and reward data provided by the environment. We ran 20 trials of 15000 episodes each, and the mean reward the agent accumulated on each episode of the CartPole environment is plotted below:

The paper also compares the rewards obtained by the fully ablated Active Inference agent with standard reinforcement-learning baselines of Q-learn and Actor-Critic. The results are plotted below:

**Limitations/Discussion**

The main contribution to the success of the proposed approach is the entropy term in the loss function. Without the entropy term, the Active Inference agent converges to a lower mean reward which is comparable to the performance of the actor-critic and slightly better than the Q-learn algorithm.

**References**

[1] [2]

(No references cited)

Please note that

---

**Summary Statistics:**
- Input: 11,835 words (78,839 chars)
- Output: 458 words
- Compression: 0.04x
- Generation: 29.6s (15.4 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
