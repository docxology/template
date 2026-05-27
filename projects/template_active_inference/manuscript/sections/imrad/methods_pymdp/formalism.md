Given generative matrices $A,B,C,D$, pymdp computes state beliefs $q(s)$ via variational inference (`infer_states`). The Agent is configured with planning horizon $H =$ {{si_tmaze_policy_len}}, which defines the **policy depth** used when constructing candidate policies (logged as `num_policies` in `output/data/si_tmaze_summary.json`).

This exemplar records belief entropy per step; extending to full expected-free-energy policy selection (`infer_policies`) is documented as a follow-on track.
