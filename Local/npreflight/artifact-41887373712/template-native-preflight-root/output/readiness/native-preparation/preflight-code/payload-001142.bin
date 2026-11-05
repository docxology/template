"""Reconstruct original source labels while admitting current source bytes.

Only native receipt replay uses this projection. Pipeline/cache fingerprint
schemas are unchanged, and original paths are never reopened on the reader.
"""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.core.pipeline import fingerprints
from infrastructure.core.pipeline.fingerprints import (
    _observe_loaded_implementation,
    canonical_digest,
    tree_records,
)


def native_source_content_identity(
    reader_root: Path,
    project_dir: Path,
    custody: dict[str, str],
    *,
    definition_path: Path | None = None,
) -> str:
    """Preserve original source fingerprint names, ordering and exclusion rules.

    The caller first admits producer custody and the current public source
    digest. Loaded implementation verification independently refuses changed
    executable source. Exact current SDK bytes enter the original SDK role.
    """
    observed = _observe_loaded_implementation()
    original_root = Path(custody["root"])
    original_sdk = Path(custody["implementation_root"])
    current_sdk = Path(fingerprints.__file__).resolve().parents[2]
    candidate_sdk = reader_root / "infrastructure"
    # A producer importing its candidate has one infrastructure role. An
    # external reader SDK must be byte-identical to that admitted role.
    if original_sdk == original_root / "infrastructure" and current_sdk != candidate_sdk.resolve():
        if tree_records(candidate_sdk, source=True) != tree_records(current_sdk, source=True):
            raise ValueError("reader SDK differs from the original candidate implementation")
    roots = [candidate_sdk, reader_root / "scripts", project_dir]
    originals = [original_root / path.relative_to(reader_root) for path in roots]
    if original_sdk != original_root / "infrastructure":
        roots.append(current_sdk)
        originals.append(original_sdk)
    for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml"):
        roots.append(reader_root / name)
        originals.append(original_root / name)
    if definition_path is not None:
        roots.append(definition_path)
        originals.append(original_root / definition_path.relative_to(reader_root))
    excluded = (project_dir / "output").absolute()
    reusable = {path: rows for path, rows in observed.items() if not excluded.is_relative_to(path)}
    pairs = dict(zip(originals, roots, strict=True))
    base = Path(os.path.commonpath([str(path.absolute().parent) for path in pairs]))
    return canonical_digest(
        [
            (
                str(original.absolute().relative_to(base)),
                reusable[current.absolute()]
                if current.absolute() in reusable
                else tree_records(current, source=True, excluded_roots=frozenset({excluded})),
            )
            for original, current in sorted(pairs.items(), key=lambda item: item[0].as_posix())
        ]
    )
