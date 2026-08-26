"""Coverage-provenance invariant tests for the mermaid lint total budget.

The repo-wide mermaid sweep previously used a fixed 300s wall-clock budget.
As the documentation surface grew past ~250 diagrams, loaded machines began
tripping that budget *before* reaching later blocks, producing failures that
indicted specific diagrams ("total timeout ... before rendering
<file>:<line>") which were never attempted. These tests pin the scaling
contract that replaces the fixed guess.
"""

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


def _fake_mmdc(tmp_path, name="fake_mmdc"):
    fake = tmp_path / name
    fake.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    fake.chmod(0o755)
    return str(fake)


def test_validate_blocks_scales_default_budget_from_discovered_blocks(tmp_path, monkeypatch) -> None:
    """The None default computes its budget from len(blocks)."""
    md = tmp_path / "p.md"
    md.write_text("```mermaid\nflowchart TB\n  A-->B\n```\n", encoding="utf-8")
    blocks = ml.find_mermaid_blocks([tmp_path])
    assert len(blocks) == 1

    captured = {}
    real_scaled = ml.scaled_total_timeout

    def spy(block_count: int) -> float:
        captured["count"] = block_count
        return real_scaled(block_count)

    monkeypatch.setattr(ml, "scaled_total_timeout", spy)
    monkeypatch.setattr(ml, "resolve_mmdc_executable", lambda *a, **k: _fake_mmdc(tmp_path))

    failures = ml.validate_blocks(blocks, timeout_seconds=30)
    # Budget computation saw the discovered workload.
    assert captured["count"] == len(blocks)
    # The failure (if any) comes from the fake mmdc exit code, never from a
    # 124 "before rendering" indictment on a fresh run.
    for f in failures:
        assert f.returncode != 124
        assert "before rendering" not in f.stderr


def test_explicit_caller_budget_bypasses_scaling(tmp_path, monkeypatch) -> None:
    """An explicit total_timeout_seconds is honored verbatim."""

    def boom(block_count: int) -> float:  # known-wrong sentinel
        raise AssertionError("scaling must not run when budget is explicit")

    md = tmp_path / "q.md"
    md.write_text("```mermaid\nflowchart LR\n  X-->Y\n```\n", encoding="utf-8")
    blocks = ml.find_mermaid_blocks([tmp_path])
    monkeypatch.setattr(ml, "scaled_total_timeout", boom)
    monkeypatch.setattr(
        ml,
        "resolve_mmdc_executable",
        lambda *a, **k: _fake_mmdc(tmp_path, "fake_mmdc2"),
    )

    failures = ml.validate_blocks(blocks, timeout_seconds=5, total_timeout_seconds=60)
    assert all(f.returncode == 3 for f in failures)


def test_module_env_override_documented_in_docs_agents_table() -> None:
    """Docs table must stay in sync with the implementation contract."""
    agents = ml.__file__.replace("mermaid_lint.py", "AGENTS.md")
    text = open(agents, encoding="utf-8").read()
    # The documented env var must remain part of the public tuning surface.
    assert "TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT" in text
