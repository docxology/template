"""Direct leg-deterministic negative controls for ``manuscript.sheaf.semantic_issues``.

``semantic_gluing_issues`` aggregates cross-track disagreement checks. On the
tracked snapshot it returns no issues for these particular checks, so their
issue-append branches only ran when a gate rebuilt state. These tests run the
aggregator against an isolated project-tree copy (see ``direct_recompute_support``)
and inject one specific defect at a time, asserting that the exact disagreement
string -- carrying the injected value -- appears in the returned issue list.

Per tests/AGENTS.md leg-safety we never assert the pristine copy validates as
"current": each assertion binds to the value we injected (e.g. ``saved=424242``),
proving the detector read our defect rather than that the snapshot is clean. All
mutations are byte-for-byte restored in ``finally`` so the module-scoped copy
stays reusable and the git-tracked tree is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.sheaf.semantic_issues import semantic_gluing_issues

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("semantic_issues_tree"))


@pytest.mark.timeout(300)
def test_flags_stale_manuscript_variable(copied_root: Path) -> None:
    """A forged saved manuscript variable is reported stale against the live value."""
    variables_path = copied_root / "output" / "data" / "manuscript_variables.json"
    original = variables_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["sheaf_track_count"] = 424242  # implausible marker value
        variables_path.write_text(json.dumps(payload), encoding="utf-8")
        issues = semantic_gluing_issues(copied_root)
        assert isinstance(issues, list)
        assert any(
            "manuscript variable 'sheaf_track_count' is stale" in issue and "saved=424242" in issue for issue in issues
        ), issues
    finally:
        variables_path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_pymdp_mode_mismatch(copied_root: Path) -> None:
    """A summary/mode that disagrees with analysis_statistics is reported."""
    summary_path = copied_root / "output" / "data" / "si_tmaze_summary.json"
    original = summary_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["mode"] = "__forced_mismatch__"
        summary_path.write_text(json.dumps(payload), encoding="utf-8")
        issues = semantic_gluing_issues(copied_root)
        assert any("pymdp mode mismatch" in issue and "__forced_mismatch__" in issue for issue in issues), issues
    finally:
        summary_path.write_text(original, encoding="utf-8")
