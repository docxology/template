"""Finite independent TeX expression trees for actual native package readback.

Grouping, fractions, roots, scripts, accents, fonts and array cells survive.
Only typography spacing/sizing and named equivalent operator spellings are
canonicalized. Unknown commands remain explicit failures, never deleted.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar, cast

MAX_EXPRESSION_BYTES = 64 * 1024
MAX_TOKENS = 20_000
MAX_DEPTH = 96
_TOKENS = re.compile(r"\\[A-Za-z]+|\\[^A-Za-z]|[^\s]", re.UNICODE)
_ALIASES = {
    "tfrac": "frac",
    "dfrac": "frac",
    "leq": "le",
    "geq": "ge",
    "rightarrow": "to",
    "lVert": "Vert",
    "rVert": "Vert",
    "parallel": "Vert",
    "widehat": "hat",
    "dots": "ldots",
}
_SPACING = {",", "!", ";", ":", " ", "quad", "qquad", "enspace", "thinspace"}
_SYMBOLS = frozenset(
    {
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "varepsilon",
        "lambda",
        "mu",
        "sigma",
        "rho",
        "kappa",
        "Delta",
        "pi",
        "omega",
        "theta",
        "nabla",
        "infty",
        "approx",
        "pm",
        "times",
        "cdot",
        "le",
        "ge",
        "in",
        "to",
        "leftarrow",
        "ast",
        "star",
        "blacksquare",
        "dots",
        "ldots",
        "Vert",
        "vert",
        "%",
        "{",
        "}",
        "|",
    }
)
_OPERATORS = frozenset({"min", "max", "log", "ln", "lim", "arg", "sin", "cos", "exp", "int", "sum", "prod"})
_STYLES = frozenset({"mathbb", "mathbf", "mathrm", "mathit", "mathsf", "mathtt", "mathcal", "boldsymbol"})
_ACCENTS = frozenset({"widehat", "hat", "overline", "bar", "dot", "ddot", "vec", "tilde", "widetilde"})


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _bounded_parse(function: Callable[Concatenate[_Parser, _P], _R]) -> Callable[Concatenate[_Parser, _P], _R]:
    def bounded(self: _Parser, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        self.depth += 1
        try:
            if self.depth > MAX_DEPTH:
                raise ValueError("native Office math exceeds finite nesting budget")
            return function(self, *args, **kwargs)
        finally:
            self.depth -= 1

    return bounded


class _Parser:
    def __init__(self, expression: str, *, omit_roman_style: bool = False):
        self.tokens = _TOKENS.findall(expression)
        self.index = 0
        self.depth = 0
        self.omit_roman_style = omit_roman_style
        if len(self.tokens) > MAX_TOKENS:
            raise ValueError("native Office math exceeds finite token budget")

    @_bounded_parse
    def argument(self) -> tuple[Any, ...]:
        if self.index >= len(self.tokens):
            raise ValueError("native Office math argument is missing")
        if self.tokens[self.index] == "{":
            self.index += 1
            return self.sequence("}")
        return (self.atom(),)

    @_bounded_parse
    def atom(self) -> Any:
        if self.index >= len(self.tokens):
            raise ValueError("native Office math atom is missing")
        token = self.tokens[self.index]
        self.index += 1
        if token == "{":
            return ("group", self.sequence("}"))
        if not token.startswith("\\"):
            return ("glyph", token)
        command = _ALIASES.get(token[1:], token[1:])
        if command in {"left", "right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr"}:
            # Sizing leaves the actual following fence obligatory.
            if command == "right" and self.index < len(self.tokens) and self.tokens[self.index] == ".":
                self.index += 1
                return ("invisible-fence",)
            return self.atom()
        if command in {"lbrack", "rbrack", "ast"}:
            return ("glyph", {"lbrack": "[", "rbrack": "]", "ast": "*"}[command])
        if command in _SYMBOLS:
            return ("symbol", "Vert" if command == "|" else command)
        if command in _OPERATORS:
            return ("operator", command)
        if command == "frac":
            return ("fraction", self.argument(), self.argument())
        if command == "sqrt":
            degree: tuple[Any, ...] = ()
            if self.index < len(self.tokens) and self.tokens[self.index] == "[":
                self.index += 1
                degree = self.sequence("]")
            return ("root", degree, self.argument())
        if command in _STYLES | _ACCENTS:
            argument = self.argument()
            if command == "mathrm" and self.omit_roman_style:
                return ("group", argument)
            return ("style" if command in _STYLES else "accent", command, argument)
        if command in {"text", "operatorname"}:
            argument = self.argument()
            return ("text" if command == "text" else "operator-text", argument)
        if command == "begin":
            environment = self.argument()
            name = "".join(node[1] for node in environment if node[0] == "glyph")
            if name not in {"aligned", "matrix", "bmatrix", "pmatrix", "cases", "array"}:
                raise ValueError(f"native Office math environment unsupported: {name}")
            rows: list[list[tuple[Any, ...]]] = [[]]
            while self.index < len(self.tokens):
                rows[-1].append(self.sequence(None, stop_array=True))
                token = self.tokens[self.index]
                self.index += 1
                if token == "&":
                    continue
                if token == "\\\\":
                    rows.append([])
                    continue
                if token == "\\end":
                    if self.argument() != environment:
                        raise ValueError("native Office math environment end differs")
                    return ("array", name, tuple(tuple(row) for row in rows))
                raise ValueError("native Office math array delimiter unsupported")
            raise ValueError("native Office math environment has no end")
        raise ValueError(f"native Office math command unsupported: {token}")

    @_bounded_parse
    def sequence(self, end: str | None, *, stop_array: bool = False) -> tuple[Any, ...]:
        result: list[Any] = []
        while self.index < len(self.tokens):
            token = self.tokens[self.index]
            if end and token == end:
                self.index += 1
                return tuple(result)
            if stop_array and token in {"&", "\\\\", "\\end"}:
                return tuple(result)
            if token.startswith("\\") and token[1:] in _SPACING:
                self.index += 1
                continue
            if token in {"^", "_"}:
                self.index += 1
                if not result:
                    raise ValueError("native Office script has no base")
                argument = self.argument()
                if not argument:
                    continue
                base = result.pop()
                if base[0] == "group" and len(base[1]) == 1:
                    base = base[1][0]
                result.append(("script", token, base, argument))
                continue
            value = self.atom()
            if value[0] == "group" and (self.index == len(self.tokens) or self.tokens[self.index] not in {"^", "_"}):
                result.extend(value[1])
            else:
                result.append(value)
        if end:
            raise ValueError("native Office math group has no end")
        return tuple(result)


def office_math_expression(expression: str, *, omit_roman_style: bool = False) -> tuple[Any, ...]:
    """Parse every source symbol into an independent ordered expression tree."""
    if len(expression.encode()) > MAX_EXPRESSION_BYTES:
        raise ValueError("native Office math exceeds finite expression budget")
    parser = _Parser(expression, omit_roman_style=omit_roman_style)
    result = parser.sequence(None)
    if not result:
        raise ValueError("native Office math expression is empty")

    def arrays(value):
        if not isinstance(value, tuple):
            return value
        value = tuple(arrays(child) for child in value)
        result = []
        index = 0
        while index < len(value):
            if (
                index + 2 < len(value)
                and value[index] == ("symbol", "{")
                and isinstance(value[index + 1], tuple)
                and value[index + 1][:2] == ("array", "matrix")
                and value[index + 2] == ("invisible-fence",)
            ):
                result.append(("array", "cases", value[index + 1][2]))
                index += 3
            else:
                result.append(value[index])
                index += 1
        return tuple(result)

    return cast(tuple[Any, ...], arrays(result))


def office_roman_source_segments(expression: str) -> tuple[str, ...]:
    """Retain explicit upright unit characters for direct DOCX OMML custody."""
    tree = office_math_expression(expression)
    segments = []

    def glyphs(node):
        if not isinstance(node, tuple):
            return ""
        if len(node) == 2 and node[0] == "glyph":
            return node[1]
        if node and node[0] == "script":
            return glyphs(node[2]) + glyphs(node[3])
        return "".join(glyphs(child) for child in node)

    def walk(node):
        if not isinstance(node, tuple):
            return
        if node[:2] == ("style", "mathrm"):
            segment = glyphs(node[2])
            if not segment:
                raise ValueError("DOCX upright math source requires a supported glyph segment")
            segments.append(segment)
        for child in node:
            walk(child)

    walk(tree)
    return tuple(segments)
