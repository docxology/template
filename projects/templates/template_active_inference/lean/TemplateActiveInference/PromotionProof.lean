namespace TemplateActiveInference

/-- Boolean finite witness for the seven requirements in the track-promotion rule. -/
structure PromotionProof where
  producer : Bool
  artifact : Bool
  manuscriptConsumer : Bool
  typedClaimEvidence : Bool
  semanticRestriction : Bool
  validationGate : Bool
  negativeControl : Bool
  deriving DecidableEq, Repr

/-- A promotion row is complete only when every required evidence lane is present. -/
def PromotionProof.complete (row : PromotionProof) : Bool :=
  row.producer
    && row.artifact
    && row.manuscriptConsumer
    && row.typedClaimEvidence
    && row.semanticRestriction
    && row.validationGate
    && row.negativeControl

theorem promotion_complete_iff_all_fields (row : PromotionProof) :
    row.complete = true ↔
      row.producer = true
        ∧ row.artifact = true
        ∧ row.manuscriptConsumer = true
        ∧ row.typedClaimEvidence = true
        ∧ row.semanticRestriction = true
        ∧ row.validationGate = true
        ∧ row.negativeControl = true := by
  unfold PromotionProof.complete
  simp only [Bool.and_eq_true, and_assoc]

theorem promotion_missing_producer_incomplete
    (row : PromotionProof)
    (h : row.producer = false) :
    row.complete = false := by
  unfold PromotionProof.complete
  simp [h]

theorem promotion_all_fields_complete :
    (PromotionProof.mk true true true true true true true).complete = true := by
  rfl

end TemplateActiveInference
