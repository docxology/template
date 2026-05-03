"""Direct-call CLI tests for citation module — exercise main() in-process for
coverage (subprocess tests in test_cli.py validate end-to-end behaviour).
"""

from __future__ import annotations

import json
from pathlib import Path


from infrastructure.reference.citation.cli import build_parser, main


REPO_ROOT = Path(__file__).resolve().parents[3]
EXEMPLAR = REPO_ROOT / "projects" / "template_code_project" / "manuscript" / "references.bib"


def test_validate_passes_on_exemplar(capsys):
    rc = main(["validate", str(EXEMPLAR)])
    assert rc == 0


def test_validate_strict_flags_missing(tmp_path: Path):
    bib = tmp_path / "bad.bib"
    bib.write_text("@article{k, title={Only title}}\n", encoding="utf-8")
    assert main(["validate", str(bib), "--strict"]) == 1


def test_validate_non_strict_returns_zero_on_warnings(tmp_path: Path):
    bib = tmp_path / "bad.bib"
    bib.write_text("@article{k, title={T}}\n", encoding="utf-8")
    assert main(["validate", str(bib)]) == 0


def test_validate_returns_2_on_parse_error(tmp_path: Path):
    bib = tmp_path / "bad.bib"
    bib.write_text("@article{k, title={Unterminated", encoding="utf-8")
    assert main(["validate", str(bib)]) == 2


def test_format_overwrites_in_place(tmp_path: Path):
    src = tmp_path / "in.bib"
    src.write_text(
        '@article{k, title="Hi", author={Alice and Bob}, year=2024,}\n',
        encoding="utf-8",
    )
    assert main(["format", str(src)]) == 0
    formatted = src.read_text(encoding="utf-8")
    assert "  title={Hi}," in formatted
    assert "  year={2024}\n" in formatted


def test_format_writes_to_output_path(tmp_path: Path):
    src = tmp_path / "in.bib"
    src.write_text("@article{k, title={Hi}}\n", encoding="utf-8")
    out = tmp_path / "out.bib"
    assert main(["format", str(src), "--output", str(out)]) == 0
    assert out.exists()


def test_convert_papers_list_format(tmp_path: Path):
    in_path = tmp_path / "p.json"
    in_path.write_text(
        json.dumps(
            [{"id": "x", "title": "T", "authors": ["Smith, A"], "year": 2024}]
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "out.bib"
    assert main(["convert", str(in_path), str(out_path)]) == 0
    assert "@article{smith2024" in out_path.read_text(encoding="utf-8")


def test_convert_dict_wrapper_format(tmp_path: Path):
    in_path = tmp_path / "p.json"
    in_path.write_text(
        json.dumps(
            {
                "papers": [
                    {"id": "x", "title": "T", "authors": ["Smith, A"], "year": 2024}
                ]
            }
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "out.bib"
    assert main(["convert", str(in_path), str(out_path)]) == 0


def test_convert_to_stdout_dash(tmp_path: Path, capsys):
    in_path = tmp_path / "p.json"
    in_path.write_text(
        json.dumps([{"id": "x", "title": "T", "authors": ["Smith, A"], "year": 2024}]),
        encoding="utf-8",
    )
    assert main(["convert", str(in_path), "-"]) == 0
    captured = capsys.readouterr()
    assert "@article{smith2024" in captured.out


def test_convert_invalid_payload_returns_2(tmp_path: Path):
    in_path = tmp_path / "p.json"
    in_path.write_text(json.dumps({"not_papers": []}), encoding="utf-8")
    out_path = tmp_path / "out.bib"
    assert main(["convert", str(in_path), str(out_path)]) == 2


def test_build_parser_returns_argparse():
    import argparse
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
