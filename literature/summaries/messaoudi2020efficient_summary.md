# Efficient embedding network for 3D brain tumor segmentation

**Authors:** Hicham Messaoudi, Ahror Belaid, Mohamed Lamine Allaoui, Ahcene Zetout, Mohand Said Allili, Souhil Tliba, Douraied Ben Salem, Pierre-Henri Conze

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [messaoudi2020efficient.pdf](../pdfs/messaoudi2020efficient.pdf)

**Generated:** 2025-12-02 09:44:28

---

**Overview/Summary**

The paper proposes a novel 3D brain tumor segmentation network based on an efficient encoder-decoder architecture. The authors argue that the learning transfer from weights trained on 2D natural images can be exploited for processing 3D medical images, which is not well-explored in the current literature. They design an embedding network to directly embed a 3D image into a feature space and then use this representation for 3D brain tumor segmentation. The authors also claim that the learning technique can be improved by robustifying it, keeping the original size of the data and stacking the 4 modalities together.

**Key Contributions/Findings**

The main contributions of the paper are the following:

1. **Efficient encoder-decoder architecture**: The authors design an efficient encoder-decoder network for 3D brain tumor segmentation. This is a novel contribution that is not well-explored in the current literature.
2. **Learning transfer from 2D to 3D**: The authors argue that the learning technique can be improved by robustifying it, keeping the original size of the data and stacking the 4 modalities together. However, no experimental results are provided to support this claim.

**Methodology/Approach**

The authors design an encoder-decoder network for 3D brain tumor segmentation. The proposed network is based on a U-Net architecture with a feature pyramid that consists of a series of convolutional and downsampling layers. The authors also use the group normalization (GN) technique to improve the performance of the network.

**Results/Data**

The authors provide experimental results for the 3D brain tumor segmentation task. The proposed network is compared with several state-of-the-art methods, including the original U-Net architecture, the ResNeXt-50 model and the EfficientNetB0 model. The comparison is based on a dataset of 4 modalities (T1, T2, FLAIR, and ADC). The authors also provide the results for the segmentation task with the original size of the data.

**Limitations/Discussion**

The paper does not discuss any limitations or future work in detail. However, it is mentioned that the learning technique can be improved by robustifying it, keeping the original size of the data and stacking the 4 modalities together. The authors also claim that the results for the segmentation task with the original size of the data are better than those with the 3D image inputs. This is a novel contribution that is not well-explored in the current literature.

**References**

The paper provides references to several papers, including the following:

1. [1] S. Bakas, H. Akbari, A. Sotiras, M. Bilello, M. Rozycki, and J. Kirby et al., "Segmentation labels and radiomic features for the pre- operative scans of the tcga-gbm collection," The Cancer Imaging Archive, 2017.
2. [2] S. Bakas, H. Akbari, A. Sotiras, M. Bilello, M. Rozycki, and J. Kirby et al., "Segmentation labels and radiomic features for the pre- operative scans of the tcga-gbm collection," The Cancer Imaging Archive, 2017.
3. [3] S. Bakas, M. Reyes, A. Jakab, S. Bauer, M. Rempfler, and A. Crimi et al., "Identifying the best machine learning algorithms for brain tumor segmentation, progression assessment, and overall survival prediction in the brats challenge," arXiv preprint arXiv:1811.02629, 2018.
4. [5] O. Ronneberger, P. Fischer, and T. Brox, "U-Net: Convolutional networks for biomedical image segmentation," In International Conference on Medical Image Computing and Computer-Assisted Intervention, pages 234–241, 2015. DOI: 10.1007/978-3-319-24574-4 28.
5. [12] Mingxing Tan and Quoc V. Le, "Eﬃcientnet: Rethinking model scaling for convolutional neural networks," In Proceedings of Machine Learning Research, editor, 36th International Conference on Machine Learning (ICML), volume 97, pages 10691–10700, Long Beach, California, USA, 2019.
6. [13] K. Souadih, A. Belaid, D. Ben Salem, and P. H. Conze, "Automatic forensic identiﬁcation using 3D sphenoid sinus segmentation and deep characterization," Med. Biol. Eng. Comput., 58:291–306, 2020.
7. [14] R. Zaouche, A. Belaid, S. Aloui, B. Solaiman, L. Lecornu, D. Ben Salem, and S. Tliba, "Semi-automatic method for low-grade gliomas segmentation in magnetic resonance imaging," IRBM, 39(2):116–128, 2018.
8. [15] R. Zaouche, A. Belaid, S. Aloui, B. Solaiman, L. Lecornu, D. Ben Salem, and S. Tliba, "Semi-automatic method for low-grade gliomas segmentation in magnetic resonance imaging," IRBM, 39(2):116–128, 2018.
9. [10] O. Ronneberger, P. Fischer, and T. Brox, "U-Net: Convolutional networks for biomedical image segmentation," In International Conference on Medical Image Computing and Computer-Assisted Intervention, pages 234–241, 2015. DOI: 10.1007/978-3-319-24574-4 28.
10. [9] Andriy Myronenko. "3D MRI brain tumor segmentation using autoencoder regularization." BrainLes@MICCAI, 2:311–320, 2018. DOI:10.1007/978-3-030-11726-9 28.

