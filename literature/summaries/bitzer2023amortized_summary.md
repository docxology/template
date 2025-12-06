# Amortized Inference for Gaussian Process Hyperparameters of Structured Kernels

**Authors:** Matthias Bitzer, Mona Meister, Christoph Zimmer

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [bitzer2023amortized.pdf](../pdfs/bitzer2023amortized.pdf)

**Generated:** 2025-12-05 14:03:30

---

=== PAPER CONTENT  ===
Title: Amortized Inference for Gaussian Process Hyperparameters of Structured Kernels
(https://arxiv.org/abs/2207.07692)
Matthias Bitzer1 Mona Meister1 Christoph Zimmer1
1Bosch Center for Artificial Intelligence, Renningen, Germany

In the following sections, we give further information about our method. We start by giving more experimental details. Then
we illustrate the application of our method on an extended set of simulated datasets via plots of the predictive distributions. Finally,
we give the proofs for the invariances and equivariances of our amortization network.

A EXPERIMENTAL DETAILS

Architecture  - Dataset-Encoder. The dataset-encoder consists of four transformer blocks each consisting of a stack of
Transformer-Encoder sublayers [Vaswani et al., 2017] where each sublayer has a multi-head-attention layer and an
element- wise MLP layer as the two trainable parts. We don’ t use dropout and positional encodings in our architecture as it would disable equivariances [Lee et al., 2019].


Table 2: Dataset-Encoder Configuration.
Block Num. of Layers Embedding Dim. Hidden Dim. in MLP
Transformer no. 1 (used in step 3) 4 256 512
Transformer no. 2 (used in step 5) 4 256 512
Transformer no. 3 (used in step 7) 4 512 512
Transformer no. 4 (used in step 9) 4 512 512

Architecture  - Kernel-Encoder-Decoder. The kernel-encoder-decoder consists of two stacks of Kernel-Encoder-Block layers, which are also specified via an embedding dimension and the hidden dimension of its MLP layer. Furthermore, the
kernel-encoder-decoder also contains one transformer block.

Table 3: Kernel-Encoder-Decoder Configuration.
Block Num. of Layers Embedding Dim. Hidden Dim. in MLP
Kernel-Encoder-Block stack 1 (used in step 1) 3 512 1024
Transformer block (used in step 2) 4 512 1024
Kernel-Encoder-Block stack 2 (used in step 4) 3 512 1024

Architecture  - Output layer. Each base- symbol specific MLP layer has one hidden layer with dimension dh = 200. The
MLP layer for the noise variance prediction consists of two hidden layers with dimension dh1 = 200 and dh2 = 100.

Sampling distribution. We use as base symbols SE, LIN and PER and its two gram multiplications like, e.g. SE × LIN. We simulate datasets of sizes between n  = 10 and n  = 250  (drawn uniformly) and in

[... truncated for summarization ...]

=== END PAPER CONTENT ===
Critical Instructions: You are summarizing a scientific research paper. You MUST follow ALL rules below:
1. ONLY use information that appears in the paper text above. Do NOT add external knowledge, assumptions, or invented details.
2. Provide a comprehensive summary that covers the key aspects of the paper. Use section headers that make sense for the content, such as: Overview/Summary (what the paper is about)
Key Contributions/Findings (main results and advances)
Methodology/Approach (how the research was conducted)
Results/Data (what was found or measured)
Limitations/Discussion (weaknesses and future work)
3. Word count: Aim for 400-700 words of substantive, detailed content. Focus on quality over quantity.
4. CONTENT FOCUS:
    - For PHYSICS papers: Highlight specific equations, experimental parameters, energy scales, detection methods, and statistical significance
    - For COMPUTER SCIENCE papers: Detail algorithms, complexity analysis, dataset characteristics, performance metrics, and comparisons
    - For BIOLOGY papers: Include species, sample sizes, statistical methods, biological mechanisms, and experimental conditions
    - For MATHEMATICS papers: Cover theorems, proofs, mathematical objects, computational complexity, and theoretical implications
5. DOMAIN- SPECIFIC EMPHASIS:
    - For PHYSICS papers: Highlight specific equations, experimental parameters, energy scales, detection methods, and statistical significance
    - For COMPUTER SCIENCE papers: Detail algorithms, complexity analysis, dataset characteristics, performance metrics, and comparisons
    - For BIOLOGY papers: Include species, sample sizes, statistical methods, biological mechanisms, and experimental conditions
    - For MATHEMATICS papers: Cover theorems, proofs, mathematical objects, computational complexity, and theoretical implications
6. QUALITY STANDARDS:
    - Be substantive: Provide detailed analysis rather than surface- level descriptions
    - Explain significance: Discuss why methods, results, and contributions matter
    - Maintain coherence: Ensure different sections complement rather than repeat each other
    - Use evidence: Support claims with specific details from the paper
7. ACCURACY REQUIREMENTS:
    - NO HALLUCINATION: Only discuss what the paper explicitly states
    - NO REPETITION: Avoid repeating the same information in multiple places
    - NO META-COMMENTARY: Do not mention being an AI or that this is a summary
    - SCIENTIFIC TONE: Use formal, academic language throughout
8. FLEXIBLE STRUCTURE: Use the section headers that best fit the paper' s content. You may use fewer or more sections as appropriate, or even combine related information.

Begin your summary now:

---

**Summary Statistics:**
- Input: 16,349 words (94,622 chars)
- Output: 723 words
- Compression: 0.04x
- Generation: 43.3s (16.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
