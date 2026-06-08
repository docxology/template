"""Figure generation: halftone "engravings" and grayscale newspaper charts.

A newspaper without art is a memo. This module produces two families of images,
both in the monochrome idiom of newsprint:

1. **Halftone engravings** (Pillow): procedural grayscale scenes — the harbor,
   the lighthouse, the redwoods — passed through a 45-degree halftone screen so
   they read as classic dot-screened newspaper photographs.
2. **Charts** (Matplotlib, Agg): a seven-day forecast, a tide curve and a
   Dungeness-crab landings bar chart, all styled in black-and-gray with serif
   labels so they sit naturally beside the type.

Every generator writes a deterministic PNG to ``output/figures/`` and returns
its path. :func:`generate_all` runs the standard set an edition references; it
raises on the first failure rather than emitting a broken image silently.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

INK = 12  # near-black gray level


# ---------------------------------------------------------------------------
# Halftone engraving machinery
# ---------------------------------------------------------------------------


def _vertical_gradient(w: int, h: int, top: int, bottom: int) -> Image.Image:
    """An L-mode image with a smooth vertical gradient (top→bottom gray)."""
    img = Image.new("L", (w, h))
    px = img.load()
    assert px is not None
    for y in range(h):
        v = int(top + (bottom - top) * (y / max(1, h - 1)))
        for x in range(w):
            px[x, y] = v
    return img


def _halftone(gray: Image.Image, cell: int = 5, max_radius: float | None = None) -> Image.Image:
    """Render an L-mode image as a 45-degree halftone dot screen (mode '1')."""
    gray = gray.filter(ImageFilter.GaussianBlur(0.6))
    w, h = gray.size
    src = gray.load()
    assert src is not None
    out = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(out)
    r_max = max_radius if max_radius is not None else cell * 0.80
    step = cell
    row = 0
    y = 0
    while y < h + cell:
        offset = (step // 2) if (row % 2) else 0
        x = -offset
        while x < w + cell:
            sx = min(max(int(x), 0), w - 1)
            sy = min(max(int(y), 0), h - 1)
            pixel = src[sx, sy]
            gray_level = float(pixel[0] if isinstance(pixel, tuple) else pixel)
            darkness = 1.0 - (gray_level / 255.0)
            r = darkness * r_max
            if r > 0.35:
                draw.ellipse((x - r, y - r, x + r, y + r), fill=0)
            x += step
        y += step
        row += 1
    return out


def _frame(img: Image.Image) -> Image.Image:
    """Add a thin keyline border for a printed-cut, engraving-plate feel."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle((1, 1, w - 2, h - 2), outline=0, width=1)
    draw.rectangle((4, 4, w - 5, h - 5), outline=0, width=1)
    return img


def harbor_scene(width: int = 960, height: int = 600) -> Image.Image:
    """A foggy harbor: horizon, breakwater, pilings, a distant light."""
    sky = _vertical_gradient(width, height, top=235, bottom=205)
    sea_top = int(height * 0.52)
    draw = ImageDraw.Draw(sky)
    # Sea
    draw.rectangle((0, sea_top, width, height), fill=150)
    for i in range(sea_top, height, 6):  # gentle swell banding
        shade = 150 - int(18 * math.sin(i / 14.0))
        draw.line((0, i, width, i), fill=shade)
    # Distant headland with the lighthouse
    draw.polygon(
        [(width * 0.66, sea_top), (width * 0.78, sea_top - 46), (width * 0.9, sea_top)],
        fill=95,
    )
    draw.rectangle((width * 0.77, sea_top - 78, width * 0.79, sea_top - 44), fill=40)
    draw.ellipse((width * 0.762, sea_top - 92, width * 0.802, sea_top - 72), fill=235)  # lamp glow
    # Breakwater rock pile
    draw.polygon([(0, height), (0, sea_top + 30), (width * 0.36, height)], fill=70)
    # Dock pilings in the foreground
    for k in range(7):
        x = int(width * (0.10 + k * 0.085))
        draw.rectangle((x, sea_top - 8, x + 7, height - 40), fill=45)
        draw.rectangle((x - 6, sea_top - 12, x + 13, sea_top - 6), fill=55)
    # A moored hull
    draw.polygon(
        [
            (width * 0.55, height - 90),
            (width * 0.74, height - 90),
            (width * 0.70, height - 60),
            (width * 0.59, height - 60),
        ],
        fill=60,
    )
    draw.rectangle((width * 0.585, height - 120, width * 0.6, height - 90), fill=60)  # mast
    return _frame(_halftone(sky, cell=5))


