# Deep active inference agents using Monte-Carlo methods

**Authors:** Zafeirios Fountas, Noor Sajid, Pedro A. M. Mediano, Karl Friston

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [fountas2020deep.pdf](../pdfs/fountas2020deep.pdf)

**Generated:** 2025-12-03 05:13:30

---

**Overview/Summary**
The paper introduces a novel deep reinforcement learning (RL) agent that uses Monte-Carlo methods for inference and control. The agent is based on the active inference framework, which posits that the brain's function is to infer its own internal state given sensory input. This is in contrast with the more traditional RL approach of using the environment as an external source of information. In this paper, the authors present a deep neural network-based implementation of this idea and show how it can be used for control. The main contribution is the use of Monte-Carlo methods to perform inference and control. The agent uses a transition model (a forward model) to predict its own internal state given an observation, but also has access to a world model that predicts observations from any given state. This allows the agent to make predictions about the future based on what it can observe now. The authors compare this with the traditional approach of using only the environment as a source of information and show how the new method performs better in some cases.

**Key Contributions/Findings**
The main contributions are the use of Monte-Carlo methods for inference and control, and the use of an internal model to make predictions about the future. The authors also provide a number of other results, including that the agent is able to learn from delayed rewards, and that it can be used in continuous time domains. The authors show how their approach performs better than traditional RL approaches in some cases.

**Methodology/Approach**
The authors use the active inference framework as the basis for their work. This involves using a forward model (a transition model) to predict the agent's internal state given an observation, and also have access to a world model that can be used to make predictions about future observations. The authors show how this allows them to perform better than traditional RL approaches in some cases.

**Results/Data**
The authors compare their method with a number of other methods. They use a set of standard continuous control problems as the testbed, and show that the agent is able to learn from delayed rewards. They also provide results for both discrete and continuous time domains. The authors show how they are able to perform better than traditional RL approaches in some cases.

**Limitations/Discussion**
The authors discuss a number of limitations with their work. These include that it does not scale well, and that the agent is not able to learn from delayed rewards in all cases. They also mention that there are other ways to use the internal model for control, which they do not explore.

**References**
[1] Levine, S., 2018. Reinforcement learning and control as probabilistic inference: Tutorial and review. arXiv preprint arXiv:1805.00909 [cs.LG].

---

**Summary Statistics:**
- Input: 9,939 words (58,989 chars)
- Output: 457 words
- Compression: 0.05x
- Generation: 28.2s (16.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
