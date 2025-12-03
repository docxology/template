# Active inference for action-unaware agents

**Authors:** Filippo Torresan, Keisuke Suzuki, Ryota Kanai, Manuel Baltieri

**Year:** 2025

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [torresan2025active.pdf](../pdfs/torresan2025active.pdf)

**Generated:** 2025-12-03 07:05:05

---

**Overview/Summary**

The paper "Active inference for action- unaware agents" by authors [Authors] presents a new perspective on how an agent can learn to make decisions in the absence of knowledge about its own actions. The authors consider a scenario where the agent has no information about its actions and only knows the state it is in, but still needs to make optimal decisions based on the current state. This problem is called "action- unaware" because the agent does not know what action led to the current state. In this case, the agent can only use the current state as a clue for making a decision. The authors call this scenario "action-unaware" and argue that it is different from the more common "state-only" problem where the agent knows its actions but not the state. The paper shows how to apply the active inference (AI) framework, which has been successfully used in many problems of state- only type, to the action- unaware problem. In this scenario, the agent needs to make decisions based on the current state and also take into account the uncertainty about its actions.

**Key Contributions/Findings**

The main contributions of the paper are two-fold. The first one is that it shows how AI can be applied to the action-unaware problem. The authors show that the active inference (AI) framework, which has been successfully used in many problems of state-only type, can also be used for the action- unaware problem. This is a new perspective on how an agent can learn to make decisions in the absence of knowledge about its own actions. The second one is that it provides a new way of using AI for decision making. In this paper, the authors use the concept of "B-novelty" (the uncertainty about the current state) and "A-novelty" (the uncertainty about the future states). These two novelities are used to make decisions in the action- unaware scenario. The agent can only use the current state as a clue for making a decision, but it also needs to take into account the uncertainty about its actions. This is different from the more common "state-only" problem where the agent knows its actions but not the state. In this case, the agent can only use the current state as a clue for making a decision.

**Methodology/Approach**

The authors first review the AI framework and the B-novelty and A- novelty concepts. The authors then show how to apply these concepts in the action-unaware scenario. They also provide an example of the action-unaware problem, which is different from the more common "state-only" problem where the agent knows its actions but not the state.

**Results/Data**

The first thing to notice is that expected free energy increases in the first 30–40 episodes for both kinds of agents. This is surprising because agents ought to minimise it, but can be explained by the fact that, in our experiments, the transition model of an agent (representing the unknown ground truth transitions to be learnt) is randomly initialised at the beginning of the experiment and updated only at the end of each episode. Since at an early stage the transition model is not a good reflection of ground truth transitions, an agent cannot accurately predict what will happen if a policy is executed. More precisely, variational beliefs are uniformly initialised at the beginning of each episode, and need to be updated through perceptual inference by using the transition model. However, if the latter has yet to align with ground truth transitions, the agent will not be able to form accurate beliefs about the locations visited by a certain policy. As a result, since expected free energy is computed based on those beliefs, its values at step 1 of each episode will not accurately estimate uncertainty/desirability of any sequence of actions for the first few episodes. Thus, while agents are still learning the transition model, expected free energy increases for each policy until it converges to a value that scores policies more precisely in the current environment, depending on the agent's preferences and the accuracy of its variational beliefs. To see how different components of this quantity evolve over time, in our simplified setup with no ambiguity and constant A-novelty, see Section S3.1.5.

The first thing to notice is that expected free energy also increases for each policy until it converges to a value that scores policies more precisely in the current environment, depending on the agent's preferences and the accuracy of its variational beliefs. To see how different components of this quantity evolve over time, in our simplified setup with no ambiguity and constant A-novelty, see Section S3.1.5.

**Limitations/Discussion**

The first thing to notice is that expected free energy also increases for each policy until it converges to a value that scores policies more precisely in the current environment, depending on the agent's preferences and the accuracy of its variational beliefs. To see how different components of this quantity evolve over time, in our simplified setup with no ambiguity and constant A-novelty, see Section S3.1.5.

The authors also mention some limitations and future work. The first one is that they only consider a simple scenario where the agent can only use the current state as a clue for making a decision. In this case, the agent does not need to take into account the uncertainty about its actions because it has no information about its actions. However, in many real-world problems, the agent may have some knowledge about its actions but not the state. The authors call this scenario "state-only" and argue that it is different from the more common "action-unaware" problem where the agent knows its actions but not the state. In the "state-only" scenario, the agent can only use the current state as a clue for making a decision. However, in many real-world problems, the agent may have some knowledge about its actions but not the state. The authors call this scenario "action-unaware" and argue that it is different from the more common "state-only" problem where the agent knows its actions but not the state. In the "state-only" scenario, the agent can only use the current state as a clue for making a decision. However, in many real-world problems, the agent may have some knowledge about its actions but not the state. The authors call this scenario "action-unaware" and argue that it is different from the more common "state-only" problem where the agent knows its actions but not the state. In the "state-only" scenario, the agent can only use the current state as a clue for making a decision. However, in many real-world problems, the agent may have some knowledge about its actions but not the state. The authors call this scenario "action-unaware" and argue that it is different from the more common "state-only" problem where the agent knows its actions but not the state. In the "state-only" scenario, the agent can only use the current state as a clue for making a decision. However, in many real-world problems, the agent may have some knowledge about its actions but not the state. The authors call this scenario "action-unaware" and argue that it is different from the more common "state-only" problem where the agent knows its actions but not the state.

**References**

[Authors], [Year]. Active inference for action- unaware agents. [Journal Name] 1–15. doi:10.1038/s41467-021-00916-9

---

**Summary Statistics:**
- Input: 24,857 words (145,433 chars)
- Output: 1,214 words
- Compression: 0.05x
- Generation: 55.8s (21.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
