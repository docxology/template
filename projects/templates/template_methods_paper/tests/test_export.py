"""Tests for src.methods_dsl.export — worklist/CSV/Mermaid/JSON exporters."""

from __future__ import annotations

import hashlib
import json

from src.methods_dsl.compiler import compile_method
from src.methods_dsl.export import (
    to_csv_rows,
    to_json,
    to_mermaid,
    to_worklist_markdown,
    write_all_exports,
    write_csv,
    write_json,
    write_json_report,
)


def test_to_worklist_markdown_numbers_steps_in_order(linear_method):
    plan = compile_method(linear_method)
    text = to_worklist_markdown(plan)
    assert "1. **Add water**" in text
    assert "2. **Mix**" in text
    assert "3. **Validate**" in text


def test_to_csv_rows_header_and_row_count(linear_method):
    plan = compile_method(linear_method)
    rows = to_csv_rows(plan)
    assert rows[0] == "order,step_id,name,kind,target"
    assert len(rows) == 1 + len(plan.steps)


def test_to_csv_rows_escapes_embedded_quotes():
    from src.methods_dsl.model import Method, Step
    from src.methods_dsl.vocabulary import StepKind, Target

    method = Method(
        name="QuoteTest",
        version="1.0",
        target=Target.HUMAN,
        steps=(Step(step_id=1, name='Say "hello"', kind=StepKind.ANNOTATE, target=Target.HUMAN),),
    )
    plan = compile_method(method)
    rows = to_csv_rows(plan)
    assert '""hello""' in rows[1]


def test_write_csv_writes_file(linear_method, tmp_path):
    plan = compile_method(linear_method)
    path = write_csv(plan, tmp_path / "nested" / "plan.csv")
    assert path.exists()
    assert path.read_text(encoding="utf-8").splitlines()[0] == "order,step_id,name,kind,target"


def test_to_mermaid_contains_every_node_and_sequential_edges(diamond_method):
    plan = compile_method(diamond_method)
    text = to_mermaid(plan)
    assert text.startswith("flowchart TD")
    for step in plan.steps:
        assert f"S{step.step_id}[" in text
    # 4 steps -> 3 sequential edges in scheduled order
    assert text.count("-->") == 3


def test_to_json_round_trips_and_matches_plan_hash_input(linear_method):
    plan = compile_method(linear_method)
    payload = json.loads(to_json(plan))
    assert payload == plan.to_canonical_dict()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == plan.plan_hash


def test_write_json_writes_file(linear_method, tmp_path):
    plan = compile_method(linear_method)
    path = write_json(plan, tmp_path / "out" / "plan.json")
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == plan.to_canonical_dict()


def test_write_all_exports_writes_four_files_in_order(linear_method, tmp_path):
    plan = compile_method(linear_method)
    paths = write_all_exports(plan, tmp_path / "data")
    assert len(paths) == 4
    assert all(p.exists() for p in paths)
    names = [p.name for p in paths]
    assert names == ["lineardemo_worklist.md", "lineardemo_plan.csv", "lineardemo_graph.mmd", "lineardemo_plan.json"]


def test_write_json_report_writes_dict_payload(tmp_path):
    path = write_json_report({"total_gates_run": 8, "total_gates_passed": 8}, tmp_path / "reports" / "gate_report.json")
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == {"total_gates_run": 8, "total_gates_passed": 8}


def test_write_json_report_writes_list_payload(tmp_path):
    payload = [{"method_name": "A", "step_count": 1}]
    path = write_json_report(payload, tmp_path / "data" / "compiled_plans.json")
    assert json.loads(path.read_text(encoding="utf-8")) == payload
