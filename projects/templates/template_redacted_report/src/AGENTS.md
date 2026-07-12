# src - AGENTS.md

Keep release-safety logic in `src/redacted_report/`. Avoid operational content and keep examples invented. Artifact I/O belongs in `redacted_report/artifacts.py`; it must call the typed domain API and reject unsafe free-form identifiers, replacement text, malformed spans, and undeclared policies before writing public JSON.
