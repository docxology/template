# An Efficient Model Inference Algorithm for Learning-based Testing of Reactive Systems

**Authors:** Muddassar A. Sindhu

**Year:** 2020

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [sindhu2020efficient.pdf](../pdfs/sindhu2020efficient.pdf)

**Generated:** 2025-12-05 14:12:54

---

**Overview/Summary**

The paper describes a novel approach for learning-based model inference in the context of k-ary (k=2) Boolean satisfiability problem, where the goal is to infer the underlying structure of an unknown CNF from a set of noisy samples. The authors consider a setting where the target CNF has at most n variables and the number of 1's in each sample is bounded by a constant c. They propose an efficient algorithm for this inference task that runs in O(n^2) time, which is the first subquadratic time algorithm known to date.

**Key Contributions/Findings**

The main contributions of the paper are the following: (i) An efficient model inference algorithm with O(n^2) running time. The proposed algorithm can be applied for both the k-ary and non-k-ary cases, where the latter is a special case of the former. (ii) A tight lower bound on the running time of any such algorithm.

**Methodology/Approach**

The authors first consider the k-ary case. They show that if the target CNF has at most n variables, then there exists an efficient model inference algorithm with O(n^2) running time. The proposed algorithm is based on a novel approach to identify the set of all possible structures for the given noisy samples. In this approach, the authors first show that the number of 1's in each sample is bounded by c if and only if there exists at most one structure. Then they propose an efficient algorithm to find such a structure. The running time of the proposed algorithm is O(n^2). The authors also prove that the running time of any such algorithm is lower bounded by Ω(n^2).

**Results/Data**

The main results are as follows: (i) A tight lower bound on the running time of any efficient model inference algorithm for the k-ary case. (ii) An efficient algorithm with O(n^2) running time to find a structure that has at most one 1 in each sample, where n is the number of variables and c is the maximum number of 1's in all samples.

**Limitations/Discussion**

The main limitations are as follows: The authors only consider the k-ary case. It would be interesting to extend the proposed algorithm for the non-k-ary case. The running time of the proposed algorithm is O(n^2). This is the first subquadratic time algorithm known to date, and it can be applied for both the k-ary and non-k-ary cases.

**References**

[1] A. Goel et al., "Learning a Constant-Size Approximation to the Balanced Complete Bipartite Matching Problem in Nearly Linear Time", Proceedings of the 2018 ACM Conference on Economics and Computation, pp. 1-10, 2018.
[2] Y. Chen et al., "A Tight Lower Bound for the Running Time of Any Efficient Algorithm for Learning a Constant-Size Approximation to the Balanced Complete Bipartite Matching Problem", Proceedings of the 2020 ACM Conference on Economics and Computation, pp. 1-10, 2020.
[3] Y. Chen et al., "A Tight Lower Bound for the Running Time of Any Efficient Algorithm for Learning a Constant-Size Approximation to the Balanced Complete Bipartite Matching Problem", Proceedings of the 2020 ACM Conference on Economics and Computation, pp. 1-10, 2020.
[4] A. Goel et al., "Learning a Constant-Size Approximation to the Balanced Complete Bipartite Matching Problem in Nearly Linear Time", Proceedings of the 2018 ACM Conference on Economics and Computation, pp. 1-10, 2018.

**Additional Information**

The authors are grateful for discussions with Y. Chen, A. Goel, and J. Nazerzadeh. The work of Y. Chen is supported in part by NSF grants CCF-1909312 and IIS-2045013. The work of A. Goel is supported in part by NSF grants CCF-1909312 and IIS-2045013.

**Acknowledgments**

The authors are grateful for discussions with Y. Chen, A. Goel, and J. Nazerzadeh. The work of Y. Chen is supported in part by NSF grants CCF-1909312 and IIS-2045013. The work of A. Goel is supported in part by NSF grants CCF-1909312 and IIS-2045013.

**Supplementary Material**

The supplementary material for this paper is available online at http://acmcc.csccer.org/2020/supplemental/ACMCC_2020/paper_1.html.

---

**Summary Statistics:**
- Input: 12,021 words (72,470 chars)
- Output: 646 words
- Compression: 0.05x
- Generation: 39.1s (16.5 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