def lighthouse_scene(width: int = 720, height: int = 760) -> Image.Image:
    """Battery Point: a squat light on a rock above the surf."""
    sky = _vertical_gradient(width, height, top=238, bottom=212)
    draw = ImageDraw.Draw(sky)
    horizon = int(height * 0.62)
    draw.rectangle((0, horizon, width, height), fill=158)
    for i in range(horizon, height, 7):
        draw.line((0, i, width, i), fill=158 - int(14 * math.sin(i / 12.0)))
    # Rock island
    draw.polygon(
        [(width * 0.12, height), (width * 0.30, horizon - 18), (width * 0.70, horizon - 18), (width * 0.9, height)],
        fill=70,
    )
    # Keeper's house
    cx = width * 0.5
    draw.rectangle((cx - 78, horizon - 96, cx + 78, horizon - 18), fill=225)
    draw.polygon([(cx - 90, horizon - 96), (cx, horizon - 140), (cx + 90, horizon - 96)], fill=90)
    # Tower
    draw.rectangle((cx - 18, horizon - 188, cx + 18, horizon - 96), fill=235)
    draw.rectangle((cx - 22, horizon - 214, cx + 22, horizon - 188), fill=45)  # lantern room
    draw.polygon([(cx - 24, horizon - 214), (cx, horizon - 240), (cx + 24, horizon - 214)], fill=80)
    draw.ellipse((cx - 12, horizon - 210, cx + 12, horizon - 192), fill=245)  # light
    return _frame(_halftone(sky, cell=5))


def redwoods_scene(width: int = 720, height: int = 520) -> Image.Image:
    """Old-growth trunks dissolving into coastal fog."""
    fog = _vertical_gradient(width, height, top=245, bottom=170)
    draw = ImageDraw.Draw(fog)
    trunks = [0.08, 0.20, 0.33, 0.5, 0.63, 0.78, 0.9]
    for i, t in enumerate(trunks):
        x = int(width * t)
        w = 26 + (i % 3) * 12
        shade = 60 + (i % 4) * 18
        draw.rectangle((x, 0, x + w, height), fill=shade)
        # bark striations
        for s in range(0, height, 9):
            draw.line((x + 3, s, x + w - 3, s + 4), fill=shade - 22)
    # ground litter
    draw.rectangle((0, int(height * 0.9), width, height), fill=95)
    return _frame(_halftone(fog, cell=4))


def lily_fields_scene(width: int = 960, height: int = 600) -> Image.Image:
    """Rows of coastal bulb fields converging into morning fog."""
    sky = _vertical_gradient(width, height, top=243, bottom=214)
    draw = ImageDraw.Draw(sky)
    horizon = int(height * 0.40)
    vpx = width * 0.52  # vanishing point
    # Low hills behind the fog
    draw.polygon(
        [
            (0, horizon),
            (width * 0.3, horizon - 26),
            (width * 0.62, horizon - 10),
            (width, horizon - 30),
            (width, horizon),
            (0, horizon),
        ],
        fill=176,
    )
    # A barn and a windbreak tree on the horizon
    draw.rectangle((width * 0.14, horizon - 34, width * 0.2, horizon), fill=120)
    draw.polygon([(width * 0.135, horizon - 34), (width * 0.17, horizon - 50), (width * 0.205, horizon - 34)], fill=100)
    draw.ellipse((width * 0.74, horizon - 54, width * 0.82, horizon), fill=110)
    # Field ground (light), with dark converging furrows for strong row reading
    draw.rectangle((0, horizon, width, height), fill=186)
    n = 16
    for i in range(-n, n + 1):
        x_near = vpx + i * (width / n) * 2.0
        w_line = 1 if abs(i) > 8 else 3
        draw.line((x_near, height, vpx, horizon), fill=78, width=w_line)
    # Rows of pale blooms catching the light, as foreground bands
    for t, band in ((0.66, 5), (0.82, 8), (0.96, 12)):
        y = int(horizon + (height - horizon) * t)
        draw.line((0, y, width, y), fill=232, width=band)
    return _frame(_halftone(sky, cell=4))


