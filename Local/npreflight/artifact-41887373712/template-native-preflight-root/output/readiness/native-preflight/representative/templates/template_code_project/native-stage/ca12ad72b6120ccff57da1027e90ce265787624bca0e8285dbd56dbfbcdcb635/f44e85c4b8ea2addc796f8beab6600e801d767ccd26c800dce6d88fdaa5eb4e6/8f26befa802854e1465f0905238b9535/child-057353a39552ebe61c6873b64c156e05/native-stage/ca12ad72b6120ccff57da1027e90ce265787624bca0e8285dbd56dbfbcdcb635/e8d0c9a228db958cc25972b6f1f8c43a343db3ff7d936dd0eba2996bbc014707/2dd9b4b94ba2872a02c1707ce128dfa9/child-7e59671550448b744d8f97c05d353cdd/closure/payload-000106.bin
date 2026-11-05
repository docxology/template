"""Observe the existing six plotted figures inside the actual analysis scope.

Only the runtime's genuine supervised branch calls this helper. It emits DATA
through existing completed-write/returned-read APIs; no companion grants native
ownership, scientific interpretation or library admission.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from io import BytesIO
from pathlib import Path
from typing import Any, TypedDict

from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from infrastructure.core.analysis_read_custody import read_analysis_bytes
from infrastructure.core.analysis_write_custody import current_analysis_write_project, write_analysis_bytes

SELECTED = {
    "convergence_plot.png": ("convergence.py", "generate_convergence_plot"),
    "convergence_rate_comparison.png": ("convergence.py", "generate_convergence_rate_plot"),
    "step_size_sensitivity.png": ("sensitivity.py", "generate_step_size_sensitivity_plot"),
    "algorithm_complexity.png": ("scientific_complexity.py", "generate_complexity_visualization"),
    "stability_analysis.png": ("scientific_stability.py", "generate_stability_visualization"),
    "performance_benchmark.png": ("scientific_stability.py", "generate_benchmark_visualization"),
}


class _SaveOptions(TypedDict):
    dpi: int
    bbox_inches: str
    facecolor: str
    edgecolor: str


SAVE: _SaveOptions = {"dpi": 300, "bbox_inches": "tight", "facecolor": "white", "edgecolor": "none"}


def _number(value: Any) -> str:
    """Serialize exact actual binary64, including explicit plotted infinities."""
    if isinstance(value, bool):
        raise ValueError("Code figure numeric payload cannot be a boolean")
    number = float(value)
    if number != number:
        raise ValueError("Code selected figure has an unsupported NaN/masked artist")
    return number.hex()


def _array(value: Any) -> Any:
    value = value.tolist() if hasattr(value, "tolist") else value
    if isinstance(value, (list, tuple)):
        if len(value) > 100_000:
            raise ValueError("Code selected figure exceeds its actual bounded plotted-series ceiling")
        return [_array(item) for item in value]
    return _number(value)


def _transform(ax: Any, transform: Any) -> str:
    if transform == ax.transData:
        return "data"
    if transform == ax.get_xaxis_transform():
        return "vertical"
    if transform == ax.get_yaxis_transform():
        return "horizontal"
    raise ValueError("Code figure artist uses an unsupported actual Source transform")


def _text(ax: Any, text: Any) -> dict[str, Any]:
    row = {"text": text.get_text(), "position": _array(text.get_position()), "annotation_xy": None}
    if hasattr(text, "xy"):
        if not isinstance(text.xycoords, str) or not isinstance(text.anncoords, str):
            raise ValueError("Code figure annotation uses unsupported actual Source coordinates")
        row.update(
            annotation_xy=_array(text.xy), coordinate="annotation", xycoords=text.xycoords, textcoords=text.anncoords
        )
    else:
        row["coordinate"] = _transform(ax, text.get_transform())
    return row


def observe_figure(figure: Figure) -> list[dict[str, Any]]:
    """Read actual ordered artists, axes meanings and retained label geometry."""
    if not isinstance(figure, Figure) or not 0 < len(figure.axes) <= 8:
        raise ValueError("Code figure requires the actual bounded matplotlib Figure/Axes")
    if figure.artists or figure.images or figure.legends or figure.subfigs:
        raise ValueError("Code figure contains an unsupported actual Source figure artist")
    axes = []
    for ax in figure.axes:
        colorbar = getattr(ax, "_colorbar", None)
        if ax.artists or ax.tables or ax.child_axes:
            raise ValueError("Code figure contains an unsupported actual Source axes artist")
        if colorbar is None and ax.collections:
            raise ValueError("Code figure contains an unsupported actual Source collection")
        if colorbar is not None and (
            list(ax.collections) != [colorbar.dividers, colorbar.solids]
            or colorbar.dividers.get_segments()
            or colorbar.solids.get_clim() != colorbar.mappable.get_clim()
            or colorbar.solids.get_cmap().name != colorbar.mappable.get_cmap().name
            or (colorbar.orientation, colorbar.spacing, colorbar.extend) != ("vertical", "uniform", "neither")
        ):
            raise ValueError("Code figure lost its fixed Source colorbar range/artist roster")
        if any(len(items) > 10_000 for items in (ax.lines, ax.patches, ax.images, ax.texts)):
            raise ValueError("Code figure has too many actual native artists")
        lines = []
        for line in ax.lines:
            lines.append(
                {
                    "x": _array(line.get_xdata(orig=False)),
                    "y": _array(line.get_ydata(orig=False)),
                    "transform": _transform(ax, line.get_transform()),
                    "label": line.get_label(),
                }
            )
        bars = []
        for patch in ax.patches:
            if not isinstance(patch, Rectangle):
                raise ValueError("Code figure requires its fixed actual rectangular bar artists")
            bars.append({key: _number(getattr(patch, "get_" + key)()) for key in ("x", "y", "width", "height")})
        images = [
            {
                "array": _array(image.get_array()),
                "extent": _array(image.get_extent()),
                "clim": _array(image.get_clim()),
                "cmap": image.get_cmap().name,
                "origin": image.origin,
            }
            for image in ax.images
        ]
        legend = ax.get_legend()
        axes.append(
            {
                "title": ax.get_title(),
                "xlabel": ax.get_xlabel(),
                "ylabel": ax.get_ylabel(),
                "xscale": ax.get_xscale(),
                "yscale": ax.get_yscale(),
                "xlim": _array(ax.get_xlim()),
                "ylim": _array(ax.get_ylim()),
                "lines": lines,
                "bars": bars,
                "images": images,
                "texts": [_text(ax, text) for text in ax.texts],
                "legend": None if legend is None else [text.get_text() for text in legend.get_texts()],
                "colorbar": None
                if not hasattr(ax, "_colorbar")
                else {"clim": _array(ax._colorbar.mappable.get_clim()), "cmap": ax._colorbar.mappable.get_cmap().name},
                "xticklabels": [text.get_text() for text in ax.get_xticklabels()],
                "yticklabels": [text.get_text() for text in ax.get_yticklabels()],
                "position": _array(ax.get_position().bounds),
            }
        )
    return axes


def _producer(root: Path, name: str) -> dict[str, Any]:
    expected_file, expected_function = SELECTED[name]
    source = root / "src/template_code_project/figures" / expected_file
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame is not None else None
        while frame is not None:
            if Path(frame.f_code.co_filename).absolute() == source.absolute():
                if frame.f_code.co_name != expected_function:
                    raise ValueError("Code figure save lost its actual selected Source caller")
                return {
                    "source": source.relative_to(root).as_posix(),
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "function": frame.f_code.co_name,
                    "line": frame.f_lineno,
                }
            frame = frame.f_back
    finally:
        del frame
    raise ValueError("Code figure save omitted its actual Source generator frame")


def save_native_figure(root: Path, path: Path, figure: Figure) -> None:
    """Keep one actual save, then its exact completed PNG and artist DATA."""
    root, path = root.absolute(), path.absolute()
    if current_analysis_write_project() != root:
        raise ValueError("Code figure capture requires its existing genuine actual analysis scope")
    if path != root / "output/figures" / path.name or path.name not in SELECTED:
        raise ValueError("Code figure save is outside its actual six selected Source targets")
    producer = _producer(root, path.name)
    before = observe_figure(figure)
    with BytesIO() as stream:
        figure.savefig(stream, format="png", **SAVE)
        content = stream.getvalue()
    after = observe_figure(figure)
    # Layout/tick placement may be calculated by savefig; actual scientific
    # artists and Source labels/scales must not change during the same save.
    stable = ("title", "xlabel", "ylabel", "xscale", "yscale", "lines", "bars", "images", "texts", "legend", "colorbar")
    if [{key: row[key] for key in stable} for row in before] != [{key: row[key] for key in stable} for row in after]:
        raise ValueError("Code plotted scientific payload changed during its actual PNG save")
    if not content.startswith(b"\x89PNG\r\n\x1a\n") or len(content) > 32 * 1024 * 1024:
        raise ValueError("Code actual figure save did not return its bounded PNG")
    write_analysis_bytes(root, path, content)
    returned = read_analysis_bytes(root, path)
    if returned != content:
        raise ValueError("Code figure returned PNG differs from its actual completed write")
    if any(text.get_transform() != figure.transFigure for text in figure.texts):
        raise ValueError("Code figure title uses unsupported actual Source coordinates")
    observation = {
        "producer": producer,
        "save": SAVE,
        "figure_texts": [
            {"text": text.get_text(), "position": _array(text.get_position()), "coordinate": "figure"}
            for text in figure.texts
        ],
        "png": {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        },
        "axes": after,
    }
    companion = root / "output/data" / ("native_figure_" + path.stem + ".json")
    companion.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(observation, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if len(body) > 8 * 1024 * 1024:
        raise ValueError("Code figure observed payload exceeds its existing retained-body bound")
    write_analysis_bytes(root, companion, body)
    if read_analysis_bytes(root, companion) != body:
        raise ValueError("Code figure companion changed across actual completed write/read")
