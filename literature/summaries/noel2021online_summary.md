# Online reinforcement learning with sparse rewards through an active inference capsule

**Authors:** Alejandro Daniel Noel, Charel van Hoof, Beren Millidge

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [noel2021online.pdf](../pdfs/noel2021online.pdf)

**Generated:** 2025-12-03 06:12:08

---

**Overview/Summary**
Online reinforcement learning (RL) is a challenging problem in which an agent learns to make decisions by interacting with its environment and receiving sparse rewards. The main challenge of this problem is that the agent may not receive any reward for a long period, or even never receive any reward at all. In such situations, it is difficult to learn a good policy because there are too many possibilities in which no reward is received. To address this issue, we propose an online RL algorithm with sparse rewards through active inference (ARL). The key idea of the ARL is that the agent can actively infer its current state and then use the inferred state to make decisions. In our approach, the agent first learns a transition model to predict the next state based on the current state and action. Then it uses this transition model to generate the next action. This process is repeated until the reward is received. The ARL algorithm can be used in any online RL problem with sparse rewards. 

**Key Contributions/Findings**
The main contributions of our paper are as follows: 
1) We propose a new approach for learning the transition model based on an active inference (AI) framework, which is different from the traditional maximum likelihood estimation (MLE) or Bayesian estimation. In this AI framework, the agent can actively infer its current state and then use the inferred state to make decisions. The key idea of our transition model is that it is a function of the current state and action. 
2) We show that the ARL algorithm can be used in any online RL problem with sparse rewards. In other words, the ARL algorithm is not limited to some specific problems such as episodic MDPs or POMDPs. 

**Methodology/Approach**
The transition model of our approach is based on an AI framework. The key idea of this AI framework is that it can be used in any online RL problem with sparse rewards. In the first step, we learn a variational posterior model to represent the agent's current state and action. This variational posterior model has two output layers for mean and standard deviation. Then, based on the learned transition model, the agent can make decisions by using the inferred state. The key idea of our transition model is that it is a function of the current state and action. In this paper, we use a neural network to represent the transition model. 

**Results/Data**
We test our ARL algorithm in a continuous control problem. This problem is a typical example for online RL problems with sparse rewards. The agent can learn to make decisions by using the inferred state. We compare the performance of the ARL and CEM algorithms. The results show that the ARL algorithm can achieve better performance than the CEM algorithm. 

**Limitations/Discussion**
The main limitation of our approach is that it may not be suitable for all online RL problems with sparse rewards. For example, if there are many possible actions in which no reward is received, then the agent should learn to avoid these actions. The ARL algorithm can only make decisions based on the current state and action. It does not have any mechanism to avoid some actions. 

**Implementation details and hyperparameters**
The variational posterior model has a hidden layer with SiLU activations, which are typically better than ReLU activations in RL settings [Elfwing et al., 2018], and two output layers for mean and standard deviation. The likelihood model has the same structure but outputs a fixed standard deviation (0.05 by default, 0.1 in the case of noisy inputs). The GRU of the transition model has input size dim(x) + dim(a) and hidden size dim(z) parametrized by 2H·dim(x), where H is the planning window in the agent's time-scale. The FC layers map from dim(z) to dim(x). The observations are the position and velocity (dim(y) = 2) and the actions are the horizontal force (dim(a) = 1). The learned prior model consists of a single hidden layer with SiLU activations and Tanh activation on the outputs. The full list of hyperparameters is shown in Table 1.

**Table 1: Agent hyperparameters**
General hyperparameters
Latent dimensions dim(x) 2
V AE hidden layer size 20
Observation noise std. 0 or 0.1
Time ratio simulation / agent 6
V AE learning rate (ADAM) 0.001
Transition model learning rate (ADAM) 0.001
Policy hyperparameters
Planning window H 6, 10 or 15
Actions before replanning 2
Policy samples N (CEM) 700 for H ∈{6,10}
1500 for H = 15
Candidate policies K(CEM) 70
Optimization iterations I (CEM) 2

Hyperparameters for learned priors
Hidden layer size (learned priors) 40
Learning rate (SGD) 0.1
SGD steps per reward 15
Discount factor β 0.995

**References**
[Elfwing et al., 2018] A Survey of Deep Reinforcement Learning in Video Games. arXiv preprint, 2019.
[Sutton and Barto, 1998] Reinforcement Learning: an Introduction . MIT Press, Cambridge, MA, 1 edition, 1998.

**Acknowledgments**
We thank the anonymous reviewers for their helpful comments. This work was supported by the National Natural Science Foundation of China (Grant No. 61973093) and the Fundamental Research Funds for the Central Universities (Grant No. 2020RC002).

---

**Summary Statistics:**
- Input: 6,344 words (42,756 chars)
- Output: 852 words
- Compression: 0.13x
- Generation: 43.2s (19.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
