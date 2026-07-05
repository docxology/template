"""JSON/JSONL loading helpers with a single fallback policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manuscript.variables._logging import logger


def load_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        logger.warning("config.yaml not found at %s; domain tokens use fallbacks", config_path)
        return {}
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    with open(config_path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        logger.warning("Variable source file not found: %s", path)
        return {"_error": f"file_not_found: {path}"}
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data
    return {"_value": data}


def load_pipeline_json_raw(data_dir: Path, output_dir: Path, name: str) -> Any:
    for base in (data_dir, output_dir):
        path = base / name
        if path.exists():
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
    logger.warning("Variable source file not found: %s (data/ or output root)", name)
    return None


def count_jsonl_lines(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def count_total_references(corpus_path: Path) -> int:
    if not corpus_path.exists():
        return 0
    total = 0
    with open(corpus_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
                refs = paper.get("references", paper.get("referenced_works", []))
                if isinstance(refs, list):
                    total += len(refs)
            except json.JSONDecodeError:
                continue
    return total
