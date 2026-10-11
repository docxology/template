# part_II — Authored unit

The canonical chapters and unit introduction in this directory are fully authored. Their order, display titles, labs, and question banks come from [`../config.yaml`](../config.yaml). Each chapter develops assumptions, worked mathematics, an actual model or fixture figure, a lab with a solution, and answered practice questions.

Run `scripts/audit_textbook_quality.py --require-complete` from the project directory to verify completion across the whole configured book. Use `scripts/scaffold_chapter.py` only to create missing new draft files; its tests use separate temporary fixtures. The canonical structure uses `units:`, and older `parts:` configurations require migration.

See the [authoring appendix](../appendices/appendix_authoring_guide.md) for source custody, primary references, computation checks, and extending the book.
