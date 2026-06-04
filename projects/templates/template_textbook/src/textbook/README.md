# `src/textbook/`

Core book engine (Layer-2 logic for this exemplar).

**Contents.** `config.py` loads `manuscript/config.yaml` (single source of truth); `models.py` worked formalisms; `content.py` scaffolds/validates sections against the per-chapter contract; `toc.py` auto-numbers parts→chapters; `constants.py` holds CITATION_KEYS / GLOSSARY_ANCHORS / REQUIRED_TOKENS.

**Contract.** All structure/logic lives here; scripts only orchestrate. No mocks; deterministic; 90% coverage.

See the project [`AGENTS.md`](../../AGENTS.md) and [`docs/`](../../docs/) for the full map.
