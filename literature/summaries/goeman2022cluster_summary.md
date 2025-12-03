# Cluster extent inference revisited: quantification and localization of brain activity

**Authors:** Jelle J. Goeman, Paweł\ Górecki, Ramin Monajemi, Xu Chen, Thomas E. Nichols, Wouter Weeda

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [goeman2022cluster.pdf](../pdfs/goeman2022cluster.pdf)

**Generated:** 2025-12-03 06:07:16

---

**Overview/Summary**

The paper presents a novel closed testing procedure for cluster extent inference based on random field theory (RFT) and permutation tests. The goal is to control the false discovery rate (FDR) over all clusters, which is called the "familywise error rate" in this context. This approach provides a more powerful alternative to the classic voxel-wise inference that controls the FDR over all voxels. The authors show that the closed testing procedure can be used for both cluster extent and voxel-wise inference by choosing different values of kM, where kM is the smallest value such that P(χM∩Z)>kM)≤α. The paper also provides a fast algorithm to find the z-score threshold corresponding to any given kM. 

**Key Contributions/Findings**

The main contributions of this paper are: (1) the closed testing procedure for cluster extent inference; and (2) the fast algorithm for finding the z-threshold corresponding to a given kM. The authors show that the TDP lower bound for a set V is simply the fraction of voxelwise signiﬁcant voxels among the voxels inV, which is the TDP upper bound for the same setV when kM=0. 

**Methodology/Approach**

The paper starts with some background information on cluster extent inference and its relationship to classic voxel-wise inference. The authors then present the closed testing procedure for cluster extent inference based on RFT. The main result is that the TDP lower bound for a set V is simply the fraction of voxelwise signiﬁcant voxels among the voxels inV, which is the TDP upper bound for the same setV when kM=0. In addition, they provide a fast algorithm to find the z-threshold corresponding to any given kM using permutations. 

**Results/Data**

The paper presents some results on the performance of the proposed closed testing procedure and the fast algorithm for finding the z-threshold. The authors use 1064 tests based on cuboid data. They found that nearly 50% of tests were completed with no error, and the worst errors of 5-6% has only ∼5% of tests. A more detailed summary is depicted in Figure 5 with boxplots of errors for each value of kM, where the 0% represents no error. The results obtained on cuboid tests indicate that nearly half of the tests were completed with no error, and the worst errors of 5-6% has only ∼5% of tests. 

**Limitations/Discussion**

The paper does not discuss any limitations or future work.

**References**

None given in this text.

---

**Summary Statistics:**
- Input: 21,332 words (119,324 chars)
- Output: 396 words
- Compression: 0.02x
- Generation: 25.9s (15.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
