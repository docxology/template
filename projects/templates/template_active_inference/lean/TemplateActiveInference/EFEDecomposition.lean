namespace TemplateActiveInference

/-- Identity residual of an EFE decomposition: `(risk + ambiguity) + (pragmatic + epistemic)`.
Zero exactly when the two canonical EFE decompositions agree. Mirrors the Python
`EFETerms.identity_residual` in `src/simulation/efe_decomposition.py`. -/
def efeIdentityResidual (risk ambiguity pragmatic epistemic : Int) : Int :=
  (risk + ambiguity) + (pragmatic + epistemic)

/-- The EFE additive identity. From the definitional relations
`risk = -entropy - pragmatic` and `epistemic = entropy - ambiguity`,
the residual `(risk + ambiguity) + (pragmatic + epistemic)` collapses to `0`. -/
theorem efe_additive_identity_from_relations
    (entropy pragmatic ambiguity risk epistemic : Int)
    (hrisk : risk = -entropy - pragmatic)
    (hepi : epistemic = entropy - ambiguity) :
    efeIdentityResidual risk ambiguity pragmatic epistemic = 0 := by
  simp only [efeIdentityResidual, hrisk, hepi]
  omega

/-- Equivalent statement: Expected Free Energy `G = risk + ambiguity`
equals the negated value term `-(pragmatic + epistemic)`. -/
theorem efe_total_eq_neg_value
    (entropy pragmatic ambiguity risk epistemic : Int)
    (hrisk : risk = -entropy - pragmatic)
    (hepi : epistemic = entropy - ambiguity) :
    risk + ambiguity = -(pragmatic + epistemic) := by
  omega

/-- Integer witness: per-step EFE terms summed over a length-3 horizon. -/
def efeRiskTerms : List Int := [-3, -1, 0]
def efeAmbiguityTerms : List Int := [2, 1, 1]
def efePragmaticTerms : List Int := [1, 0, -1]
def efeEpistemicTerms : List Int := [0, 0, 0]

/-- Concrete finite witness: the summed-term residual is exactly zero (`decide`). -/
theorem efe_witness_residual_zero :
    efeIdentityResidual
      (efeRiskTerms.foldl (· + ·) 0)
      (efeAmbiguityTerms.foldl (· + ·) 0)
      (efePragmaticTerms.foldl (· + ·) 0)
      (efeEpistemicTerms.foldl (· + ·) 0) = 0 := by
  decide

end TemplateActiveInference
