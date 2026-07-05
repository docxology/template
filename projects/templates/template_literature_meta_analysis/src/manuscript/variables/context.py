"""Shared extraction context for pipeline artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from manuscript.variables.io import count_jsonl_lines, load_config, load_json


@dataclass
class ExtractContext:
    output_dir: Path
    data_dir: Path
    project_root: Path
    cfg: dict[str, Any]
    corpus_size: int

    @classmethod
    def from_output_dir(cls, output_dir: Path, cfg: dict[str, Any] | None = None) -> ExtractContext:
        data_dir = output_dir / "data"
        project_root = output_dir.parent
        config = cfg if cfg is not None else load_config(project_root)
        corpus_path = data_dir / "corpus.jsonl"
        if not corpus_path.exists():
            corpus_path = output_dir / "corpus.jsonl"
        return cls(
            output_dir=output_dir,
            data_dir=data_dir,
            project_root=project_root,
            cfg=config,
            corpus_size=count_jsonl_lines(corpus_path),
        )

    def load_json(self, name: str) -> dict[str, Any]:
        payload = load_json(self.data_dir / name)
        if payload.get("_error") is not None:
            payload = load_json(self.output_dir / name)
        if payload.get("_error") is not None:
            return {}
        return payload

    def load_json_raw(self, name: str) -> Any:
        from manuscript.variables.io import load_pipeline_json_raw

        return load_pipeline_json_raw(self.data_dir, self.output_dir, name)
