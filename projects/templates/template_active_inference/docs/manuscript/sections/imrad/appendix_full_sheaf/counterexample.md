The appendix counterexample fragment points to
`output/reports/counterexample_matrix.json`, the expected-failure matrix that
keeps promoted validation gates falsifiable. It currently records
{{counterexample_count}} known-bad fixtures, and the hydrated pass flag is
`{{counterexample_all_known_bad_fail}}`, meaning those fixtures are expected to
fail rather than sneak through a positive-control gate.

This row is the negative-control ledger for the sheaf. Each counterexample names
a promoted track, target validation gate, mutation, and observed expected-failure
status. A new live track without a counterexample row is therefore visibly
incomplete in the track-improvement scope.
