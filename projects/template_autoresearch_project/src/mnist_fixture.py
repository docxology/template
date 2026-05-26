"""Offline MNIST fixture generation helpers.

These helpers are used only by the explicit fixture-regeneration script. The
default AutoResearch run reads the checked-in fixture and does not download
data.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import struct
from pathlib import Path
from typing import Final, TypedDict
from urllib.parse import urlparse
from urllib.request import urlopen

import numpy as np

SOURCE_BASE_URL: Final = "https://storage.googleapis.com/cvdf-datasets/mnist"


class SourceFile(TypedDict):
    """Verified source-file metadata for one MNIST gzip archive."""

    filename: str
    sha256: str
    size_bytes: int


SOURCE_FILES: Final[dict[str, SourceFile]] = {
    "train_images": {
        "filename": "train-images-idx3-ubyte.gz",
        "sha256": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
        "size_bytes": 9_912_422,
    },
    "train_labels": {
        "filename": "train-labels-idx1-ubyte.gz",
        "sha256": "3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
        "size_bytes": 28_881,
    },
    "test_images": {
        "filename": "t10k-images-idx3-ubyte.gz",
        "sha256": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
        "size_bytes": 1_648_877,
    },
    "test_labels": {
        "filename": "t10k-labels-idx1-ubyte.gz",
        "sha256": "f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
        "size_bytes": 4_542,
    },
}


def regenerate_mnist_fixture(
    project_root: Path,
    *,
    train_per_class: int = 200,
    test_per_class: int = 50,
    seed: int = 20_260_525,
) -> tuple[Path, Path]:
    """Download verified MNIST source files and write the deterministic fixture."""
    data_dir = project_root / "data"
    cache_dir = data_dir / "_mnist_source_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    train_images = _read_idx_images(_verified_source(cache_dir, "train_images"))
    train_labels = _read_idx_labels(_verified_source(cache_dir, "train_labels"))
    test_images = _read_idx_images(_verified_source(cache_dir, "test_images"))
    test_labels = _read_idx_labels(_verified_source(cache_dir, "test_labels"))

    train_indices = _stratified_indices(train_labels, per_class=train_per_class, seed=seed)
    test_indices = _stratified_indices(test_labels, per_class=test_per_class, seed=seed + 1)
    output_path = data_dir / "mnist_small.npz"
    np.savez_compressed(
        output_path,
        x_train=train_images[train_indices],
        y_train=train_labels[train_indices],
        x_test=test_images[test_indices],
        y_test=test_labels[test_indices],
        train_indices=train_indices,
        test_indices=test_indices,
    )
    npz_sha = _sha256(output_path)
    provenance = {
        "classes": list(range(10)),
        "dataset": "MNIST handwritten digit database",
        "fixture_id": "mnist_small",
        "npz_sha256": npz_sha,
        "source_base_url": SOURCE_BASE_URL,
        "source_files": SOURCE_FILES,
        "subset_seed": seed,
        "test_per_class": test_per_class,
        "train_per_class": train_per_class,
        "x_test_shape": [int(test_per_class * 10), 28, 28],
        "x_train_shape": [int(train_per_class * 10), 28, 28],
    }
    provenance_path = data_dir / "mnist_small_provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path, provenance_path


def _verified_source(cache_dir: Path, key: str) -> Path:
    meta = SOURCE_FILES[key]
    filename = str(meta["filename"])
    path = cache_dir / filename
    if not path.exists():
        with urlopen(_source_url(filename), timeout=60) as response:  # noqa: S310  # nosec B310
            path.write_bytes(response.read())
    expected_size = int(meta["size_bytes"])
    if path.stat().st_size != expected_size:
        raise ValueError(f"unexpected MNIST source size for {filename}: {path.stat().st_size}")
    digest = _sha256(path)
    if digest != meta["sha256"]:
        raise ValueError(f"unexpected MNIST source sha256 for {filename}: {digest}")
    return path


def _source_url(filename: str) -> str:
    """Return the fixed public MNIST URL after enforcing an HTTPS source."""
    url = f"{SOURCE_BASE_URL}/{filename}"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "storage.googleapis.com":
        raise ValueError(f"unexpected MNIST source URL: {url}")
    return url


def _read_idx_images(path: Path) -> np.ndarray:
    with gzip.open(path, "rb") as handle:
        magic, count, rows, cols = struct.unpack(">IIII", handle.read(16))
        if magic != 2051 or rows != 28 or cols != 28:
            raise ValueError(f"unsupported MNIST image file: {path}")
        payload = np.frombuffer(handle.read(), dtype=np.uint8)
    return payload.reshape(count, rows, cols)


def _read_idx_labels(path: Path) -> np.ndarray:
    with gzip.open(path, "rb") as handle:
        magic, count = struct.unpack(">II", handle.read(8))
        if magic != 2049:
            raise ValueError(f"unsupported MNIST label file: {path}")
        payload = np.frombuffer(handle.read(), dtype=np.uint8)
    if payload.shape != (count,):
        raise ValueError(f"MNIST label count mismatch in {path}")
    return payload.astype(np.int64)


def _stratified_indices(labels: np.ndarray, *, per_class: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    indices: list[np.ndarray] = []
    for label in range(10):
        class_indices = np.flatnonzero(labels == label)
        if class_indices.size < per_class:
            raise ValueError(f"not enough examples for label {label}")
        indices.append(np.sort(rng.choice(class_indices, size=per_class, replace=False)))
    return np.concatenate(indices).astype(np.int64)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
