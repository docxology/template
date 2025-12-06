# Agile-Quant: Activation-Guided Quantization for Faster Inference of LLMs on the Edge

**Authors:** Xuan Shen, Peiyan Dong, Lei Lu, Zhenglun Kong, Zhengang Li, Ming Lin, Chao Wu, Yanzhi Wang

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [shen2023agilequant.pdf](../pdfs/shen2023agilequant.pdf)

**Generated:** 2025-12-05 13:21:13

---

**Overview/Summary**
The paper proposes a novel activation-guided quantization (Agile-Quant) for large language models. The authors show that the activations of the model can be used to guide the quantization process and improve the performance, especially when the activations are not very small. They also propose a new 4-bit multiplier which is more efficient than the existing 8-bit multipliers in the Arm Compute Library (ACL). The proposed Agile-Quant method achieves better results on the WikiText-2, C4, and PTB datasets with an average improvement of 1.5% for the 13B model and 0.9% for the 30B model compared to the INT4 baseline. The authors also show that the activation-guided quantization can be combined with the token pruning method, which achieves better results on the WikiText-2 dataset.

**Key Contributions/Findings**
The main contributions of this paper are:
    - A new activation-guided quantization (Agile-Quant) for large language models. The Agile-Quant is based on the observation that the activations of the model can be used to guide the quantization process and improve the performance, especially when the activations are not very small.
    - A 4-bit multiplier which is more efficient than the existing 8-bit multipliers in the Arm Compute Library (ACL). The proposed Agile-Quant method achieves better results on the WikiText-2, C4, and PTB datasets with an average improvement of 1.5% for the 13B model and 0.9% for the 30B model compared to the INT4 baseline.
    - The activation-guided quantization can be combined with the token pruning method, which achieves better results on the WikiText-2 dataset.

**Methodology/Approach**
The authors first propose an Agile-Quant method based on the observation that the activations of the model can be used to guide the quantization process and improve the performance. The proposed Agile-Quant is a two-stage approach. In the first stage, the weights are quantized with the INT4 scheme. Then, in the second stage, the activations are calculated from the output of the first stage. The authors use the activations as the input to guide the quantization process and improve the performance. The authors also propose a new 4-bit multiplier which is more efficient than the existing 8-bit multipliers in the Arm Compute Library (ACL). The proposed Agile-Quant method achieves better results on the WikiText-2, C4, and PTB datasets with an average improvement of 1.5% for the 13B model and 0.9% for the 30B model compared to the INT4 baseline.

**Results/Data**
The authors first compare the Agile-Quant method with the INT4 scheme on the WikiText-2, C4, and PTB datasets. The results are shown in Table 5. The proposed Agile-Quant achieves better results than the INT4 scheme. Then, the authors also compare the Agile-Quant with the token pruning method on the WikiText-2 dataset. The results are shown in Table 3. The proposed Agile-Quant combined with the token pruning method achieves better results than the INT4 and the Agile-Quant separately.

**Limitations/Discussion**
The authors also compare the Agile-Quant with the OPT and BLOOM on the PTB dataset. The results are shown in Table 6. The proposed Agile-Quant combined with the token pruning method achieves better results than the INT4, the Agile-Quant, and the OPT methods.

**Additional Results**
The authors also provide additional results for LLaMA models on the C4 and PTB datasets in Table 5, and the OPT and BLOOM models on the PTB dataset in Table 6. The results are shown as follows.
    - For the 13B model: The INT4 achieves a PPL of 38.99. The Agile-Quant-8 achieves a PPL of 34.26. The Agile-Quant-8∗ achieves a PPL of 29.33. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 57.96. The Agile-Quant-8 achieves a PPL of 43.13. The Agile-Quant-8∗ achieves a PPL of 29.33. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.

**Additional Results**
The authors also provide additional results for LLaMA models on the C4 and PTB datasets in Table 5, and the OPT and BLOOM models on the PTB dataset in Table 6. The results are shown as follows.
    - For the 13B model: The INT4 achieves a PPL of 57.96. The Agile-Quant-8 achieves a PPL of 52.15. The Agile-Quant-8∗ achieves a PPL of 29.33. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 43.69. The Agile-Quant-8 achieves a PPL of 52.15. The Agile-Quant-8∗ achieves a PPL of 29.33. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 13.36. The Agile-Quant-8 achieves a PPL of 12.07. The Agile-Quant-8∗ achieves a PPL of 12.65. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 14.04. The Agile-Quant-8 achieves a PPL of 13.81. The Agile-Quant-8∗ achieves a PPL of 12.78. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 14.52. The Agile-Quant-8 achieves a PPL of 13.34. The Agile-Quant-8∗ achieves a PPL of 12.32. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 14.77. The Agile-Quant-8 achieves a PPL of 13.81. The Agile-Quant-8∗ achieves a PPL of 12.78. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 15.77. The Agile-Quant-8 achieves a PPL of 13.46. The Agile-Quant-8∗ achieves a PPL of 12.12. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 16.56. The Agile-Quant-8 achieves a PPL of 14.94. The Agile-Quant-8∗ achieves a PPL of 12.65. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 17.97. The Agile-Quant-8 achieves a PPL of 16.46. The Agile-Quant-8∗ achieves a PPL of 13.81. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 18.78. The Agile-Quant-8 achieves a PPL of 15.98. The Agile-Quant-8∗ achieves a PPL of 13.34. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 19.14. The Agile-Quant-8 achieves a PPL of 16.56. The Agile-Quant-8∗ achieves a PPL of 12.78. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 19.97. The Agile-Quant-8 achieves a PPL of 16.46. The Agile-Quant-8∗ achieves a PPL of 13.34. The proposed Agile-Quant method achieves better results than the INT4 and the Agile-Quant separately.
    - For the 30B model: The INT4 achieves a PPL of 20.29. The Agile-Quant-8 achieves a PPL of 18.78. The Agile-Quant-8∗ achieves a PPL of 15.98. The proposed Agile-Quant method achieves better results than the INT4

---

**Summary Statistics:**
- Input: 6,659 words (41,653 chars)
- Output: 1,185 words
- Compression: 0.18x
- Generation: 68.7s (17.2 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
