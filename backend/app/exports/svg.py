from __future__ import annotations

from html import escape


PIECE_COLORS = {
    "front": "#d8a454",
    "back": "#76d8c4",
    "sleeve": "#c9d7ee",
    "neckband": "#ef8f7a",
}

DEFAULT_APPEARANCE = {
    "base_color": "#d8a454",
    "accent_color": "#1f6f68",
    "motif": "none",
    "scale": 8,
    "angle": 0,
    "opacity": 0.38,
}


def layout_pattern(pattern: dict, spacing: float = 18) -> list[tuple[dict, float, float]]:
    cursor = 0.0
    placed = []
    for piece in pattern["pieces"]:
        box = piece["bbox"]
        x_offset = cursor - box["min_x"]
        y_offset = -box["min_y"]
        placed.append((piece, x_offset, y_offset))
        cursor = x_offset + box["max_x"] + spacing
    return placed


def points_to_polyline(points: list[list[float]], x_offset: float = 0, y_offset: float = 0) -> str:
    return " ".join(f"{x + x_offset:.3f},{y + y_offset:.3f}" for x, y in points)


def export_svg(pattern: dict, appearance: dict | None = None) -> str:
    return export_svg_bundle([pattern], appearance)


def export_svg_bundle(patterns: list[dict], appearance: dict | None = None) -> str:
    textile = _appearance(appearance)
    layouts = []
    y_cursor = 0.0
    max_width = 160.0
    for pattern in patterns:
        placed = layout_pattern(pattern)
        row_height = max((piece["bbox"]["max_y"] + y for piece, _, y in placed), default=120)
        row_width = max((piece["bbox"]["max_x"] + x for piece, x, _ in placed), default=160)
        layouts.append((pattern, placed, y_cursor))
        max_width = max(max_width, row_width + 16)
        y_cursor += row_height + 28

    height = max(y_cursor, 120) + 8
    label = " / ".join(escape(pattern["size"]) for pattern in patterns)
    rows = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 {max_width:.3f} {height:.3f}">',
        "<defs>",
        _textile_pattern_def(textile),
        "<style>",
        "text{font-family:Aptos,Helvetica,Arial,sans-serif}.fabric{stroke:none}.stitch{fill:none;stroke-width:.45}.cut{fill:none;stroke:#f6f0e4;stroke-width:.35;stroke-dasharray:2 1}.grain{stroke:#a9b7aa;stroke-width:.28;stroke-dasharray:1.5 1.5}.notch{fill:none;stroke:#ff6f59;stroke-width:.35}.measure{stroke:#8fa1b5;stroke-width:.25;stroke-dasharray:1 1}.label{fill:#f2eadf;font-size:3.8px;font-weight:700;letter-spacing:.08em}.meta{fill:#b7c0c9;font-size:2.8px}",
        "</style>",
        "</defs>",
        f'<rect x="-8" y="-8" width="{max_width:.3f}" height="{height:.3f}" fill="#111417"/>',
        f'<text class="meta" x="0" y="-2">AtelierCAD Patron T-shirt | Taille {label} | unité cm</text>',
    ]
    for pattern, placed, y_origin in layouts:
        size = escape(pattern["size"])
        rows.append(f'<text class="meta" x="0" y="{y_origin + 5:.3f}">TAILLE {size}</text>')
        for piece, x, y in placed:
            y += y_origin + 8
            color = PIECE_COLORS.get(piece["id"], "#d8a454")
            d = _offset_path_d(piece["stitchPath"], x, y)
            fill = textile["base_color"] if textile["motif"] == "none" else "url(#fabric-motif)"
            fill_opacity = max(0.12, textile["opacity"] * 0.72) if textile["motif"] == "none" else 1
            rows.append(f'<polygon class="fabric" points="{points_to_polyline(piece["cutPoints"], x, y)}" fill="{fill}" opacity="{fill_opacity:.3f}"/>')
            rows.append(f'<path class="stitch" d="{d}" stroke="{color}"/>')
            rows.append(f'<polyline class="cut" points="{points_to_polyline(piece["cutPoints"], x, y)}"/>')
            grain = piece["grainline"]
            rows.append(
                f'<line class="grain" x1="{grain["start"][0] + x:.3f}" y1="{grain["start"][1] + y:.3f}" '
                f'x2="{grain["end"][0] + x:.3f}" y2="{grain["end"][1] + y:.3f}"/>'
            )
            for notch in piece["notches"]:
                nx, ny = notch["point"][0] + x, notch["point"][1] + y
                rows.append(f'<path class="notch" d="M {nx - 1:.3f} {ny:.3f} L {nx:.3f} {ny - 1.6:.3f} L {nx + 1:.3f} {ny:.3f}"/>')
            for measurement in piece["measurements"]:
                sx, sy = measurement["start"][0] + x, measurement["start"][1] + y
                ex, ey = measurement["end"][0] + x, measurement["end"][1] + y
                lx, ly = (sx + ex) / 2, (sy + ey) / 2
                rows.append(f'<line class="measure" x1="{sx:.3f}" y1="{sy:.3f}" x2="{ex:.3f}" y2="{ey:.3f}"/>')
                rows.append(f'<text class="meta" x="{lx:.3f}" y="{ly - 1:.3f}" text-anchor="middle">{escape(measurement["label"])} {measurement["value"]:.2f}cm</text>')
            lx, ly = piece["labelPoint"][0] + x, piece["labelPoint"][1] + y
            rows.append(f'<text class="label" x="{lx:.3f}" y="{ly:.3f}" text-anchor="middle">{escape(piece["name"])} {size}</text>')
    rows.append("</svg>")
    return "\n".join(rows)