**References**

[1] S. Bakas, H. Akbari, A. Sotiras, M. Bilello, M. Rozycki, and J. Kirby et al., "Segmentation labels and radiomic features for the pre- operative scans of the tcga-gbm collection." The Cancer Imaging Archive, 2017. DOI:10.7937/TCIA.2017.KLXWJJ1Q.
[2] S. Bakas, H. Akbari, A. Sotiras, M. Bilello, M. Rozycki, and J. Kirby et al., "Segmentation labels and radiomic features for the pre- operative scans of the tcga-gbm collection." The Cancer Imaging Archive, 2017. DOI:10.7937/TCIA.2017.GJQ7R0EF.
[3] S. Bakas, M. Reyes, A. Jakab, S. Bauer, M. Rempfler, and A. Crimi et al., "Identifying the best machine learning algorithms for brain tumor segmentation, progression assessment, and overall survival prediction in the brats challenge." arXiv preprint arXiv:1811.02629, 2018.
[5] O. Ronneberger, P. Fischer, and T. Brox. U-Net: Convolutional networks for biomedical image segmentation. In International Conference on Medical Image Computing and Computer-Assisted Intervention, pages 234–241, 2015. DOI:10.1007/978-3-319-24574-4 28.
[12] Mingxing Tan and Quoc V. Le. "Eﬃcientnet: Rethinking model scaling for convolutional neural networks." In Proceedings of Machine Learning Research, editor, 36th International Conference on Machine Learning (ICML), volume 97, pages 10691–10700, Long Beach, California, USA, 2019.
[13] K. Souadih, A. Belaid, D. Ben Salem, and P. H. Conze. "Automatic forensic identiﬁcation using 3D sphenoid sinus segmentation and deep characterization." Med. Biol. Eng. Comput., 58:291–306, 2020.
[14] R. Zaouche, A. Belaid, S. Aloui, B. Solaiman, L. Lecornu, D. Ben Salem, and S. Tliba. "Semi-automatic method for low-grade gliomas segmentation in magnetic resonance imaging." IRBM, 39(2):116–128, 2018.
[15] R. Zaouche, A. Belaid, S. Aloui, B. Solaiman, L. Lecornu, D. Ben Salem, and S. Tliba. "Semi-automatic method for low-grade gliomas segmentation in magnetic resonance imaging." IRBM, 39(2):116–128, 2018.
[10] Andriy Myronenko. "3D MRI brain tumor segmentation using autoencoder regularization." BrainLes@MICCAI, 2:311–320, 2018. DOI:10.1007/978-3-030-11726-9 28.

**References**

[1] S. Bakas, H. Akbari, A. Sotiras, M. Bilello, M. Rozycki, and J. Kirby et al., "Segmentation labels and radiomic features for the pre- operative scans of the tcga-gbm collection." The Cancer Imaging Archive,

---

**Summary Statistics:**
- Input: 3,563 words (22,825 chars)
- Output: 1,036 words
- Compression: 0.29x
- Generation: 82.6s (12.5 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
