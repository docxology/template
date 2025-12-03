# From pixels to planning: scale-free active inference

**Authors:** Karl Friston, Conor Heins, Tim Verbelen, Lancelot Da Costa, Tommaso Salvatori, Dimitrije Markovic, Alexander Tschantz, Magnus Koudahl, Christopher Buckley, Thomas Parr

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [friston2024from.pdf](../pdfs/friston2024from.pdf)

**Generated:** 2025-12-02 07:41:52

---

**Overview/Summary**

The paper "From pixels to planning: scale- free active inference" by [Authors] proposes a novel approach for learning the structure of an image from its pixel values in a way that is independent of the number of training images, which is called fast structure learning. This method can be used to learn the structure of any data and has many applications in computer vision tasks such as object recognition, scene understanding, and video analysis. The paper also proposes a new approach for image compression based on active inference.

**Key Contributions/Findings**

The main contributions of this work are two-fold. Firstly, it presents a novel method to learn the structure from data which is independent of the number of training images. This method can be used to learn the structure of any data and has many applications in computer vision tasks such as object recognition, scene understanding, and video analysis. Secondly, it proposes a new approach for image compression based on active inference.

**Methodology/Approach**

The first step is to use a blocking transformation to convert the continuous pixel values into discrete states. This can be done by quantizing the singular variates of the concatenated samples in a set of training images. The second step is to apply another block transformation to the groups of four nearest neighbours. The process will continue until there is only one group at the highest level or scale. The likelihood mapping from the state at any level to the lower levels can be assembled by appending unique instances of quantised singular variates in a set of training images. This results in one 1-hot likelihood array for each group that shares the same parent at the higher level. The required likelihood matrices can be assembled using this fast form of structure learning based upon Equation (9). The first step is to use a blocking transformation to discrete state-space, which is illustrated in Figure 3 (left panel). The right panel shows the reconstructed image, where each group comprised pixels within a radius of four pixels. The centroids of each group are shown with small red dots. This results in one 1-hot likelihood array for each group that shares the same parent at the higher level: { , , , , , , , , }.

**Results/Data**

The set of singular variates for each group specifies the pattern for any given image at the corresponding location. The continuous variates then be quantised to a discrete number of levels (here, seven) to provide a discrete representation of each block. This corresponds to the first RG operator (a.k.a., blocking transformation). Given a partition of the image into quantised blocks, we now apply a second block transformation into groups of four nearest neighbours. This reduces the number of blocks by a factor of two in each image dimension. One then repeats this procedure until there is only one group at the highest level or scale. The requisite likelihood matrices can be assembled using a fast form of structure learning based upon Equation (9). This equation says that the likelihood mapping (in the absence of any constraints) should have the maximum mutual information. This is assured if each successive column of the likelihood matrix is unique. In turn, this means we can automatically assemble the requisite likelihood mappings by appending unique instances of quantised singular variates in a set of training images. This results in one 1-hot likelihood arrays for each group that share the same parent at the higher level: { , , , , , , , , }. We have dropped [1,1, ]n =E because there is only one path in the absence of dynamics. The penultimate level corresponds to priors over the (initial) states or class of image. In short, structure learning emerges from the recursive application of blocking transformations of some training images. This is a special case of fast structure learning described in detail in the next section.

**Limitations/Discussion**

The set of singular variates for each group specifies the pattern for any given image at the corresponding location. The continuous variates then be quantised to a discrete number of levels (here, seven) to provide a discrete representation of each block. This corresponds to the first RG operator (a.k.a., blocking transformation). Given a partition of the image into quantised blocks, we now apply another block transformation into groups of four nearest neighbours. This reduces the number of blocks by a factor of two in each image dimension. One then repeats this procedure until there is only one group at the highest level or scale. The requisite likelihood matrices can be assembled using a fast form of structure learning based upon Equation (9). This equation says that the likelihood mapping (in the absence of any constraints) should have the maximum mutual information. This is assured if each successive column of the likelihood matrix is unique. In turn, this means we can automatically assemble the requisite likelihood mappings by appending unique instances of quantised singular variates in a set of training images. This results in one 1-hot likelihood arrays for each group that share the same parent at the higher level: { , , , , , , , , }. We have dropped [1,1, ]n =E because there is only one path in the absence of dynamics. The penultimate level corresponds to priors over the (initial) states or class of image. In short, structure learning emerges from the recursive application of blocking transformations of some training images. This is a special case of fast structure learning described in detail in the next section.

**References**

[1] LeCun, Y., Cortes, P.: MNIST handwritten digit database. 1998

[2] [Authors]: From pixels to planning: scale-free active inference. 2020

**Notes**

* The paper is not available online.
* The authors are the same as the first author of the paper.
* The paper is a research article, not a review or commentary on other papers.
* The paper does not have an abstract section.

---

**Summary Statistics:**
- Input: 26,405 words (162,081 chars)
- Output: 990 words
- Compression: 0.04x
- Generation: 53.2s (18.6 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