def _appearance(appearance: dict | None) -> dict:
    merged = {**DEFAULT_APPEARANCE, **(appearance or {})}
    return {
        "base_color": _hex(merged["base_color"], DEFAULT_APPEARANCE["base_color"]),
        "accent_color": _hex(merged["accent_color"], DEFAULT_APPEARANCE["accent_color"]),
        "motif": merged["motif"] if merged["motif"] in {"none", "stripes", "checks", "dots", "rib", "heather"} else "none",
        "scale": min(24, max(2, float(merged["scale"]))),
        "angle": min(90, max(-90, float(merged["angle"]))),
        "opacity": min(0.85, max(0.1, float(merged["opacity"]))),
    }


def _hex(value: str, fallback: str) -> str:
    value = str(value)
    if len(value) == 7 and value.startswith("#") and all(char in "0123456789abcdefABCDEF" for char in value[1:]):
        return value
    return fallback


def _textile_pattern_def(appearance: dict) -> str:
    if appearance["motif"] == "none":
        return ""
    scale = appearance["scale"]
    base_opacity = max(0.12, appearance["opacity"] * 0.35)
    motif_opacity = max(0.08, appearance["opacity"])
    base = escape(appearance["base_color"])
    accent = escape(appearance["accent_color"])
    rows = [
        f'<pattern id="fabric-motif" patternUnits="userSpaceOnUse" width="{scale:.3f}" height="{scale:.3f}" patternTransform="rotate({appearance["angle"]:.3f})">',
        f'<rect width="{scale:.3f}" height="{scale:.3f}" fill="{base}" opacity="{base_opacity:.3f}"/>',
    ]
    if appearance["motif"] == "stripes":
        rows.append(f'<rect width="{max(0.7, scale * 0.28):.3f}" height="{scale:.3f}" fill="{accent}" opacity="{motif_opacity:.3f}"/>')
    elif appearance["motif"] == "checks":
        stripe = max(0.7, scale * 0.22)
        rows.append(f'<rect width="{stripe:.3f}" height="{scale:.3f}" fill="{accent}" opacity="{motif_opacity:.3f}"/>')
        rows.append(f'<rect width="{scale:.3f}" height="{stripe:.3f}" fill="{accent}" opacity="{motif_opacity * 0.82:.3f}"/>')
    elif appearance["motif"] == "dots":
        rows.append(f'<circle cx="{scale / 2:.3f}" cy="{scale / 2:.3f}" r="{max(0.6, scale * 0.18):.3f}" fill="{accent}" opacity="{motif_opacity:.3f}"/>')
    elif appearance["motif"] == "rib":
        rows.append(f'<rect x="{scale * 0.18:.3f}" width="{max(0.35, scale * 0.08):.3f}" height="{scale:.3f}" fill="{accent}" opacity="{motif_opacity:.3f}"/>')
        rows.append(f'<rect x="{scale * 0.58:.3f}" width="{max(0.35, scale * 0.05):.3f}" height="{scale:.3f}" fill="{accent}" opacity="{motif_opacity * 0.55:.3f}"/>')
    elif appearance["motif"] == "heather":
        rows.append(f'<path d="M 0 {scale * 0.25:.3f} L {scale:.3f} 0" stroke="{accent}" stroke-width="{max(0.25, scale * 0.045):.3f}" opacity="{motif_opacity * 0.55:.3f}"/>')
        rows.append(f'<path d="M 0 {scale * 0.8:.3f} L {scale:.3f} {scale * 0.2:.3f}" stroke="{accent}" stroke-width="{max(0.18, scale * 0.032):.3f}" opacity="{motif_opacity * 0.34:.3f}"/>')
    rows.append("</pattern>")
    return "".join(rows)


def _offset_path_d(d: str, x_offset: float, y_offset: float) -> str:
    tokens = d.split()
    out: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"M", "L"}:
            x = float(tokens[index + 1]) + x_offset
            y = float(tokens[index + 2]) + y_offset
            out.extend([token, f"{x:.3f}", f"{y:.3f}"])
            index += 3
        elif token == "C":
            values = [float(tokens[index + i]) for i in range(1, 7)]
            values = [
                values[0] + x_offset,
                values[1] + y_offset,
                values[2] + x_offset,
                values[3] + y_offset,
                values[4] + x_offset,
                values[5] + y_offset,
            ]
            out.extend(["C", *(f"{value:.3f}" for value in values)])
            index += 7
        elif token == "Z":
            out.append("Z")
            index += 1
        else:
            index += 1
    return " ".join(out)
