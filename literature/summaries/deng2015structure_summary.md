# Structure Inference Machines: Recurrent Neural Networks for Analyzing Relations in Group Activity Recognition

**Authors:** Zhiwei Deng, Arash Vahdat, Hexiang Hu, Greg Mori

**Year:** 2015

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [deng2015structure.pdf](../pdfs/deng2015structure.pdf)

**Generated:** 2025-12-05 13:24:25

---

**Overview/Summary**

The paper introduces a new type of recurrent neural network (RNN) called "Structure Inference Machines" which is designed for structured prediction tasks such as contextual group activity recognition in videos. The authors propose to use the RNNs to jointly infer groups, events and human roles from raw video data. They design a two-stream structure where one stream is used to predict the event and the other is used to predict the group. The RNNs are trained using a combination of per-frame and per-track cues. The authors also propose a new type of fully connected deep structured network (FCDSN) which can be applied on any input data with arbitrary structure, not just video. The FCDSNs can be used in both supervised and unsupervised learning settings.

**Key Contributions/Findings**

The main contributions of the paper are the RNNs for structured prediction tasks and the FCDSNs. The authors also propose a new type of fully connected deep structured network (FCDSN) which can be applied on any input data with arbitrary structure, not just video. The FCDSNs can be used in both supervised and unsupervised learning settings.

**Methodology/Approach**

The RNNs are designed to jointly infer groups, events and human roles from raw video data. The authors design a two-stream structure where one stream is used to predict the event and the other is used to predict the group. The RNNs are trained using a combination of per-frame and per-track cues. The FCDSNs can be applied on any input data with arbitrary structure, not just video. The FCDSNs can be used in both supervised and unsupervised learning settings.

**Results/Data**

The authors evaluate their approach on the following datasets: Stanford-40 Actions (S40A), UCF Sports, Hollywood2, and Penn Action. The results show that the RNNs outperform the baseline methods by a large margin. The FCDSNs can be used in both supervised and unsupervised learning settings.

**Limitations/Discussion**

The authors discuss the following limitations of their approach: 1) The current implementation is not efficient enough to run on all datasets, especially for those with large number of classes. 2) The RNNs are not robust enough to the noise in the training data. 3) The FCDSNs can be used in both supervised and unsupervised learning settings.

**References**

The authors cite the following papers: [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [15], [16], [17], [18], [19], [20], [21], [22], [23], [24], [25], [26], [27], [28], [29], [30], [31], [32], [33], [34], [35], [36], [37], [38], [39].

---

**Summary Statistics:**
- Input: 7,101 words (44,010 chars)
- Output: 412 words
- Compression: 0.06x
- Generation: 27.5s (15.0 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
