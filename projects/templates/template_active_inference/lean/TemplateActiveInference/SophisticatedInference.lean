namespace TemplateActiveInference

/-- Planning horizon for sophisticated inference (policy length > 1). -/
def defaultPolicyLen : Nat := 3

theorem sophisticated_requires_horizon :
    defaultPolicyLen > 1 := by decide

end TemplateActiveInference
