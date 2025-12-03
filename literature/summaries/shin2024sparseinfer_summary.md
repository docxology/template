# SparseInfer: Training-free Prediction of Activation Sparsity for Fast LLM Inference

**Authors:** Jiho Shin, Hoeseok Yang, Youngmin Yi

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [shin2024sparseinfer.pdf](../pdfs/shin2024sparseinfer.pdf)

**Generated:** 2025-12-03 07:27:20

---

**Overview/Summary**

The paper "SparseInfer: Training-free Prediction of Activation Sparsity in Large Language Models" proposes a new method called SparseInfer for predicting the activation sparsity of large language models without training any additional parameters. The authors show that the activation patterns in a pre-trained model are not random and can be predicted with high accuracy, which is useful for reducing the computational cost of the model at inference time. They also demonstrate that the prediction error is highly correlated to the magnitude of the activations, and the method can be used to achieve the state-of-the-art performance on some large language models.

**Key Contributions/Findings**

The main contributions of this paper are:

* The authors show that the activation patterns in a pre-trained model are not random and can be predicted with high accuracy.
* They demonstrate that the prediction error is highly correlated to the magnitude of the activations, and the method can be used to achieve the state-of-the-art performance on some large language models.

**Methodology/Approach**

The authors first analyze the activation patterns in a pre-trained model. The analysis shows that the activation sparsity in a pre-trained model is not random and has a strong correlation with the magnitude of the activations. They also find that the prediction error is highly correlated to the magnitude of the activations, which inspires them to propose a new method called SparseInfer for predicting the activation sparsity. The authors use a training-free approach by using the information from the pre-trained model itself and do not need any additional parameters or data.

**Results/Data**

The results show that the prediction error is highly correlated to the magnitude of the activations, which inspires them to propose a new method called SparseInfer for predicting the activation sparsity. The authors use a training-free approach by using the information from the pre-trained model itself and do not need any additional parameters or data. They also demonstrate that the method can be used to achieve the state-of-the-art performance on some large language models.

**Limitations/Discussion**

The limitations of this paper are:

* The authors only use a few large language models for evaluation, which may not cover all possible scenarios.
* The prediction error is highly correlated to the magnitude of the activations. This means that the method can be used to achieve the state-of-the-art performance on some large language models.

**References**

---

**Summary Statistics:**
- Input: 6,111 words (38,836 chars)
- Output: 388 words
- Compression: 0.06x
- Generation: 23.9s (16.3 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
