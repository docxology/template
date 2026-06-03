namespace TemplateActiveInference

/-- The centered 2x2 Ising coupling entries used by the analytical toy. -/
def isingCouplingEntries : List Int := [1, -1, -1, 1]

def isingCouplingSum : Int := isingCouplingEntries.foldl (· + ·) 0

theorem ising_coupling_sum_zero : isingCouplingSum = 0 := by
  decide

end TemplateActiveInference