def baseball_scene(width: int = 960, height: int = 600) -> Image.Image:
    """A dusk infield with a knot of players celebrating at home plate."""
    sky = _vertical_gradient(width, height, top=120, bottom=205)  # dusk, dark above
    draw = ImageDraw.Draw(sky)
    field_top = int(height * 0.5)
    draw.rectangle((0, field_top, width, height), fill=168)  # grass
    # Infield dirt arc
    draw.polygon([(width * 0.5, field_top + 6), (width * 0.16, height), (width * 0.84, height)], fill=148)
    # Base diamond (home at bottom centre)
    home = (width * 0.5, height * 0.92)
    first = (width * 0.66, height * 0.74)
    second = (width * 0.5, height * 0.6)
    third = (width * 0.34, height * 0.74)
    for b in (first, second, third):
        draw.rectangle((b[0] - 6, b[1] - 6, b[0] + 6, b[1] + 6), fill=235)
    draw.line([home, first, second, third, home], fill=210, width=2)
    # Light standards with glow
    for lx in (0.1, 0.9):
        x = width * lx
        draw.rectangle((x - 3, height * 0.08, x + 3, field_top), fill=70)
        draw.ellipse((x - 26, height * 0.05, x + 26, height * 0.13), fill=235)
    # Bleacher silhouette
    draw.polygon(
        [(0, field_top), (0, field_top - 26), (width * 0.4, field_top - 26), (width * 0.4, field_top)], fill=85
    )
    # The celebrating knot at home plate — clearer separated figures, one with
    # arms raised at the centre.
    cx, cy = home[0], home[1] - 4
    for k, dx in enumerate((-40, -24, -8, 9, 25, 41)):
        head_r = 9
        draw.ellipse((cx + dx - head_r, cy - 64, cx + dx + head_r, cy - 64 + 2 * head_r), fill=40)
        draw.polygon([(cx + dx - 12, cy - 46), (cx + dx + 12, cy - 46), (cx + dx + 8, cy), (cx + dx - 8, cy)], fill=38)
        if k == 2:  # centre figure, arms up
            draw.line((cx + dx - 10, cy - 44, cx + dx - 20, cy - 70), fill=38, width=4)
            draw.line((cx + dx + 10, cy - 44, cx + dx + 20, cy - 70), fill=38, width=4)
    return _frame(_halftone(sky, cell=5))


