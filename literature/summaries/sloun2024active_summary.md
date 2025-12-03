# Active inference and deep generative modeling for cognitive ultrasound

**Authors:** Ruud JG van Sloun

**Year:** 2024

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1109/TUFFC.2024.3466290

**PDF:** [sloun2024active.pdf](../pdfs/sloun2024active.pdf)

**Generated:** 2025-12-02 10:19:52

---

=== OVERVIEW ===

The paper presents a novel approach to cognitive ultrasound imaging and active inference for dynamic scenes in which the target is not fixed but moves within the scene. The authors propose an active inference framework that uses deep generative models to model the underlying unobserved anatomy and the observed multipath clutter, and then use this model to perform information-seeking actions such as beamforming and subsampling.

=== KEY CONTRIBUTIONS/ FINDINGS ===

The main contributions of the paper are:

1. The authors propose a novel active inference framework for cognitive ultrasound imaging that uses deep generative models to model the underlying unobserved anatomy and the observed multipath clutter, and then use this model to perform information-seeking actions such as beamforming and subsampling.

2. They present an application of the proposed approach in which the target is not fixed but moves within the scene. The authors show that heart rate estimation using cognitive adaptive steering remains accurate (within 5 bpm of the ground truth) at about 20 dB lower SNR levels compared to non-adaptive steering, a direct result of the dramatic reduction in beamforming gain when the target moved out of the static beam.

3. They present another application of the proposed approach in which the agent is tasked with the suppression of multipath clutter from (linearly) beamformed RF data patches y in cardiac imaging. The authors show that heart rate estimation using cognitive adaptive steering remained accurate at about 20 dB lower SNR levels compared to non-adaptive steering, a direct result of the dramatic reduction in beamforming gain when the target moved out of the static beam.

4. They present an application of the proposed approach in which the agent is tasked with the selection of k scanlines that maximize expected information gain. The authors show that heart rate estimation using cognitive adaptive steering remained accurate at about 20 dB lower SNR levels compared to non-adaptive steering, a direct result of the dramatic reduction in beamforming gain when the target moved out of the static beam.

=== METHOD/ APPROACH ===

The paper presents an active inference framework for cognitive ultrasound imaging. The authors propose a novel application of this framework that uses deep generative models to model the underlying unobserved anatomy and the observed multipath clutter, and then use this model to perform information-seeking actions such as beamforming and subsampling.

=== RESULTS/ DATA ===

The paper presents two applications of the proposed approach. In the first application, the authors show a real-time implementation of the perception-action loop for a dynamic Doppler target mimicking a beating fetal heart in a lab setup. The results are presented in Figure 3. The information-seeing agent accurately tracks the moving target and retains precise downstream heart-rate estimates by adequately steering the beam and maintaining high Doppler SNR.

The second application is to suppress multipath clutter from (linearly) beamformed RF data patches y in cardiac imaging. In this case, the authors show that heart rate estimation using cognitive adaptive steering remained accurate at about 20 dB lower SNR levels compared to non-adaptive steering, a direct result of the dramatic reduction in beamforming gain when the target moved out of the static beam.

The third application is to select k scanlines that maximize expected information gain. The authors show that heart rate estimation using cognitive adaptive steering remained accurate at about 20 dB lower SNR levels compared to non-adaptive steering, a direct result of the dramatic reduction in beamforming gain when the target moved out of the static beam.

=== LIMITATIONS/DISCUSSION ===

The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 11,072 words (71,102 chars)
- Output: 596 words
- Compression: 0.05x
- Generation: 31.0s (19.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
