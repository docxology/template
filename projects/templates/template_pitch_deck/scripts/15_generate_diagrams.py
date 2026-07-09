#!/usr/bin/env python3
"""Stage-02 analysis: render this deck's Mermaid diagrams to PNG.

Runs before ``20_render_decks.py`` (lexicographically between the content
audit and the render step) so the diagram files referenced by
``manuscript/deck_content_*.yaml`` (``figure: <name>.png``) exist before
rendering needs them. Uses
``infrastructure.rendering.mermaid_figure.render_mermaid_png`` — the first
standalone (non-manuscript-fence) Mermaid-to-PNG capability in this
repository's infrastructure layer.

Three real, repo-accurate diagrams (not decorative-only): the two-layer
architecture split (infra vs. project `src/`), the actual core pipeline
stage sequence (see root `CLAUDE.md`'s "Pipeline Stages" section — this is
the real 10-stage core+LLM path, not an invented simplification), and the
integrity-gate stack this project and repo actually enforce (each node names
a real file/policy — see the node labels' source comments below).

Deterministic: re-running with unchanged diagram source is a no-op (the
renderer skips re-invoking ``mmdc`` when the ``.mmd`` sidecar already matches).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("pitch_deck.diagrams")

TWO_LAYER_ARCHITECTURE_MERMAID = """flowchart TB
    subgraph L1["Layer 1 — infrastructure/"]
        R["rendering/<br/>PDF · HTML · PPTX · DOCX · EPUB"]
        V["validation/"]
        P["publishing/"]
        PR["provenance/"]
    end
    subgraph L2["Layer 2 (projects/*/src/)"]
        A["template_template<br/>introspection + metrics"]
        B["template_pitch_deck<br/>content + tokens + lint"]
        C["... every other<br/>public exemplar"]
    end
    S["scripts/ — thin orchestrators<br/>(coordinate, no business logic)"]

    L1 --> S
    L2 --> S
    S --> O["output/ — PDF, PPTX,<br/>figures, data"]
"""

# Matches root CLAUDE.md's "Pipeline Stages" section verbatim (the 10-stage
# core+LLM default path) — not an invented simplification. Two rows (not one
# long horizontal chain) so the diagram fills a 16:9 slide's height, not just
# a thin strip across the middle.
PIPELINE_STAGES_MERMAID = """flowchart TB
    subgraph Row1["Core"]
        direction LR
        C[Clean Output] --> E[Environment Setup]
        E --> IT["Infrastructure Tests"]
        IT --> PT["Project Tests<br/>90% coverage floor"]
        PT --> A["Run Analysis"]
    end
    subgraph Row2["Render, validate, ship"]
        direction LR
        R["Render PDF"] --> V["Validate Output"]
        V --> L1["LLM Review<br/>(optional)"]
        L1 --> L2["LLM Translations<br/>(optional)"]
        L2 --> O["Copy Outputs"]
    end
    Row1 --> Row2
"""

# Every node names a mechanism that actually exists in this repo — none are
# aspirational. Source per node: token audit -> src/token_resolution.py;
# cliche lint -> src/cliche_lint.py; diligence citations -> src/diligence_audit.py;
# no-mocks policy -> root CLAUDE.md "No Mocks Policy"; coverage floors ->
# this project's pyproject.toml (fail_under=90) + .github/workflows/ci.yml
# (--cov-fail-under=60); reproducibility invariant -> reportlab
# Canvas(invariant=1) in infrastructure/rendering/slide_deck.py; drift check
# -> scripts/audit/check_template_drift.py; security scan ->
# bandit -c bandit.yaml; confidentiality invariant ->
# scripts/audit/check_tracked_all.py.
#: Subgraph titles kept deliberately short (single line at the rendered
#: width) — a prior longer two-line title ("This deck's own content gates",
#: "Build-correctness gates (every exemplar)") wrapped and was clipped by the
#: row of boxes rendered immediately below it (red-team finding, 2026-07-09,
#: confirmed via page raster on both the medium and long decks).
INTEGRITY_STACK_MERMAID = """flowchart TB
    subgraph G1["This deck's gates"]
        direction LR
        TOK["Token audit<br/>fail on any {{TOKEN}}"] --> CLI["Cliche lint<br/>word-boundary denylist"]
        CLI --> DIL["Diligence audit<br/>citation coverage"]
    end
    subgraph G2["Build-correctness gates"]
        direction LR
        NM["No-mocks policy"] --> COV["Coverage floors<br/>90% project / 60% infra"]
        COV --> REP["Reproducibility invariant<br/>byte-identical PDF"]
    end
    subgraph G3["Repo-wide gates"]
        direction LR
        DRI["Drift check"] --> SEC["Security scan<br/>bandit"]
        SEC --> CONF["Confidentiality invariant<br/>tracked-project guard"]
    end
    G1 --> G2 --> G3
"""

DIAGRAMS: dict[str, str] = {
    "two_layer_architecture.png": TWO_LAYER_ARCHITECTURE_MERMAID,
    "pipeline_stages.png": PIPELINE_STAGES_MERMAID,
    "integrity_stack.png": INTEGRITY_STACK_MERMAID,
}


def main(argv: list[str] | None = None) -> int:
    from infrastructure.rendering.mermaid_figure import render_mermaid_png

    root = project_root()
    figures_dir = root / "output" / "figures"

    for filename, source in DIAGRAMS.items():
        output_path = figures_dir / filename
        try:
            render_mermaid_png(source, output_path)
        except Exception as exc:  # noqa: BLE001 - mmdc/Chrome absence is environment-dependent, not a code bug
            logger.warning(
                "Could not render %s (mmdc/Chrome unavailable in this environment) — "
                "diagram slides referencing it will render without a figure: %s",
                filename,
                exc,
            )
            continue
        logger.info("Wrote diagram: %s", output_path)
        print(output_path)

    return 0  # environment-dependent mmdc/Chrome absence is never a hard failure


if __name__ == "__main__":
    sys.exit(main())
