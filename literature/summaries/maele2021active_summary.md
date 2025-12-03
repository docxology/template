# Active Vision for Robot Manipulators Using the Free Energy Principle

**Authors:** Toon Van de Maele, Tim Verbelen, Ozan Çatal, C. D. Boom, B. Dhoedt

**Year:** 2021

**Source:** semanticscholar

**Venue:** Frontiers in Neurorobotics

**DOI:** 10.3389/fnbot.2021.642780

**PDF:** [maele2021active.pdf](../pdfs/maele2021active.pdf)

**Generated:** 2025-12-02 07:17:50

---

**Overview/Summary**

The paper introduces an active vision framework for a robot manipulator to select viewpoints in order to learn about its environment and to manipulate objects. The authors propose the free energy principle (FEP) to determine the best viewpoint, which is different from the expected free energy principle used in computer vision. They also introduce an aggregation strategy for the approximate posterior distribution that can be computed efficiently.

**Key Contributions/Findings**

The main contributions of this paper are:
1. The authors propose a new active vision framework based on the FEP and the aggregation strategy.
2. The FEP is different from the expected free energy principle used in computer vision, which is a well-known concept that can be found in many papers. In the FEP, the agent's internal model of the environment is updated by an observation, but it does not update the state distribution entirely. Instead, the FEP updates the mean and variance of the approximate posterior distribution.
3. The aggregation strategy for the approximate posterior is a key component of this paper. This strategy can be computed efficiently.

**Methodology/Approach**

The authors first learn the model parameters from a prerecorded dataset. Then, they use these learned model parameters in the proposed active vision scheme to select viewpoints and to manipulate the objects. The model architecture for the FEP is identical to the one used in the previous experiments, but with 256 latent state space dimensions.

**Results/Data**

The authors design two cases for the active vision experiments in the robotic workspace. In the first case, they put an additional constraint on the height of the agent and only allow the agent to move in the x and y direction of the workspace, i.e., parallel with the table. They choose this to limit the potential viewpoints of the agent to observe the epistemic and instrumental behavior in more detail, with respect to the imagined views. In the second case, they allow the agent to also move along the z-axis. We can now evaluate the global behavior of the agent and observe that when it explores a new area, it will first prefer viewpoints from higher vantage points in which it can observe a large piece of the workspace, after which it will move down to acquire more detailed observations.

**Limitations/Discussion**

The authors do not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 15,212 words (91,787 chars)
- Output: 388 words
- Compression: 0.03x
- Generation: 25.2s (15.4 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
