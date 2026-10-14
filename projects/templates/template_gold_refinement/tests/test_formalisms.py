from __future__ import annotations

import json

from template_gold_refinement.formalisms import (
    FORMALISMS,
    equation_labels,
    formalism_equation_blocks,
    formalism_records,
    formalism_table_rows,
    formalism_traceability_rows,
    format_table_code,
)


def test_equation_labels_are_unique_and_expected():
    labels = equation_labels()
    assert len(labels) == len(set(labels))
    assert set(labels) == {
        "eq:purity_functional",
        "eq:monotone_refinery",
        "eq:token_digest",
        "eq:claim_support",
        "eq:integrity_vector",
        "eq:certification_predicate",
        "eq:adversarial_assay",
    }


def test_formalism_table_references_every_equation():
    rows = formalism_table_rows()
    for label in equation_labels():
        assert f"[@{label}]" in rows


def test_equation_blocks_define_every_label_once():
    blocks = formalism_equation_blocks()
    for label in equation_labels():
        assert blocks.count(f"{{#{label}}}") == 1


def test_traceability_rows_include_sources():
    rows = formalism_traceability_rows()
    for item in FORMALISMS:
        assert item.source in rows
        assert f"`{item.source}`" in rows
        assert item.formalism_id in rows
    assert rows.replace("`", "") == "\n".join(
        f"| {item.formalism_id} | {item.equation_label} | {item.source} | {item.statement} |" for item in FORMALISMS
    )
    for original, expected in (
        (
            "manuscript/config.yaml#gold_refinement.lexicon.boundary_terms[1]",
            "`manuscript/config.yaml#gold_refinement.lexicon.boundary_terms`[1]",
        ),
        ("GoldRefinementConfig and TokenPlan", "`GoldRefinementConfig` and `TokenPlan`"),
        ("ordinary prose 99.9% non-claim", "ordinary prose 99.9% non-claim"),
        ("`existing_path.py` and test_file.py.", "`existing_path.py` and `test_file.py`."),
        ("``unfamiliar_path.py``", "``unfamiliar_path.py``"),
        ("`unclosed_path.py", "`unclosed_path.py"),
        ("x" * 8193, "x" * 8193),
        ("source_path.py\nunchanged", "source_path.py\nunchanged"),
        ("**bold_file.py**", "**bold_file.py**"),
        ("*italic_file.py*", "*italic_file.py*"),
        ("_italic_file.py_", "_italic_file.py_"),
        ("[source_file.py](https://example.org)", "[source_file.py](https://example.org)"),
        ("Source: ordinary label and e.g. prose", "Source: ordinary label and e.g. prose"),
        ("<code>source_file.py</code>", "<code>source_file.py</code>"),
        ("$source_file.py$", "$source_file.py$"),
        (r"\(source_file.py\)", r"\(source_file.py\)"),
        ("[malformed_source.py", "[malformed_source.py"),
        ("output/figures/*.png", "`output/figures/*.png`"),
        ("folder/*file.py*", "folder/*file.py*"),
        ("Aa" + "A" * 300 + "-", "Aa" + "A" * 300 + "-"),
        ("src/refinery.py::run_refinery()", "`src/refinery.py::run_refinery`()"),
    ):
        projected = format_table_code(original)
        assert projected == expected
        assert projected.replace("`", "") == original.replace("`", "")
        assert format_table_code(projected) == projected


def test_formalism_records_are_json_serializable():
    payload = json.dumps(formalism_records())
    assert "purity_functional" in payload
    assert "adversarial_assay" in payload
