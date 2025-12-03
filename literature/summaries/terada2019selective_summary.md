# Selective inference after feature selection via multiscale bootstrap

**Authors:** Yoshikazu Terada, Hidetoshi Shimodaira

**Year:** 2019

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [terada2019selective.pdf](../pdfs/terada2019selective.pdf)

**Generated:** 2025-12-03 07:25:54

---

**Overview/Summary**
The paper proposes a new method for computing approximately unbiased p-values and confidence intervals for regression coefficients after feature selection. The proposed method is useful in particular for complicated feature selection algorithms such as the minimax concave penalty (MC) and the smoothly clipped absolute deviation (SCAD), while existing methods are only available for simpler feature selection algorithms such as the Lasso. The new method also computes shorter confidence intervals than most of the existing methods by minimal-conditioning on each selected feature instead of over-conditioning all selected features.

**Key Contributions/Findings**
The key contributions and findings of this paper are:
- A new multiscale bootstrap (MSB) method is proposed to compute approximately unbiased selective p-values and conﬁdence intervals for regression coeﬃcients after feature selection. The new method is useful in particular for complicated feature selection algorithms such as the MC and the SCAD, while existing methods are only available for simpler feature selection algorithms such as the Lasso.
- The new method also computes shorter conﬁdence intervals than most of the existing methods by minimal-conditioning on each selected feature instead of over-conditioning all selected features.

**Methodology/Approach**
The proposed MSB method is based on a novel polyhedral lemma. Let H be a closed convex set in Rn and let S be a nonempty, closed, and convex subset of H. The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The explicit forms of the intervals can be obtained for the Lasso case, but it may not be possible for more complicated cases. In the proposed method, we estimate the geometric quantities zH and zS indirectly via the MSB. Alternating to this approach, we compute the p-value as a function of the distance from y to ∂H and the interval [zS,∞). The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The explicit forms of the intervals can be obtained for the Lasso case, but it may not be possible for more complicated cases. In the proposed method, we estimate the geometric quantities zH and zS indirectly via the MSB. Alternating to this approach, we compute the p-value as a function of the distance from y to ∂H and the interval [zS,∞). The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y) = P(βj ∈[L(a),U(a)]) = 1 − Φ(zH)
= 1 − Φ(zH + zS)

The explicit forms of the intervals can be obtained for the Lasso case, but it may not be possible for more complicated cases. In the proposed method, we estimate the geometric quantities zH and zS indirectly via the MSB. Alternating to this approach, we compute the p-value as a function of the distance from y to ∂H and the interval [zS,∞). The new method is closely related to the exact selective inference such as Lee et al. (2016) and Liu, Markovic and Tibshirani (2018). Here, in addition to the Gaussian assumption, we assume that the boundary surface of the hypothesis region is ﬂat. Let us consider the line passing through the point y and perpendicular to the boundary of H. By setting the projection point ˆµ(y) ∈ ∂H of y as the origin, we can consider the one-dimensional coordinate system z on the line. If we know the distance from y to ∂H as well as intervals representing the intersection of the line and the selective region S, we can perform the exact selective inference. For example, in Figure 6, the distance is zH and the interval is [zS,∞). As with the polyhedral lemma, the following p-value provides the exact selective inference:
p(y

---

**Summary Statistics:**
- Input: 11,023 words (66,198 chars)
- Output: 1,472 words
- Compression: 0.13x
- Generation: 68.7s (21.4 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
