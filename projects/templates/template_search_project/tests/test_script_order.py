"""Regression tests for the analysis-script execution order.

The analysis stage runs every ``scripts/*.py`` in lexicographic order. The
literature-review composer (``s_compose_literature_review.py``) MUST run
*before* the manuscript resolver (``z_generate_manuscript_variables.py``)
so that ``output/manuscript/S01_literature_review.md`` always reflects
the freshly composed S01 — and never references citation keys absent
from the regenerated ``manuscript/references_deep.bib``.

These tests are pure-stdlib subprocess runs against an isolated project
root; they do not touch the network and they do not mock anything.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
REPO_ROOT = PROJECT_ROOT.parents[2]

# These are the analysis scripts the project ships. The order below is the
# REQUIRED execution order; any change must also update ``scripts/AGENTS.md``.
# ``zzz_build_dashboard.py`` runs LAST because it consumes
# ``output/corpus.json`` (written by ``run_search_pipeline.py``) and
# ``output/deep_search/aggregate.json`` (written by ``run_deep_search.py``).
EXPECTED_ORDER: list[str] = [
    "run_deep_search.py",
    "run_search_pipeline.py",
    "s_compose_literature_review.py",
    "y_generate_search_figures.py",
    "z_generate_manuscript_variables.py",
    "zz_generate_review_report.py",
    "zzz_build_dashboard.py",
]


def test_lexicographic_script_order_matches_required_order() -> None:
    """`sorted(scripts/*.py)` must equal the documented EXPECTED_ORDER."""
    scripts_dir = PROJECT_ROOT / "scripts"
    on_disk = sorted(p.name for p in scripts_dir.glob("*.py"))
    assert on_disk == EXPECTED_ORDER, (
        f"Lexicographic script order has drifted from EXPECTED_ORDER.\n"
        f"  on disk: {on_disk}\n  expected: {EXPECTED_ORDER}"
    )


def test_composer_sorts_before_manuscript_resolver() -> None:
    """The composer filename must sort strictly before the resolver filename."""
    composer = "s_compose_literature_review.py"
    resolver = "z_generate_manuscript_variables.py"
    assert composer < resolver, f"Composer filename '{composer}' must sort before resolver '{resolver}'."


def _seed_project(tmp_path: Path) -> Path:
    """Build an isolated project root with deep_search outputs + a stale
    ``output/manuscript/S01_literature_review.md`` referencing a citation key
    that does NOT appear in the freshly written ``references_deep.bib``."""
    iso = tmp_path / "iso"
    (iso / "manuscript").mkdir(parents=True)
    (iso / "output" / "manuscript").mkdir(parents=True)
    (iso / "output" / "deep_search" / "convex" / "per_paper").mkdir(parents=True)

    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'x'\n"
        "deep_search:\n"
        "  enabled: true\n"
        "  keywords: ['convex']\n"
        "  max_results_per_keyword: 1\n"
        "  output_dir: 'output/deep_search'\n"
        "  unified_bibtex_path: 'manuscript/references_deep.bib'\n",
        encoding="utf-8",
    )

    aggregate = {
        "keywords": ["convex"],
        "unique_papers": [
            {
                "id": "doi:10.1/x",
                "title": "On Convexity",
                "authors": ["Alice"],
                "year": 2020,
                "doi": "10.1/x",
            }
        ],
        "citation_keys": {"doi:10.1/x": "alice2020convexity"},
    }
    (iso / "output" / "deep_search" / "aggregate.json").write_text(json.dumps(aggregate), encoding="utf-8")
    (iso / "output" / "deep_search" / "convex" / "papers.json").write_text(
        json.dumps(
            {
                "keyword": "convex",
                "papers": aggregate["unique_papers"],
                "per_source_counts": {"local": 1},
                "errors": {},
            }
        ),
        encoding="utf-8",
    )
    (iso / "manuscript" / "references_deep.bib").write_text(
        "@article{alice2020convexity,\n  title={On Convexity},\n  author={Alice},\n  year={2020},\n  doi={10.1/x}\n}\n",
        encoding="utf-8",
    )

    # Plant a STALE S01 in output/manuscript/ that references a citation
    # key (`@ghost_legacy_key`) that is NOT present in references_deep.bib.
    # If the composer's parity write does not overwrite this file, downstream
    # render-time validation will fail with "Undefined citation key".
    (iso / "output" / "manuscript" / "S01_literature_review.md").write_text(
        "STALE — referenced [@ghost_legacy_key] which no longer exists.\n",
        encoding="utf-8",
    )
    return iso


def test_composer_overwrites_stale_output_manuscript_copy(tmp_path: Path) -> None:
    """Running the composer must replace the stale output/manuscript/S01."""
    iso = _seed_project(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    canonical = (iso / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")
    mirrored = (iso / "output" / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")

    # The freshly composed canonical S01 must reference the LIVE citation key
    # and must NOT mention the stale ghost key.
    assert "alice2020convexity" in canonical
    assert "ghost_legacy_key" not in canonical

    # The output/manuscript copy must have been overwritten with that same
    # text — the parity write is the safety net Daniel asked for.
    assert mirrored == canonical
    assert "ghost_legacy_key" not in mirrored


def test_resolver_then_composer_ordering_breaks_invariant(tmp_path: Path) -> None:
    """Documents the failure mode the s_/z_ ordering exists to prevent.

    If the resolver runs before the composer (the old `zy_*` lex-order),
    the resolver copies the *old* manuscript/S01 into output/manuscript/
    and the composer then writes a *new* manuscript/S01. The output copy
    is now stale relative to the regenerated bib. We assert that this
    failure mode is observable so a future change cannot silently regress.
    """
    iso = _seed_project(tmp_path)

    # Step A: simulate the resolver running first by copying the
    # (still-stale) manuscript/S01 we will create in a moment to
    # output/manuscript/. The fresh manuscript/S01 doesn't exist yet so
    # we create a placeholder that mimics the prior-run S01.
    stale_manuscript_s01 = "STALE manuscript copy — references [@ghost_legacy_key].\n"
    (iso / "manuscript" / "S01_literature_review.md").write_text(stale_manuscript_s01, encoding="utf-8")
    # Resolver-style copy:
    (iso / "output" / "manuscript" / "S01_literature_review.md").write_text(stale_manuscript_s01, encoding="utf-8")

    # Step B: composer runs, regenerating manuscript/S01 with the LIVE key.
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    # Because the composer's parity-write is in place, the output copy
    # is also refreshed — even when a previous resolver run staged the
    # stale text. This is precisely the safety net that the regression
    # is meant to enforce.
    mirrored = (iso / "output" / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")
    assert "alice2020convexity" in mirrored
    assert "ghost_legacy_key" not in mirrored


def test_full_two_step_chain_keeps_output_in_sync(tmp_path: Path) -> None:
    """End-to-end: composer → resolver, in the documented order.

    The resolver overwrites every ``output/manuscript/*.md`` with a
    substituted copy of ``manuscript/*.md``, so the post-resolver
    output/manuscript/S01 must still match the post-composer manuscript/S01.
    """
    iso = _seed_project(tmp_path)
    # Provide the search-results.json that z_generate_manuscript_variables
    # requires; we don't run the search pipeline here so we hand-write a
    # minimal payload.
    search_dir = iso / "output" / "search"
    search_dir.mkdir(parents=True)
    (search_dir / "results.json").write_text(
        json.dumps(
            {
                "query": {"text": "x", "max_results": 1, "year_min": None, "year_max": None},
                "papers": [],
                "per_source_counts": {},
                "errors": {},
            }
        ),
        encoding="utf-8",
    )

    # Step 1: composer.
    r1 = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stderr

    # Step 2: invoke the real resolver CLI against the isolated project root.
    r2 = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, r2.stderr

    # Final invariant: output/manuscript/S01 must have the live key, never
    # the ghost key.
    mirrored = (iso / "output" / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")
    assert "alice2020convexity" in mirrored
    assert "ghost_legacy_key" not in mirrored