def crab_boat_scene(width: int = 960, height: int = 600) -> Image.Image:
    """A crab boat stacked with pots, running for the harbor on flat water."""
    sky = _vertical_gradient(width, height, top=224, bottom=196)
    draw = ImageDraw.Draw(sky)
    sea_top = int(height * 0.56)
    draw.rectangle((0, sea_top, width, height), fill=158)
    for i in range(sea_top, height, 6):
        draw.line((0, i, width, i), fill=158 - int(12 * math.sin(i / 13.0)))
    # Distant breakwater
    draw.rectangle((0, sea_top - 6, width * 0.3, sea_top + 4), fill=120)
    # Hull
    hx0, hx1 = width * 0.28, width * 0.82
    hy = sea_top + 30
    draw.polygon([(hx0, hy), (hx1, hy), (hx1 - 26, hy + 46), (hx0 + 16, hy + 46)], fill=55)
    # Cabin
    draw.rectangle((hx0 + 24, hy - 40, hx0 + 92, hy), fill=80)
    draw.rectangle((hx0 + 34, hy - 32, hx0 + 60, hy - 12), fill=210)  # window
    # Mast + rigging
    draw.rectangle((hx0 + 56, hy - 96, hx0 + 60, hy - 40), fill=60)
    draw.line((hx0 + 58, hy - 96, hx1 - 30, hy), fill=70)
    # Stack of crab pots (grid of squares) on the afterdeck
    px0, py0 = hx0 + 104, hy - 30
    for r in range(2):
        for c in range(5):
            x = px0 + c * 26
            y = py0 + r * 16
            draw.rectangle((x, y, x + 22, y + 14), outline=40, fill=150, width=2)
            draw.line((x + 11, y, x + 11, y + 14), fill=60)
    # A fisherman silhouette
    fx = hx0 + 92
    draw.ellipse((fx - 6, hy - 56, fx + 6, hy - 44), fill=45)
    draw.polygon([(fx - 7, hy - 44), (fx + 7, hy - 44), (fx + 5, hy - 14), (fx - 5, hy - 14)], fill=40)
    # Gulls
    for gx, gy in ((width * 0.2, height * 0.2), (width * 0.26, height * 0.26), (width * 0.6, height * 0.16)):
        draw.line((gx - 7, gy, gx, gy - 5), fill=60)
        draw.line((gx, gy - 5, gx + 7, gy), fill=60)
    return _frame(_halftone(sky, cell=5))


# ---------------------------------------------------------------------------
# Color graphics (for display advertising — demonstrates color-image support)
# ---------------------------------------------------------------------------


def ad_bakery_logo(size: int = 380) -> Image.Image:
    """A warm color badge for a bakery display ad (sun over a loaf)."""
    img = Image.new("RGB", (size, size), "#F6E7C7")
    d = ImageDraw.Draw(img)
    cx, cy = size / 2, size * 0.40
    for a in range(0, 360, 24):  # sun rays
        rad = math.radians(a)
        d.line((cx, cy, cx + math.cos(rad) * size * 0.30, cy + math.sin(rad) * size * 0.30), fill="#E59A2B", width=6)
    d.ellipse((cx - size * 0.16, cy - size * 0.16, cx + size * 0.16, cy + size * 0.16), fill="#F2B441")
    # loaf
    ly = size * 0.72
    d.rounded_rectangle(
        (size * 0.22, ly - size * 0.13, size * 0.78, ly + size * 0.10), radius=size * 0.11, fill="#9C5A2A"
    )
    for sx in (0.36, 0.5, 0.64):  # scoring
        d.line((size * sx, ly - size * 0.12, size * (sx + 0.04), ly + size * 0.06), fill="#6E3C18", width=5)
    d.rectangle((6, 6, size - 7, size - 7), outline="#6E3C18", width=5)
    return img


