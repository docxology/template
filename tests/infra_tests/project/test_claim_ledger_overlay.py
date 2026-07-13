"""Public exemplar claim-ledger overlay contract."""

from pathlib import Path

import yaml

from infrastructure.project.public_scope import public_project_names

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_every_public_exemplar_has_a_valid_claim_ledger() -> None:
    """Every public exemplar exposes at least one source-bound claim row."""
    for project_name in public_project_names(REPO_ROOT):
        ledger = REPO_ROOT / "projects" / project_name / "data/claim_ledger.yaml"
        assert ledger.is_file(), project_name
        payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), project_name
        claims = payload.get("claims")
        assert isinstance(claims, list) and claims, project_name
        for claim in claims:
            assert isinstance(claim, dict), project_name
            assert claim.get("claim_id") or claim.get("id"), project_name
