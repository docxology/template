"""Shared helpers for canonical sheaf-track consolidation tests."""

from __future__ import annotations

from contextlib import contextmanager
import json
import re
from collections.abc import Callable
from pathlib import Path

import yaml

JsonMutation = Callable[[dict], object]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextmanager
def temporary_json_mutation(path: Path, mutate: Callable[[dict], None]):
    original = _load(path)
    payload = json.loads(json.dumps(original, sort_keys=True))
    try:
        mutate(payload)
        _write(path, payload)
        yield payload
    finally:
        _write(path, original)


@contextmanager
def temporary_text_mutation(path: Path, mutate: Callable[[str], str]):
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(mutate(original), encoding="utf-8")
        yield path.read_text(encoding="utf-8")
    finally:
        path.write_text(original, encoding="utf-8")


@contextmanager
def temporary_yaml_mutation(path: Path, mutate: Callable[[dict], None]):
    original = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    payload = json.loads(json.dumps(original))
    assert isinstance(payload, dict)
    try:
        mutate(payload)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        yield payload
    finally:
        path.write_text(yaml.safe_dump(original, sort_keys=False), encoding="utf-8")


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _set_value(path: tuple[str | int, ...], value: object) -> JsonMutation:
    def mutate(data: dict) -> None:
        target: object = data
        for key in path[:-1]:
            if isinstance(target, dict):
                target = target[key]
            elif isinstance(target, list) and isinstance(key, int):
                target = target[key]
            else:
                raise TypeError(f"cannot index {type(target).__name__} with {key!r}")

        final_key = path[-1]
        if isinstance(target, dict):
            target[final_key] = value
        elif isinstance(target, list) and isinstance(final_key, int):
            target[final_key] = value
        else:
            raise TypeError(f"cannot set {final_key!r} on {type(target).__name__}")

    return mutate


def _drop_last_row(*, update_row_count: bool = False) -> JsonMutation:
    def mutate(data: dict) -> None:
        data["rows"] = data["rows"][:-1]
        if update_row_count:
            data["row_count"] = len(data["rows"])

    return mutate


def _combine_mutations(*mutations: JsonMutation) -> JsonMutation:
    def mutate(data: dict) -> None:
        for mutation in mutations:
            mutation(data)

    return mutate


def _break_visualization_statistical_row(data: dict) -> None:
    statistical_index = next(
        index for index, row in enumerate(data["rows"]) if row.get("figure_id") == "si_belief_entropy_curve"
    )
    data["rows"][statistical_index]["statistically_backed"] = False
    data["all_statistical_sources_present"] = True


def _break_statistical_bridge_visualization_binding(data: dict) -> None:
    first_section = data["rows"][0]["figure_reference_sections"][0]
    data["rows"][0]["reference_track_bindings"][first_section] = ["prose"]
    data["rows"][0]["reference_sections_visualization_bound"] = True
    data["all_reference_sections_visualization_bound"] = True


def _drop_transition_covered_model(data: dict) -> None:
    data["covered_models"] = data["covered_models"][:-1]
    data["all_reachable_states_covered"] = True


VERSIONED_TRACK_RE = re.compile(r"(?:^|_)v[2-9]$")
