#!/usr/bin/env python3
"""Build handbook JSON artifacts from the fixture corpus (thin orchestrator)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

project_root = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.core.logging_utils import get_logger

from src.corpus_io import load_corpus
from src.handbook_md import (
    build_full_handbook_body,
    build_glossary_md,
    build_toc_md,
)
from src.metrics import build_metrics_report
from src.synthesis import synthesize

logger = get_logger(__name__)
fixture_path = project_root / "data" / "fixtures" / "riverbend_area.yaml"
out_data = project_root / "output" / "data"
out_md = project_root / "output" / "data" / "handbook_body.md"


def main() -> None:
    out_data.mkdir(parents=True, exist_ok=True)

    corpus = load_corpus(fixture_path)
    synth = synthesize(corpus)
    metrics = build_metrics_report(synth)

    outline_payload = [
        {
            "section_id": s.section_id,
            "title": s.title,
            "depth": s.depth,
            "theme_ids": list(s.theme_ids),
        }
        for s in synth.sections
    ]

    report_path = out_data / "handbook_report.json"
    outline_path = out_data / "area_outline.json"
    report_path.write_text(
        json.dumps(
            {
                "metrics": metrics,
                "outline": outline_payload,
                "gaps": list(synth.gaps),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    outline_path.write_text(json.dumps(outline_payload, indent=2) + "\n", encoding="utf-8")

    body = build_full_handbook_body(synth)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(body, encoding="utf-8")

    glossary_path = out_data / "theme_glossary.md"
    glossary_path.write_text(build_glossary_md(corpus), encoding="utf-8")

    toc_path = out_data / "handbook_toc.md"
    toc_path.write_text(build_toc_md(synth), encoding="utf-8")

    logger.info("Wrote %s", report_path)
    logger.info("Wrote %s", outline_path)
    logger.info("Wrote %s", out_md)
    logger.info("Wrote %s", glossary_path)
    logger.info("Wrote %s", toc_path)
    print(str(report_path))
    print(str(outline_path))
    print(str(out_md))
    print(str(glossary_path))
    print(str(toc_path))


if __name__ == "__main__":
    main()
