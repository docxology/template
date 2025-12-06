# AESPA: Accuracy Preserving Low-degree Polynomial Activation for Fast Private Inference

**Authors:** Jaiyoung Park, Michael Jaemin Kim, Wonkyung Jung, Jung Ho Ahn

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [park2022aespa.pdf](../pdfs/park2022aespa.pdf)

**Generated:** 2025-12-05 13:13:40

---

**Overview/Summary**
The paper proposes a new protocol for private inference called DELPHI (Differentially Private Low-degree Polynomial Inference) that allows users to perform low-precision private inference with high accuracy and efficiency. The authors first introduce the concept of "ReLU budget" which is the number of ReLU operations in a model, and show that the ReLU budget can be used as an indicator for the trade-off between accuracy and efficiency in private inference. They then propose a new protocol called DELPHI that uses a linear polynomial to approximate the original model's output. The main idea behind this protocol is to use a low-precision approximation of the original model, which can be computed with high efficiency while keeping the accuracy as the original model. The authors show that the proposed protocol can achieve better performance than the state-of-the-art private inference protocols in terms of both accuracy and efficiency.

**Key Contributions/Findings**
The main contributions of this paper are three-fold. First, the authors propose a new protocol called DELPHI for private inference. Second, they provide an algorithm to generate the low-precision approximation model with high accuracy. Third, they show that the proposed protocol can achieve better performance than the state-of-the-art private inference protocols in terms of both accuracy and efficiency.

**Methodology/Approach**
The authors first introduce the concept of "ReLU budget" which is the number of ReLU operations in a model. The authors then propose an algorithm to generate a low-precision approximation model with high accuracy, called AESPA (Accuracy Preserving Low-degree Polynomial Inference). The main idea behind this protocol is to use a linear polynomial to approximate the original model's output. This new protocol can achieve better performance than the state-of-the-art private inference protocols in terms of both accuracy and efficiency.

**Results/Data**
The authors evaluate the proposed DELPHI on several datasets including MNIST, CIFAR-10, and COVW2. The results show that the proposed protocol can achieve better performance than the state-of-the-art private inference protocols in terms of both accuracy and efficiency. For example, the proposed protocol can reduce the inference time by 4x to 5x while keeping the test accuracy as high as the original model on MNIST.

**Limitations/Discussion**
The authors also discuss several limitations and future work for this paper. First, the authors mention that the current implementation of DELPHI is not optimized for efficiency. Second, the authors note that the proposed protocol can be used to perform private inference with a fixed ReLU budget. Third, the authors suggest that the proposed protocol can be used as a building block to design other protocols. Finally, the authors mention that the accuracy and efficiency of the proposed protocol are sensitive to the number of ReLU operations in the original model.

**Summary**
The paper proposes a new protocol called DELPHI for private inference. The main idea behind this protocol is to use a low-precision approximation of the original model's output. This new protocol can achieve better performance than the state-of-the-art private inference protocols in terms of both accuracy and efficiency.

---

**Summary Statistics:**
- Input: 7,951 words (52,933 chars)
- Output: 492 words
- Compression: 0.06x
- Generation: 27.6s (17.8 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
