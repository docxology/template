"""Source-bound handoff refusals and pure hosted-origin verdict controls.

Receipt envelopes exercise only schema and exact-Git-Source refusals; they are
not accepted class evidence. Origin verdicts consume
illustrative metadata, not authenticated hosted originals. Hosted qualification
and complete native-cell-union acceptance remain separate production gates.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from infrastructure.publishing.composed_receipt import (
    COMPOSED_RECEIPT_PATH,
    SCHEMA,
    _origin_verdict,
    validate_composed_receipt,
)
from infrastructure.publishing.release_acceptance import MissingAcceptanceHandoff, validate_handoff_inputs
from tests.infra_tests.project.test_public_reference import _git


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    """Commit real version metadata for guards that precede profile resolution."""
    shutil.copyfile(Path(__file__).resolve().parents[3] / "pyproject.toml", tmp_path / "pyproject.toml")
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "add", "--", "pyproject.toml")
    _git(tmp_path, "commit", "--quiet", "-m", "Owned source-bound handoff metadata DATA")
    return tmp_path


@pytest.fixture
def handoff_root(tmp_path: Path) -> Path:
    """Input-only controls need the real version metadata, not full Source."""
    shutil.copyfile(Path(__file__).resolve().parents[3] / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def _revision(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").decode().strip()


def _written(root: Path, payload: dict[str, str]) -> Path:
    """Write only the envelope consumed by these early refusal controls."""
    target = root / COMPOSED_RECEIPT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


@pytest.mark.parametrize("values", [("123", "", ""), ("", "789", ""), ("", "", "a" * 64), ("123", "789", "")])
def test_partial_hosted_handoff_is_refused(values: tuple[str, str, str], handoff_root: Path) -> None:
    """A partly supplied carrier must refuse rather than fall through to composed."""
    with pytest.raises(ValueError, match="every one of run id"):
        validate_handoff_inputs(handoff_root, *values, composed_receipt=COMPOSED_RECEIPT_PATH)


def test_no_handoff_at_all_is_refused(handoff_root: Path) -> None:
    """Publication never proceeds without a named evidence shape."""
    with pytest.raises(MissingAcceptanceHandoff):
        validate_handoff_inputs(handoff_root, "", "", "")


def test_composed_receipt_with_a_stale_commit_is_refused(source_root: Path) -> None:
    """A receipt bound to another commit must refuse."""
    target = _written(source_root, {"schema_version": SCHEMA, "source_commit": "0" * 40})
    with pytest.raises(ValueError, match="different source commit"):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_with_an_unsupported_schema_is_refused(source_root: Path) -> None:
    """A foreign schema must refuse rather than be interpreted loosely."""
    target = _written(
        source_root,
        {"schema_version": "template-composed-acceptance-v0", "source_commit": _revision(source_root)},
    )
    with pytest.raises(ValueError, match="schema is unsupported"):
        validate_composed_receipt(source_root, target)


def test_origin_verdict_refuses_a_run_that_did_not_succeed() -> None:
    """Control: a claimed success whose run concluded failure is refused, not downgraded."""
    with pytest.raises(ValueError, match="did not succeed"):
        _origin_verdict(
            {"status": "completed", "conclusion": "failure", "head_sha": "0" * 40}, expected_head_sha="0" * 40
        )
    for conclusion in ("cancelled", "timed_out", "action_required"):
        with pytest.raises(ValueError, match="did not succeed"):
            _origin_verdict(
                {"status": "completed", "conclusion": conclusion, "head_sha": "0" * 40}, expected_head_sha="0" * 40
            )


def test_origin_verdict_requires_the_exact_commit() -> None:
    """A successful run for a different commit cannot support this class."""
    with pytest.raises(ValueError, match="bound to another commit"):
        _origin_verdict(
            {"status": "completed", "conclusion": "success", "head_sha": "1" * 40}, expected_head_sha="0" * 40
        )


def test_origin_verdict_treats_an_unobservable_origin_as_declared() -> None:
    """An unresolvable observation is a claim, never proof."""
    assert _origin_verdict({"status": None, "conclusion": None}, expected_head_sha="0" * 40) == "declared"


def test_origin_verdict_refuses_a_run_that_has_not_completed() -> None:
    """A resolved run still in progress cannot have produced a claimed pass."""
    with pytest.raises(ValueError, match="is not completed"):
        _origin_verdict({"status": "in_progress", "conclusion": "", "head_sha": "0" * 40}, expected_head_sha="0" * 40)


def test_origin_verdict_accepts_a_completed_successful_run() -> None:
    """The positive side of the verdict, so the refusals above are meaningful."""
    assert (
        _origin_verdict(
            {"status": "completed", "conclusion": "success", "head_sha": "0" * 40}, expected_head_sha="0" * 40
        )
        == "observed"
    )

