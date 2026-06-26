# Abstract {#sec:abstract}

This paper presents `Deterministic bounded AutoResearch for a small MNIST neural-network task`, a public template exemplar that
turns an AutoResearch loop into ordinary reproducible research infrastructure.
The case study is intentionally small but concrete: `2000` training
and `500` test images from `MNIST handwritten digit database` are evaluated by the
bounded `small MNIST neural-network classification` loop. The run evaluates
`4` of `5` proposed candidates,
including `Tiny patch-attention classifier`, selects
`exp-mlp-tanh-64` (`MLP`,
`50890` parameters), and improves `test_accuracy` from
`82.6%` to `89.4%`
(`6.8%` absolute change). The validated diagnostic layer reports
macro F1 `89.4%`, bootstrap accuracy interval
`86.4% to 92.0%`, Brier score `0.161`,
negative log likelihood `0.361`, top-2 accuracy
`95.6%`, and exact McNemar p-value `0.000`.
The same pipeline writes proposal, candidate, run, review, benchmark, evidence,
figure, confusion-matrix, statistical-summary, probability-quality, and
security-integrity artifacts from declared output contracts; uses
`0` LLM calls at USD `0.00` cost; and records
`7` configured stages, `6` supported
local-artifact claims, and `78` required artifacts.
The local security attestation status is `passed`,
with `0` checksum mismatch(es). The final
readiness status is `passed`, with review gates deferred to a
human rather than self-approved by the generated run.
