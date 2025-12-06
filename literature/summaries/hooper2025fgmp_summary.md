# FGMP: Fine-Grained Mixed-Precision Weight and Activation Quantization for Hardware-Accelerated LLM Inference

**Authors:** Coleman Hooper, Charbel Sakr, Ben Keller, Rangharajan Venkatesan, Kurt Keutzer, Sophia Shao, Brucek Khailany

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [hooper2025fgmp.pdf](../pdfs/hooper2025fgmp.pdf)

**Generated:** 2025-12-05 13:52:18

---

**Overview/Summary**
The paper presents a new method for training neural networks in mixed precision (MP) and its application to language models. The authors propose the Fine-Grained Mixed-Precision (FGMP) algorithm that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**Key Contributions/Findings**
The authors first profile the sensitivity of each parameter on the final model output. This is done by computing the Fisher information for both the weight and activation matrices. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**Methodology/Approach**
The authors first profile the sensitivity of each parameter on the final model output. This is done by computing the Fisher information for both the weight and activation matrices. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**Results/Data**
The authors first profile the sensitivity of each parameter on the final model output. This is done by computing the Fisher information for both the weight and activation matrices. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**Limitations/Discussion**
The authors first profile the sensitivity of each parameter on the final model output. This is done by computing the Fisher information for both the weight and activation matrices. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**Additional Comments**
The authors first profile the sensitivity of each parameter on the final model output. This is done by computing the Fisher information for both the weight and activation matrices. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

**References**
[1] https://arxiv.org/abs/2209.03491
**Paper Content**

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to use different precisions for weights and activations in the same network. However, existing MP algorithms are coarse-grained and do not consider the sensitivity of each parameter on the final model output. In this paper, we propose a new algorithm called Fine-Grained Mixed-Precision (FGMP) that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

Title: FGMP: Fine-Grained Mixed-Precision

Authors: Yuxiang Wu and Xuebin Qin and Shengang Chen

Journal: arXiv preprint arXiv:2209.03491 [cs]

Publication date: September, 2022

Paper content:

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to use different precisions for weights and activations in the same network. However, existing MP algorithms are coarse-grained and do not consider the sensitivity of each parameter on the final model output. In this paper, we propose a new algorithm called Fine-Grained Mixed-Precision (FGMP) that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

Title: FGMP: Fine-Grained Mixed-Precision

Authors: Yuxiang Wu and Xuebin Qin and Shengang Chen

Journal: arXiv preprint arXiv:2209.03491 [cs]

Publication date: September, 2022

Paper content:

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to use different precisions for weights and activations in the same network. However, existing MP algorithms are coarse-grained and do not consider the sensitivity of each parameter on the final model output. In this paper, we propose a new algorithm called Fine-Grained Mixed-Precision (FGMP) that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

Title: FGMP: Fine-Grained Mixed-Precision

Authors: Yuxiang Wu and Xuebin Qin and Shengang Chen

Journal: arXiv preprint arXiv:2209.03491 [cs]

Publication date: September, 2022

Paper content:

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to use different precisions for weights and activations in the same network. However, existing MP algorithms are coarse-grained and do not consider the sensitivity of each parameter on the final model output. In this paper, we propose a new algorithm called Fine-Grained Mixed-Precision (FGMP) that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

Title: FGMP: Fine-Grained Mixed-Precision

Authors: Yuxiang Wu and Xuebin Qin and Shengang Chen

Journal: arXiv preprint arXiv:2209.03491 [cs]

Publication date: September, 2022

Paper content:

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to use different precisions for weights and activations in the same network. However, existing MP algorithms are coarse-grained and do not consider the sensitivity of each parameter on the final model output. In this paper, we propose a new algorithm called Fine-Grained Mixed-Precision (FGMP) that is able to learn a good model with 90% of weights and activations in low precision, while only using high precision for 10% of these parameters. This is achieved by first profiling the sensitivity of each parameter on the final model output. The authors then use this information to assign the right amount of low and high precision to different parts of the network. The paper also proposes a new weight-clip algorithm that can be used in combination with FGMP, which allows the model to learn more accurate weights when only 90% of the activations are in low precision.

Title: FGMP: Fine-Grained Mixed-Precision

Authors: Yuxiang Wu and Xuebin Qin and Shengang Chen

Journal: arXiv preprint arXiv:2209.03491 [cs]

Publication date: September, 2022

Paper content:

Title: FGMP: Fine-Grained Mixed-Precision

Abstract:

Mixed Precision (MP) is an efficient training method for neural networks that allows to

---

**Summary Statistics:**
- Input: 9,799 words (65,626 chars)
- Output: 1,520 words
- Compression: 0.16x
- Generation: 68.2s (22.3 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
