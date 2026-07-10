# Abstract

This exemplar demonstrates a **data descriptor** workflow in which the schema,
file inventory, provenance chain, license boundary, and validation gate are
treated as first-class research artifacts rather than afterthoughts. It ships a
small, public, synthetic demonstration dataset (two CSV files under
`data/fixtures/`) and a machine-readable descriptor
(`data/example_descriptor.json`) that declares each file's media type, sha256
checksum, and row count alongside a six-field data dictionary with typed
constraints. A tested validation library (`src/data_descriptor/`) checks the
descriptor's shape, safety, and completeness; recomputes each declared checksum
and row count against the bytes on disk; and emits a deterministic,
metadata-only release manifest suitable for pre-publication review. Every figure
and quantitative claim in this manuscript is produced by that library and
regenerated on demand, so the prose describes structure and provenance rather
than transcribing values that would drift. This is a template with a
demonstration dataset: it makes no scientific claim about the data, only about
how to describe and release a dataset responsibly.



---



# Introduction {#sec:introduction}

A *data descriptor* (or data paper) publishes a dataset as a citable research
object. Unlike an analysis paper, its contribution is not a statistical finding
but a **contract**: a precise, machine-readable account of what the dataset
contains, how it was produced, how it is licensed, and what quality guarantees
it carries. The FAIR guiding principles — Findable, Accessible, Interoperable,
Reusable [@wilkinson2016fair] — frame why this matters: a dataset is only
reusable to the extent that its structure and provenance are legible to both
humans and machines.

## What this template provides

This exemplar packages the recurring moving parts of a data descriptor so that a
fork can start from a working, tested baseline:

- A **schema / data dictionary**: named fields with declared types,
  nullability, units, and value constraints (patterns, enumerations, numeric
  bounds).
- A **file inventory**: each shipped file with its media type, a sha256
  checksum, and a row count.
- A **provenance chain**: the ordered steps and agents that produced the release.
- A **license boundary**: an explicit reuse license, and the discipline of
  publishing *metadata and checksums* rather than bundling restricted bytes.
- A **validation gate**: a tested library that rejects malformed, unsafe, or
  incomplete descriptors and verifies declared checksums against real bytes.

## Scope and honesty

The shipped dataset is **synthetic and deliberately small** — it exists to make
the workflow runnable and testable, not to support any empirical claim. Its
values are generated deterministically. Accordingly, this manuscript restricts
its claims to dataset *structure, provenance, quality, and release readiness*.
When a real dataset is forked in, the same validation and figure code applies
unchanged; only the descriptor and fixture files are replaced. The sections that
follow describe the demonstration dataset ([@sec:data]), its schema
([@sec:schema]), its provenance ([@sec:provenance]), and the quality gate that
binds the descriptor to the bytes it names ([@sec:quality]), and close with
usage and forking notes ([@sec:usage]).



---



# Data description {#sec:data}

The demonstration dataset consists of two comma-separated files under
`data/fixtures/`, described by the machine-readable descriptor
`data/example_descriptor.json`:

- `fixtures/measurements.csv` — one row per synthetic sample, with a bounded
  measurement, an assignment group, a capture instrument, and a collection date.
- `fixtures/subjects.csv` — one row per synthetic subject, with an enrollment
  site and date. Each measurement references a subject through the `subject_id`
  foreign key.

## File inventory

The descriptor declares each file's media type, sha256 checksum, and row count.
[@fig:file_inventory] shows the declared row counts, read directly from the
descriptor by `file_inventory_rows()` in `src/data_descriptor/figures.py` and
plotted by the thin analysis script
[`scripts/generate_figures.py`](../scripts/generate_figures.py).

