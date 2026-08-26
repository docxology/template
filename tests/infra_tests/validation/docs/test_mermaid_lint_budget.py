"""Coverage-provenance invariant tests for the mermaid lint total budget.

The repo-wide mermaid sweep previously used a fixed 300s wall-clock budget.
As the documentation surface grew past ~250 diagrams, loaded machines began
tripping that budget *before* reaching later blocks, producing failures that
indicted specific diagrams ("total timeout ... before rendering
<file>:<line>") which were never attempted. These tests pin the scaling
contract that replaces the fixed guess.
"""

import os
from pathlib import Path

import infrastructure.validation.docs.mermaid_lint as ml


def test_scaled_budget_floors_at_legacy_fixed_budget_for_small_trees() -> None:
    # Trees at or below the legacy break-even block count keep the exact old
    # default: 300s.
    assert ml.scaled_total_timeout(0) == 300.0
    assert ml.scaled_total_timeout(100) == 300.0
    assert ml.scaled_total_timeout(150) == 300.0


def test_scaled_budget_grows_linearly_above_break_even() -> None:
    # 268 discovered diagrams is today's live surface; 2s/block must exceed
    # the legacy floor there, and grow linearly beyond it.
    assert ml.scaled_total_timeout(268) == 536.0
    assert ml.scaled_total_timeout(400) == 800.0
    # Monotonicity as a cheap oracle against future edits.
    values = [ml.scaled_total_timeout(n) for n in (150, 200, 268, 400, 1000)]
    assert values == sorted(values)


def test_scaled_budget_is_capped() -> None:
    # A discovery bug counting non-block matches must not yield an unbounded
    # budget: the cap binds regardless of count.
    assert ml.scaled_total_timeout(10**9) == 3600.0


def test_raised_env_floor_raises_the_computed_floor() -> None:
    """Raising TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT raises the floor.

    The module reads the variable once at import; this pins the documented
    contract by adjusting the parsed scalar directly (no reload flakiness).
    """
    saved = ml._MMDC_TOTAL_TIMEOUT_SECONDS
    try:
        ml._MMDC_TOTAL_TIMEOUT_SECONDS = 900.0
        # 268 * 2 = 536 < raised floor 900 -> floor wins.
        assert ml.scaled_total_timeout(268) == 900.0
        # Scaling can still exceed the raised floor for big trees.
        assert ml.scaled_total_timeout(600) == 1200.0
    finally:
        ml._MMDC_TOTAL_TIMEOUT_SECONDS = saved


def _install_stub_mmdc(root: Path, *, body: str = "#!/bin/sh\nexit 3\n") -> Path:
    """Install a real executable mmdc stub at the repo-local discovery path."""
    bin_dir = root / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake = bin_dir / "mmdc"
    fake.write_text(body, encoding="utf-8")
    fake.chmod(0o755)
    return fake


def test_validate_blocks_scales_default_budget_from_discovered_blocks(tmp_path) -> None:
    """The None default computes its budget from len(blocks).

    A real file-backed mmdc stub is installed at the repo-local discovery path
    and the working directory switches to the temp tree, so validate_blocks
    resolves and executes a real CLI with no module globals replaced. The stub
    exits 3 immediately; every failure must carry that code — a pre-render
    total-budget failure would surface as 124 with a "before rendering"
    message instead.
    """
    md = tmp_path / "p.md"
    md.write_text("```mermaid\nflowchart TB\n  A-->B\n```\n", encoding="utf-8")
    blocks = ml.find_mermaid_blocks([tmp_path])
    assert len(blocks) == 1

    _install_stub_mmdc(tmp_path)
    original_chdir = os.getcwd()
    os.chdir(tmp_path)
    try:
        failures = ml.validate_blocks(blocks, timeout_seconds=30)
    finally:
        os.chdir(original_chdir)

    for f in failures:
        assert f.returncode == 3
        assert "before rendering" not in f.stderr


def test_explicit_caller_budget_bypasses_scaling(tmp_path) -> None:
    """An explicit total_timeout_seconds is honored verbatim.

    Known-wrong control: pass an explicit 2s budget with a sleeping mmdc. The
    caller value must reach the batch loop unchanged — the failure is a
    per-budget 124 ("batch timed out after 2") rather than any scaled budget
    computed by validate_blocks itself.
    """
    md = tmp_path / "q.md"
    md.write_text("```mermaid\nflowchart LR\n  X-->Y\n```\n", encoding="utf-8")
    _install_stub_mmdc(
        tmp_path,
        body="#!/usr/bin/env python3\nimport time\ntime.sleep(30)\n",
    )

    original_chdir = os.getcwd()
    os.chdir(tmp_path)
    try:
        failures = ml.validate_blocks(
            ml.find_mermaid_blocks([tmp_path]),
            timeout_seconds=1,
            total_timeout_seconds=2,
            retries_on_timeout=0,
        )
    finally:
        os.chdir(original_chdir)

    assert len(failures) == 1
    assert failures[0].returncode == 124
    # Total budget (not per-render timeout) expired first: the failure is
    # attributed to the block with a total-timeout message, proving the
    # explicit 2s budget was used verbatim rather than any scaled default.
    assert "total timeout after 2s before rendering" in failures[0].stderr


def test_module_env_override_documented_in_docs_agents_table() -> None:
    """Docs table must stay in sync with the implementation contract."""
    agents = ml.__file__.replace("mermaid_lint.py", "AGENTS.md")
    text = open(agents, encoding="utf-8").read()
    # The documented env var must remain part of the public tuning surface.
    assert "TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT" in text
