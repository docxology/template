# Deep Computational Model for the Inference of Ventricular Activation Properties

**Authors:** Lei Li, Julia Camps, Abhirup Banerjee, Marcel Beetz, Blanca Rodriguez, Vicente Grau

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [li2022deep.pdf](../pdfs/li2022deep.pdf)

**Generated:** 2025-12-05 12:57:48

---

**Overview/Summary**

The paper "Deep Computational Model for the Inference of Ventricular Activation Sequence" proposes a novel deep learning-based approach to infer the ventricular activation sequence from the 12-lead electrocardiogram (ECG) in an individual. The authors use a reference anatomy and a simulation framework, which is based on a realistic biventricular model with the Purkinje system, to generate a large number of synthetic ECGs for training and testing their deep learning-based approach. The proposed method outperforms the state-of-the-art methods in terms of both accuracy and robustness.

**Key Contributions/Findings**

The main contributions of this paper are the development of a novel simulation framework based on a realistic biventricular model with the Purkinje system, which is used to generate a large number of synthetic ECGs for training and testing the proposed deep learning-based approach. The authors also propose a new method that uses a graph convolutional neural network (GCNN) to infer the ventricular activation sequence from the 12-lead ECG. This paper demonstrates the accuracy and robustness of the GCNN in both the reference anatomy and the real anatomy.

**Methodology/Approach**

The proposed simulation framework is based on a realistic biventricular model with the Purkinje system, which is used to generate a large number of synthetic ECGs for training and testing. The authors use the tetrahedral mesh generator TetGen to create a 3D ventricular model. The 3D ventricular model is then discretized into a 2D surface mesh, where the activation time at each node on the 2D surface is recorded as the earliest activation site (EASI). The ECGs are

---

**Summary Statistics:**
- Input: 4,865 words (31,828 chars)
- Output: 254 words
- Compression: 0.05x
- Generation: 67.6s (3.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
