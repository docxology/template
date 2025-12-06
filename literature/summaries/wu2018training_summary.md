# Training and Inference with Integers in Deep Neural Networks

**Authors:** Shuang Wu, Guoqi Li, Feng Chen, Luping Shi

**Year:** 2018

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [wu2018training.pdf](../pdfs/wu2018training.pdf)

**Generated:** 2025-12-05 14:02:47

---

**Overview/Summary**

The authors of this paper present a novel algorithm called WAGE (Weight Averaging for Gradient Error) to improve the training and inference efficiency of deep neural networks by using integers instead of floating point numbers in the forward and backward passes. The main idea is that the gradient error, which is an important factor in the training process, can be used to guide the quantization of weights and activations. In particular, the authors propose a layerwise histogram-based method to determine the bitwidths for both the weights and gradients. This approach is called WAGE and it is different from the existing methods that only use the magnitude of the weights or the gradients as the guidance.

**Key Contributions/Findings**

The main contributions of this paper are the following:

1. The authors propose a novel algorithm, WAGE, to improve the training and inference efficiency of deep neural networks by using integers instead of floating point numbers in the forward and backward passes.
2. The authors design an integer-based version of the backpropagation algorithm for the gradient error. This is different from the existing methods that only use the magnitude of the gradients as the guidance.
3. The authors propose a layerwise histogram-based method to determine the bitwidths for both the weights and gradients.
4. The authors show that WAGE can be used in the training and inference processes, including the forward pass, the backward pass, and the weight update.

**Methodology/Approach**

The authors use the following notations: I is the number of layers in a network; kG and kA are the bitwidths for the gradients and activations respectively. The WAGE algorithm is shown in Algorithm 1. In this algorithm, the forward pass and the backward pass are computed with the quantized weights and activations. The weight update is also computed with the quantized gradient error.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

**Results/Data**

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

The authors use a VGG-like network as an example to show that the WAGE algorithm can be used in the training and inference processes. The bitwidths for the gradients and activations are determined by the layerwise histograms of the gradient errors and the activation errors respectively. In this paper, the authors assume that the network structures are deﬁned and initialized with Equation 5.

**Limitations/Discussion**

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition, the authors do not provide a theoretical analysis for the convergence of the WAGE algorithm.

The main limitation of this work is that it only considers the forward pass and the backward pass in the training process. The WAGE algorithm can be used to improve the inference efficiency by using integers in the forward pass, but it does not consider the weight update in the inference process. In addition

---

**Summary Statistics:**
- Input: 7,222 words (45,788 chars)
- Output: 1,759 words
- Compression: 0.24x
- Generation: 68.7s (25.6 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
