from __future__ import annotations

import json

from formalisms import (
    FORMALISMS,
    equation_labels,
    formalism_equation_blocks,
    formalism_records,
    formalism_table_rows,
    formalism_traceability_rows,
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
        assert item.formalism_id in rows


def test_formalism_records_are_json_serializable():
    payload = json.dumps(formalism_records())
    assert "purity_functional" in payload
    assert "adversarial_assay" in payload
