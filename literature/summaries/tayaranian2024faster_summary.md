# Faster Inference of Integer SWIN Transformer by Removing the GELU Activation

**Authors:** Mohammadreza Tayaranian, Seyyed Hasan Mozafari, James J. Clark, Brett Meyer, Warren Gross

**Year:** 2024

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [tayaranian2024faster.pdf](../pdfs/tayaranian2024faster.pdf)

**Generated:** 2025-12-05 13:02:17

---

**Overview/Summary**
The paper "Faster Inference of Integer SWIN Transformer by Removing" is a scientific research paper in the field of computer science, specifically in the area of deep learning and artificial intelligence. The authors present a new method for accelerating the inference speed of the integer version of the popular SWIN transformer model. This is achieved by removing the bias term that is fused to it during training. They also use knowledge distillation to maintain the accuracy of the original model. The main contributions of this work are the two techniques: (1) removing the bias term and (2) using knowledge distillation.

**Key Contributions/Findings**
The authors demonstrate that the integer version of the SWIN transformer can be accelerated by a factor of 11.7 on average, with a maximum acceleration of 15.5 times, compared to the original method for post-training quantization, while maintaining the accuracy of the original model. The main results and advances are summarized as follows: (1) this paper proposes two techniques that can accelerate the inference speed of the integer version of the SWIN transformer by a factor of 11.7 on average; (2) the proposed method is compared with the state-of-the-art post-training quantization methods, such as Q-ViT and FQ-ViT, and achieves better performance than them.

**Methodology/Approach**
The authors first introduce the integer version of the SWIN transformer model, which is a fully-quantized vision transformer. The main components of this method are: (1) removing the bias term that is fused to it during training; (2) using knowledge distillation. They also compare the proposed method with the state-of-the-art post-training quantization methods, such as Q-ViT and FQ-ViT, and achieve better performance than them.

**Results/Data**
The authors use a set of 10 image classification datasets for evaluation. The results are shown in Table 1, where "Full" is the original method for post-training quantization, "PTQ4VIT" is the Q-ViT method, "FQ-ViT" is the FQ-ViT method, and "Ours" is the proposed method. The inference speed of each model on a single V100 GPU is shown in Table 2. The accuracy of each model on the ImageNet dataset is shown in Table 3.

**Limitations/Discussion**
The authors state that this paper proposes two techniques to accelerate the inference speed of the integer version of the SWIN transformer by a factor of 11.7 on average, with a maximum acceleration of 15.5 times, compared to the original method for post-training quantization, while maintaining the accuracy of the original model. The authors also compare the proposed method with the state-of-the-art post-training quantization methods, such as Q-ViT and FQ-ViT, and achieve better performance than them. However, the paper does not discuss the limitations or future work.

**References**
The references are listed at the end of

---

**Summary Statistics:**
- Input: 3,814 words (23,298 chars)
- Output: 443 words
- Compression: 0.12x
- Generation: 27.9s (15.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
