"""Binding tests for ``data/claim_ledger.yaml``.

Every claim's ``source`` must resolve to a real file and its ``value`` must
match the live code or manuscript prose. This gate exists because claim-ledger
``source`` strings are free text: a dead module reference (e.g. a non-existent
``src/pipeline.py``) used to slip through with no test noticing — the
evidence-registry collector registers the ledger but does not validate the
source paths. This suite closes that gap.
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
LEDGER = PROJECT_ROOT / "data" / "claim_ledger.yaml"

REQUIRED_FIELDS = {
    "claim_id",
    "kind",
    "value",
    "source",
    "source_tier",
    "freshness",
    "artifact_path",
}


def _load_claims() -> list[dict]:
    payload = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    assert isinstance(payload, dict) and "claims" in payload
    claims = payload["claims"]
    assert isinstance(claims, list) and claims, "claim ledger must not be empty"
    return claims


def _source_path(source: str) -> Path | None:
    """Best-effort extraction of the file path from a free-text source string.

    Handles both ``path/to/file.py export settings`` and
    ``path/to/file.py::function_name`` forms.
    """
    token = (source.split("::", 1)[0].split()[0]) if source else ""
    if not token:
        return None
    candidate = REPO_ROOT / token
    return candidate if candidate.exists() else None


def test_ledger_has_expected_shape():
    claims = _load_claims()
    for claim in claims:
        missing = REQUIRED_FIELDS - set(claim)
        assert not missing, f"claim {claim.get('claim_id')} missing fields: {sorted(missing)}"
        assert claim["source_tier"] in {"project_source", "manuscript_claim"}


def test_every_claim_source_resolves_to_a_real_file():
    claims = _load_claims()
    for claim in claims:
        path = _source_path(claim["source"])
        assert path is not None, f"claim {claim['claim_id']} source does not resolve: {claim['source']!r}"
        assert path.is_file(), f"claim {claim['claim_id']} source is not a file: {path}"


def test_claim_values_bind_to_live_code():
    claims = {c["claim_id"]: c for c in _load_claims()}

    dpi = claims["figure-export-dpi"]
    figures_src = (REPO_ROOT / "projects/templates/template_prose_project/src/figures.py").read_text(encoding="utf-8")
    assert dpi["value"] == 300
    assert "dpi=300" in figures_src, "figure-export-dpi claim no longer matches src/figures.py"

    denominator = claims["citation-density-denominator"]
    checks_src = (REPO_ROOT / "projects/templates/template_prose_project/src/pipeline/checks.py").read_text(
        encoding="utf-8"
    )
    assert denominator["value"] == 1000
    assert "1000.0" in checks_src, "citation-density-denominator claim no longer matches the check"

    sibling = claims["comparison-sibling-word-count"]
    intro = (REPO_ROOT / "projects/templates/template_prose_project/manuscript/01_introduction.md").read_text(
        encoding="utf-8"
    )
    assert sibling["value"] == 200
    assert "sit at 200" in intro, "comparison-sibling-word-count claim no longer matches the prose"