![File inventory: declared row counts per file, from `file_inventory_rows()`. The measurement table is the larger of the two files; the subject table is its dimension companion. Both are declared as `text/csv`. The bar values are the row counts recorded in the descriptor, not re-derived here — the quality gate ([@sec:quality]) is where declared and actual counts are reconciled.](figures/file_inventory.png){#fig:file_inventory}

Running the script regenerates the figures under `manuscript/figures/`; the prose
below and in later sections describes what those artifacts show. Because the
figures are produced from the descriptor and the fixture bytes, they cannot drift
from the data without the tests and the quality gate noticing.

## Release boundary

The descriptor is deliberately a *metadata* object. For a real dataset, the
descriptor and its checksums can be published even when the underlying bytes are
access-controlled: the checksums let a downstream user verify integrity once they
obtain the files through the appropriate channel. In this template the fixture
bytes are public and small, so they are shipped alongside the descriptor and used
to demonstrate end-to-end verification.



---



# Schema and data dictionary {#sec:schema}

The descriptor's `fields` list is the dataset's **data dictionary**: it names
each column of the primary measurement table and declares its type, nullability,
optional unit, and value constraints. [@fig:schema_overview] renders this
dictionary directly from the descriptor via `schema_table_rows()` in
`src/data_descriptor/figures.py`.

![Field schema / data dictionary: one row per declared field, with type, nullability, unit, and a compact constraint label, from `schema_table_rows()`. Identifier fields carry regular-expression patterns; the categorical fields carry closed enumerations; the quantitative field carries a unit and numeric bounds. The table is generated from `data/example_descriptor.json` and cannot silently disagree with it.](figures/schema_overview.png){#fig:schema_overview}

## Field contract

The six declared fields exercise the constraint vocabulary the validator
understands:

- **`sample_id`** (`string`, not null) — the primary key, constrained to the
  pattern `^S[0-9]{3}$`.
- **`subject_id`** (`string`, not null) — foreign key into `fixtures/subjects.csv`,
  constrained to `^P[0-9]{3}$`.
- **`group`** (`category`, not null) — a closed enumeration of `control` and
  `treatment`.
- **`value`** (`number`, not null) — the measurement, carrying the unit
  `normalized_score` and numeric bounds `[0, 1]`.
- **`collected_on`** (`date`, not null) — an ISO-8601 collection date.
- **`instrument`** (`category`, not null) — a closed enumeration of `sensor_a`
  and `sensor_b`.

## Schema fingerprint

`descriptor_fingerprint()` reduces the field list to a stable, order-independent
sha256 fingerprint over `(name, type, nullable)` triples. Reordering the fields
leaves the fingerprint unchanged, so two descriptors with the same schema hash
identically regardless of authoring order — the property is asserted directly in
the test suite. The fingerprint is what lets a release manifest reference "the
schema" by a single value that changes if and only if the field contract changes.

## Constraint validation

The validator flags quantitative fields that lack a unit, categorical fields that
lack allowed values, enumerations that are present but empty, numeric bounds where
the minimum exceeds the maximum, and patterns declared on non-text fields. On the
shipped descriptor none of these fire — the data dictionary above is complete, so
the readiness score is unpenalised (see [@sec:quality]).



---



# Provenance {#sec:provenance}

Provenance records *how the release came to be*. The descriptor's `provenance`
list is an ordered chain of steps, each naming the agent responsible.
[@fig:provenance_flow] renders that chain via `provenance_steps()` in
`src/data_descriptor/figures.py`.

![Provenance chain: the ordered steps that produced the release, from `provenance_steps()`. Each box is a declared step; the label beneath is the responsible agent. The chain runs left to right from raw collection to the packaged, metadata-only release manifest.](figures/provenance_flow.png){#fig:provenance_flow}

## Methods: the provenance chain

The provenance chain is this descriptor's methods section — it records the
generation and processing methodology step by step. The shipped descriptor
declares four steps:

1. **collect** — a synthetic fixture generator emits the deterministic
   measurement and subject tables.
2. **clean** — identifiers are normalized and the measurement range is bounded.
3. **validate** — the descriptor is checked for schema, constraint, and
   byte-level agreement.
4. **package** — the metadata-only release manifest is emitted.

## Why depth matters

The validator treats provenance shorter than two steps as a warning — a release
that records only "we have the data" but not "how it was produced and checked" is
thinner than a reusable descriptor should be. The four-step chain here pairs a
collection origin with an explicit validation and packaging trail, which is the
minimum a downstream reuser needs to judge whether the dataset was produced the
way they require. For a real dataset, these steps would cite concrete tools,
versions, and operators rather than the template's synthetic agents.



---



# Quality validation {#sec:quality}

The quality gate is what separates a descriptor that merely *claims* to describe a
dataset from one that *provably* does. It has two layers: structural validation of
the descriptor, and byte-level reconciliation of the descriptor against the files
it names.

## The validation gate reacts to defects

`validate_descriptor()` emits severity-tagged findings for missing required keys,
unsafe or duplicate file paths, malformed checksums, unknown media types,
duplicate or malformed fields, constraint violations, missing primary keys, and
thin provenance. `build_descriptor_report()` folds these into a readiness score,
penalising each error and warning.

To show the gate is not vacuous, [@fig:quality_gate] compares the shipped fixture
against a deliberately-perturbed copy produced by `demo_broken_descriptor()`
(which strips the license, corrupts a checksum, zeroes a row count, and removes a
unit). The clean fixture produces zero findings; the perturbed demo produces
several errors and warnings.

![Quality gate: validation findings by severity for the clean fixture descriptor (left, zero findings) versus a deliberately-broken demonstration copy (right). The demonstration perturbation is clearly named in code and never treated as real data — it exists only to prove the gate reacts. Counts come from `severity_counts()`.](figures/quality_gate.png){#fig:quality_gate}

## Descriptor↔file verification

A checksum is only meaningful if something checks it. `verify_descriptor_files()`
recomputes the sha256 digest and data-row count of every declared file that is
present on disk and compares them to the descriptor's declarations, reporting each
file as `verified`, `checksum_mismatch`, `row_mismatch`, or `absent`. Files a
descriptor references but does not bundle are reported as `absent` rather than as
failures — verification is asserted only for bytes that are actually present, which
is what makes the metadata-only release boundary honest.

[@fig:checksum_verification] shows this reconciliation for the shipped fixture:
both files verify, declared and actual row counts agree, and each recomputed
checksum matches its declaration, so the readiness score is unpenalised.

![Descriptor↔file verification: declared versus recomputed row counts and checksum agreement per file, from `verify_descriptor_files()`. Both shipped fixture files verify against their bytes on disk; the title reports the descriptor's readiness score. If a fixture file were edited without updating the descriptor, the corresponding row would flip to a mismatch status and the test suite would fail.](figures/checksum_verification.png){#fig:checksum_verification}

## Machine-readable release manifest

`build_release_bundle_manifest()` packages the above into a deterministic,
JSON-ready manifest containing the schema fingerprint, per-file checksums and row
counts, field-level unit/bounds/enumeration summaries, provenance steps, and the
readiness verdict — carrying metadata and checksums, never the dataset bytes. The
thin script
[`scripts/generate_release_artifacts.py`](../scripts/generate_release_artifacts.py)
writes this manifest (plus the readiness report and constraint summary) under
`output/reports/` for pre-publication review.

## Validation evidence

Every capability above is exercised by the zero-mock `tests/` suite: structural
validation and negative controls, order-independent schema fingerprints,
byte-level verification against real temporary files, figure-data preparation, and
an integration test that runs the figure script end to end and asserts real PNGs
are written. Coverage exceeds the 90% project gate with no mocks.



---



# Usage notes {#sec:usage}

## Regenerating the artifacts

From the monorepo root, regenerate the figures and the release-review artifacts:

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
uv run python projects/templates/template_data_descriptor/scripts/generate_release_artifacts.py
```

The first writes the five figures under `manuscript/figures/`; the second writes
the descriptor readiness report, field-constraint summary, and metadata-only
release manifest under `output/reports/`. Both are thin orchestrators: all
computation lives in the tested `src/data_descriptor/` package.

## Forking in a real dataset

To adapt this template to a real dataset:

1. Replace the fixture files under `data/fixtures/` with your data files (or, for
   restricted data, leave them out and publish descriptor + checksums only).
2. Edit `data/example_descriptor.json`: update `name`, `license`, the `files`
   inventory (path, media type, sha256 checksum, row count), the `fields` data
   dictionary, `primary_key`, and the `provenance` chain.
3. Recompute each file's checksum and row count and record them in the
   descriptor. For present files, `verify_descriptor_files()` will confirm the
   descriptor matches the bytes; a mismatch fails the test suite.
4. Extend field constraints (patterns, enumerations, numeric bounds, units)
   before publishing real data, and keep the provenance chain honest — cite real
   tools, versions, and operators.

Use `scripts/audit/copy_exemplar.py` from the monorepo to fork the template
cleanly, and keep `domain_profile.yaml` and `experiment_plan.yaml` aligned with
your dataset.

## Boundaries and claims

This is a template with a synthetic demonstration dataset. Its claims are limited
to dataset structure, schema completeness, provenance depth, license state,
byte-level integrity, and release readiness — never to any empirical effect in the
data. When you fork it, keep that discipline: a data descriptor earns trust by
describing a dataset precisely and verifiably, not by over-claiming what the
dataset shows.



---



# References {#sec:references}

This exemplar draws on established data-publishing practice: the FAIR guiding
principles for reusable data [@wilkinson2016fair], datasheets-style structured
dataset documentation [@gebru2021datasheets], the W3C PROV data model for
provenance [@moreau2013prov], and the Frictionless Data Package container format
for machine-readable descriptors [@frictionless2023datapackage].

The bibliography lives in [`manuscript/references.bib`](references.bib) and is
read by Pandoc during PDF render; every `[@key]` citation in the manuscript is
resolved against that file. To validate that `references.bib` is syntactically
clean and complete:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_data_descriptor/manuscript/references.bib --strict
```
