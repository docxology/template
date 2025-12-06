# Realising Synthetic Active Inference Agents, Part II: Variational Message Updates

**Authors:** Thijs van de Laar, Magnus Koudahl, Bert de Vries

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1162/neco_a_01713

**PDF:** [laar2023realising.pdf](../pdfs/laar2023realising.pdf)

**Generated:** 2025-12-05 12:48:14

---

**Overview/Summary**

The current paper is a companion to [1] and provides an operational framework for synthetic active inference (SAI) in the context of Forney-Style Factor Graphs (FFGs). The authors provide an alternative formulation of the SAI problem, which they call Realising Synthetic Active Inference Agents. This work is motivated by the fact that the EFE optimisation viewpoint does not readily extend to message passing on free-form models [2]. The paper starts with a discussion of the GFE and BFE objectives in the context of FFGs, which are used as an alternative to the traditional variational approach for constrained optimisation. It then uses these ideas to formulate SAI as a problem of constrained optimisation.

**Key Contributions/Findings**

The authors provide a new formulation of the SAI problem, and show that this can be solved by a message passing algorithm on FFGs. The key contribution is the derivation of the message update expressions for the constrained free energy (C) approach, which they call the Constrained Forney-Style Factor Graph (CFFG). They also provide an example of SAI in a temporal setting.

**Methodology/Approach**

The authors begin by discussing the GFE and BFE objectives. The CFE is defined as the sum of the EFE and the prior beliefs on future outcomes, which they call the expected free energy (EFE) term. They then formulate the SAI problem in terms of a CFFG. This is done by first defining the GM for the forward process and the backward process. The CFFG is constructed from these two sub-models. The authors also provide an example of how to construct the CFFG for the temporal case, which they call the Constrained Forney-Style Factor Graph (CFFG). This is done by first defining the GM for the forward and backward processes. The CFFG is then constructed from these two sub-models. The authors show that the CFE can be solved by a message passing algorithm on the CFFG, which they call the Constrained Forney-Style Variational Message Passing (CFVP). They also provide an example of how to construct the CFFG for the temporal case.

**Results/Data**

The paper provides two main results. The first is the formulation of the SAI problem in terms of a CFFG, and the second is the derivation of the CFVP algorithm. It also provides an example of how to apply this to the temporal case. The authors do not provide any data or experimental results.

**Limitations/Discussion**

The paper does not discuss limitations or future work.

---

**Summary Statistics:**
- Input: 11,402 words (68,442 chars)
- Output: 404 words
- Compression: 0.04x
- Generation: 25.3s (16.0 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
