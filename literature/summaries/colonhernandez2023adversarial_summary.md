# Adversarial Transformer Language Models for Contextual Commonsense Inference

**Authors:** Pedro Colon-Hernandez, Henry Lieberman, Yida Xin, Claire Yin, Cynthia Breazeal, Peter Chin

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [colonhernandez2023adversarial.pdf](../pdfs/colonhernandez2023adversarial.pdf)

**Generated:** 2025-12-03 03:29:55

---

**Overview/Summary**

The paper proposes a new approach to contextual commonsense inference by combining three knowledge bases (KBs): ConceptNet, ATOMIC 2020, and GLUCOSE. The authors first describe the challenges in the current state of the art for performing joint inference on multiple KBs. They then introduce their proposed method that involves converting each assertion into a tuple format with four fields: subject, relation, object, and specificity. This is followed by aligning the tuples from all three KBs to the same set of stories (ROCStories corpus) using vectorization and nearest neighbors. The aligned KBs are then shufﬂed together and used as training data for a contextual commonsense inference model that performs joint inference. They also propose a new approach to generate missing speciﬁcity in ATOMIC 2020, which is the opposite problem of GLUCOSE (i.e., it does not provide speciﬁc instances of general templates). The paper concludes by discussing the potential applications and future work for this new method.

**Key Contributions/Findings**

The main contributions of the paper are the following. First, the authors propose a new approach to perform joint inference on multiple KBs that can be applied to any number of KBs. Second, they show how to generate missing speciﬁcity in ATOMIC 2020. The proposed method is based on the idea of using the GLUCOSE KB as the gold standard for generating general and speciﬁc assertions from the other two KBs. The authors also provide a new approach to generate speciﬁc instances of the templates that are used by the GLUCOSE KB, which is the opposite problem of what ATOMIC 2020 does (i.e., it provides general versions of rules). These contributions can be applied to any number of KBs.

**Methodology/Approach**

The authors use a tuple format with four fields: subject, relation, object, and specificity. The speciﬁcity is whether the assertion is about speciﬁc entities in the aligned story or if it is a general version of an assertion. This can be seen as whether the assertion is a general template with variables (i.e., a general instance) or a speciﬁc instance of this template. To make the difference between speciﬁc and general assertions clear, they give the following example. Using the same story as before: John is a regular person who has a dog. John, every day, goes out to walk his dog.  . From here, we can infer the speciﬁc assertion:  “John is capable of walking his dog”. The assertion is speciﬁc because it ﬁlls out a broadly applicable template that speaks about John and his dog from the story. From the sentence, we can also infer the general version of the assertion:  “Someone_  who has Something_  (that is a dog) enables Someone_  to walk the Something_  (that is a dog)”. This latter assertion is general because it speaks in a template format that contains variables. The authors use this story and target sentence as an example, but they do not provide any details about how the alignment of the tuples from all three KBs to the same set of stories was done.

**Results/Data**

The authors do not report any results or data for the proposed method. They only describe the approach and its potential applications.

**Limitations/Discussion**

The paper does not discuss the limitations of the proposed method, but it mentions some future work that could be conducted. The authors propose to use this new method to perform joint inference on multiple KBs in other areas such as natural language processing (NLP) or computer vision (CV). They also mention that they do not implement the approach for generating general speciﬁcity from ConceptNet, but it is possible to run a classiﬁer that would determine whether a given set of tokens is a person, place, object, among others. With this information we could ﬁll out, as an example, the template that GLUCOSE broadly utilize which is:  {Category}({Description}), relation, {Possibly Other Category} ({Possibly Other Description}). From ConceptNet, we could ﬁnd the relation:  “a dog, IsA, animal”. A general version of this assertion can be  “Something_ (that is a dog), IsA, Something_ (that is an animal)”. Although the authors describe this process, they do not implement it in their work. The authors also mention that they could possibly use this method to generate speciﬁc instances of the templates that are used by the GLUCOSE KB, which is the opposite problem of what ATOMIC 2020 does (i.e., it provides general versions of rules). These contributions can be applied to any number of KBs. The authors also propose a new approach to generate speciﬁc assertions for ATOMIC 2020 we can do the following. We can ﬁrst identify variables (PersonX, PersonY , etc.) that are present in the general templates that are used by the GLUCOSE KB. With this information we could ﬁll out, as an example, the template that GLUCOSE broadly utilize which is:  {Category}({Description}), relation, {Possibly Other Category} ({Possibly Other Description}). From ConceptNet, we could ﬁnd the relation:  “a dog, IsA, animal”. A general version of this assertion can be  “Something_ (that is a dog), IsA, Something_ (that is an animal)”. Although the authors describe this process, they do not implement it in their work. The authors also mention that they could possibly use this method to generate speciﬁc instances of the templates that are used by the GLUCOSE KB, which is the opposite problem of what ATOMIC 2020 does (i.e., it provides general versions of rules). These contributions can be applied to any number of KBs.

**Limitations/Discussion**

The paper does not discuss the limitations of the proposed method. It mentions that the authors do not implement the approach for generating general speciﬁcity from ConceptNet, but it is possible to run a classiﬁer that would determine whether a given set of tokens is a person, place, object, among others. With this information we could ﬁll out, as an example, the template that GLUCOSE broadly utilize which is:  {Category}({Description}), relation, {Possibly Other Category} ({Possibly Other Description}). From ConceptNet, we could ﬁnd the relation:  “a dog, IsA, animal”. A general version of this assertion can be  “Something_ (that is a dog), IsA, Something_ (that is an animal)”. Although the authors describe this process, they do not implement it in their work. The authors also mention that they could possibly use this method to generate speciﬁc instances of the templates that are used by the GLUCOSE KB, which is the opposite problem of what ATOMIC 2020 does (i.e., it provides general versions of rules). These contributions can be applied to any number of KBs. The authors also propose a new approach to generate speciﬁc assertions for ATOMIC 2020 we can do the following. We can ﬁrst identify variables (PersonX, PersonY , etc.) that are present in the general templates that are used by the GLUCOSE KB. With this information we could ﬁll out, as an example, the template that GLUCOSE broadly utilize which is:  {Category}({Description}), relation, {Possibly Other Category} ({Possibly Other Description}). From ConceptNet, we could ﬁnd the relation:  “a dog, IsA, animal”. A general version of this assertion can be  “Something_ (that is a dog), IsA, Something_ (that is an animal)”. Although the authors describe this process, they do not implement it in their work. The authors also mention that they could possibly use this method to generate speciﬁc instances of the templates that are used by the GLUCOSE KB, which is the opposite problem of what ATOMIC 2020 does (i.e., it provides general versions of rules). These contributions can be applied to any number of KBs.

---

**Summary Statistics:**
- Input: 15,494 words (98,492 chars)
- Output: 1,238 words
- Compression: 0.08x
- Generation: 62.2s (19.9 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
