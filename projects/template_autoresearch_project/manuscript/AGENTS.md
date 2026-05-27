# Manuscript Notes

Do not hard-code generated loop counts in manuscript prose. Add variables in
`src/manuscript_tokens_core.py` or `src/manuscript_tokens_ml.py` (re-exported via
`src/manuscript_variables.py`) and verify token coverage in
`tests/test_manuscript_variables.py`.
