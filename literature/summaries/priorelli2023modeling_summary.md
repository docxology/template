# Modeling motor control in continuous-time Active Inference: a survey

**Authors:** Matteo Priorelli, Federico Maggiore, Antonella Maselli, Francesco Donnarumma, Domenico Maisto, Francesco Mannella, Ivilin Peev Stoianov, Giovanni Pezzulo

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1109/TCDS.2023.3338491

**PDF:** [priorelli2023modeling.pdf](../pdfs/priorelli2023modeling.pdf)

**Generated:** 2025-12-03 03:44:38

---

**Overview/Summary**

The paper presents a unified Active Inference (AI) model for both goal-directed motor behavior and unintentional motor adjustments that arise from multisensory conflicts associated with self-perception. The authors use the classic rubber hand illusion as a paradigm to study how the brain processes its own bodily state, and in particular, how this processing can influence intentional actions. The paper is organized into three sections: Introduction, Methodology/Approach, and Results/Data.

**Key Contributions/Findings**

The main contribution of the paper is that it provides a unified AI model for both goal-directed motor behavior and unintentional motor adjustments that arise from multisensory conflicts associated with self-perception. The authors show that this single model can account for different types of intentional actions, such as reaching to a target, and unintentional motor adjustments that are often seen in the context of an ownership illusion. This is achieved by setting the attractor (i.e., the desired state) of the internal model to either the current arm configuration or the target location, depending on whether the agent has a goal to reach or not. The authors also show that this single model can account for different types of unintentional motor adjustments, such as the alignment of the physical hand with its visual counterpart during an ownership illusion and the reaching under visuo-proprioceptive conflict.

**Methodology/Approach**

The paper presents a 1-DoF (degree-of-freedom) agent whose configuration is uniquely described by its elbow's joint angle and angular velocity. The internal model of the arm dynamics, fµ(µθ, µθT), is a damped oscillator where the attractor is either set to the arm configuration µθT in which the hand is on target (for reaching actions) or to the current state when the agent has no intention to move. The internal estimate of the sensory noise in the visual domain is increased to roughly account for the fact that while undergoing an ownership illusion the agent is still aware that its own bodily state is not matching with the visual one. In this paper, the authors assume that the ownership illusion is in place by treating the visual input from the fake hand as if

---

**Summary Statistics:**
- Input: 14,823 words (94,879 chars)
- Output: 348 words
- Compression: 0.02x
- Generation: 70.3s (4.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
