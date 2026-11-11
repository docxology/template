"""Canonical executable capabilities that declarations cannot weaken.

Project declarations add policy and may narrow selection. Renaming a stable
key cannot remove a known target's live, opt-in, cleanup, or nonreuse duties.
Unrecognized project scripts retain their explicit declared contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from collections.abc import Iterable


@dataclass(frozen=True)
class TargetContract:
    tags: tuple[str, ...] = ()
    opt_in: bool = False
    cacheable: bool = True
    clean: bool = False
    infrastructure_tests: bool = False
    validation_boundary: bool = False


_SCRIPTS = {
    "scripts/pipeline/stage_00_setup.py": TargetContract(("core", "setup"), cacheable=False),
    "scripts/pipeline/stage_01_test.py": TargetContract(("core", "tests"), cacheable=False),
    "scripts/pipeline/stage_02_analysis.py": TargetContract(("core",), cacheable=False),
    "scripts/pipeline/stage_03_render.py": TargetContract(("core",)),
    "scripts/pipeline/stage_04_validate.py": TargetContract(("core",), validation_boundary=True),
    "scripts/pipeline/stage_05_copy.py": TargetContract(("core",), cacheable=False),
    "scripts/pipeline/stage_06_llm_review.py": TargetContract(("llm", "live"), cacheable=False),
    "scripts/pipeline/stage_08_connector_search.py": TargetContract(("science", "live"), True, False),
    "scripts/pipeline/stage_09_provenance_record.py": TargetContract(("provenance",), True, False),
    "scripts/pipeline/stage_11_ebook.py": TargetContract(("core", "ebook"), True),
    "scripts/pipeline/stage_12_metadata.py": TargetContract(("core", "metadata"), True, False),
    "scripts/pipeline/stage_13_docxplus.py": TargetContract(("core", "docxplus"), True),
    "scripts/runner/bundle_executable.py": TargetContract(("bundle",), True, False),
    "scripts/runner/archive_publication.py": TargetContract(("archival", "live"), True, False),
}
_METHODS = {
    "_run_clean_outputs": TargetContract(("core", "clean"), cacheable=False, clean=True),
    "run_project_tests": TargetContract(("core", "tests"), cacheable=False),
    "run_infrastructure_tests": TargetContract(("core", "tests"), cacheable=False, infrastructure_tests=True),
}
_UNRECOGNIZED = TargetContract()


def canonical_target_contract(script: str | None, method: str | None, args: Iterable[str] = ()) -> TargetContract:
    """Look up admitted lexical targets, normalizing harmless path spelling."""
    if script is not None:
        normalized = Path(script).as_posix()
        contract = _SCRIPTS.get(normalized, _UNRECOGNIZED)
        if normalized == "scripts/pipeline/stage_01_test.py" and "--infra-only" in args:
            return replace(contract, infrastructure_tests=True)
        return contract
    return _METHODS.get(method or "", _UNRECOGNIZED)


def effective_target_tags(tags: Iterable[str], script: str | None, method: str | None) -> tuple[str, ...]:
    """Preserve declaration order while adding binding executable capabilities."""
    return tuple(dict.fromkeys((*tags, *canonical_target_contract(script, method).tags)))


__all__ = ["TargetContract", "canonical_target_contract", "effective_target_tags"]
