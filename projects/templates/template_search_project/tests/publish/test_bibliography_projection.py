"""Real generated/curated citation and render-boundary controls."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.reference.citation import BibDatabase, BibEntry, parse_bibtex
from infrastructure.rendering._bibliography import pandoc_bibliography_args, resolve_bibliography
from infrastructure.rendering._manuscript_source import resolve_manuscript_dir
from template_search_project.pipeline.composition import compose_literature_review
from template_search_project.pipeline.pipeline import run_literature_pipeline
from template_search_project.publish.bibliography import (
    GENERATED_BIB_NAME,
    GENERATED_SUPPLEMENT_NAME,
    generated_path,
    project_bibliographies,
    write_generated_bibliography,
)
from template_search_project.publish.config import DeepSearchConfig, ProjectConfig, SearchConfig
from template_search_project.publish.deep_custody import admit_composed_supplement, admit_deep_producer
from template_search_project.publish.manuscript_variables import (
    compute_variables,
    write_resolved_manuscript_tree,
    write_variables,
)
from template_search_project.search.deep_search import run_deep_search


def _entry(**fields: str) -> BibEntry:
    return BibEntry(
        "article", "alice2024finding", {"title": "Finding", "author": "Alice Curry", "year": "2024", **fields}
    )


def _author(root: Path, text: str) -> Path:
    target = root / "manuscript" / "references.bib"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


def test_curated_metadata_and_annotations_survive_projection(tmp_path: Path):
    authored = _author(
        tmp_path,
        "@article{alice2024finding, title={FINDING}, author={Curry, Alice}, year={2024}, doi={10.1/X}, abstract={Curated annotation}}\n",
    )
    baseline = authored.read_bytes()
    full = write_generated_bibliography(
        tmp_path,
        "output/bibliography/references.bib",
        BibDatabase(entries=[_entry(doi="https://doi.org/10.1/x", abstract="Generated annotation")]),
    )
    projected = project_bibliographies(tmp_path, (str(full),))
    assert not parse_bibtex(projected.read_text()).entries
    assert projected.read_bytes() == b"% No additional generated bibliography entries.\n"
    assert authored.read_bytes() == baseline
    receipt = json.loads((tmp_path / "output" / "bibliography_projection.json").read_text())
    assert receipt["authored_sources"]["manuscript/references.bib"] == hashlib.sha256(baseline).hexdigest()
    assert receipt["projected_keys"] == []
    assert receipt["projected_sha256"] == hashlib.sha256(projected.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "Another finding"),
        ("author", "Bob Curry"),
        ("year", "2025"),
        ("doi", "10.1/different"),
        ("journal", "Different Journal"),
        ("url", "https://example.org/DifferentCase"),
        ("url", "https://example.org/differentcase/"),
    ],
)
def test_meaningful_key_collision_fails_before_output_write(tmp_path: Path, field: str, value: str):
    authored = _author(
        tmp_path,
        "@article{alice2024finding, title={Finding}, author={Alice Curry}, year={2024}, doi={10.1/x}, journal={Journal}, url={https://example.org/differentcase}}\n",
    )
    baseline = authored.read_bytes()
    with pytest.raises(ValueError, match="Bibliography collision"):
        write_generated_bibliography(
            tmp_path,
            "output/bibliography/references.bib",
            BibDatabase(
                entries=[
                    _entry(
                        **(
                            {"doi": "10.1/x", "journal": "Journal", "url": "https://example.org/differentcase"}
                            | {field: value}
                        )
                    )
                ]
            ),
        )
    assert authored.read_bytes() == baseline
    assert not (tmp_path / "output" / "bibliography" / "references.bib").exists()


@pytest.mark.parametrize(
    "path", ["manuscript/references.bib", "output/../manuscript/ref.bib", "output/bib/ref.txt", "/outside/ref.bib"]
)
def test_generated_path_rejects_authoring_escape(tmp_path: Path, path: str):
    with pytest.raises(ValueError, match="Generated bibliography"):
        generated_path(tmp_path, path)


def test_duplicate_keys_and_reserved_authored_name_are_refused(tmp_path: Path):
    _author(tmp_path, "@article{a, title={A}}\n@article{A, title={A}}\n")
    with pytest.raises(ValueError, match="Duplicate curated"):
        project_bibliographies(tmp_path, ())
    (tmp_path / "manuscript" / "references.bib").unlink()
    (tmp_path / "manuscript" / GENERATED_BIB_NAME).write_text("% authored collision")
    with pytest.raises(ValueError, match="reserved generated name"):
        project_bibliographies(tmp_path, ())


def test_generated_keys_across_two_runs_have_one_renderer_definition(tmp_path: Path):
    first = write_generated_bibliography(tmp_path, "output/bibliography/one.bib", BibDatabase(entries=[_entry()]))
    second = write_generated_bibliography(tmp_path, "output/bibliography/two.bib", BibDatabase(entries=[_entry()]))
    projected = project_bibliographies(tmp_path, (str(first), str(second), "output/bibliography/absent.bib"))
    assert parse_bibtex(projected.read_text()).keys() == ["alice2024finding"]
    receipt = json.loads((tmp_path / "output" / "bibliography_projection.json").read_text())
    assert len(receipt["key_origins"]["alice2024finding"]) == 2
    with pytest.raises(ValueError, match="Duplicate generated"):
        write_generated_bibliography(tmp_path, "output/bibliography/bad.bib", BibDatabase(entries=[_entry(), _entry()]))


def test_output_symlink_cannot_modify_authored_bibliography(tmp_path: Path):
    authored = _author(tmp_path, "% authored source\n")
    (tmp_path / "output" / "bibliography").mkdir(parents=True)
    (tmp_path / "output" / "bibliography" / "references.bib").symlink_to(authored)
    with pytest.raises(ValueError, match="symlink"):
        write_generated_bibliography(tmp_path, "output/bibliography/references.bib", BibDatabase(entries=[_entry()]))
    assert authored.read_text() == "% authored source\n"


def _variables():
    return compute_variables(
        config_query="Current finding",
        config_max_results=25,
        config_sources=["local"],
        search_result_payload={},
    )


@pytest.mark.parametrize("alias", ["parent", "01_main.md", "config.yaml", "references.bib"])
def test_hydration_output_alias_cannot_change_authored_inputs(tmp_path: Path, alias: str):
    authored = _author(tmp_path, "% curated source\n")
    manuscript = authored.parent
    (manuscript / "01_main.md").write_text("# {{CONFIG_QUERY}}\n")
    (manuscript / "config.yaml").write_text("paper:\n  title: Authored\n")
    before = {p.name: p.read_bytes() for p in manuscript.iterdir()}
    output = tmp_path / "output" / "manuscript"
    output.parent.mkdir()
    if alias == "parent":
        output.symlink_to(manuscript, target_is_directory=True)
    else:
        output.mkdir()
        (output / alias).symlink_to(manuscript / alias)
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        write_resolved_manuscript_tree(
            tmp_path,
            _variables(),
            config=ProjectConfig(title="Controlled", search=SearchConfig(query="finding", sources=["local"])),
        )
    assert {p.name: p.read_bytes() for p in manuscript.iterdir()} == before


def test_variables_output_parent_alias_cannot_change_authored_json(tmp_path: Path):
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "manuscript_variables.json"
    source.write_text("authored source")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "data").symlink_to(manuscript, target_is_directory=True)
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        write_variables(_variables(), tmp_path / "output" / "data" / source.name, project_root=tmp_path)
    assert source.read_text() == "authored source"


def test_disabled_deep_hydration_omits_stale_deep_bibliography_and_supplement(tmp_path: Path):
    authored = _author(tmp_path, "% curated source\n")
    (authored.parent / "01_main.md").write_text("# {{CONFIG_QUERY}}\n")
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    (output / GENERATED_SUPPLEMENT_NAME).write_text("stale historical deep analysis")
    normal = write_generated_bibliography(
        tmp_path, "output/bibliography/references.bib", BibDatabase(entries=[_entry()])
    )
    deep = normal.with_name("references_deep.bib")
    deep.write_text("@article{old1999historical, title={Old}, author={History}, year={1999}}\n")
    before = {p.name: p.read_bytes() for p in authored.parent.iterdir()}
    resolved = write_resolved_manuscript_tree(
        tmp_path,
        _variables(),
        config=ProjectConfig(title="Controlled", search=SearchConfig(query="finding", sources=["local"])),
    )
    assert not (resolved / GENERATED_SUPPLEMENT_NAME).exists()
    assert parse_bibtex((resolved / GENERATED_BIB_NAME).read_text()).keys() == ["alice2024finding"]
    assert deep.read_text().startswith("@article{old1999historical")
    assert {p.name: p.read_bytes() for p in authored.parent.iterdir()} == before


def test_generated_supplement_leaf_alias_is_refused_during_disabled_hydration(tmp_path: Path):
    authored = _author(tmp_path, "% authored remains\n")
    (authored.parent / "01_main.md").write_text("# Main\n")
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    (output / GENERATED_SUPPLEMENT_NAME).symlink_to(authored)
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        write_resolved_manuscript_tree(
            tmp_path,
            _variables(),
            config=ProjectConfig(title="Controlled", search=SearchConfig(query="finding", sources=["local"])),
        )
    assert authored.read_text() == "% authored remains\n"


def test_reserved_supplement_cannot_be_authored_then_removed_as_generated(tmp_path: Path):
    authored = _author(tmp_path, "% authored remains\n")
    (authored.parent / GENERATED_SUPPLEMENT_NAME).write_text("authored supplement")
    with pytest.raises(ValueError, match="reserved generated supplement"):
        write_resolved_manuscript_tree(
            tmp_path,
            _variables(),
            config=ProjectConfig(title="Controlled", search=SearchConfig(query="finding", sources=["local"])),
        )
    assert (authored.parent / GENERATED_SUPPLEMENT_NAME).read_text() == "authored supplement"
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("change", ["none", "missing", "content", "inputs", "producer", "manual", "bool-schema"])
def test_composed_supplement_requires_exact_current_dependency_bytes(tmp_path: Path, change: str):
    """Fixture dependency summaries exercise projection, not provider execution."""
    config = DeepSearchConfig(enabled=True, keywords=["controlled"])
    deep = tmp_path / config.output_dir
    deep.mkdir(parents=True)
    producer = deep / "producer_receipt.json"
    producer.write_text("fixture producer identity")
    aggregate = deep / "aggregate.json"
    aggregate.write_bytes(b"{}")
    admitted = {aggregate: b"{}"}
    target = tmp_path / "output/manuscript" / GENERATED_SUPPLEMENT_NAME
    target.parent.mkdir()
    target.write_bytes(b"current composed supplement")
    summary = {
        "schema_version": 1,
        "kind": "deep-search-composition",
        "generated_supplement": True,
        "producer_receipt_sha256": hashlib.sha256(producer.read_bytes()).hexdigest(),
        "producer_inputs": {"output/deep_search/aggregate.json": hashlib.sha256(b"{}").hexdigest()},
        "supplement_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
    if change == "content":
        target.write_text("older composition")
    elif change == "inputs":
        admitted[aggregate] = b'{"new":true}'
    elif change == "producer":
        producer.write_text("new source/config producer identity")
    elif change == "manual":
        summary["generated_supplement"] = False
    elif change == "bool-schema":
        summary["schema_version"] = True
    summary_path = deep / "composition_summary.json"
    if change != "missing":
        summary_path.write_text(json.dumps(summary))
    if change == "none":
        assert admit_composed_supplement(tmp_path, config, admitted) == target.read_bytes()
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            admit_composed_supplement(tmp_path, config, admitted)


def test_missing_supplement_allows_hydration_before_explicit_composition(tmp_path: Path):
    assert admit_composed_supplement(tmp_path, DeepSearchConfig(enabled=True, keywords=["x"]), {}) is None


@pytest.mark.timeout(60)
def test_real_local_producers_hydration_and_pandoc_consume_extra_citations_and_supplement(tmp_path: Path):
    """The actual renderer's input union reaches real Pandoc; authors stay intact."""
    authored = _author(tmp_path, "% curated bibliography remains byte-identical\n")
    manuscript = tmp_path / "manuscript"
    (manuscript / "config.yaml").write_text("paper:\n  title: Controlled output\n")
    (manuscript / "01_main.md").write_text("# Main\n\nA curated authored paragraph.\n")
    (manuscript / "S01_literature_review.md").write_text("# Authored appendix\n\nAuthored material.\n")
    before = {p.name: p.read_bytes() for p in manuscript.iterdir()}
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            [
                {
                    "id": "new-paper",
                    "title": "Fresh Finding",
                    "authors": ["Curry, Alice"],
                    "year": 2024,
                    "venue": "Journal",
                    "venue_type": "journal",
                }
            ]
        )
    )
    config = ProjectConfig(
        title="Controlled",
        search=SearchConfig(query="finding", sources=["local"]),
        deep_search=DeepSearchConfig(
            enabled=True,
            keywords=["finding"],
            sources=["local"],
            fetch_abstracts=False,
            fetch_fulltext=False,
            llm_per_paper=False,
        ),
    )
    run_literature_pipeline(config, project_root=tmp_path, corpus_path=corpus)
    deep = run_deep_search(config.deep_search, project_root=tmp_path, corpus_path=corpus)
    assert deep.aggregate_json_path is not None
    assert compose_literature_review(tmp_path, config) == 0
    variables = compute_variables(
        config_query="finding",
        config_max_results=25,
        config_sources=["local"],
        search_result_payload={"papers": [dict(title="Fresh Finding")]},
    )
    resolved = write_resolved_manuscript_tree(tmp_path, variables, config=config)
    assert resolve_manuscript_dir(tmp_path) == resolved
    bibliography = resolve_bibliography(resolved)
    assert (resolved / GENERATED_BIB_NAME) in bibliography
    supplement = resolved / GENERATED_SUPPLEMENT_NAME
    assert "Fresh Finding" in supplement.read_text()
    command = shutil.which("pandoc")
    assert command is not None, "Actual configured rendering acceptance requires Pandoc"
    rendered = subprocess.run(
        [
            command,
            str(resolved / "01_main.md"),
            str(supplement),
            "--to=html",
            "--citeproc",
            *pandoc_bibliography_args(bibliography),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert "Fresh Finding" in rendered.stdout
    assert 'class="citation"' in rendered.stdout
    assert "Curry" in rendered.stdout
    assert "citation not found" not in rendered.stderr.lower()
    assert {p.name: p.read_bytes() for p in manuscript.iterdir()} == before
    assert authored.read_bytes() == before[authored.name]
    # Receipt-bound producer artifacts remain consumable after composition.
    admit_deep_producer(tmp_path, config.deep_search, tmp_path / "output" / "deep_search")
    deep.aggregate_json_path.write_text("{}")
    assert compose_literature_review(tmp_path, config) == 1


@pytest.mark.parametrize(
    "mode",
    [
        "failed",
        "bool_schema",
        "missing_artifacts",
        "missing_aggregate",
        "malformed_path",
        "absolute_path",
        "null_digest",
        "stale_source",
    ],
)
def test_deep_dependency_receipt_fails_closed(tmp_path: Path, mode: str):
    from template_search_project.publish.deep_custody import begin_deep_producer, finish_deep_producer

    config = DeepSearchConfig(enabled=True, keywords=["finding"], write_unified_bibtex=False)
    out = tmp_path / "output" / "deep_search"
    out.mkdir(parents=True)
    (out / "aggregate.json").write_text("{}")
    receipt_path = finish_deep_producer(tmp_path, config, begin_deep_producer(config), out)
    receipt = json.loads(receipt_path.read_text())
    if mode == "failed":
        receipt["status"] = "failed"
    elif mode == "bool_schema":
        receipt["schema_version"] = True
    elif mode == "missing_artifacts":
        receipt["artifacts"] = None
    elif mode == "missing_aggregate":
        receipt["artifacts"] = {"output/other.json": "0" * 64}
    elif mode == "malformed_path":
        receipt["artifacts"]["output/../outside.json"] = "0" * 64
    elif mode == "absolute_path":
        receipt["artifacts"][str(out / "aggregate.json")] = hashlib.sha256(b"{}").hexdigest()
    elif mode == "null_digest":
        receipt["artifacts"]["output/deep_search/aggregate.json"] = None
    elif mode == "stale_source":
        receipt["source_hashes"] = {}
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="Deep-search producer"):
        admit_deep_producer(tmp_path, config, out)


def test_partial_and_symlinked_deep_outputs_do_not_admit_composition(tmp_path: Path):
    from template_search_project.publish.deep_custody import begin_deep_producer, finish_deep_producer

    config = DeepSearchConfig(enabled=True, keywords=["finding"], write_unified_bibtex=False)
    out = tmp_path / "output" / "deep_search"
    out.mkdir(parents=True)
    (out / "aggregate.json").write_text("{}")
    initial = begin_deep_producer(config)
    finish_deep_producer(tmp_path, config, initial, out, successful=False)
    with pytest.raises(ValueError, match="not an admitted"):
        admit_deep_producer(tmp_path, config, out)
    linked = tmp_path / "actual"
    linked.mkdir()
    (out / "linked-notes").symlink_to(linked, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        finish_deep_producer(tmp_path, config, initial, out)
