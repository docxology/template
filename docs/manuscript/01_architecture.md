# Architecture

The template separates shared infrastructure from research projects.
Layer 1 defines the run configuration, orchestration, rendering, and
validation. Layer 2 projects supply domain methods and data, tests,
analysis producers, and manuscript sections. This separation lets a
numerical project produce tables and figures while a prose project
can share the document build machinery. The repository's earlier
publication discusses the architecture and its ergonomics
[@friedman2026template].

Canonical public examples live under `projects/templates/`. Local projects
can be selected by a qualified lifecycle name such as `working/example`.
The qualified name identifies a project independently of the name of its
manuscript folder. The infrastructure manuscript uses the same project
registration mechanism as downstream standalone checkouts
[@template-source].
