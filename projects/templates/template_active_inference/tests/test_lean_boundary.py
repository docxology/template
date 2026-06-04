from pathlib import Path

from visualizations.lean_boundary import load_lean_boundary_rows


def test_load_lean_boundary_rows(project_root: Path) -> None:
    rows = load_lean_boundary_rows(project_root)
    assert rows
    names = {row.name for row in rows}
    assert "sophisticated_requires_horizon" in names
    assert "ising_coupling_sum_zero" in names
    assert "graph_world_three_steps_reach_goal" in names
    assert "policy_enumeration_contains_forward" in names
    assert all(row.status == "proved" for row in rows)


def test_load_lean_boundary_rows_detects_sorry(tmp_path: Path) -> None:
    lean_dir = tmp_path / "lean" / "TemplateActiveInference"
    lean_dir.mkdir(parents=True)
    (lean_dir / "Stub.lean").write_text(
        "theorem broken : True := by\n  sorry\n\ntheorem fine : True := trivial\n",
        encoding="utf-8",
    )
    rows = load_lean_boundary_rows(tmp_path)
    by_name = {row.name: row for row in rows}
    assert by_name["broken"].status == "sorry"
    assert by_name["fine"].status == "proved"
