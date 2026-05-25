"""Direct-call CLI tests for search module — exercise main() in-process."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.search.literature.cli import build_parser, main


def _corpus(tmp_path: Path) -> Path:
    path = tmp_path / "c.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "doi:10.1/x",
                    "title": "Convex Optimization",
                    "authors": ["Boyd, Stephen", "Vandenberghe, Lieven"],
                    "year": 2004,
                    "doi": "10.1/x",
                    "venue": "Cambridge",
                    "venue_type": "book",
                    "publisher": "Cambridge UP",
                },
                {
                    "id": "arxiv:1412.6980",
                    "title": "Adam: A method for stochastic optimization",
                    "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
                    "year": 2014,
                    "venue": "ICLR",
                    "venue_type": "conference",
                },
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_build_parser_returns_argparse():
    import argparse

    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_search_local_to_stdout(tmp_path: Path, capsys):
    corpus = _corpus(tmp_path)
    rc = main(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["per_source_counts"] == {"local": 1}
    assert payload["papers"][0]["title"] == "Convex Optimization"


def test_search_local_to_file(tmp_path: Path):
    corpus = _corpus(tmp_path)
    out = tmp_path / "results.json"
    rc = main(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--output",
            str(out),
        ]
    )
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload["papers"]) == 1


def test_to_bibtex_from_local(tmp_path: Path, capsys):
    corpus = _corpus(tmp_path)
    rc = main(
        [
            "to-bibtex",
            "optimization",
            "--source",
            "local",
            "--corpus",
            str(corpus),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "@book{boyd2004convex" in out
    assert "@inproceedings{" in out


def test_to_bibtex_with_output_path(tmp_path: Path):
    corpus = _corpus(tmp_path)
    out = tmp_path / "out.bib"
    rc = main(
        [
            "to-bibtex",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--output",
            str(out),
        ]
    )
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "@book{boyd2004convex" in text


def test_search_with_year_filters(tmp_path: Path, capsys):
    corpus = _corpus(tmp_path)
    rc = main(
        [
            "search",
            "optimization",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--from-year",
            "2010",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    years = [p["year"] for p in payload["papers"]]
    assert all(y >= 2010 for y in years if y is not None)


def test_search_unknown_source_exits(tmp_path: Path):
    with pytest.raises(SystemExit) as exc:
        main(["search", "x", "--source", "fictional"])
    assert "Unknown source" in str(exc.value)


def test_search_local_requires_corpus(tmp_path: Path):
    with pytest.raises(SystemExit) as exc:
        main(["search", "x", "--source", "local"])
    assert "corpus" in str(exc.value).lower()


def test_search_paperclip_requires_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("PAPERCLIP_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        main(["search", "x", "--source", "paperclip"])
    assert "PAPERCLIP_API_KEY" in str(exc.value)


def test_search_with_cache(tmp_path: Path, capsys):
    corpus = _corpus(tmp_path)
    cache_dir = tmp_path / "cache"
    rc = main(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--cache-dir",
            str(cache_dir),
        ]
    )
    assert rc == 0
    files = list(cache_dir.glob("search_*.json"))
    assert len(files) == 1
    # Re-run with --no-cache; cache should still have one entry.
    capsys.readouterr()
    rc = main(
        [
            "search",
            "convex",
            "--source",
            "local",
            "--corpus",
            str(corpus),
            "--cache-dir",
            str(cache_dir),
            "--no-cache",
        ]
    )
    assert rc == 0
