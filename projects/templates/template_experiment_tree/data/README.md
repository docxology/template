# data/

Committed evidence inputs backing the tree's claim ledger. The single file
here is [claim_ledger.yaml](claim_ledger.yaml): one entry per public claim
with the source paths that verify it. `manuscript/config.yaml` points at
this file so generated manuscript tokens bind to these evidence paths.

Regenerate nothing by hand; add a `claims:` entry only together with the
answering tree node it documents.
