# Data

Static project data lives here. Generated data belongs under `output/data/`.

`claim_ledger.yaml` records local claims that should stay tied to config, source, or generated artifacts. Add rows when manuscript prose starts relying on a new durable source fact.

Method claims need evidence too. If a fork expands `madlib.method_protocol`, `pipeline_phases`, `quality_probes`, `failure_modes`, or `audit_rules` in a way that supports a new claim, add a claim-ledger row pointing to the config key, source module, generated artifact, or external record that makes the claim reviewable.

Review-packet claims should point to generated output surfaces, not just prose. Include data, reports, figures, validation reports, and output statistics when the method says a reviewer can audit the handoff.
