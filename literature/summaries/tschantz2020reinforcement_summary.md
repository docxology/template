# Reinforcement Learning through Active Inference

**Authors:** Alexander Tschantz, Beren Millidge, Anil K. Seth, Christopher L. Buckley

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [tschantz2020reinforcement.pdf](../pdfs/tschantz2020reinforcement.pdf)

**Generated:** 2025-12-03 03:37:28

---

**Overview/Summary**

The paper "Reinforcement Learning through Active Inference" presents a novel approach to reinforcement learning (RL) by applying the active inference framework in the context of deep probabilistic models. The authors argue that the traditional RL paradigm is based on an incorrect assumption about the nature of the environment, and they provide a new perspective for understanding the role of the agent's beliefs in the process of decision-making. In particular, the paper shows how to apply the active inference framework to model-based reinforcement learning (RL) by using a probabilistic transition model as the state predictor. The authors also show that the use of an ensemble- based approach is consistent with the active inference paradigm and has several advantages over the traditional single-model approaches.

**Key Contributions/Findings**

The key contributions of this paper are twofold: First, it provides a new perspective for understanding the role of the agent's beliefs in the process of decision-making. The authors show that the traditional RL paradigm is based on an incorrect assumption about the nature of the environment. Second, they provide a novel approach to model-based reinforcement learning by using a probabilistic transition model as the state predictor.

**Methodology/Approach**

The paper implements the probabilistic models using an ensemble- based approach. The authors use an ensemble of point-estimate parameters θ= {θ0,...,θB} trained on different batches of the dataset Dare maintained and treated as samples from the posterior distribution p(θ|D). Besides consistency with the active inference framework, this probabilistic model enables the active resolution of model uncertainty, capture both epistemic and aleatoric uncertainty, and help avoid over-ﬁtting in low data regimes. This design choice means that we use a trajectory sampling method when evaluating beliefs about future variables (Chua et al., 2018a). Here, an ensemble of point-estimate parameters θ= {θ0,...,θB} trained on different batches of the dataset Dare maintained and treated as samples from the posterior distribution p(θ|D) is used. Besides consistency with the active inference framework, this probabilistic model enables the active resolution of model uncertainty, capture both epistemic and aleatoric uncertainty, and help avoid over-ﬁtting in low data regimes (Fort et al., 2019; Chitta et al., 2018). The transition model is implemented as p(st|st−1,θ,π) as N(st; fθ(st−1),fθ(st−1)), where fθ(·) are a set of function approximators fθi(·)= {fθ0(·),...,f θB(·)}. In the current paper, fθi(st−1) is a two- layer feed-forward network with 400 hidden units and swish activation function. Following previous work (Shyam et al., 2018), the authors predict state deltas rather than the next states (Shyam et al., 2018). The reward model is implemented as p(oτ|sτ,θ,π) = N(oτ; fλ(sτ),1), where fλ(·) are some arbitrary function approximators. In the current paper, fλ(·) is a two layer feed-forward network with 400 hidden units and ReLU activation function. Learning a reward model offers several plausible beneﬁts outside of the active inference framework, as it abolishes the requirement that rewards can be directly calculated from observations or states (Chua et al., 2018a). The global prior is implemented as pΦ(o) as a Gaussian with unit variance centred around the maximum reward for the respective environment. The authors leave it to future work to explore the effects of more intricate priors.

**Results/Data**

The authors list the full set of hyperparameters below: Hyperparameters
Hidden layer size 400
Learning rate 0.001
Training-epochs 100
Planning-horizon 30
N-candidates (CEM) 700
Top-candidates (CEM) 70
Optimisation-iterations (CEM) 7

**Limitations/Discussion**

The authors do not discuss the limitations of their work. However, it is clear that the paper has several potential limitations. First, the use of an ensemble-based approach may lead to a high computational cost. Second, the use of an ensemble-based approach in the current paper may make it difficult to understand the role of the information gain term in the active inference framework. The authors provide a simple application of Bayes' rule to derive the expected information gain as the divergence between the state likelihood and marginal, given the parameters, which decomposes into an entropy of an average minus an average of entropies (Eq. 13). Unfortunately, this term does not have an analytical solution. However, it can be approximated numerically using a variety of techniques for entropy estimation. In their paper, they use the nearest neighbour entropy approximation (Mirchev et al., 2018).

**Environment Details**

The Mountain Car environment ( S⊆ R2A⊆ R1) requires an agent to drive

[... truncated for summarization ...]

=== END OF PAPER CONTENT ===

---

**Summary Statistics:**
- Input: 7,391 words (50,765 chars)
- Output: 719 words
- Compression: 0.10x
- Generation: 41.9s (17.1 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
