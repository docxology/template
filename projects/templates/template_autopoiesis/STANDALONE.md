# STANDALONE.md — template_autopoiesis

## Standalone Usage Guide

This project is designed to run as part of the `template` repository checkout, but the core generation pipeline can be used standalone with some limitations.

---

## What is vendored into child projects

When `materialize()` generates a child project, the following are vendored from the parent `src/`:

| Vendored artifact | Source | Child path |
|---|---|---|
| `primitives/__init__.py` | `src/primitives/__init__.py` | `primitives/__init__.py` |
| `primitives/base.py` | `src/primitives/base.py` | `primitives/base.py` |
| `primitives/{domain}.py` | `src/primitives/{domain}.py` | `primitives/{domain}.py` |
| `figures.py` | `src/figures.py` | `figures.py` |

The child project does **not** require the parent `src/` at runtime — it runs entirely from its vendored sources.

Optional infrastructure modules (logging, glossary_gen, figure_manager, etc.) are vendored as single-file stubs if the source is not found in the `infrastructure/` tree.

---

## What is NOT vendored

- `infrastructure/rendering` — PDF/HTML rendering pipeline
- `infrastructure/validation` — prerender validation
- Multi-file subpackages — only single-file modules are supported

---

## Running standalone (outside repo)

```bash
# From the template_autopoiesis project directory:
pip install numpy matplotlib pyyaml qrcode pillow
pytest tests/ -q

# To generate a child project:
python scripts/autopoiesis.py materialize --out-root /tmp/children
```

---

## Limitations

- **No PDF rendering** of child manuscripts — requires Chrome/Pandoc via infrastructure
- **Byte-stability** is within-platform only (same Python, same OS)
- **Multi-file vendor deps** are not supported — single-file stubs only
- **Grammar config** must be at `manuscript/config.yaml` — path is not configurable at CLI level
- **Infrastructure deps** (logging, glossary_gen, etc.) will be stubs if infrastructure tree is absent
