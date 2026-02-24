"""Tests for data loader module."""

import json
import pytest
from pathlib import Path
from data.loader import DataLoader

@pytest.fixture
def loader():
    """Create DataLoader instance."""
    return DataLoader()

def test_loader_initialization():
    """Test DataLoader initialization."""
    loader = DataLoader()
    assert loader.data_root.exists()
    assert loader.data_root.name == "data"

def test_load_corpus_exists(loader):
    """Test loading existing corpus."""
    # We know corpus/abstracts.json should exist as we created it
    texts = loader.load_corpus("corpus/abstracts.json")
    assert isinstance(texts, list)
    assert len(texts) > 0
    assert all(isinstance(t, str) for t in texts)

def test_load_corpus_not_found(loader):
    """Test loading non-existent corpus."""
    with pytest.raises(FileNotFoundError):
        loader.load_corpus("non_existent.json")

def test_loader_custom_data_root(tmp_path):
    """Test DataLoader with custom data_root."""
    loader = DataLoader(data_root=tmp_path)
    assert loader.data_root == tmp_path


def test_save_and_load_custom_corpus(loader, tmp_path):
    """Test saving and loading custom corpus."""
    # Temporarily override data_root to tmp_path for this test
    loader.data_root = tmp_path

    texts = ["Abstract 1", "Abstract 2"]
    filename = "custom_corpus.json"

    # Save
    path = loader.save_corpus(texts, filename)
    assert path.exists()

    # Load
    loaded_texts = loader.load_corpus(filename)
    assert loaded_texts == texts


def test_load_corpus_dict_format(tmp_path):
    """Test loading corpus in dict format with 'abstracts' key."""
    loader = DataLoader(data_root=tmp_path)
    corpus_file = tmp_path / "dict_corpus.json"
    corpus_file.write_text(json.dumps({"abstracts": ["text1", "text2", "text3"]}))

    texts = loader.load_corpus("dict_corpus.json")
    assert texts == ["text1", "text2", "text3"]


def test_load_corpus_invalid_format(tmp_path):
    """Test loading corpus with invalid format raises ValueError."""
    loader = DataLoader(data_root=tmp_path)
    bad_file = tmp_path / "bad_corpus.json"
    bad_file.write_text(json.dumps({"wrong_key": "not a list"}))

    with pytest.raises(ValueError, match="Invalid corpus format"):
        loader.load_corpus("bad_corpus.json")
