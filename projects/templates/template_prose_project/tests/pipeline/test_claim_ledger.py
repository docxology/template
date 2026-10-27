"""Binding tests for ``data/claim_ledger.yaml``.

Every claim's ``source`` must resolve to a real file and its ``value`` must
match the live code or manuscript prose. This gate exists because claim-ledger
``source`` strings are free text: a dead module reference (e.g. a non-existent
``src/pipeline.py``) used to slip through with no test noticing — the
evidence-registry collector registers the ledger but does not validate the
source paths. This suite closes that gap.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FIELDS = {
    "claim_id",
    "kind",
    "value",
    "source",
    "source_tier",
    "freshness",
    "artifact_path",
}


def _load_claims(project_root: Path = PROJECT_ROOT) -> list[dict]:
    ledger = project_root / "data" / "claim_ledger.yaml"
    payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
    assert isinstance(payload, dict) and "claims" in payload
    claims = payload["claims"]
    assert isinstance(claims, list) and claims, "claim ledger must not be empty"
    return claims


def _source_path(source: str, project_root: Path = PROJECT_ROOT) -> Path | None:
    """Resolve current code/manuscript claim sources within the own project."""
    tokens = source.split("::", 1)[0].split()
    if not tokens:
        return None
    token = tokens[0]
    relative = Path(token)
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        return None
    if relative.parts[0] not in {"src", "manuscript"}:
        return None
    root = project_root.resolve(strict=True)
    candidate = root / relative
    if any(path.is_symlink() for path in (candidate, *candidate.parents) if path != root and path.is_relative_to(root)):
        return None
    try:
        resolved = candidate.resolve(strict=True)
    except OSError, RuntimeError:
        return None
    return resolved if resolved.is_relative_to(root) and resolved.is_file() else None


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


def _assert_claim_values(project_root: Path = PROJECT_ROOT) -> None:
    claims = {c["claim_id"]: c for c in _load_claims(project_root)}

    dpi = claims["figure-export-dpi"]
    figures_path = _source_path(dpi["source"], project_root)
    assert figures_path is not None, "figure-export-dpi declared source does not resolve"
    figures_src = figures_path.read_text(encoding="utf-8")
    assert dpi["value"] == 300
    assert "dpi=300" in figures_src, "figure-export-dpi claim no longer matches src/figures/figures.py"

    denominator = claims["citation-density-denominator"]
    checks_path = _source_path(denominator["source"], project_root)
    assert checks_path is not None, "citation-density-denominator declared source does not resolve"
    checks_src = checks_path.read_text(encoding="utf-8")
    assert denominator["value"] == 1000
    assert "1000.0" in checks_src, "citation-density-denominator claim no longer matches the check"

    sibling = claims["comparison-sibling-word-count"]
    intro_path = _source_path(sibling["source"], project_root)
    assert intro_path is not None, "comparison-sibling-word-count declared source does not resolve"
    intro = intro_path.read_text(encoding="utf-8")
    assert sibling["value"] == 200
    assert "sit at 200" in intro, "comparison-sibling-word-count claim no longer matches the prose"


def test_claim_values_bind_to_live_code():
    _assert_claim_values()


@pytest.fixture
def standalone_project(tmp_path: Path) -> Path:
    project = tmp_path / "standalone"
    for lane in ("src", "manuscript", "data"):
        shutil.copytree(PROJECT_ROOT / lane, project / lane, ignore=shutil.ignore_patterns("__pycache__"))
    return project


def test_standalone_ledger_retains_real_sources_and_claim_values(standalone_project: Path):
    claims = _load_claims(standalone_project)
    assert {claim["claim_id"]: claim["value"] for claim in claims} == {
        "figure-export-dpi": 300,
        "comparison-sibling-word-count": 200,
        "citation-density-denominator": 1000,
    }
    for claim in claims:
        assert _source_path(claim["source"], standalone_project) is not None
    _assert_claim_values(standalone_project)


def test_claim_source_rejects_external_files_and_foreign_prefixes(standalone_project: Path):
    outside = standalone_project.parent / "outside.py"
    outside.write_text("value = 300\n")
    foreign = standalone_project / "projects/templates/foreign/source.py"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("value = 300\n")
    for source in (
        str(outside),
        "../outside.py",
        "src/../../outside.py",
        "projects/templates/foreign/source.py",
        "",
        ".",
        "   ",
    ):
        assert _source_path(source, standalone_project) is None


def test_claim_source_rejects_missing_and_redirected_sources(standalone_project: Path):
    assert _source_path("src/missing.py", standalone_project) is None
    outside = standalone_project.parent / "outside.py"
    outside.write_text("value = 300\n")
    (standalone_project / "src/redirect.py").symlink_to(outside)
    assert _source_path("src/redirect.py", standalone_project) is None


def test_claim_value_binding_rejects_real_source_tampering(standalone_project: Path):
    source = standalone_project / "src/template_prose_project/figures/figures.py"
    original = source.read_text()
    assert "dpi=300" in original
    source.write_text(original.replace("dpi=300", "dpi=299"))
    with pytest.raises(AssertionError, match="figure-export-dpi claim no longer matches"):
        _assert_claim_values(standalone_project)


def test_claim_value_binding_rejects_ledger_value_tampering(standalone_project: Path):
    ledger = standalone_project / "data/claim_ledger.yaml"
    original = ledger.read_text()
    assert "value: 300" in original
    ledger.write_text(original.replace("value: 300", "value: 301"))
    with pytest.raises(AssertionError):
        _assert_claim_values(standalone_project)


@pytest.mark.parametrize(
    ("claim_id", "wrong_source"),
    [
        ("figure-export-dpi", "src/template_prose_project/pipeline/checks.py"),
        ("citation-density-denominator", "src/template_prose_project/figures/figures.py"),
        ("comparison-sibling-word-count", "src/template_prose_project/pipeline/checks.py"),
    ],
)
def test_claim_value_binding_rejects_wrong_existing_own_source(
    standalone_project: Path, claim_id: str, wrong_source: str
):
    ledger = standalone_project / "data/claim_ledger.yaml"
    payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
    selected = next(claim for claim in payload["claims"] if claim["claim_id"] == claim_id)
    original_path = _source_path(selected["source"], standalone_project)
    assert original_path is not None
    original_bytes = original_path.read_bytes()
    wrong_path = _source_path(wrong_source, standalone_project)
    assert wrong_path is not None and wrong_path != original_path
    selected["source"] = wrong_source
    ledger.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(AssertionError, match=claim_id + " claim no longer matches"):
        _assert_claim_values(standalone_project)
    assert original_path.read_bytes() == original_bytes
