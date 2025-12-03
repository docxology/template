# Contrastive Active Inference

**Authors:** Pietro Mazzaglia, Tim Verbelen, Bart Dhoedt

**Year:** 2021

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [mazzaglia2021contrastive.pdf](../pdfs/mazzaglia2021contrastive.pdf)

**Generated:** 2025-12-02 12:45:33

---

**Overview/Summary**

Contrastive active inference (CAI) is a novel approach to learning generative models of the environment and making decisions in partially observable environments. The key insight behind CAI is that it learns to make decisions by optimizing an evidence bound on the expected free energy, which is the difference between the accuracy of the model and its complexity. This paper provides a detailed introduction to the CAI approach, including the theoretical foundations and the derivations of the equations provided in the original paper.

**Key Contributions/Findings**

The main contribution of this paper is the CAI algorithm that can be used to learn generative models of the environment for perception and make decisions. The key findings are the contrastive free energy (CFE) which is a bound on the expected free energy, the FAIF which is an upper bound on the CFE, and the FFAF which is a balance between the complexity and the accuracy.

**Methodology/Approach**

The approach to learning generative models of the environment for perception is based on the variational lower bound. The objective is to build a model of the environment for perception. Since computing the posterior p(ot) is intractable, we learn to approximate it with a variational distribution q(ot). This process provides an upper bound on the surprisal (-log evidence) of the model: −log p(ot) =−log
X
st
p(ot, st)
=−log
X
st
p(ot, st)q(ot)
q(ot)
=−log

Eq(st)

p(ot, st)
q(ot)

≤ −Eq(st)[log q(st) − log p(ot, st)]
where we applied Jensen's inequality in the fourth row. The free energy of the past can be mainly rewritten in two ways: F  = Eq(st)[log q(st) − log p(ot, st)] and DKL [q(st)||p(st|ot)]| {z} . The first expression highlights the evidence bound on the model's evidence, and the second expression shows the balance between the complexity of the state model and the accuracy of the likelihood one. From the latter, the FAIF (Equation 2) can be obtained by expliciting p(st) as p(st|st−1, at−1), according to the Markov assumption, and by choosing q(st) =q(st|ot) as the approximate variational distribution.

The approach to learning generative models of the environment for making decisions is based on the variational lower bound. The objective is to find the distributions of future states and actions. If we consider expectations taken over trajectories sampled from q(ot, st, at) =p(ot|st)q(st, at), the expected free energy G (Equation 3) becomes: G  = Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log p(st|ot) − log ˜p(ot)] . The agent's generative model is assumed to be biased towards its preferred outcomes, distributed according to the prior ˜p(ot), and we aim to
find the distributions of future states and actions by applying variational inference, with the variational distribution q(st, at). If we consider expectations taken over trajectories sampled from q(ot, st, at) =p(ot|st)q(st, at), the expected free energy G (Equation 3) becomes: G  ≈Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log q(st|ot) − log ˜p(ot)] . The agent's model likelihood over actions is assumed to be uniform and constant. Thus, we can rewrite the above result as: G ≈Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log q(st|ot) − log ˜p(ot)] . The CFE is a bound on the expected free energy. This means that if we use the CAI algorithm to learn the generative model of the environment for making decisions, the CFE will be an upper bound on the FFAF.

**Results/Data**

The paper provides the derivations of the equations provided in the original paper. The first part is about the free energy of the past and the second part is about the free energy of the future. For the past, the objective is to build a model of the environment for perception. Since computing the posterior p(ot) is intractable, we learn to approximate it with a variational distribution q(ot). This process provides an upper bound on the surprisal (-log evidence) of the model: −log p(ot)  =−log
X
st
p(ot, st)
=−log
X
st
p(ot, st)q(ot)
q(ot)
=−log

Eq(st)

p(ot, st)
q(ot)

≤ −Eq(st)[log q(st) − log p(ot, st)]
where we applied Jensen's inequality in the fourth row. The free energy of the past can be mainly rewritten in two ways: F  = Eq(st)[log q(st) − log p(ot, st)] and DKL [q(st)||p(st|ot)]| {z} . The first expression highlights the evidence bound on the model's evidence, and the second expression shows the balance between the complexity of the state model and the accuracy of the likelihood one. From the latter, the FAIF (Equation 2) can be obtained by expliciting p(st) as p(st|st−1, at−1), according to the Markov assumption, and by choosing q(st) =q(st|ot) as the approximate variational distribution.

The paper also provides the derivations of the equations provided in the original paper. The first part is about the free energy of the past and the second part is about the free energy of the future. For the past, the objective is to find the distributions q(st). If we consider expectations taken over trajectories sampled from q(ot, st, at) =p(ot|st)q(st, at), the expected free energy G (Equation 3) becomes: G  = Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log p(st|ot) − log ˜p(ot)] . The agent's generative model is assumed to be biased towards its preferred outcomes, distributed according to the prior ˜p(ot), and we aim to
find the distributions of future states and actions by applying variational inference, with the variational distribution q(st, at). If we consider expectations taken over trajectories sampled from q(ot, st, at) =p(ot|st)q(st, at), the expected free energy G (Equation 3) becomes: G  ≈Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log q(st|ot) − log ˜p(ot)] . The agent's model likelihood over actions is assumed to be uniform and constant. Thus, we can rewrite the above result as: G ≈Eq(ot,st,at)[log q(at|st) + logq(st|st−1, at−1) − log p(at) − log q(st|ot) − log ˜p(ot)] . The CFE is a bound on the expected free energy. This means that if we use the CAI algorithm to learn the generative model of the environment for making decisions, the CFE will be an upper bound on the FFAF.

**Limitations/Discussion**

The paper does not provide any discussion about limitations or future work in the original text.

---

**Summary Statistics:**
- Input: 8,702 words (55,322 chars)
- Output: 1,035 words
- Compression: 0.12x
- Generation: 58.8s (17.6 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
