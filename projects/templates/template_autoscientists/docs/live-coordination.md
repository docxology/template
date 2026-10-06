# Bounded local coordination

The default `--mode core` comparison uses the unchanged deterministic proposer.
`--mode live` requires an explicitly selected installed Ollama model and a literal
loopback HTTP endpoint. It never acquires a model, invokes a paid API, modifies
source, or substitutes the deterministic proposer after a provider failure.

From the public platform checkout, with the selected model already installed and
a loopback-only Ollama service running:

```bash
uv run python projects/templates/template_autoscientists/scripts/run_search_comparison.py \
  --mode live --model llama3.2:1b --endpoint http://127.0.0.1:11434 \
  --output-dir output/.pipeline/local_coordination/selected-run
```

Each arm executes 3–6 sequential proposals (default 6). The coordinated arm
assigns axes to three teams and uses the shared champion, experiment log,
dead-end registry, ranking, confirmation, and stagnation reorganization. Its live
stagnation window is 3 and retirement threshold is 2 so the bounded experiment
can exercise those decisions. The baseline uses one team, the same objective,
starting point and three confirmation seeds, with structural coordination off.
Every generation reads the actual preceding state. A strict JSON response may
change one assigned axis by a finite nonzero step in `[-1,1]`; executable code,
paths, coercions, duplicate keys, and retired directions are rejected.

The arms have equal generation, prediction-token, request-time and experiment
ceilings. Each arm also has an equal independent wall-clock ceiling, at most half
the total run deadline, so the baseline does not receive a different nominal
allowance from running second. Actual consumed tokens and time are recorded and
can differ. Both perform three
initial objective evaluations and three per experiment. The run has an explicit
total deadline (at most 600 seconds) and each request a supervised process-group
deadline (at most 60 seconds). The provider must report the selected model, a
complete nonempty generation, a positive exact integer token count within the
prediction ceiling, and the same installed SHA-256 digest before and after every
generation and across both arms.

`coordination_receipt.json` records settings, configs, the exact source manifest,
active producer source, model digest, every prompt context, provider request and
response bytes, execution diagnostics, proposals, observed outcomes, actual
budgets, clean/reported summaries, and artifact hashes. Both full arm transcripts
are retained. Null and negative effects pass when the contract is satisfied;
successful operation makes no claim of general coordination superiority. The
separate offline comparison is labeled `core` with zero model generations.

The source manifest binds all public platform Python under `infrastructure/` and
`scripts/`, root package/lock metadata, and the actual active producer source.
Controller and workers check the loaded implementation before each generation
and before receipt promotion. Workers compare their exact source closure and
interpreter/distribution identity with the controller's declaration before and
after the provider call. Hashing replacement disk files cannot certify a stale
loaded implementation; source or environment drift fails the run. Trusted
startup seeds the actual already-running main CodeType and audits each later
selected public module before execution. All captured execution records are
compared with held current source, including removed modules, and cache bytes
are checked against their execution-time SHA. The main-frame comparison binds
compiled code fields, not original comment bytes.

Receipts live only beneath a fresh
`output/.pipeline/local_coordination/<run>/` directory. Historical publication
outputs remain intact. Missing service/model or exhausted deadlines return 75
with a blocked receipt; responding malformed generations or source drift return
1 with failed evidence. A failed arm prevents the baseline or summary from being
presented as complete acceptance.

The ordinary suite uses a real controlled loopback HTTP conformance oracle and
actual supervised Python workers. Its synthetic identity demonstrates contract
behavior and is not installed-model acceptance. For actual model acceptance:

```bash
TEMPLATE_AUTOSCIENTISTS_MODEL=llama3.2:1b \
TEMPLATE_AUTOSCIENTISTS_ENDPOINT=http://127.0.0.1:11434 \
uv run pytest projects/templates/template_autoscientists/tests/search/test_live_comparison.py \
  -m requires_ollama --no-cov
```

This test fails when the required capability is missing. Neither the short live
run nor the deterministic testbed reproduces long-running open-ended scientific
agents, host code mutation, parallel compute, or external publication.
