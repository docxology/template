"""Typed model objects for Generalized Notation Notation."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

ArrayF = NDArray[np.float64]


@dataclass(frozen=True)
class GnnVariable:
    name: str
    dims: tuple[int, ...]
    dtype: str
    comment: str = ""
    value: ArrayF | None = None

    @property
    def size(self) -> int:
        n = 1
        for d in self.dims:
            n *= d
        return n


@dataclass(frozen=True)
class GnnConnection:
    source: str
    target: str
    directed: bool
    label: str | None = None


@dataclass
class GnnModel:
    section: str
    version: str
    name: str
    variables: dict[str, GnnVariable] = field(default_factory=dict)
    connections: list[GnnConnection] = field(default_factory=list)
    ontology: dict[str, str] = field(default_factory=dict)
    model_parameters: dict[str, str] = field(default_factory=dict)
    annotation: str = ""
    equations: list[str] = field(default_factory=list)
    time: str = ""

    def variable(self, name: str) -> GnnVariable:
        if name not in self.variables:
            raise KeyError(f"GNN model declares no variable {name!r}")
        return self.variables[name]

    def has(self, name: str) -> bool:
        return name in self.variables
