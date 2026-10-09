"""Bounded independent SVG geometry for original Mermaid graph witnesses."""

from __future__ import annotations

import math
import re
from typing import Any

from defusedxml.ElementTree import fromstring

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(rf"[a-zA-Z]|{NUMBER}")
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def numbers(text: str) -> list[float]:
    tokens = re.findall(NUMBER, text)
    remainder = re.sub(NUMBER, "", text)
    if remainder.strip(" ,\t\r\n"):
        raise ValueError("Mermaid SVG numeric geometry contains unsupported syntax")
    result = [float(token) for token in tokens]
    if len(result) > 20_000 or any(not math.isfinite(x) or abs(x) > 1_000_000 for x in result):
        raise ValueError("Mermaid SVG numeric geometry exceeds its finite bound")
    return result


def multiply(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    a, b, c, d, e, f = left
    g, h, i, j, k, offset_y = right
    return (
        a * g + c * h,
        b * g + d * h,
        a * i + c * j,
        b * i + d * j,
        a * k + c * offset_y + e,
        b * k + d * offset_y + f,
    )


def transform(text: str) -> tuple[float, ...]:
    result: tuple[float, ...] = IDENTITY
    matches = list(re.finditer(r"([A-Za-z]+)\s*\(([^()]*)\)", text))
    if re.sub(r"([A-Za-z]+)\s*\(([^()]*)\)", "", text).strip(" ,\t\r\n") or len(matches) > 32:
        raise ValueError("Mermaid SVG transform has unsupported/unbounded syntax")
    for match in matches:
        name, values = match[1], numbers(match[2])
        matrix: tuple[float, ...]
        if name == "translate" and len(values) in {1, 2}:
            matrix = (1, 0, 0, 1, values[0], values[1] if len(values) == 2 else 0)
        elif name == "scale" and len(values) in {1, 2}:
            matrix = (values[0], 0, 0, values[-1], 0, 0)
        elif name == "matrix" and len(values) == 6:
            matrix = tuple(values)
        elif name == "rotate" and len(values) in {1, 3}:
            angle = math.radians(values[0])
            cosine, sine = math.cos(angle), math.sin(angle)
            matrix = (cosine, sine, -sine, cosine, 0, 0)
            if len(values) == 3:
                matrix = multiply(
                    multiply((1, 0, 0, 1, values[1], values[2]), matrix),
                    (1, 0, 0, 1, -values[1], -values[2]),
                )
        else:
            raise ValueError("Mermaid SVG transform operation requires independent interpretation")
        result = multiply(result, matrix)
    if abs(result[0] * result[3] - result[1] * result[2]) < 1e-12:
        raise ValueError("Mermaid SVG transform collapsed actual geometry")
    return result


def point(matrix: tuple[float, ...], value: tuple[float, float]) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    x, y = value
    return (a * x + c * y + e, b * x + d * y + f)


def path_geometry(text: str) -> dict[str, Any]:
    """Interpret actual path commands/endpoints/tangents, never a DOM pass bit."""
    if len(text) > 256_000 or TOKEN.sub("", text).strip(" ,\t\r\n"):
        raise ValueError("Mermaid SVG path exceeds its finite grammar")
    tokens = TOKEN.findall(text)
    if not tokens or len(tokens) > 20_000:
        raise ValueError("Mermaid SVG path is empty/unbounded")
    arity = {
        "M": 2,
        "L": 2,
        "H": 1,
        "V": 1,
        "C": 6,
        "S": 4,
        "Q": 4,
        "T": 2,
        "A": 7,
        "Z": 0,
    }
    command = None
    index = 0
    current = (0.0, 0.0)
    start = None
    endpoints = []
    controls = []
    segments = []
    commands = []
    closed = False
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command is None or command.upper() not in arity:
            raise ValueError("Mermaid SVG path command is unsupported")
        upper = command.upper()
        count = arity[upper]
        if upper == "Z":
            if start is None:
                raise ValueError("Mermaid SVG close has no subpath")
            segments.append((current, start))
            current = start
            endpoints.append(current)
            commands.append((upper, []))
            closed = True
            command = None
            continue
        if index + count > len(tokens) or any(value.isalpha() for value in tokens[index : index + count]):
            raise ValueError("Mermaid SVG path has incomplete coordinates")
        values = [float(value) for value in tokens[index : index + count]]
        index += count
        if any(not math.isfinite(value) or abs(value) > 1_000_000 for value in values):
            raise ValueError("Mermaid SVG path coordinates exceed finite bounds")
        origin = current
        relative = command.islower()

        def xy(x: float, y: float) -> tuple[float, float]:
            return (x + origin[0], y + origin[1]) if relative else (x, y)

        if upper in {"M", "L", "T"}:
            end = xy(*values)
        elif upper == "H":
            end = (values[0] + origin[0] if relative else values[0], origin[1])
        elif upper == "V":
            end = (origin[0], values[0] + origin[1] if relative else values[0])
        elif upper in {"C", "S", "Q"}:
            pairs = [xy(values[j], values[j + 1]) for j in range(0, len(values), 2)]
            controls.extend(pairs[:-1])
            end = pairs[-1]
        else:
            if values[0] < 0 or values[1] < 0 or values[3] not in {0, 1} or values[4] not in {0, 1}:
                raise ValueError("Mermaid SVG elliptical arc parameters differ")
            end = xy(values[-2], values[-1])
        if upper == "M":
            start = end
            command = "l" if relative else "L"
        else:
            segments.append((current, end))
        current = end
        endpoints.append(end)
        commands.append((upper, values))
    if not endpoints:
        raise ValueError("Mermaid SVG path has no actual points")
    return {
        "endpoints": endpoints,
        "controls": controls,
        "segments": segments,
        "commands": commands,
        "closed": closed,
    }


class SvgGeometry:
    """Decode finite original XML and all parent transforms without a renderer."""

    def __init__(self, data: bytes):
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Mermaid SVG exceeds finite byte bound")
        self.root = fromstring(data)
        self.elements = list(self.root.iter())
        if self.root.tag != "{http://www.w3.org/2000/svg}svg" or len(self.elements) > 100_000:
            raise ValueError("Mermaid SVG root/node budget differs")
        self.parents = {child: parent for parent in self.elements for child in parent}
        self.ids: dict[str, Any] = {}
        for element in self.elements:
            local = self.local(element)
            if local in {
                "script",
                "image",
                "img",
                "iframe",
                "object",
                "embed",
                "a",
                "video",
                "audio",
            }:
                raise ValueError("Mermaid SVG contains unsupported active/external content")
            identity = element.get("id")
            if identity:
                if identity in self.ids:
                    raise ValueError("Mermaid SVG contains duplicate identities")
                self.ids[identity] = element
            for key, value in element.attrib.items():
                if key.rsplit("}", 1)[-1].lower().startswith("on"):
                    raise ValueError("Mermaid SVG contains active events")
                if key.rsplit("}", 1)[-1] == "href" and not value.startswith("#"):
                    raise ValueError("Mermaid SVG reference escapes original bytes")
                self.urls(value)
            if local == "style":
                if "@import" in (element.text or "").lower():
                    raise ValueError("Mermaid SVG imports external styles")
                self.urls(element.text or "")
        box = numbers(self.root.get("viewBox", ""))
        if len(box) != 4 or min(box[2:]) <= 0 or box[2] * box[3] > 60_000_000:
            raise ValueError("Mermaid SVG viewBox has invalid bounded geometry")
        self.viewbox = box

    @staticmethod
    def local(element: Any) -> str:
        return str(element.tag).rsplit("}", 1)[-1]

    @staticmethod
    def urls(text: str) -> None:
        if any(not item.strip(" \r\n\t\"'").startswith("#") for item in re.findall(r"url\(([^)]+)\)", text, re.I)):
            raise ValueError("Mermaid SVG URL escapes admitted bytes")

    def world(self, element: Any) -> tuple[float, ...]:
        parents = []
        while element is not None:
            parents.append(element)
            element = self.parents.get(element)
        result: tuple[float, ...] = IDENTITY
        for parent in reversed(parents):
            result = multiply(result, transform(parent.get("transform", "")))
        return result

    def shape(self, element: Any) -> dict[str, Any] | None:
        local = self.local(element)

        def scalar(key: str, default: str = "0") -> float:
            value = numbers(element.get(key, default))
            if len(value) != 1:
                raise ValueError("Mermaid SVG primitive scalar differs")
            return value[0]

        circle = None
        if local == "rect":
            x, y, w, h = scalar("x"), scalar("y"), scalar("width"), scalar("height")
            if min(w, h) <= 0:
                return None
            points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        elif local in {"circle", "ellipse"}:
            x, y = scalar("cx"), scalar("cy")
            rx = scalar("r") if local == "circle" else scalar("rx")
            ry = rx if local == "circle" else scalar("ry")
            if min(rx, ry) <= 0:
                return None
            points = [
                (x - rx, y - ry),
                (x + rx, y - ry),
                (x + rx, y + ry),
                (x - rx, y + ry),
            ]
            circle = (x, y, rx, ry)
        elif local == "polygon":
            values = numbers(element.get("points", ""))
            if len(values) < 6 or len(values) % 2:
                raise ValueError("Mermaid SVG polygon geometry differs")
            points = list(zip(values[::2], values[1::2]))
        elif local == "path":
            geometry = path_geometry(element.get("d", ""))
            if not geometry["closed"]:
                return None
            points = geometry["endpoints"] + geometry["controls"]
        else:
            return None
        matrix = self.world(element)
        actual = [point(matrix, p) for p in points]
        xs = [p[0] for p in actual]
        ys = [p[1] for p in actual]
        box = [min(xs), min(ys), max(xs), max(ys)]
        if min(box[2] - box[0], box[3] - box[1]) <= 0:
            return None
        return {
            "primitive": local,
            "box": box,
            "points": actual,
            "circle": circle,
            "matrix": matrix,
        }

    def frame(self, group: Any) -> dict[str, Any]:
        shapes = []
        for element in group.iter():
            ancestor = element
            skip = False
            while ancestor is not group:
                if (
                    self.local(ancestor) in {"foreignObject", "marker", "defs"}
                    or "label" in ancestor.get("class", "").split()
                ):
                    skip = True
                    break
                ancestor = self.parents.get(ancestor)
                if ancestor is None:
                    break
            if not skip:
                shape = self.shape(element)
                if shape:
                    shapes.append(shape)
        if not shapes:
            raise ValueError("Mermaid source node has no actual graphic boundary")
        return max(
            shapes,
            key=lambda s: (s["box"][2] - s["box"][0]) * (s["box"][3] - s["box"][1]),
        )

    def edge_points(self, element: Any) -> dict[str, Any]:
        matrix = self.world(element)
        if self.local(element) == "line":
            values = [numbers(element.get(key, ""))[0] for key in ("x1", "y1", "x2", "y2")]
            points = [
                point(matrix, (values[0], values[1])),
                point(matrix, (values[2], values[3])),
            ]
        elif self.local(element) == "path":
            geometry = path_geometry(element.get("d", ""))
            points = [point(matrix, p) for p in geometry["endpoints"]]
        else:
            raise ValueError("Mermaid source edge has no independent line/path geometry")
        if len(points) < 2 or math.dist(points[0], points[-1]) < 1e-6:
            raise ValueError("Mermaid source edge has collapsed endpoints")
        return {"start": points[0], "end": points[-1], "points": points}


def boundary_distance(frame: dict[str, Any], position: tuple[float, float]) -> float:
    """Actual endpoint distance from the decoded node boundary."""
    if frame["circle"]:
        x, y, rx, ry = frame["circle"]
        matrix = frame["matrix"]
        cx, cy = point(matrix, (x, y))
        sx = math.hypot(matrix[0], matrix[1])
        sy = math.hypot(matrix[2], matrix[3])
        radius = math.sqrt(((position[0] - cx) / (rx * sx)) ** 2 + ((position[1] - cy) / (ry * sy)) ** 2)
        return float(abs(radius - 1) * min(rx * sx, ry * sy))
    points = frame["points"]

    def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        dx, dy = b[0] - a[0], b[1] - a[1]
        denominator = dx * dx + dy * dy
        t = (
            0
            if not denominator
            else max(
                0,
                min(
                    1,
                    ((position[0] - a[0]) * dx + (position[1] - a[1]) * dy) / denominator,
                ),
            )
        )
        return math.dist(position, (a[0] + t * dx, a[1] + t * dy))

    return min(distance(a, b) for a, b in zip(points, points[1:] + points[:1]))