def ad_realty_logo(size: int = 380) -> Image.Image:
    """A navy/teal badge for a real-estate ad (a house over waves)."""
    img = Image.new("RGB", (size, size), "#E9EFF3")
    d = ImageDraw.Draw(img)
    # house
    d.polygon([(size * 0.5, size * 0.16), (size * 0.18, size * 0.44), (size * 0.82, size * 0.44)], fill="#2E8B8B")
    d.rectangle((size * 0.27, size * 0.44, size * 0.73, size * 0.70), fill="#1F3A5F")
    d.rectangle((size * 0.44, size * 0.52, size * 0.56, size * 0.70), fill="#E9EFF3")  # door
    # waves
    for i, y in enumerate((0.80, 0.88)):
        pts = []
        for x in range(0, size + 20, 20):
            pts.append((x, size * y + (10 if (x // 20) % 2 else -10)))
        d.line(pts, fill="#2E8B8B" if i == 0 else "#1F3A5F", width=6, joint="curve")
    d.rectangle((6, 6, size - 7, size - 7), outline="#1F3A5F", width=5)
    return img


def ad_grocery_logo(size: int = 380) -> Image.Image:
    """A fresh green/orange badge for a market ad (produce basket)."""
    img = Image.new("RGB", (size, size), "#EAF3E4")
    d = ImageDraw.Draw(img)
    # basket
    d.polygon(
        [
            (size * 0.22, size * 0.52),
            (size * 0.78, size * 0.52),
            (size * 0.70, size * 0.84),
            (size * 0.30, size * 0.84),
        ],
        fill="#8B5A2B",
    )
    # produce
    d.ellipse((size * 0.30, size * 0.34, size * 0.46, size * 0.56), fill="#E2722E")  # orange
    d.ellipse((size * 0.46, size * 0.30, size * 0.62, size * 0.54), fill="#C0392B")  # apple
    d.ellipse((size * 0.58, size * 0.36, size * 0.72, size * 0.56), fill="#3E8E41")  # green
    d.line((size * 0.54, size * 0.30, size * 0.56, size * 0.22), fill="#3E8E41", width=5)  # stem
    d.rectangle((6, 6, size - 7, size - 7), outline="#3E6E34", width=5)
    return img


def ad_festival_banner(width: int = 720, height: int = 240) -> Image.Image:
    """A vibrant color banner for a community festival ad (sun, sea, bunting)."""
    img = Image.new("RGB", (width, height), "#7FB7D6")
    d = ImageDraw.Draw(img)
    # sky to sea
    d.rectangle((0, int(height * 0.62), width, height), fill="#2E8B8B")
    for i in range(int(height * 0.62), height, 8):
        d.line((0, i, width, i), fill="#247373" if (i // 8) % 2 else "#2E8B8B")
    # sun
    sx, sy = width * 0.82, height * 0.32
    for a in range(0, 360, 30):
        rad = math.radians(a)
        d.line((sx, sy, sx + math.cos(rad) * 56, sy + math.sin(rad) * 56), fill="#F2C53D", width=6)
    d.ellipse((sx - 34, sy - 34, sx + 34, sy + 34), fill="#F4D35E")
    # bunting
    colors = ["#E2722E", "#C0392B", "#F2C53D", "#3E8E41", "#1F6F8B"]
    n = 12
    for k in range(n):
        x0 = k * (width / n)
        x1 = (k + 1) * (width / n)
        d.polygon([(x0, 8), (x1, 8), ((x0 + x1) / 2, 44)], fill=colors[k % len(colors)])
    # a sailboat
    bx, by = width * 0.2, height * 0.74
    d.polygon([(bx, by), (bx + 70, by), (bx + 56, by + 22), (bx + 14, by + 22)], fill="#F6E7C7")
    d.polygon([(bx + 34, by - 50), (bx + 34, by), (bx + 4, by)], fill="#FFFFFF")
    d.polygon([(bx + 40, by - 50), (bx + 40, by), (bx + 70, by)], fill="#E9EFF3")
    return img


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------


def _newsprint_axes(ax: "plt.Axes") -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("0.15")
        ax.spines[spine].set_linewidth(0.8)
    ax.tick_params(colors="0.15", labelsize=8)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontfamily("serif")


def weather_chart(path: Path) -> Path:
    """Write the 7-day high/low forecast chart to ``path``; return ``path``."""
    days = ["Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue"]
    highs = [59, 61, 60, 63, 65, 62, 60]
    lows = [48, 49, 47, 50, 52, 51, 49]
    fig, ax = plt.subplots(figsize=(3.4, 2.0), dpi=300)
    ax.fill_between(days, lows, highs, color="0.82", zorder=1)
    ax.plot(days, highs, color="0.10", lw=1.6, marker="o", ms=3, zorder=3, label="High")
    ax.plot(days, lows, color="0.45", lw=1.4, marker="o", ms=3, ls="--", zorder=3, label="Low")
    for x, hi, lo in zip(range(len(days)), highs, lows):
        ax.annotate(
            f"{hi}°",
            (x, hi),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=7,
            family="serif",
            color="0.1",
        )
        ax.annotate(
            f"{lo}°",
            (x, lo),
            textcoords="offset points",
            xytext=(0, -10),
            ha="center",
            fontsize=7,
            family="serif",
            color="0.35",
        )
    ax.set_ylim(40, 72)
    ax.set_yticks([45, 55, 65])
    _newsprint_axes(ax)
    ax.legend(frameon=False, fontsize=7, loc="upper left", prop={"family": "serif"})
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def tide_chart(path: Path) -> Path:
    """Write the 24-hour mixed-semidiurnal tide curve to ``path``; return ``path``."""
    hours = [h / 2 for h in range(0, 49)]
    # Mixed semidiurnal tide typical of the North Coast.
    tide = [3.6 + 2.7 * math.sin((h / 6.2 + 0.6) * math.pi) + 0.9 * math.sin((h / 3.05) * math.pi) for h in hours]
    fig, ax = plt.subplots(figsize=(3.4, 1.8), dpi=300)
    ax.fill_between(hours, [min(tide) - 0.5] * len(hours), tide, color="0.85", zorder=1)
    ax.plot(hours, tide, color="0.10", lw=1.4, zorder=3)
    ax.set_xlim(0, 24)
    ax.set_xticks([0, 6, 12, 18, 24])
    ax.set_xticklabels(["12a", "6a", "12p", "6p", "12a"])
    ax.set_ylabel("feet", fontsize=8, family="serif", color="0.15")
    _newsprint_axes(ax)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def crab_landings_chart(path: Path) -> Path:
    """Write the monthly Dungeness-crab landings bar chart to ``path``; return ``path``."""
    months = ["Dec", "Jan", "Feb", "Mar", "Apr", "May"]
    pounds = [410, 980, 1240, 760, 540, 305]  # thousands of lbs
    fig, ax = plt.subplots(figsize=(3.4, 2.1), dpi=300)
    bars = ax.bar(months, pounds, color="0.30", edgecolor="0.05", width=0.66)
    bars[2].set_color("0.08")  # peak month
    for b, v in zip(bars, pounds):
        ax.annotate(
            f"{v}",
            (b.get_x() + b.get_width() / 2, v),
            textcoords="offset points",
            xytext=(0, 3),
            ha="center",
            fontsize=7,
            family="serif",
            color="0.1",
        )
    ax.set_ylabel("1,000 lbs landed", fontsize=8, family="serif", color="0.15")
    ax.set_ylim(0, 1400)
    _newsprint_axes(ax)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_SCENES: dict[str, Callable[..., Image.Image]] = {
    "harbor.png": harbor_scene,
    "lighthouse.png": lighthouse_scene,
    "redwoods.png": redwoods_scene,
    "lily_fields.png": lily_fields_scene,
    "baseball.png": baseball_scene,
    "crab_boat.png": crab_boat_scene,
}
_CHARTS = {
    "weather_7day.png": weather_chart,
    "tides.png": tide_chart,
    "crab_landings.png": crab_landings_chart,
}

# Color graphics for display advertising (RGB, not halftoned).
_COLOR_GRAPHICS: dict[str, Callable[..., Image.Image]] = {
    "ad_bakery.png": ad_bakery_logo,
    "ad_realty.png": ad_realty_logo,
    "ad_grocery.png": ad_grocery_logo,
    "ad_festival.png": ad_festival_banner,
}


def generate_all(output_dir: Path | str) -> list[Path]:
    """Generate the standard figure set into ``output_dir``; return the paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, builder in {**_SCENES, **_COLOR_GRAPHICS}.items():
        img = builder()
        dest = out / name
        img.save(dest)
        written.append(dest)
    for name, chart in _CHARTS.items():
        chart(out / name)
        written.append(out / name)
    return written


__all__ = [
    "harbor_scene",
    "lighthouse_scene",
    "redwoods_scene",
    "lily_fields_scene",
    "baseball_scene",
    "crab_boat_scene",
    "ad_bakery_logo",
    "ad_realty_logo",
    "ad_grocery_logo",
    "ad_festival_banner",
    "weather_chart",
    "tide_chart",
    "crab_landings_chart",
    "generate_all",
]
