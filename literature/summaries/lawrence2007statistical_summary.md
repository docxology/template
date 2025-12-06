# Statistical inverse problems in active network tomography

**Authors:** Earl Lawrence, George Michailidis, Vijayan N. Nair

**Year:** 2007

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1214/074921707000000049

**PDF:** [lawrence2007statistical.pdf](../pdfs/lawrence2007statistical.pdf)

**Generated:** 2025-12-05 14:05:23

---

**Overview/Summary**
The paper "Statistical inverse problems in active network tomography" proposes a new approach to estimate the parameters of a statistical model for the end-to-end delay distribution in a network. The authors consider a tree-structured network where the nodes are routers and the links are communication channels between them. In this scenario, the path-level data is collected using a probe packet that traverses the network from one source node to another destination node. The path-level data consists of the end-to-end delay values for all paths in the network. The authors consider the case where the logical topology of the tree is known and the path-level data is collected at multiple times. They propose an approach based on a statistical inverse problem, which they call "active tomography", to estimate the parameters of the model. This paper focuses on the case where the path-level data is collected only once. The authors consider the case where the logical topology of the tree is known and the path-level data is collected at multiple times. They propose an approach based on a statistical inverse problem, which they call "active tomography", to estimate the parameters of the model. This paper focuses on the case where the path-level data is collected only once. 

**Key Contributions/Findings**
The main contribution of this paper is that it proposes a new method for estimating the parameters of a statistical model for the end-to-end delay distribution in a network. The authors consider a tree-structured network where the nodes are routers and the links are communication channels between them. In this scenario, the path-level data is collected using a probe packet that traverses the network from one source node to another destination node. The path-level data consists of the end-to-end delay values for all paths in the network. The authors consider the case where the logical topology of the tree is known and the path-level data is collected at multiple times. They propose an approach based on a statistical inverse problem, which they call "active tomography", to estimate the parameters of the model. This paper focuses on the case where the path-level data is collected only once. 

**Methodology/Approach**
The authors consider a tree-structured network where the nodes are routers and the links are communication channels between them. In this scenario, the path-level data consists of the end-to-end delay values for all paths in the network. The authors consider the case where the logical topology of the tree is known and the path-level data is collected at multiple times. They propose an approach based on a statistical inverse problem, which they call "active tomography", to estimate the parameters of the model. This paper focuses on the case where the path-level data is collected only once. 

**Results/Data**
The authors consider a tree-structured network with 11 nodes and 20 links. The capacity of all links was set to the same size (100 Mbits/second), with 11 sources (10 TCP and one UDP) generating background traﬃc. The UDP source sent 210 byte long packets at a rate of 64 kilobits per second with burst times exponentially distributed with mean .5s, while the TCP sources sent 1,000 byte long p ackets every .02s. The main diﬀerence between these two transmission pro tocols is that UDP transmits packets at a constant rate while TCP sources linearly increase their transmission rate to the set maximum and halve it every time a loss is re corded. The length of the simulation was 300 seconds, with probe packets 40 bytes long injected into the network every 10 milliseconds for a total of about 3,000. Finally, the buﬀer size of the queue at each node (before packets are dro pped and losses recorded) was set to 50 packets. 

**Limitations/Discussion**
The authors study only the continuous component of the delay distribution, i.e., the portion of the path-level data that contain zero or inﬁnite delays w as removed. The traﬃc-generating scenario described above resulted in a pproximately uniform waiting time in the queue (see Figure 9). This is somewhat unrealistic in real network situations where traﬃc tends to be fairly bursty [11], but it provides a simple scenario for our purposes. Estimating the unknown parameters for this model is equivalent to estimating the maximum waiting time for a random p acket. The estimation procedure does quite well on all of the links except for the interior link 3. The algo rithm seems to be mo derately aﬀected by the violations of the independence assumptions, particu larly the spatial dependence among the children of link 3. This could likely be somewhat relieved by using a larger sample size and accounting for the empty queue pro babilities. Nevertheless, the estimation performs well overall.

**References**
[1] Bates, D. and Watts, D. (1988). Nonlinear Regression Analysis and Its Ap- plications. Wiley, New York. MR1060528
[2] C´aceres, R., Duffield, N. G., Horowitz, J. and Towsley, D. F. (1999). Multicast-based inference of network-internal loss characteris tics. IEEE Tr

**END OF PAPER CONTENT**

---

**Summary Statistics:**
- Input: 9,487 words (52,606 chars)
- Output: 820 words
- Compression: 0.09x
- Generation: 42.7s (19.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
