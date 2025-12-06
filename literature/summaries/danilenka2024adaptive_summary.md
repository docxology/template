# Adaptive Active Inference Agents for Heterogeneous and Lifelong Federated Learning

**Authors:** Anastasiya Danilenka, Alireza Furutanpey, Victor Casamayor Pujol, Boris Sedlak, Anna Lackinger, Maria Ganzha, Marcin Paprzycki, Schahram Dustdar

**Year:** 2024

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [danilenka2024adaptive.pdf](../pdfs/danilenka2024adaptive.pdf)

**Generated:** 2025-12-05 12:47:04

---

**Overview/Summary**
This work proposes a new type of agent called Adaptive Active Inference (AIF) agents for heterogeneous and dynamic federated learning (FL). The authors introduce the AIF framework to address the challenges in FL by proposing an adaptive active inference approach. This is achieved through a two-stage procedure: first, the AIF agent learns the causal graph of the problem with an unsupervised BN structure using Hill Climb Search; second, it uses the learned causal graph to actively infer and adaptively update its objective function based on the observed data. The authors show that the proposed AIF agents can detect changes in the environment and initiate system re-configuration without human supervision. They also identify two main explanations for the suboptimal performance of the AIF agents: (1) "unsupervised" BN structure learning using Hill Climb Search may struggle to discover meaningful causal relationships when limited data is available, (2) in the absence of observations with both SLOs fulfilled, an agent may either be stuck in forever exploring state or stick to the strategy that guarantees at least one SLO fulfillment and focus on exploiting suboptimal behavior. The authors also evaluate the AIF agents' behavior in a more practical experimental setup and present evaluation of the AIF agents' behavior in the presence of concept drifts and resources heterogeneity.

**Key Contributions/Findings**
The proposed AIF framework can detect changes in the environment and initiate system re-configuration with no human supervision. The two main explanations for the suboptimal performance of the AIF agents are: (1) "unsupervised" BN structure learning using Hill Climb Search may struggle to discover meaningful causal relationships when limited data is available, (2) in the absence of observations with both SLOs fulfilled, an agent may either be stuck in forever exploring state or stick to the strategy that guarantees at least one SLO fulfillment and focus on exploiting suboptimal behavior. The AIF agents' behavior in a more practical experimental setup and present evaluation of the AIF agents' behavior in the presence of concept drifts and resources heterogeneity.

**Methodology/Approach**
The authors propose an adaptive active inference (AIF) framework for heterogeneous and dynamic FL environments. In this framework, the AIF agent first learns the causal graph of the problem with an unsupervised BN structure using Hill Climb Search; second, it uses the learned causal graph to actively infer and adaptively update its objective function based on the observed data. The authors show that the proposed AIF agents can detect changes in the environment and initiate system re-configuration without human supervision.

**Results/Data**
The evaluation shows the potential of AIF agents in detecting the changes in the environment and the ability to initiate system re-configuration with no human supervision. However, the SLO fulfillment is not perfect. Two main explanations were identified up until now: (1) "unsupervised" BN structure learning using Hill Climb Search may struggle to discover meaningful causal relationships when limited data is available, (2) in the absence of observations with both SLOs fulfilled, an agent may either be stuck in forever exploring state or stick to the strategy that guarantees at least one SLO fulfillment and focus on exploiting suboptimal behavior. The authors also evaluate the AIF agents' behavior in a more practical experimental setup and present evaluation of the AIF agents' behavior in the presence of concept drifts and resources heterogeneity.

**Limitations/Discussion**
The proposed AIF framework can detect changes in the environment and initiate system re-configuration with no human supervision. However, the SLO fulfillment is not perfect. Two main explanations were identified up until now: (1) "unsupervised" BN structure learning using Hill Climb Search may struggle to discover meaningful causal relationships when limited data is available, (2) in the absence of observations with both SLOs fulfilled, an agent may either be stuck in forever exploring state or stick to the strategy that guarantees at least one SLO fulfillment and focus on exploiting suboptimal behavior. The authors also evaluate the AIF agents' behavior in a more practical experimental setup and present evaluation of the AIF agents' behavior in the presence of concept drifts and resources heterogeneity.

**References**
[45] Hill, C.L., & Lewicki, Y. (2019). Learning causal graphs with unknown hidden variables: Algorithms for equation-of-state models. In Advances in Neural Information Processing Systems 32, pp. 1448–1457.

---

**Summary Statistics:**
- Input: 10,472 words (68,059 chars)
- Output: 699 words
- Compression: 0.07x
- Generation: 35.8s (19.5 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
