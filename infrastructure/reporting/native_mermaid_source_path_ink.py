"""Finite Source path extrema and real segment directions for SVG markers.

Arc endpoint conversion follows SVG2 Appendix B.2. It is not the cubic
approximation used by the default FontTools arc fallback. Original XML and
independently held affine transforms supply every coordinate; raster pixels do
not choose extrema, tangents, clipping or a geometric tolerance.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

from infrastructure.reporting.native_mermaid_svg_geometry import IDENTITY, NUMBER, point

Vector = tuple[float, float]
MAX_SEGMENTS = 20_000


def _finite(value: Vector) -> Vector:
    if any(not math.isfinite(x) or abs(x) > 1_000_000 for x in value):
        raise ValueError("Source path coordinate exceeds its finite geometry profile")
    return value


def _difference(left: Vector, right: Vector) -> Vector:
    return (left[0] - right[0], left[1] - right[1])


def _direction(origin: Vector, values: tuple[Vector, ...]) -> Vector:
    for value in values:
        direction = _difference(value, origin)
        if direction != (0, 0):
            return direction
    return (0, 0)


@dataclass(frozen=True)
class SourcePathSegment:
    start: Vector
    end: Vector
    start_direction: Vector
    end_direction: Vector


@dataclass(frozen=True)
class SourcePathSubpath:
    start: Vector
    segments: tuple[SourcePathSegment, ...]
    closed: bool


class SourcePathPen:
    """Interpret actual parser operations, preserving each original vertex."""

    def __init__(self, matrix: tuple[float, ...] = IDENTITY):
        self.matrix = matrix
        self.bounds_pen = BoundsPen(None)
        self.extra: list[Vector] = []
        self.subpaths: list[SourcePathSubpath] = []
        self.segments: list[SourcePathSegment] = []
        self.current: Vector | None = None
        self.start: Vector | None = None
        self.count = 0

    def _position(self) -> Vector:
        if self.current is None:
            raise ValueError("Source path drawing operation has no original moveto")
        return self.current

    def _add(self, end: Vector, outgoing: Vector, incoming: Vector) -> None:
        self.count += 1
        if self.count > MAX_SEGMENTS:
            raise ValueError("Source path exceeds unchanged finite segment admission")
        self.segments.append(SourcePathSegment(self._position(), _finite(end), outgoing, incoming))
        self.current = end

    def moveTo(self, value: Vector) -> None:
        if self.current is not None:
            self.endPath()
        self.current = self.start = _finite(value)
        self.bounds_pen.moveTo(point(self.matrix, value))

    def lineTo(self, value: Vector) -> None:
        value = _finite(value)
        direction = _difference(value, self._position())
        self._add(value, direction, direction)
        self.bounds_pen.lineTo(point(self.matrix, value))

    def curveTo(self, *values: Vector) -> None:
        if len(values) != 3:
            raise ValueError("Source cubic parser operation is incomplete")
        first, second, end = (_finite(item) for item in values)
        self._add(
            end,
            _direction(self._position(), (first, second, end)),
            _direction(end, (second, first, self._position())),
        )
        previous = self.segments[-1]
        # End direction is the forward incoming tangent, not its reverse.
        self.segments[-1] = SourcePathSegment(
            previous.start,
            previous.end,
            previous.start_direction,
            (-previous.end_direction[0], -previous.end_direction[1]),
        )
        self.bounds_pen.curveTo(*(point(self.matrix, item) for item in (first, second, end)))

    def qCurveTo(self, *values: Vector) -> None:
        if len(values) != 2:
            raise ValueError("Source quadratic parser operation is incomplete")
        control, end = (_finite(item) for item in values)
        outgoing = _direction(self._position(), (control, end))
        incoming = _direction(end, (control, self._position()))
        self._add(end, outgoing, (-incoming[0], -incoming[1]))
        self.bounds_pen.qCurveTo(point(self.matrix, control), point(self.matrix, end))

    def arcTo(self, rx: float, ry: float, rotation: float, large: bool, sweep: bool, end: Vector) -> None:
        """Keep exact ellipse extrema in the actual world affine frame."""
        start = self._position()
        end = _finite(end)
        if any(not math.isfinite(x) or abs(x) > 1_000_000 for x in (rx, ry, rotation)):
            raise ValueError("Source arc radius/rotation exceeds its finite original profile")
        if start == end:
            # SVG endpoint-equal arc is omitted; it is not a full ellipse.
            return
        rx, ry = abs(rx), abs(ry)
        if rx == 0 or ry == 0:
            self.lineTo(end)
            return
        phi = math.radians(rotation % 360)
        cosine, sine = math.cos(phi), math.sin(phi)
        dx, dy = (start[0] - end[0]) / 2, (start[1] - end[1]) / 2
        xp, yp = cosine * dx + sine * dy, -sine * dx + cosine * dy
        radii_scale = xp * xp / (rx * rx) + yp * yp / (ry * ry)
        if not math.isfinite(radii_scale):
            raise ValueError("Source ellipse radii conversion is not finite")
        if radii_scale > 1:
            scale = math.sqrt(radii_scale)
            rx, ry = rx * scale, ry * scale
            coefficient = 0.0  # SVG radii correction has exactly one centre.
        else:
            denominator = rx * rx * yp * yp + ry * ry * xp * xp
            numerator = rx * rx * ry * ry - denominator
            if denominator <= 0 or numerator < 0:
                raise ValueError("Source ellipse conversion has no finite non-negative centre solution")
            coefficient = math.sqrt(numerator / denominator) * (-1 if large == sweep else 1)
        cxp, cyp = coefficient * rx * yp / ry, -coefficient * ry * xp / rx
        centre = _finite(
            (
                cosine * cxp - sine * cyp + (start[0] + end[0]) / 2,
                sine * cxp + cosine * cyp + (start[1] + end[1]) / 2,
            )
        )
        first = ((xp - cxp) / rx, (yp - cyp) / ry)
        last = ((-xp - cxp) / rx, (-yp - cyp) / ry)
        theta = math.atan2(first[1], first[0])
        delta = math.atan2(first[0] * last[1] - first[1] * last[0], first[0] * last[0] + first[1] * last[1])
        if sweep and delta < 0:
            delta += math.tau
        elif not sweep and delta > 0:
            delta -= math.tau
        ux, uy = rx * cosine, rx * sine
        vx, vy = -ry * sine, ry * cosine
        a, b, c, d, _, _ = self.matrix
        world_u = (a * ux + c * uy, b * ux + d * uy)
        world_v = (a * vx + c * vy, b * vx + d * vy)
        world_centre = point(self.matrix, centre)
        angles = []
        self.extra.extend((_finite(point(self.matrix, start)), _finite(point(self.matrix, end))))
        for u, v in zip(world_u, world_v, strict=True):
            angle = math.atan2(v, u)
            for candidate in (angle, angle + math.pi):
                distance = (candidate - theta) % math.tau if delta > 0 else (theta - candidate) % math.tau
                if distance <= abs(delta):
                    angles.append(candidate)
        self.extra.extend(
            _finite(
                (
                    world_centre[0] + world_u[0] * math.cos(angle) + world_v[0] * math.sin(angle),
                    world_centre[1] + world_u[1] * math.cos(angle) + world_v[1] * math.sin(angle),
                )
            )
            for angle in angles
        )
        sign = 1 if delta > 0 else -1

        def tangent(angle: float) -> Vector:
            return (
                sign * (-ux * math.sin(angle) + vx * math.cos(angle)),
                sign * (-uy * math.sin(angle) + vy * math.cos(angle)),
            )

        self._add(end, tangent(theta), tangent(theta + delta))
        # BoundsPen must still track the real endpoint for following curves;
        # the chord is contained in the ellipse's admitted exact enclosure.
        self.bounds_pen.lineTo(point(self.matrix, end))

    def _finish(self, closed: bool) -> None:
        if self.start is None:
            raise ValueError("Source path terminates without an original subpath")
        self.subpaths.append(SourcePathSubpath(self.start, tuple(self.segments), closed))
        self.segments = []
        self.current = self.start = None

    def closePath(self) -> None:
        if self.start is None:
            raise ValueError("Source path close has no moveto")
        if self.current != self.start:
            self.lineTo(self.start)
        self.bounds_pen.closePath()
        self._finish(True)

    def endPath(self) -> None:
        self.bounds_pen.endPath()
        self._finish(False)

    def bounds(self) -> list[float] | None:
        values = list(self.extra)
        if self.bounds_pen.bounds is not None:
            x1, y1, x2, y2 = self.bounds_pen.bounds
            values += [(x1, y1), (x2, y2)]
        return (
            [min(p[0] for p in values), min(p[1] for p in values), max(p[0] for p in values), max(p[1] for p in values)]
            if values
            else None
        )


def source_path_ink(text: str, matrix: tuple[float, ...] = IDENTITY) -> SourcePathPen:
    if len(text) > 100_000 or re.sub(rf"[MmZzLlHhVvCcSsQqTtAa]|{NUMBER}", "", text).strip(" ,\t\r\n"):
        raise ValueError("Source path exceeds its original finite grammar")
    if len(re.findall(rf"[A-Za-z]|{NUMBER}", text)) > MAX_SEGMENTS:
        raise ValueError("Source path lexical count exceeds unchanged finite admission")
    pen = SourcePathPen(matrix)
    parse_path(text, pen)
    return pen


def marker_vertices(pen: SourcePathPen) -> list[dict[str, Any]]:
    """Global start/end and every subpath vertex; no equal-coordinate dedup."""
    vertices: list[dict[str, Any]] = []
    for subpath in pen.subpaths:
        segments = subpath.segments
        if not segments:
            vertices.append({"position": subpath.start, "angle": 0.0})
            continue
        positions = [segments[0].start, *(segment.end for segment in segments)]
        # Linear direction propagation retains every original vertex. Building
        # growing prefix/suffix lists for each vertex is quadratic and violates
        # the finite Source operation even when segment counts are bounded.
        incoming: list[Vector | None] = [None] * (len(segments) + 1)
        outgoing: list[Vector | None] = [None] * (len(segments) + 1)
        for index, segment in enumerate(segments, start=1):
            incoming[index] = segment.end_direction if segment.end_direction != (0, 0) else incoming[index - 1]
        for index in range(len(segments) - 1, -1, -1):
            direction = segments[index].start_direction
            outgoing[index] = direction if direction != (0, 0) else outgoing[index + 1]
        for index, position in enumerate(positions):
            left = incoming[index]
            right = outgoing[index]
            if subpath.closed:
                left = left if left is not None else incoming[-1]
                right = right if right is not None else outgoing[0]
            if left is not None and right is not None:
                before, after = math.atan2(left[1], left[0]), math.atan2(right[1], right[0])
                turn = (after - before + math.pi) % math.tau - math.pi
                if abs(turn) == math.pi:
                    raise ValueError(
                        "Source marker antiparallel tangent requires its independently declared direction profile"
                    )
                angle = before + turn / 2
            else:
                vector = left or right or (1.0, 0.0)
                angle = math.atan2(vector[1], vector[0])
            vertices.append({"position": position, "angle": angle})
    for index, row in enumerate(vertices):
        row["attachment"] = "markerStart" if index == 0 else "markerEnd" if index == len(vertices) - 1 else "markerMid"
        row["vertex_ordinal"] = index
    return vertices
