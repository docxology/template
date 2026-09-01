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
